import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import json

import time
import re

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




def get_location_id(location_array, subDivType, headless=False, ):

    options = Options()
    if headless:
        options.add_argument("--headless=new")     
    service = Service(r"C:\ChromeDriver\chromedriver.exe")
    driver = webdriver.Chrome(service= service, options=options)
    driver.implicitly_wait(10)
    initial_url = r"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E1712&numberOfPropertiesPerPage=100"
    driver.get(initial_url)
    cookies_handler = driver.find_element(By.CSS_SELECTOR, '#onetrust-reject-all-handler')
    cookies_handler.click()
    for i, location in enumerate(location_array):  
        location_code, result_count = scrape_loc_id(driver, location)
        print(f"{i}. {location}, {location_code}: {result_count}")
        RightmoveLocationCodes(location=location, subDivType=subDivType, locationIdentifier=location_code, resultCount=result_count).save()
        
    driver.close()

           

def scrape_loc_id(driver, location):
    time.sleep(0.5)
    element = driver.find_element(By.XPATH, '//*[@id="filters-location"]//input')
    element.send_keys(Keys.CONTROL + 'a')
    element.send_keys(location)
    try:
        search_option = driver.find_elements(By.CSS_SELECTOR, 'li.autocomplete-suggestion')[0]
        time.sleep(0.5)
        search_option.click()
        time.sleep(0.5)
        url = driver.current_url
        location_code = re.search(r'locationIdentifier=(\w+%\w+)&', url).group(1) 
        result_count = driver.find_element(By.CSS_SELECTOR, '.searchHeader-resultCount').text
        if result_count:
            result_count = int(result_count.replace(',', ''))
        else:
            result_count = None
        
        return location_code, result_count
    except:
        return None, None
       


if __name__ == '__main__':

    


    stations = RightmoveLocationCodes.objects.filter(locationIdentifier__icontains='STATION', subDivType='TOWN/CITY')

    # Update nulls manually:
    for station in stations:
        print(station.location)
        print("enter code:")
        code = input()
        print("enter result count")
        count = input()
        station.locationIdentifier = code
        station.resultCount = count
        station.save()
        print(f"{station.location} complete")
        print("===============")    
    



    ## For LAD codes
    # df = pd.read_csv(r"C:\Users\callu\OneDrive\Documents\coding\rightmove_app\react_frontend\rightmove_app - Copy\src\assets\geo_data\subdivision_names\Ward_to_Local_Authority_District_to_County_to_Region_to_Country_(May_2023)_Lookup_in_United_Kingdom.csv")
    # lad_array = df['LAD23NM'].unique()
    # loc_code_array, last_idx = get_location_id(lad_array, 'LAD')

    # # For MSOA codes
    # msoa_df = pd.read_csv(r"C:\Users\callu\OneDrive\Documents\coding\rightmove_app\react_frontend\rightmove_app - Copy\src\assets\geo_data\subdivision_names\MSOA_codes_names.csv")
    # msoa_array = msoa_df['msoa21hclnm']
    # len(msoa_array.unique())
    # len(msoa_array)

    # get_location_id(msoa_array, 'TC')
    








"""
Duplicate locIDS
id	location	locationIdentifier	subDivType	resultCount
id	location	locationIdentifier	subDivType	resultCount
329	Rotherham	REGION%5E1145	LAD	1108
492	Rother	REGION%5E1145	LAD	1106 -------- doesnt show - remove
484	Wealden	REGION%5E1217	LAD	941
483	Slough	REGION%5E1217	LAD	941
496	Wokingham	REGION%5E1475	LAD	489
527	Woking	REGION%5E1475	LAD	489
420	Brentwood	REGION%5E207	LAD	813
448	Brent	REGION%5E207	LAD	813
480	Milton Keynes	REGION%5E26159	LAD	32
479	West Berkshire	REGION%5E26159	LAD	32
481	Brighton and Hove	REGION%5E26159	LAD	32
482	Portsmouth	REGION%5E26159	LAD	32
272	Hartlepool	REGION%5E601	LAD	607
513	Hart	REGION%5E601	LAD	609
476	Tower Hamlets	REGION%5E61278	LAD	1171
475	Bracknell Forest	REGION%5E61278	LAD	1171
383	Stafford	REGION%5E82665	LAD	775
375	Staffordshire Moorlands	REGION%5E82665	LAD	775
"""