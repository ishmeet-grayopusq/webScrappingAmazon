from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
import json


async def amazon_processing(product_name, url):
    # Making the HTTP Request
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
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
