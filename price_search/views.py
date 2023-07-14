from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from webscraper.property_scraper import PropertyScraper
import utils.utils as utils
import asyncio


async def async_property_scrape(price):
    return await PropertyScraper().price_search(price=price,)




@api_view(['GET'])
def search(request):
    query = request.GET.get('query')
    price = int(query)
    results_df = asyncio.run(async_property_scrape(price))
    top_vals_df = utils.get_top_cats(results_df) # top values for each col per city.
    props_json = results_df.to_json(orient='records')
    top_vals_json = top_vals_df.to_json(orient='records')
    response_json = {
        'properties': props_json,
        'summary_table': top_vals_json,
    }
    
    return Response(response_json)

