import os
import json
import uvicorn
from fastapi import FastAPI, Body, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from models import ProductInfo
from product_data_handler import (
    process_all_urls,
    single_product_data_fetcher,
    process_historical_data,
)

app = FastAPI()


class CorsMiddlewareSelf(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response


app.add_middleware(CorsMiddlewareSelf)


@app.get("/")
async def root():
    return {"app_status": "healthy"}


@app.get("/product_info")
async def product_info():
    """
    Returns a list of products that we can process as of now.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = file_obj.read()
    return json.loads(product_data)


@app.get("/all_products")
async def all_url_processor():
    """
    Returns info about current prices of all products.
    """
    # return await process_all_urls()
    return [
  {
    "Title": "Vega Atom Helmet",
    "AmazonPrice": "₹848.00",
    "FlipkartPrice": "₹890",
    "AmazonDiscount": " 5%",
    "FlipkartDiscount": "0.1%",
    "AmazonRating": "4.1 out of 5 stars",
    "FlipkartRating": "4.2 out of 5 stars",
    "AmazonReviewCount": "11006 ratings",
    "FlipkartReviewCount": "24,275 Ratings",
    "Availability": "In stock",
    "ExtractionDate": "2023-02-23"
  },
  {
    "Title": "HP Backpack",
    "AmazonPrice": "₹900.00",
    "FlipkartPrice": "₹1,456",
    "AmazonDiscount": " 55%",
    "FlipkartDiscount": "60%",
    "AmazonRating": "4.0 out of 5 stars",
    "FlipkartRating": "4.0 out of 5 stars",
    "AmazonReviewCount": "531 ratings",
    "FlipkartReviewCount": "1000 ratings",
    "Availability": "In stock",
    "ExtractionDate": "2023-02-23"
  },
  {
    "Title": "MuscleBlaze Shaker Bottle",
    "AmazonPrice": "₹249.00",
    "FlipkartPrice": "₹499",
    "AmazonDiscount": " 64%",
    "FlipkartDiscount": "50.1%",
    "AmazonRating": "3.8 out of 5 stars",
    "FlipkartRating": "4.1 out of 5 stars",
    "AmazonReviewCount": "4117 ratings",
    "FlipkartReviewCount": "8,579 Ratings",
    "Availability": "In stock",
    "ExtractionDate": "2023-02-23"
  },
  {
    "Title": "MuscleBlaze Protein",
    "AmazonPrice": "₹2649.00",
    "FlipkartPrice": "₹899",
    "AmazonDiscount": " 23%",
    "FlipkartDiscount": "42.0%",
    "AmazonRating": "4.3 out of 5 stars",
    "FlipkartRating": "4.2 out of 5 stars",
    "AmazonReviewCount": "6697 ratings",
    "FlipkartReviewCount": "96,444 Ratings",
    "Availability": "In stock",
    "ExtractionDate": "2023-02-23"
  },
  {
    "Title": "BoAt Airdopes",
    "AmazonPrice": "₹1499.00",
    "FlipkartPrice": "₹2,990",
    "AmazonDiscount": " 62%",
    "FlipkartDiscount": "20%",
    "AmazonRating": "3.9 out of 5 stars",
    "FlipkartRating": "4 out of 5 stars",
    "AmazonReviewCount": "146195 ratings",
    "FlipkartReviewCount": "50,285 Ratings",
    "Availability": "In stock",
    "ExtractionDate": "2023-02-23"
  }
]

@app.get("/single_product/{product_name}")
async def single_product_processor(product_name: str):
    """
    Extracts and returns info about 1 product from Amazon and Flipkart.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())
    return await single_product_data_fetcher(
        product_name, product_data[product_name]
    )


@app.get("/historical_data/{product_name}")
async def historical_data_generator(product_name: str):
    """
    Generates historical data for 1 product from Amazon and Flipkart.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())
    return await process_historical_data(
        product_name, product_data[product_name]
    )


if __name__ == "__main__":
    directories = os.listdir()
    if "Data" not in directories:
        os.mkdir("Data")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
