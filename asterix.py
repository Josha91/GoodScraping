import numpy as np 
import matplotlib.pyplot as plt 
from goodreads import get_score_hist
from bs4 import BeautifulSoup
import requests
import IPython 
import re
from goodreads import get_score_hist
import os
import pandas as pd
from selenium.webdriver import Chrome, Firefox
from PIL import Image
import seaborn as sns

def return_xx(string,x1,x2):
	"""Return whatever is between x1 and x2 in string"""
	if x1 == '': 
		return re.search('(.*)'+x2+'(.*)',string).group(1)
	return re.search('(.*)'+x1+'(.*)'+x2,string).group(2)

def get_authors(book):
	authors = book.find_next('span',itemprop='author')
	author_list = []
	for author in authors.findChildren('a',class_='authorName'): 
		try:
			role = author.find_next('span',class_='authorName greyText smallText role').text
			if 'anslator' in role: continue #ignore translators
		except: #role not specified
			pass
		author_list.append(author.text)
	return author_list

def get_data():
	link = lambda x: 'https://www.goodreads.com/search?page=%d&q=asterix&qid=x4kAEwfoBH&tab=books'%x
	base_link = 'http://goodreads.com'
	asterix_dic = {'name':[],'number':[],'link':[],'author 1':[],'author 2':[],'year':[]}

	page = 1
	while True:
		print(page)
		result = requests.get(link(page))
		src = result.text
		soup = BeautifulSoup(src,'lxml')

		if not "last_page" in locals():
		#Find the page after which to break out of the loop
			last_page = int(soup.find('a',class_='next_page').find_previous().text)

		books = soup.find_all('a',class_='bookTitle')
		for book in books:
			title = book.text[1:-1] #indexing cuts off newline characters
			if '#' in title: print(title)
			#dirty way of checking the title is the English version.
			#'der' because #36 only available in German...
			#Never mind... some versions only in italian... inconsistent goodreads.
			#Just select the first book
			#if not (('in' in title)|('and' in title)|('the' in title)|('der' in title)): continue
			substr = re.search('\(Ast(.?)rix(.?) #(.*)\)',title)
			if substr is not None: 
				authors = get_authors(book)
				num_tmp = substr.group(3)
				substr = substr.string[substr.start():]
				try:
					num_tmp = int(num_tmp)
				except:
					continue #not interested in omnibi
				if num_tmp in asterix_dic['number']: continue 
				year = int(book.find_next('span',class_='minirating').next_sibling.split()[2])
				#Also not interested in multiple translations. 
				#Or maybe we are? Use pandas to get all albums with number X, add all votes
	
				asterix_dic['link'].append(base_link+book['href'])
				asterix_dic['name'].append(return_xx(title,'',substr[1:-1])[:-2])
				asterix_dic['number'].append(num_tmp) 
				asterix_dic['author 1'].append(authors[0])
				try:
					asterix_dic['author 2'].append(authors[1])
				except:
					asterix_dic['author 2'].append(None)
				asterix_dic['year'].append(year)

		missing = []
		for i in np.arange(1,39): 
			if i not in asterix_dic['number']: missing.append(i)
		print(missing)
		if np.sum(len(asterix_dic['number']) )>= 38: break#break38: break #all albums found
		if page == last_page: break
		page+=1

		###WHY ON EARTH is sometimes 16 missing, and sometimes 21??? That should be detemrinistic?
	for i in range(1,6):
		asterix_dic['%dstar_vote'%i] = []

	#browser = Firefox(executable_path='/Users/houdt/Downloads/geckodriver')
	for link in asterix_dic['link']:
		score = get_score_hist(link)#,browser)
		for i in range(1,6): asterix_dic['%dstar_vote'%i].append(score['votes'][5-i])

	data = pd.DataFrame(asterix_dic).set_index('number')
	total_votes = np.sum([data['%dstar_vote'%i] for i in range(1,6)],axis=0)
	averages = np.sum([data['%dstar_vote'%i]*i for i in range(1,6)],axis=0)
	data['average'] = averages/total_votes	
	return data

def plot_asterix():
	"""
	How do we calculate the uncertainty on the average score?
	"""
	filedir = os.path.dirname(os.path.realpath(__file__))
	if not os.path.isfile(filedir+'/asterix.csv'):
		data = pd.DataFrame(get_data())
		data.to_csv('asterix.csv')
	else:
		data = pd.read_csv('asterix.csv',index_col=0).sort_index(0)

#Step 1: order by data number. 

	print(data.head)

	grouped = data.groupby(['author 1','author 2']).size().reset_index().rename(columns={0:'count'})

	fig,ax = plt.subplots(1,figsize=(10,8))
	plt.subplots_adjust(bottom=0.14,left=0.16,top=0.95,right=0.95)

	im = Image.open('asterix.png')
	height = im.size[1]
	#fig.figimage(im, 0, fig.bbox.ymax - height)
	pos = ax.get_position()
	newax = fig.add_axes([pos.x0, pos.y0, pos.x1-pos.x0-0.3, pos.y1-pos.y0-0.3], zorder=0)
	newax.imshow(im)
	newax.axis('off')
	ax.plot(data.index,data['average'],linestyle='dashed',zorder=0,color='k',label='')
	ax.scatter(data.index,data['average'],color='blue',zorder=1,label='')
	ax.plot(data.index,data['average'].rolling(5).median(),color='k',lw=3,zorder=2,label='Running median')
	clr = ['red','yellow','orange','blue']
	for j,auth2 in enumerate(data['author 2'].unique()):
		if not type(auth2) == str: #np.isnan(auth2): 
			subdata = data[data['author 2'].isnull()]
			lbl = '%s'%subdata['author 1'].iloc[0].split()[1]
		else:
			subdata = data[data['author 2'].eq(auth2)]
			lbl = r'%s & %s'%(subdata['author 1'].iloc[0].split()[1],auth2.split()[1])
		ax.scatter(subdata.index,subdata['average'],facecolors=clr[j],edgecolor='k',lw=2,s=80,label=lbl)

	ax.tick_params('both',labelsize=18)
	ax.set_xlabel('Album number',fontsize=18)
	ax.set_ylabel('Goodreads rating (out of 5)',fontsize=18)
	ax.legend(fontsize=12,loc=1)
	ax.set_ylim([3.08,4.6])

	plt.show()

	#TO DO:
	#add labels for outliers
	#add an image?
	#Add uncertainty to \mu 
	#Roos & het zwaard: some obscure swedish version... find English one. 

	IPython.embed()

#data = pd.read_csv('asterix.csv',index_col=0).sort_index(0)
#total_votes = np.sum([data['%dstar_vote'%i] for i in range(1,6)],axis=0) - 1
#averages = np.sum([(data['%dstar_vote'%i]-data['average'])*i for i in range(1,6)],axis=0)
#sample_variance = averages/total_votes
#Get student t, first see that you reproduce the example.
#uncertainty_on_mean = sample_variance/np.sqrt(total_votes)	
#IPython.embed()
plot_asterix()

#Put this in a csv file, and make sure you can load it;
#Put all of this in a function that only runs if the csv is not found
#Italian / french / english.... ?
#Play around with pandas:
#--> display the data
#--> order by (???) --> first sort
#--> later: order by 1/ authors, 2/ score, etc. 
#Make sure repeated calls to get-score_hist don't keep opening new firefox instances...!
#Why is geckodriver not found, now?
#Why are not all calls to this script identical?
#How do you close popups automatically? 

#use this as an opportunity to learn more about pandas...!

