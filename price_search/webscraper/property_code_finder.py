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




def get_location_id(location_array, headless=False,):
    location_code_array = []
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
    last_loc_idx = 0
    for i, location in enumerate(location_array):  
        location_code = scrape_loc_id(driver, location)
        # RightmoveLocationCodes(location=location, subDivType='LAD', locationIdentifier=location_code).save()
        location_code_array.append({location: location_code})
        last_loc_idx = i
    driver.close()
    return location_code_array, last_loc_idx
            #  RightmoveLocationCodes(location=location, locationIdentifier=location_code).save()

def scrape_loc_id(driver, location):
    time.sleep(0.5)
    element = driver.find_element(By.XPATH, '//*[@id="filters-location"]//input')
    element.send_keys(Keys.CONTROL + 'a')
    element.send_keys(location)
    try:
        search_option = driver.find_elements(By.CSS_SELECTOR, 'li.autocomplete-suggestion')[0]
        time.sleep(0.5)
        search_option.click()
        url = driver.current_url
        location_code = re.search(r'locationIdentifier=(\w+%\w+)&', url).group(1) 
        result_count = driver.find_element(By.CSS_SELECTOR, '.searchHeader-resultCount').text
        RightmoveLocationCodes(location=location, subDivType='LAD', locationIdentifier=location_code, resultCount=result_count).save()
        return location_code
    except:
        return None
       


if __name__ == '__main__':
    df = pd.read_csv(r"C:\Users\callu\OneDrive\Documents\coding\rightmove_app\react_frontend\rightmove_app - Copy\src\assets\geo_data\subdivision_names\Ward_to_Local_Authority_District_to_County_to_Region_to_Country_(May_2023)_Lookup_in_United_Kingdom.csv")
    lad_array = df['LAD23NM'].unique()

    
    loc_code_array, last_idx = get_location_id(lad_array)
