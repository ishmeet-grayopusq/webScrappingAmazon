import os
import json
import uvicorn
from fastapi import FastAPI, Request, Body
from models import ProductInfo
from product_data_handler import (
    process_all_urls,
    single_product_data_fetcher,
    process_historical_data,
)

app = FastAPI()


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
    return await process_all_urls()


@app.post("/single_product")
async def single_product_processor(
    requested_product: ProductInfo = Body(example={"Product_Name": "Vega Atom Helmet"}),
):
    """
    Extracts and returns info about 1 product from Amazon and Flipkart.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())
    return await single_product_data_fetcher(
        requested_product.Product_Name, product_data[requested_product.Product_Name]
    )


@app.post("/historical_data")
async def historical_data_generator(
    requested_product: ProductInfo = Body(
        example={
            "Product_Name": "Vega Atom Helmet",
        }
    ),
):
    """
    Generates historical data for 1 product from Amazon and Flipkart.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())
    return await process_historical_data(
        requested_product.Product_Name, product_data[requested_product.Product_Name]
    )


if __name__ == "__main__":
    directories = os.listdir()
    if "Data" not in directories:
        os.mkdir("Data")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
