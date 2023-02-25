from flipkart_processing import flipkart_processing
from amazon_processing import amazon_processing
from nykaa_processing import nykaa_processing
from datetime import datetime
import pandas as pd
import asyncio
import json


async def single_product_data_fetcher(product_name: str, url: dict) -> dict:
    # to extract data from a script, we need to create a User-Agent as a has blocked robots from accessing data
    amazon_coroutine = amazon_processing(product_name, url["amazon"])
    flipkart_coroutine = flipkart_processing(product_name, url["flipkart"])
    nykaa_coroutine = nykaa_processing(product_name, url["nykaa"])
    amazon_result, flipkart_result, nykaa_result = await asyncio.gather(
        amazon_coroutine, flipkart_coroutine, nykaa_coroutine
    )
    processing_df = pd.DataFrame(
        [
            [
                product_name,
                amazon_result["Price"],
                flipkart_result["Price"],
                nykaa_result["Price"],
                amazon_result["Discount"],
                flipkart_result["Discount"],
                nykaa_result["Discount"],
                amazon_result["Rating"],
                flipkart_result["Rating"],
                nykaa_result["Rating"],
                amazon_result["Review Count"],
                flipkart_result["Review Count"],
                nykaa_result["Review Count"],
                amazon_result["Availability"],
                flipkart_result["Availability"],
                nykaa_result["Availability"],
                datetime.now().date(),
            ]
        ],
        columns=[
            "Title",
            "AmazonPrice",
            "FlipkartPrice",
            "NykaaPrice",
            "AmazonDiscount",
            "FlipkartDiscount",
            "NykaaDiscount",
            "AmazonRating",
            "FlipkartRating",
            "NykaaRating",
            "AmazonReviewCount",
            "FlipkartReviewCount",
            "NykaaReviewCount",
            "AmazonAvailability",
            "FlipkartAvailability",
            "NykaaAvailability",
            "ExtractionDate",
        ],
    )
    processing_df["ExtractionDate"] = pd.to_datetime(
        processing_df["ExtractionDate"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return json.loads(processing_df.to_json(orient="records"))[0]


async def process_historical_data(product_name, url):
    product_data = await single_product_data_fetcher(product_name, url)
    product_data_df = pd.DataFrame(
        [product_data.values()], columns=list(product_data.keys())
    )
    all_historical_data_df = pd.read_excel("Data/HistoricalData.xlsx")
    product_historical_df = all_historical_data_df[
        all_historical_data_df["Title"] == product_name
    ]
    required_data = pd.concat([product_historical_df, product_data_df])
    required_data["ExtractionDate"] = pd.to_datetime(
        required_data["ExtractionDate"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return json.loads(required_data.to_json(orient="records"))


async def process_all_urls():
    output = list()

    # opening our url file to access URLs
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())

    # iterating over the urls
    for product_name, product_urls in product_data.items():
        current_product_data = await single_product_data_fetcher(
            product_name, product_urls
        )
        output.append(current_product_data)

    return output


if __name__ == "__main__":
    urls = {
        "amazon": "https://www.amazon.in/dp/B07RFQRF46",
        "flipkart": "https://www.flipkart.com/vega-atom-motorbike-helmet/p/itmcfbfe3c4d8c2a?pid=HLMFVFY3VQZSAFYY&lid=LSTHLMFVFY3VQZSAFYY9RWBIA&marketplace=FLIPKART&q=Vega+Atom+Helmet&store=1mt%2Fztf%2Fiv8%2Ftih&srno=s_1_1&otracker=search&otracker1=search&fm=organic&iid=4a864811-20d2-4d16-b5a2-38f871aa801d.HLMFVFY3VQZSAFYY.SEARCH&ppt=hp&ppn=homepage&ssid=jxndib0xkw0000001677095701617&qH=25453736a41b000c",
    }
    asyncio.run(process_historical_data("Vega Atom Helmet", urls))
