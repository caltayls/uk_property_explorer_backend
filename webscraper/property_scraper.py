import pandas as pd
import numpy as np
import asyncio
from bs4 import BeautifulSoup
import json
import aiohttp 

import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


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
        """
        Initialise the class.
        
        Parameters
        ----------
        postcode : string
            The postcode of the desired location.
        for_sale : bool
            If True, searches properties for sale;
            If False, searches properties for rent.
        
        """
        self.scrape_type = None
        self.postcode_list = None
        self.for_sale = for_sale
        self.region_codes = None
        self.prop_array = []
        self._df = pd.DataFrame()

    
    # @property
    # def df(self):
    #     """
    #     Return formatted df.
    #     """
    #     self._format_data()
    #     return self._df
    
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
            'radius': f'&radius=3',
            'numOfProps': '&numberOfPropertiesPerPage=100',
            'sortType': '&sortType=6',
            'mustHave': f'&mustHave={"".join(f"{key}%2C" for key, value in post_data["mustHave"].items() if value)}'.strip('%2C'),
        }

        if post_data['searchType'] == 'price':
            search_filters['price'] = f'&maxPrice={post_data["price"]+5000}&minPrice={post_data["price"]-5000}'
            return search_filters
        search_filters['propertyType'] = f'&propertyTypes={post_data["propertyType"].lower()}'
        search_filters['numOfBedrooms'] = f'&maxBedrooms={post_data["numOfBedrooms"]}&minBedrooms={post_data["numOfBedrooms"]}'
        return search_filters

    async def price_search(self, post_data, search_radius: int=3, region_codes: dict=region_codes):
        """A method to explore what a specific budget is able to buy across England."""
        self.scrape_type = 'multi'
        self.region_codes = region_codes
        search_filters = self.get_search_filters(post_data)
        tasks = []
        pc_sem = asyncio.Semaphore(2)
        for city, region_code in self.region_codes.items():
            url = rf"https://www.rightmove.co.uk/property-for-sale/find.html?{region_code}{''.join(filter for filter in search_filters.values())}"
            task = asyncio.create_task(self.scrape(city, url, pc_sem))
            tasks.append(task) 
        await asyncio.gather(*tasks)
        return self._df.reset_index(drop=True)

  
    async def start_scrape(self, postcode, pc_sem, headless=False,):
        """
        Uses a webdriver to retrieve first page url. 
        Finds base url and result count.
        Used for searching by postcode
        """
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
                element.send_keys(postcode)
                element.send_keys(Keys.ENTER)
                url_base = driver.current_url
                content =  driver.page_source

            soup = BeautifulSoup(content, 'html.parser')
            result_count = int(soup.select_one('.searchHeader-resultCount').text)
        print(result_count)
        return url_base, result_count
   

    async def scrape(self, city, url, pc_sem):
        tasks = []
        # if self.scrape_type == 'singular':
        #     url_base, result_count = await self.start_scrape(postcode, pc_sem)
        #     sem = asyncio.Semaphore(2)
        #     async with aiohttp.ClientSession() as session:
        #         for i in range(0, result_count, 100):
        #             url_ext = f'&index={i}'
        #             url = url_base + url_ext
        #             task = asyncio.create_task(self.parse_data(url, session, sem))
        #             tasks.append(task)
        #         await asyncio.gather(*tasks)
        
        if self.scrape_type == 'multi':
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
        if self.scrape_type == 'multi':
            prop_df['city'] = city
        
        self._df = pd.concat((self._df, prop_df))
        
        await asyncio.sleep(2)
    
    @staticmethod
    def run_price_search(post_data, radius=3,):
        loop = asyncio.get_event_loop()
        return  loop.run_until_complete(PropertyScraper().price_search(post_data=post_data, search_radius=radius))


 

            

    
if __name__ == '__main__':

    post_data = {
        'searchType': 'features',
        'mustHave': {'garden': True, 'newHome': False, 'parking': False, 'retirementHome': False},
        'numOfBedrooms': '2', 
        'propertyType': 'Terraced'
        }
    df = PropertyScraper.run_price_search(post_data)
    df = df.reset_index(drop=True)
    
    df_dict = df.to_dict(orient='records')
    df_dict[0]    
