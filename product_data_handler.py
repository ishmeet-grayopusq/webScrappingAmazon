from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pprint import pprint
import pandas as pd
import requests
import json
import re


def single_product_data_fetcher(url: str):

	# to extract data from a script, we need to create a User-Agent as a has blocked robots from accessing data
	user_agent = UserAgent()
	headers = ({"User-Agent": user_agent.random})

	x = re.search("amazon", url)
	try:
		if x is None:
			print("flipkart link found!")
			print(url)
		else:
			# Making the HTTP Request
			print("Amazon link found!")
			webpage = requests.get(url, headers=headers)

			# Creating the Soup Object containing all the data
			soup = BeautifulSoup(webpage.content, "lxml")

			# retrieving product title
			try:
				# Outer Tag Object
				title = soup.find("span", attrs={"id": 'productTitle'})

				# Inner NavigableString Object
				title_value = title.string

				# Title as a string value
				title_string = title_value.strip().replace(',', '')

			except AttributeError:
				title_string = "NA"
			print("product Title = ", title_string)

			# retrieving price
			try:
				price = soup.find("span", attrs={'class': 'a-offscreen'}).string.strip().replace(',', '')
			except AttributeError:
				price = "NA"
			print("Product's price =", price)

			# retrieving discount
			try:
				discount = soup.find("span", attrs={'class': 'a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage'}).string.strip().replace('-',' ')
			# we are omitting unnecessary spaces and commas from our string
			except AttributeError:
				discount = "NA"
			print("Product's discount =", discount)

			# retrieving product rating
			try:
				rating = soup.find("i", attrs={'class': 'a-icon a-icon-star a-star-4-5'}).string.strip().replace(',', '')

			except AttributeError:

				try:
					rating = soup.find("span", attrs={'class': 'a-icon-alt'}).string.strip().replace(',', '')
				except:
					rating = "NA"
			print("Overall rating = ", rating)

			try:
				review_count = soup.find("span", attrs={'id': 'acrCustomerReviewText'}).string.strip().replace(',', '')

			except AttributeError:
				review_count = "NA"
			print("Total reviews = ", review_count)

			# print availablility status
			try:
				available = soup.find("div", attrs={'id': 'availability'})
				available = available.find("span").string.strip().replace(',', '')

			except AttributeError:
				available = "NA"
			print("Availability = ", available)

			processing_df = pd.DataFrame([[title_string, price, discount, rating, review_count, available]],
										 columns=['Title', 'Price', 'Discount', "Rating", "Review Count", "Availability"])

			return json.loads(processing_df.to_json(orient='records'))[0]

	except Exception as e:
		print(e)


def process_historical_data(product_name, url):
	current_data = pd.read_json(single_product_data_fetcher(url))
	df = pd.read_excel("Data/HistoricalData.xlsx")
	print("")


def process_all_urls():

	output = list()

	# opening our url file to access URLs
	file = open("url.txt", "r")

	# iterating over the urls
	for links in file.readlines():
		output.append(single_product_data_fetcher(links))

	return output


if __name__ == "__main__":
	process_historical_data("Vega Atom Helmet", "https://www.amazon.in/dp/B07RFQRF46")
	pprint(process_all_urls(), indent=4)
