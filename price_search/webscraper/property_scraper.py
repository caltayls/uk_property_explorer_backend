import pandas as pd
import numpy as np
import asyncio
from bs4 import BeautifulSoup
import json
import aiohttp 
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options



import os
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rightmove_app.settings')
django.setup()
from price_search.models import RightmoveLocationCodes


region_codes = {
    'London': r'locationIdentifier=REGION%5E87490',
    'Manchester': r'locationIdentifier=REGION%5E904',
    'Birmingham': r'locationIdentifier=REGION%5E162',
    'Leeds': r'locationIdentifier=REGION%5E787',
    'Portsmouth': r'locationIdentifier=REGION%5E1089',
    'Newcastle': r'locationIdentifier=REGION%5E984',
    'Sheffield': r'locationIdentifier=REGION%5E1195',
    'Middlesbrough': r'locationIdentifier=REGION%5E933',
    'Leicester': r'locationIdentifier=REGION%5E789',
}

class PropertyScraper:
    """Scrapes rightmove data and formats it into a pd.DateFrame. 
    """
   
    def __init__(self, for_sale=True):

        self.scrape_type = None
        self.postcode_list = None
        self.for_sale = for_sale
        self.location_codes = None
        self.prop_array = []
        self._df = pd.DataFrame()

    
    async def async_pc_scrape(self, headless=True):
        """async scrape of same postcode"""
        pc_tasks = []
        pc_sem = asyncio.Semaphore(2)
        for postcode in self.postcode_list:
            task = asyncio.create_task(self.scrape(postcode, pc_sem))
            pc_tasks.append(task)
        await asyncio.gather(*pc_tasks)
        self._df = pd.DataFrame(self.prop_array)
    
    def get_search_filters(self, post_data): 
        search_filters = {
            'dontShow': '&dontShow=retirement%2CsharedOwnership',
            'numOfProps': '&numberOfPropertiesPerPage=100',
            'sortType': '&sortType=6',
            'mustHave': f'&mustHave={"".join(f"{key}%2C" for key, value in post_data["mustHave"].items() if value)}'.strip('%2C'),
        }

        if post_data['searchType'] == 'price':
            price = int(post_data["price"])
            search_filters['price'] = f'&maxPrice={price+5000}&minPrice={price-5000}'
            return search_filters
        search_filters['propertyType'] = f'&propertyTypes={post_data["propertyType"].lower()}'
        search_filters['numOfBedrooms'] = f'&maxBedrooms={post_data["numOfBedrooms"]}&minBedrooms={post_data["numOfBedrooms"]}'
        return search_filters

    async def search(self, post_data, location_codes):
        """A method to explore what a specific budget is able to buy across England."""
        self.location_codes = location_codes
        search_filters = self.get_search_filters(post_data)
        tasks = []
        pc_sem = asyncio.Semaphore(2)
        for city, location_code in self.location_codes.items():
            location_code = f'locationIdentifier={location_code}'
            url = rf"https://www.rightmove.co.uk/property-for-sale/find.html?{location_code}{''.join(filter for filter in search_filters.values())}"
            url = url + f"&radius=0"
            task = asyncio.create_task(self.scrape(city, url))
            tasks.append(task) 
        await asyncio.gather(*tasks)
        return self._df.reset_index(drop=True)

  
    async def code_unknown_scrape(self, location, pc_sem, headless=False,):

        async with pc_sem:
            options = Options()
            if headless:
                options.add_argument("--headless=new")     
            service = Service(r"C:\ChromeDriver\chromedriver.exe")
            with webdriver.Chrome(service= service, options=options) as driver:   
                initial_url = r"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E1712&numberOfPropertiesPerPage=100"
                driver.get(initial_url)
                element = driver.find_element(By.XPATH, '//*[@id="filters-location"]//input')
                element.send_keys(Keys.CONTROL + 'a')
                element.send_keys(location)
                element.send_keys(Keys.ENTER)
                url_base = driver.current_url
                content =  driver.page_source

            soup = BeautifulSoup(content, 'html.parser')
            result_count = int(soup.select_one('.searchHeader-resultCount').text)
        print(result_count)
        return url_base, result_count
   

    async def scrape(self, city, url):
        tasks = []

        print(city)
        sem = asyncio.Semaphore(2)
        async with aiohttp.ClientSession() as session:
            task = asyncio.create_task(self.parse_data(url, session, sem, city))
            tasks.append(task)
            await asyncio.gather(*tasks)
            await asyncio.sleep(2)


    async def parse_data(self, url, session, sem, city):
        async with session.get(url) as response:
            async with sem:
                content = await response.text()
        soup = BeautifulSoup(content, 'html.parser')
        scripts = soup.select("script")
        # Array element 5 works at time of testing. however, 11 worked prior. keep eye on this.
        script_inner_html = scripts[5].text
        trimmed_str = script_inner_html.strip('window.jsonModel = ')
        prop_dict = json.loads(trimmed_str)
        prop_info_array = prop_dict['properties']
        prop_df = pd.DataFrame(prop_info_array)
        prop_df['city'] = city
        
        self._df = pd.concat((self._df, prop_df))
        
        await asyncio.sleep(2)
    
    @staticmethod
    def run_search(post_data, region_code_dict):
        loop = asyncio.get_event_loop()
        return  loop.run_until_complete(PropertyScraper().search(post_data=post_data, region_codes=region_code_dict))


 

def get_region_code_dict(post_data):
    if post_data['whatToSearch'] == 'Major towns and cities within a region':
        with open('data/regions-major-towns-cities.json', 'r') as f:
            regions_towns = json.load(f)
        region = post_data['region']
        town_array = regions_towns[region]
        records = RightmoveLocationCodes.objects.filter(location__in=town_array, subDivType='TOWN/CITY')
    elif post_data['whatToSearch'] == 'London Boroughs':
        with open('data/region_lad_relationships.json', 'r') as f:
            regions_lads = json.load(f)
        borough_array = regions_lads['London']
        records = RightmoveLocationCodes.objects.filter(location__in=borough_array, subDivType='LAD')
    
    region_dict = {record.location: record.locationIdentifier for record in records}
    return region_dict         

    
if __name__ == '__main__':

    get_region_code_dict('North West')
    # post_data = {
    #     'mustHave': {'garden': True, 'newHome': False, 'parking': False, 'retirementHome': False},
    #     'numOfBedrooms': 2,
    #     'propertyType': "Semi-detached",
    #     'searchType': "features"
    # }

    # search = PropertyScraper.run_search(post_data)

    # search
