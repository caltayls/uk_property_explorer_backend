from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from webscraper.property_scraper import PropertyScraper
import utils.utils as utils
import asyncio
import json


async def async_property_scrape(post_data):
    return await PropertyScraper().price_search(post_data)


@api_view(['GET', 'POST'])
def search(request):
    post_data = request.data
    if post_data:
        results_df = asyncio.run(async_property_scrape(post_data))
        summary_df = utils.get_summary_table(results_df, post_data['searchType']) 
        props_json = results_df.to_dict(orient='records')
        summary_json = summary_df.to_dict(orient='records')
        response_json = {
            'properties': props_json,
            'summaryTable': summary_json,
        }
 

    return Response(response_json)
    # return Response({'a':[{'a':'s'}, {'b':6}]})

