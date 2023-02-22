def main(URL):
	from bs4 import BeautifulSoup
	import requests
	import re
	# opening our output file in append mode
	File = open("mergedOutput.csv", "a")

	# to extract data from a script, we need to create a User-Agent as amazom has blocked robots from accessing data
	HEADERS = ({"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"})

	x = re.search("amazon", URL)
	try:
		if x is None:
			print("flipkart link found!")
			print(URL)
		else:
			# Making the HTTP Request
			print("Amazon link found!")
			webpage = requests.get(URL, headers=HEADERS)

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

			# saving the title in the file
			File.write(f"{title_string},")

			# retrieving price
			try:
				price = soup.find("span", attrs={'class': 'a-offscreen'}).string.strip().replace(',', '')
			except AttributeError:
				price = "NA"
			print("Product's price =", price)

			# saving
			File.write(f"{price},")

			# retrieving discount
			try:
				discPrice = soup.find("span", attrs={'class': 'a-size-large a-color-price savingPriceOverride aok-align-center reinventPriceSavingsPercentageMargin savingsPercentage'}).string.strip().replace('-',' ')
			# we are omitting unnecessary spaces and commas from our string
			except AttributeError:
				discPrice = "NA"
			print("Product's discount =", discPrice)

			# saving
			File.write(f"{discPrice},")

			# retrieving product rating
			try:
				rating = soup.find("i", attrs={'class': 'a-icon a-icon-star a-star-4-5'}).string.strip().replace(',', '')

			except AttributeError:

				try:
					rating = soup.find("span", attrs={'class': 'a-icon-alt'}).string.strip().replace(',', '')
				except:
					rating = "NA"
			print("Overall rating = ", rating)

			File.write(f"{rating},")

			try:
				review_count = soup.find("span", attrs={'id': 'acrCustomerReviewText'}).string.strip().replace(',', '')

			except AttributeError:
				review_count = "NA"
			print("Total reviews = ", review_count)
			File.write(f"{review_count},")

			# print availablility status
			try:
				available = soup.find("div", attrs={'id': 'availability'})
				available = available.find("span").string.strip().replace(',', '')

			except AttributeError:
				available = "NA"
			print("Availability = ", available)

			# saving the availability and closing the line
			File.write(f"{available},\n")

			print()
			# closing the file
			File.close()
	except Exception as e:
		print(e)

if __name__ == '__main__':
# opening our url file to access URLs
	file = open("url.txt", "r")

	# iterating over the urls
	for links in file.readlines():
		main(links)