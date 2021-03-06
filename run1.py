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
SEP = '[\s.,=?!:@<>()\"-;\'&_\\{\\}\\|\\[\\]\\\\]+'
A = 1.0
B = 1.0
G = 1.0
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


def get_idf_dictionary(results):
  indexing_docs = []
  term_freq = defaultdict()
  doc_inverted = defaultdict()
  docCount = defaultdict(int)
  for document in results:
    filtered_wordList = []
    index_word = 0
    wordList_doc = {}
    wordList_doc['tvfV'] = {}
    wordList_doc['relevant'] = document['relevant']
    wordList_doc[ID] = document[ID]
    #wordList = re.sub(r'[^\w\s]','',wordList)  # Using Regular expressions to take out punctuation
    #wordList = set(wordList.split()) #Splitting on whitespace and taking the set of terms.
    wordList = re.compile(SEP).split(document['description']) + re.compile(SEP).split(document['title'])
    
    for word in wordList:
      if word in stopWords:
        continue
      if len(word) <= 1:
        continue
      word = word.lower()
      filtered_wordList.append(word)
      if word in wordList_doc['tvfV']:
        wordList_doc['tvfV'][word] = wordList_doc['tvfV'][word] + 1
      else:
        wordList_doc['tvfV'][word] = 1
      if word in term_freq:
        term_freq[word] = term_freq[word] + 1
      else:
        term_freq[word] = 1
      
      
      if not doc_inverted.has_key(word):
        doc_inverted[word] = {}
      if doc_inverted[word][document[ID]].has_key("b"):
        doc_inverted[word][document[ID]]["b"].append(index_word)
      else:
        doc_inverted[word][document[ID]]["b"] = index_word
      
      index_word = index_word + 1
    
    indexing_docs.append(wordList_doc)
  
  return indexing_docs, doc_inverted


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
				with open(PRINT_PATH, 'a') as f:
					f.write("Invalid input, exiting..\n")
				print "Invalid Input, exiting .. \n"
				return
		with open(PRINT_PATH, 'a') as f:
			f.write("Add Summary Feedback to the transcript\n")
		if (num_Relevant <= 0):
			with open(PRINT_PATH, 'a') as f:
				f.write("Error: Exiting, Irrelevant results with feedback\n")
			print "Error: Exiting, Irrelevant results with feedback\n"
			return
		with open(PRINT_PATH, 'a') as f:
				f.write("Precision " + str(float(num_Relevant)/MAX_DISPLAY) + "\n")
			print "Precision " + str(float(num_Relevant)/MAX_DISPLAY)"
		
		if float(num_Relevant)/MAX_DISPLAY < precision:
			with open(PRINT_PATH, 'a') as f:
				f.write("As per the current run the precision is " + str(precision) + "\n")
			print "As per the current run the precision is " + str(precision)
			new_terms, query_vectors = order_next_query(query, results, num_Relevant, num_Non_Relevant)
			with open(PRINT_PATH, 'a') as f:
				f.write("Strings added to the query to refine results" str(new_terms) + "\n")
			print "Strings added to the query to refine results" str(new_terms)
		else:
			with open(PRINT_PATH, 'a') as f:
				f.write("Desired Precision Acquired. Program Exiting\n")
			print "Desired Precision Acquired. Program Exiting" 
			return
		
		iter_no = iter_no + 1

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
	