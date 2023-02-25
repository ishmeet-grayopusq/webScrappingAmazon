from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import requests
import json


async def nykaa_processing(product_name, url):
    page = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        },
    )

    soup = BeautifulSoup(
        page.content, "html.parser"
    )  # it gives us the visual representation of data

    # title of the product
    try:
        title = soup.findAll(attrs={"class": "css-1gc4x7i"})[0].next.text
    except AttributeError as e:
        title = "NA"
    print("Product Title:", title)

    # Name of the product
    try:
        name = soup.findAll(attrs={"class": "css-1gc4x7i"})[0].next.text
        prod_name = ""
        for i in name:
            if i == "," or i == "-":
                break
            else:
                prod_name += i
    except AttributeError as e:
        prod_name = "NA"
    print("Product Name:", prod_name)

    # size of the product
    try:
        product_size = (
            soup.findAll(attrs={"class": "css-pzbce3"})[0]
            .text.replace("(", "")
            .replace(")", "")
        )
    except AttributeError as e:
        product_size = "NA"
    print("Product Size:", product_size)

    # discounted price of the product
    try:
        discounted_price = soup.findAll(attrs={"class": "css-1jczs19"})[0].text
    except AttributeError as e:
        discounted_price = "NA"
    print("Current price:", discounted_price)

    # discount in percentage
    try:
        discount_percent = soup.findAll(attrs={"class": "css-bhhehx"})[0].text[0:3]
    except AttributeError as e:
        discount_percent = "NA"
    print("Discount (in %):", discount_percent)

    # star ratings for the product
    try:
        star = soup.findAll(attrs={"class": "css-m6n3ou"})[0].text[0:3] + " out of 5.0"
    except AttributeError:
        star = "NA"
    print("Ratings (stars):", star)

    # Item in stock check
    try:
        stock_status = soup.find("div", class_="1yzjeg6")
        if stock_status is None:
            stock_status = "In Stock"
        else:
            stock_status = stock_status.text
    except AttributeError:
        stock_status = "NA"
    print("Stock", stock_status)

    # product id on nykaa:
    try:
        product_id = url.split("/")
        product_id = product_id[5].split("?")[0]
    except AttributeError:
        product_id = "NA"
    print("Product id:", product_id)

    # ratings counting for the product
    try:
        ratings_count = soup.find(attrs={"class": "css-1hvvm95"}).text
    except AttributeError as e:
        ratings_count = "NA"
        print(e)
    print("Total Ratings:", ratings_count)

    processing_df = pd.DataFrame(
        [
            [
                product_name,
                discounted_price,
                discount_percent,
                star,
                ratings_count,
                stock_status,
                datetime.now().date(),
            ]
        ],
        columns=[
            "Title",
            "Price",
            "Discount",
            "Rating",
            "Review Count",
            "Availability",
            "ExtractionDate",
        ],
    )
    processing_df["ExtractionDate"] = pd.to_datetime(
        processing_df["ExtractionDate"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return json.loads(processing_df.to_json(orient="records"))[0]


if __name__ == "__main__":
    # opening our url file to access URLs
    file = open("url.txt", "r")

    # iterating over the urls
    for links in file.readlines():
        nykaa_processing(links)
