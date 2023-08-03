from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import RightmoveLocationCodes
from price_search.webscraper.property_scraper import PropertyScraper, get_region_code_dict

import utils.utils as utils
import asyncio
import json
import os

async def async_property_scrape(post_data, location_codes):
    return await PropertyScraper().search(post_data, location_codes=location_codes)

@api_view(['GET', 'POST'])
def search(request):
    post_data = request.data
    print(os.getcwd())
        
    if post_data:
        print(post_data)
        location_codes = get_region_code_dict(post_data)
        print(location_codes)
        results_df = asyncio.run(async_property_scrape(post_data, location_codes=location_codes))
        summary_df = utils.get_summary_table(results_df, post_data['searchType']) 
        props_json = results_df.fillna('null').to_dict(orient='records') #fillna(None) as JSON doesn't accept nan
        summary_json = summary_df.fillna('null').to_dict(orient='records')
        response_json = {
            'properties': props_json,
            'summaryTable': summary_json,
        }
    # Save data for testing
    save_response_data(post_data, response_json)
    
    return Response(response_json)



def save_response_data(post_data, resp):
    if post_data['region']:
        region = post_data['region'].lower().replace(' ', '_')
        search_type = post_data['searchType']
        with open(f'data/responses/reponse_{region}_{search_type}.json', 'w') as f:
            json.dump(resp, f)


# if __name__=='__main__':
#     post_data = {
#         'mustHave': {'garden': False, 'newHome': False, 'parking': False, 'retirementHome': False},
#         'numOfBedrooms': "3",
#         'propertyType': "Semi-detached",
#         'region': "North East",
#         'searchType': "features",
#         'whatToSearch': "Major towns and cities within a region"
#     }
   

#     location_codes = get_region_code_dict(post_data)
#     results_df = asyncio.run(async_property_scrape(post_data, location_codes=location_codes))
#     summary_df = utils.get_summary_table(results_df, post_data['searchType']) 
#     props_json = results_df.fillna('null').to_dict(orient='records') #fillna(None) as JSON doesn't accept nan
#     summary_json = summary_df.fillna('null').to_dict(orient='records')
#     response_json = {
#         'properties': props_json,
#         'summaryTable': summary_json,
#     }
#     # Save data for testing
#     if post_data['region']:
#         /region = post_data['region'].lower().replace(' ', '_')
#         search_type = post_data['searchType']
#         path = f'data/responses/reponse_{region}_{search_type}.json'
#         with open(path, 'w') as f:
#             json.dump(response_json, f)