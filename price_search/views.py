from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from webscraper.property_scraper import PropertyScraper
import asyncio
import json


async def async_property_scrape(price):
    return await PropertyScraper().price_search(price=price,)


@api_view(['GET'])
def search(request):
    query = request.GET.get('query')
    price = int(query)
    results_df = asyncio.run(async_property_scrape(price))

    # results_df = await PropertyScraper.price_search(price=price)
    samp_df = results_df.groupby('city').apply(lambda x: x.sample(1)).reset_index(drop=True)
    props_json = samp_df.to_json(orient='records')
    # props_json = json.dumps(samp_dict)
    return Response({'properties': props_json})

