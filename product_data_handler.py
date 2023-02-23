from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
from pprint import pprint
import pandas as pd
import requests
import asyncio
import json
import re


async def amazon_processing(product_name, headers, url):
    # Making the HTTP Request
    webpage = requests.get(url, headers=headers)

    # Creating the Soup Object containing all the data
    soup = BeautifulSoup(webpage.content, "lxml")

    # retrieving product title
    try:
        # Outer Tag Object
        title = soup.find("span", attrs={"id": "productTitle"})

        # Inner NavigableString Object
        title_value = title.string

        # Title as a string value
        title_string = title_value.strip().replace(",", "")

    except AttributeError:
        title_string = "NA"
    print("product Title = ", title_string)

    # retrieving price
    try:
        price = (
            soup.find("span", attrs={"class": "a-offscreen"})
            .string.strip()
            .replace(",", "")
        )
    except AttributeError:
        price = "NA"
    print("Product's price =", price)

    # retrieving discount
    try:
        discount = (
            soup.find(
                "span",
                attrs={
                    "class": "a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage"
                },
            )
            .string.strip()
            .replace("-", " ")
        )
    # we are omitting unnecessary spaces and commas from our string
    except AttributeError:
        discount = "NA"
    print("Product's discount =", discount)

    # retrieving product rating
    try:
        rating = (
            soup.find("i", attrs={"class": "a-icon a-icon-star a-star-4-5"})
            .string.strip()
            .replace(",", "")
        )

    except AttributeError:
        try:
            rating = (
                soup.find("span", attrs={"class": "a-icon-alt"})
                .string.strip()
                .replace(",", "")
            )
        except:
            rating = "NA"
    print("Overall rating = ", rating)

    try:
        review_count = (
            soup.find("span", attrs={"id": "acrCustomerReviewText"})
            .string.strip()
            .replace(",", "")
        )

    except AttributeError:
        review_count = "NA"
    print("Total reviews = ", review_count)

    # print availablility status
    try:
        available = soup.find("div", attrs={"id": "availability"})
        available = available.find("span").string.strip().replace(",", "")

    except AttributeError:
        available = "NA"
    print("Availability = ", available)

    processing_df = pd.DataFrame(
        [
            [
                product_name,
                price,
                discount,
                rating,
                review_count,
                available,
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


async def flipkart_processing(product_name, headers, url):
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
            stock = "Availability: In Stock"
        else:
            stock = "Availability:", stock.text
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


async def single_product_data_fetcher(product_name: str, url: dict) -> dict:
    # to extract data from a script, we need to create a User-Agent as a has blocked robots from accessing data
    user_agent = UserAgent()
    headers = {"User-Agent": user_agent.random}
    amazon_coroutine = amazon_processing(product_name, headers, url["amazon"])
    flipkart_coroutine = flipkart_processing(product_name, headers, url["flipkart"])
    amazon_result, flipkart_result = await asyncio.gather(amazon_coroutine, flipkart_coroutine)
    processing_df = pd.DataFrame(
        [
            [
                product_name,
                amazon_result['Price'],
                flipkart_result['Price'],
                amazon_result['Discount'],
                flipkart_result['Discount'],
                amazon_result["Rating"],
                flipkart_result["Rating"],
                amazon_result["Review Count"],
                flipkart_result["Review Count"],
                amazon_result["Availability"],
                datetime.now().date(),
            ]
        ],
        columns=[
            "Title",
            "AmazonPrice",
            "FlipkartPrice",
            "AmazonDiscount",
            "FlipkartDiscount",
            "AmazonRating",
            "FlipkartRating",
            "AmazonReviewCount",
            "FlipkartReviewCount",
            "Availability",
            "ExtractionDate",
        ],
    )
    processing_df["ExtractionDate"] = pd.to_datetime(
        processing_df["ExtractionDate"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return json.loads(processing_df.to_json(orient="records"))[0]


async def process_historical_data(product_name, url):
    product_data = await single_product_data_fetcher(product_name, url)
    product_data_df = pd.DataFrame([product_data.values()], columns=product_data.keys())
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
        current_product_data = await single_product_data_fetcher(product_name, product_urls)
        output.append(current_product_data)

    return output


if __name__ == "__main__":
    asyncio.run(process_historical_data("Vega Atom Helmet", "https://www.amazon.in/dp/B07RFQRF46"))
