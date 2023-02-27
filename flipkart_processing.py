from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import requests
import json
import re


async def flipkart_processing(product_name, url):
    url_query = urlparse(url).query
    product_id = parse_qs(url_query)['pid'][0]
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
            (int(product_price.replace("₹", "").replace(",", "")) - int(discPrice.replace("₹", "").replace(",", "")))
            / int(product_price.replace("₹", "").replace(",", ""))
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

    # flipkart size code:
    try:
        size_text = list(re.findall('([0-9]+).*(kg|\s*x*[**])', soup.find("div", class_="_2NKhZn").text))
        size = " "
        for i in size_text:
            for y in i:
                size += str(y)
    except AttributeError:
        size = "NA"
    print("size:", size)

    processing_df = pd.DataFrame(
        [
            [
                product_name,
                discPrice,
                discount,
                stars,
                product_rating,
                stock,
                size,
                product_id,
                str(datetime.now().date()),
            ]
        ],
        columns=[
            "Title",
            "Price",
            "Discount",
            "Rating",
            "Review Count",
            "Availability",
            "ProductSize",
            "ProductID",
            "ExtractionDate",
        ],
    )
    processing_df["ExtractionDate"] = pd.to_datetime(
        processing_df["ExtractionDate"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return json.loads(processing_df.to_json(orient="records"))[0]
