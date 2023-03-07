from scrapyscript import Job, Processor
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlencode
import pandas as pd
import scrapy
import requests
import json
import re

import logging

# Disabling scrapy logs
logging.getLogger("scrapy").propagate = False

# Setting up generic logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

processor = Processor(settings=None)


def get_scrapeops_url(url):
    payload = {"api_key": "aefdfac4-496e-40d7-854b-f10eb619d906", "url": url}
    proxy_url = "https://proxy.scrapeops.io/v1/?" + urlencode(payload)
    return proxy_url


class AmazonScrapper(scrapy.spiders.Spider):
    name = "Amazon Scrapper"
    custom_settings = {
        "RETRY_TIMES": 100,
    }

    def __init__(self, url, product_name):
        self.url = get_scrapeops_url(url)
        self.product_name = product_name

    def start_requests(self):
        yield scrapy.Request(self.url, headers={}, callback=self.parse)

    def parse(self, response, **kwargs):
        product_id_data = re.findall("ASIN.+value.+", response.text)
        if product_id_data:
            product_id_values = re.findall('(?<=value=").+(?=">)', product_id_data[0])
            if "value" not in product_id_values:
                product_id = product_id_values[0]
            else:
                product_id = "NA"
        else:
            product_id = "NA"
        discount_val = response.css("span.savingsPercentage::text").get()
        if not discount_val:
            discount_matches = re.findall(r"(?<=\()\d+%(?=\))", response.text)
            discount_val = discount_matches[0] if discount_matches else "NA"
        return {
            "Availability": "In Stock"
            if len(response.xpath('//input[@id="buy-now-button"]')) > 0
            else "Out-Of-Stock",
            "Price": response.css("span.a-price-symbol::text").get()
            + response.css("span.a-price-whole::text").get(),
            "ReviewCount": response.xpath(
                '//span[@id="acrCustomerReviewText"]/text()'
            ).get(),
            "Rating": response.css("span.reviewCountTextLinkedHistogram").attrib[
                "title"
            ],
            "Discount": discount_val.replace("-", ""),
            "ExtractionDate": str(datetime.now().date()),
            "Title": self.product_name,
            "ProductID": product_id,
            "ProductSize": response.xpath(
                '//tr[@class="a-spacing-small po-unit_count"]//span[@class="a-size-base po-break-word"]/text()'
            ).get(),
        }


async def amazon_scrapy_processing(product_name, url):
    job = Job(AmazonScrapper, url=url, product_name=product_name)
    result = processor.run(job)
    if result:
        return result[0]
    else:
        return {
            "Availability": "",
            "Price": "",
            "ReviewCount": "",
            "Rating": "",
            "Discount": "",
            "ExtractionDate": "",
            "Title": "",
        }


async def amazon_processing(product_name, url):
    # Making the HTTP Request
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
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


if __name__ == "__main__":
    import asyncio

    results = asyncio.run(
        amazon_scrapy_processing(
            "MuscleBlaze Protein",
            "https://www.amazon.in/MuscleBlaze-Performance-Certified-Chocolate-servings/dp/B091HTLXL3",
        )
    )

    print(results)
