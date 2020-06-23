"""
Webscraping test, learning how to do BeautifulSoup.

What I want to test, is how the average rating from *reviews* compares to the average rating from reviews. 
Are reviews biased?

TO DO LIST:
1/ Automatically load a list of books (webpages) to scrape
2/ how to get all pages of reviews?
4/ Get average score of book
5/ Or the whole break down?
6/ How do we tell if it's biased or not?
7/ Make the goodreads date in a pythonic date.

Prerequisites: geckodriver
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import IPython
import numpy as np
import matplotlib.pyplot as plt 
from selenium.webdriver import Chrome, Firefox
import time

def get_reviews(source):
	"""
	Data to scrape: 
	1/ Date (so you can make a time series)
	2/ length of review. (so you can see if that is a factor)
	3/ The score. 
	"""
	#We use selenium because the url does not change for different review pages
	browser = Firefox()#webdriver.Firefox()
	browser.get(source)

	html = browser.page_source
	soup = BeautifulSoup(html,'html.parser')

	reviews = soup.find_all('div',class_="review")

	review_dict = {'date':[],'length':[],'score':[]}

	counter = 1
	while True:
		print('Page: ',counter)
		for j,rev in enumerate(soup.find_all('div',class_='review')):#reviews):
			try:
				stars = rev.find('span',class_=' staticStars notranslate')['title']
				if stars == 'it was amazing':
					review_dict['score'].append(5)
				elif stars == 'really liked it':
					review_dict['score'].append(4)
				elif stars == 'liked it':
					review_dict['score'].append(3)
				elif stars == 'it was ok':
					review_dict['score'].append(2)
				elif stars == 'did not like it':
					review_dict['score'].append(1)
			except: #no stars given
				review_dict['score'].append(np.nan)

			#text length characters
			try:
				review_dict['length'].append(len(rev.find('span',class_='readable').text))
			except:
				review_dict['length'].append(0)

			try:
				review_dict['date'].append(rev.find('a',class_='reviewDate createdAt right').text)
			except:
				review_dict['date'].append('No date')
		#go to next page.
		try: 
			element = browser.find_element_by_class_name('next_page')#browser.find_element_by_id('my_id')
			element.click()
		except: #last page reached
			break
		time.sleep(6) #sleep three seconds so page can load

		html = browser.page_source
		soup = BeautifulSoup(html,'html.parser')
		counter+=1
		print(counter,len(review_dict['date']))
		if counter > 10:
			IPython.embed()
			break

	revs = pd.DataFrame(review_dict)
	return revs#review_dict

def get_score_hist(source,browser=None):
	"""
	Data to scrape: 
	1/ Date (so you can make a time series)
	2/ length of review. (so you can see if that is a factor)
	3/ The score. 
	"""
	#We use selenium because the url does not change for different review pages
	if browser is None:
		browser = Firefox(executable_path='/Users/houdt/Downloads/geckodriver')#executable_path='/Users/houdt/Downloads/geckodriver')#webdriver.Firefox()
	browser.get(source)

	element = browser.find_element_by_id('rating_details')
	element.click()

	html = browser.page_source
	soup = BeautifulSoup(html,'html.parser')

	table = soup.find('table',id='rating_distribution')

	scores = table.find_all('td',width="90")
	score_dic = {'score':[],'percentage':[],'votes':[]}
	for j,score in enumerate(scores):
		tmp = score.text.split()
		score_dic['score'].append(5-j)
		score_dic['percentage'].append(int(tmp[0][:-1]))
		score_dic['votes'].append(int(tmp[1][1:-1]))
	return pd.DataFrame(score_dic)


def test():
	#prettify
	#Harry Potter 3, to start with. 
	link = 'https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone?ac=1&from_search=true&qid=BK7MftvUML&rank=10'
	link = 'https://www.goodreads.com/book/show/71292.Asterix_the_Gaul?ac=1&from_search=true&qid=wPPB8DOUFG&rank=1'

	result = requests.get(link)

	src = result.content

	soup = BeautifulSoup(src,'lxml')
	
	scores = get_score_hist(link)#get_reviews(link)

	#fig,ax = plt.subplots(1)
	#test if histograms are significantly different from one another.

	IPython.embed()

if __name__ == "__main__":
	test()

