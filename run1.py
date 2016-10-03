# Project 1: Information Retrieval System
# Margaret & gs2835

from sys import maxsize
from collections import defaultdict
import urllib
import urllib2
import re
import math
import string
import base64
import xml.etree.ElementTree as elementtree



stopWords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself',
                      'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they',
                      'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
                      'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
                      'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by',
                      'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above',
                      'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
                      'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
                      'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
                      'can', 'will', 'just', 'don', 'should', 'now', '~', '*', '|', '+', '-', '^', '%', '/', '.', '&', '$', '@', '!',
                      ';', ':', '<', '>']
## Constants ##
PRINT_PATH = 'transcript.txt'
URL = 'url'
MAX_DISPLAY = 10
ID = 'id'
DESCRIPTION = "description"
DELIMITERS = '[\s.,=?!:@<>()\"-;\'&_\\{\\}\\|\\[\\]\\\\]+'

# Bing Namespace 
namesp = {"atom":"http://www.w3.org/2005/Atom", "d":"http://schemas.microsoft.com/ado/2007/08/dataservices"}

# query for bing search
def bingSearch(key, query):
	
	# Query String
	getQuery = {'Query':('\'' + " ".join(query) + '\'')}
	bingURL = 'https://api.datamarket.azure.com/Bing/Search/Web?' + urllib.urlencode(getQuery) + '&$top=' + str(MAX_DISPLAY) + '&$format=Atom'
	print "URL: " + bingURL
	with open(PRINT_PATH, 'a') as f:
		f.write("URL: " + bingURL + "\n")

	# Credentials
	encrypted_Acc_Key = base64.b64encode(key + ':' + key)
	headers = {'Authorization': 'Basic ' + encrypted_Acc_Key}

	# request
	reqBing = urllib2.Request(bingURL, headers = headers)
	responseBing = urllib2.urlopen(reqBing)

	# response
	responseRaw = responseBing.read()
	formattedResults = getFormattedResults(responseRaw)
	return formattedResults

# function to process raw response to extract url, titles and descriptions

def getFormattedResults(responseRaw):
	formattedResults = []
	response_input = elementtree.fromstring(responseRaw)
	for i in response_input.findall('.//atom:entry', namsespaces=namesp):
		url = i.findall('.//d:Url', namsespaces=namesp)[0].text
		title = i.findall('.//d:Title', namsespaces=namesp)[0].text
		description = i.findall('.//d:Description', namsespaces=namesp)[0].text
		formattedResults.append({'url': url, 'title': title.encode('gbk','replace'), 'description':description.encode('gbk', 'replace')})

	return formattedResults


# to print query details: Urls, Titles, Descriptions
def setformattedResults(result, index):
	print "Output " + str(index) + "\n["
	print " URL: " + result['url']
	print " Title: " + result['title']
	print " Description: " + result['description']
	print " ]\n"
	with open(PRINT_PATH, 'a') as f:
		f.write("Output " + str(index) + "\n[")
		f.write(" URL: " + result['url'] +"\n")
		f.write(" Title: " + result['title'] + "\n")
		f.write(" Description: " + result['description'] + "\n")
		f.write(" ]\n")


# To handle stopwords and indexing docs

def docsIndex(results):
	indexDocs = [] # for list of dictionaries
	termFreq = dict()
	invertedDoc = dict()
	for r in results:
		indexDoc = {}
		indexDoc['relevant'] = r['relevant']
		indexDoc[ID] = r[ID]
		indexDoc['tfVector'] = {}
		tokens = 




