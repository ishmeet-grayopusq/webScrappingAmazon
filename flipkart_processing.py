from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import datetime
import json
import re


async def flipkart_processing(product_name, url):
    page = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        },
    )
    soup = BeautifulSoup(
        page.content, "html.parser"
    )  # it gives us the visual representation of data

    # name of the product
    try:
        name = soup.find("span", class_="B_NuCI")
        name = name.text.replace("   ", " ")
    except AttributeError:
        name = "NA"
    print("Name: ", name)

    # the discounted price
    try:
        discPrice = soup.findAll(attrs={"class": "_25b18c"})[0].next.text
    except AttributeError:
        discPrice = "NA"
    print("discPrice:", discPrice)

    # the original price
    try:
        product_price = [
            x for x in soup.findAll(attrs={"class": "_25b18c"})[0].children
        ][1].text
    except AttributeError:
        product_price = "NA"
    print("original Price: ", product_price)

    # calculating the percentage discount:
    try:
        discount = (
            (int(product_price.replace("₹", "")) - int(discPrice.replace("₹", "")))
            / int(product_price.replace("₹", ""))
        ) * 100
        discount = round(discount, 1)
        discount = str(discount) + "%"
        print("discount:", discount)
    except:
        discount = "NA"

    # the average ratings(stars)
    try:
        stars = soup.find("div", class_="_2d4LTz")
        stars = stars.text + " out of 5 stars"
    except AttributeError:
        stars = "NA"
    print("ratings:", stars)

    # the total ratings count(count)
    try:
        product_rating = re.findall(r"\d+,?\d+\sRatings", str(soup))[0]
    except (AttributeError, IndexError):
        product_rating = "NA"
    print("ratings count:", product_rating)

    # Item in stock check
    try:
        stock = soup.find("div", class_="_1dVbu9")
        if stock is None:
            stock = "In Stock"
        else:
            stock = stock.text
    except AttributeError:
        stock = "NA"
        print(stock)

    processing_df = pd.DataFrame(
        [
            [
                product_name,
                product_price,
                discount,
                stars,
                product_rating,
                stock,
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
