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


def search(key, preceision, query):
	# to record the number of iterations to ensure to get results in minimum number of iterations
	iter_no = 0

	while True:
		print 'Out Parameter Details'
		print '%-20s= %s' % ("Client key", key)
		print '%-20s= %s' % ("Query to be searched", " ".join(query))
		print '%-20s= %s' % ("Target Precision", precision)
		
		with open(PRINT_PATH, 'a') as f:
			f.write("Out Parameter Details")
			f.write('%-20s= %s\n' % ("Client key", key))
			f.write('%-20s= %s\n' % ("Query to be searched", " ".join(query)))
			f.write('%-20s= %s\n' % ("Target Precision", precision))

		results = bingSearch(key, query)

		# to gracefully exit if the number of search is less than 10
		if (len(results)<MAX_DISPLAY):
			print "Error: The number of results are less than as required by the problem statement = %d, exiting.." % len(results)
			with open(PRINT_PATH, 'a') as f:
				f.write("Error: The number of results are less than as required by the problem statement = %d, exiting..\n" % len(results))
			break

		num_Items = 0
		num_Relevant = 0
		num_Non_Relevant = 0

		print "Iterations: " + str(iter_no)
		print "Search Results: "
		print "Please follow as Y/y for relevant results, N/n for irrelevant results"

		with open(PRINT_PATH, 'a') as f:
			f.write("Iterations: " + str(iter_no) + "\n")
			f.write("Search Results: \n")
			f.write("Please follow as Y/y for relevant results, N/n for irrelevant results\n")
		
		# for relevance feedback mechanism for results
		for r in results:
			r[ID] = num_Items
			num_Items += 1
			setFormattedResults(r,num_Items)
			relevant = raw_input("Is it relevant (Y/N) ?")
			with open(PRINT_PATH, 'a') as f:
				f.write("Relevant (yes/no) ? " + relevant + "\n")
			if relevant == 'Y' or relevant == 'y' or relevant == 'yes' or relevant == 'Yes':
				r['relevant'] = True
				num_Relevant += 1
			elif relevant = 'n' or relevant == 'N' or relevant == 'no' or relevant == 'No':
				r['relevant'] = False
				num_Non_Relevant += 1
			else:
				print "Invalid Input, exiting .. \n"
				with open(PRINT_PATH, 'a') as f:
					f.write("Invalid input, exiting..\n")
				return

#function to validate the precision value input by the user	
# As described in the problem description, the precision@10 is a float value in [0,1]
def precisionValidate(precision):
	try:
		prec = float(precision)
		if (prec >= 1 or prec <= 0):
			return False
		else:
			return True
	except ValueError:
		return False


if __name__ == "__main__":
	
	if len(sys.argv) != 4:
		print "python main.py <bingKey> <precision> <query>"
		sys.exit(1)
		
	query = sys.argv[3]
	acc_Key = sys.argv[1]
	precision = sys.argv[2]
	
	if not precisionValidate(precision):
		print "Invalid Precision. Precision between [0, 1]"
		sys.exit(1)
	
	queryA = query.split()
	search(acc_Key, precision, queryA)
	