import os
import uvicorn
from fastapi import FastAPI, Request
from product_data_handler import process_all_urls, single_product_data_fetcher

app = FastAPI()


@app.get("/all_products")
async def all_url_processor():
    return process_all_urls()


@app.get("/single_product")
async def single_product_processor(request: Request):
    body = await request.json()
    return single_product_data_fetcher(body['Product_URL'])


if __name__ == "__main__":
    directories = os.listdir()
    if 'Data' not in directories:
        os.mkdir("Data")
    uvicorn.run(app, host='0.0.0.0', port=8000)
