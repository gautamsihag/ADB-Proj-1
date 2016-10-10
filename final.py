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
#import xml.etree.ElementTree as elementtree
import sys



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
MAX_DISPLAY = 10
URL = 'url'
ID = 'id'
DESCRIPTION = "description"
SEP = '[\s.,=?!:@<>()\"-;\'&_\\{\\}\\|\\[\\]\\\\]+'
URL = 'url'
TITLE = 'title'
A = 1.0
B = 1.0
G = 1.0
# Bing Namespace 
namesp = {"atom": "http://www.w3.org/2005/Atom", "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"}

### Do a Bing search on the given query ###
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

### Process raw response from Bing to extract urls, titles and descriptions ###
def getFormattedResults(responseRaw):
	formattedResults = []
	response_input = elementtree.fromstring(responseRaw)
	for i in response_input.findall('.//atom:entry', namespaces=namesp):
		url = i.findall('.//d:Url', namespaces=namesp)[0].text
		title = i.findall('.//d:Title', namespaces=namesp)[0].text
		description = i.findall('.//d:Description', namespaces=namesp)[0].text
		formattedResults.append({'url': url, 'title': title.encode('gbk','replace'), 'description':description.encode('gbk', 'replace')})

	return formattedResults




# to print query details: Urls, Titles, Descriptions
def setFormattedResults(result, index):
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
    termFreq = dict()
    doc_inverted = dict()
    for document in results:
        wordList_doc = {}
        wordList_doc['relevant'] = document['relevant']
        wordList_doc[ID] = document[ID]
        wordList_doc['tfVector'] = {}
        wordList = re.compile(SEP).split(document['description']) + re.compile(SEP).split(document['title'])
        
        filtered_wordList = []
        tokenIndex = 0
        for word in wordList:
            
            if word in stopWords or len(word) <= 1:
                continue;
            word = word.lower()
            
            filtered_wordList.append(word)
            
            # Compute the Un-normalized term tfVector  for each term
            if word in wordList_doc['tfVector']:
                wordList_doc['tfVector'][word] = wordList_doc['tfVector'][word] + 1
            else:
                wordList_doc['tfVector'][word] = 1
            
            # Compute the total term frequencies of each term
            if word in termFreq:
                termFreq[word] = termFreq[word] + 1;
            else:
                termFreq[word] = 1
            
            #Compute the inverted files    
            if not doc_inverted.has_key(word):
                doc_inverted[word] = { }

            if not doc_inverted[word].has_key(document[ID]):
                doc_inverted[word][document[ID]] = { }
            
            # Calculate inverted document body
            if doc_inverted[word][document[ID]].has_key("b"):
                doc_inverted[word][document[ID]]["b"].append(tokenIndex)
            else:
                doc_inverted[word][document[ID]]["b"] = [tokenIndex]

            tokenIndex = tokenIndex + 1
                
        indexing_docs.append(wordList_doc)
    
    return indexing_docs, doc_inverted

#############################



def implemented_rocchio(OldQuery, indexing_docs, doc_inverted, num_Relevant, num_Non_Relevant):
  weights_term = {}
  for word in OldQuery:
    weights_term[word] = 1.0
  
  weights = {}
  for word in doc_inverted.iterkeys():
    # weight vector initialization for each term in inverted file
    weights[word] = 0.0
    
  tf_weights_relevant = {}
  tf_weights_nonrelevant = {}
  # calculation of weights for relevant and nonrelevant vectors
  for doc in indexing_docs:
    if doc['relevant']:
      for word in doc["tfVector"]:
        if word in tf_weights_relevant:
          tf_weights_relevant[word] = tf_weights_relevant[word] + doc["tfVector"][word]
        else:
          tf_weights_relevant[word] = doc["tfVector"][word]
    else:
        for word in doc["tfVector"]:
            if word in tf_weights_nonrelevant:
                tf_weights_nonrelevant[word] = tf_weights_nonrelevant[word] + doc["tfVector"][word]
            else:
                tf_weights_nonrelevant[word] = doc["tfVector"][word]
  
  # Calculating vector values for Rocchio expansion
  
  for word in doc_inverted.iterkeys():
    idf = math.log(float(len(indexing_docs)) / float(len(doc_inverted[word].keys())), MAX_DISPLAY)
    
    # for second & third terms of Roccio's Algorithm
    for doc_id in doc_inverted[word].iterkeys():
      if indexing_docs[doc_id]['relevant']:
        weights[word] = weights[word] + B * idf * (float(tf_weights_relevant[word]) / num_Relevant)
      else:
        weights[word] = weights[word] - G * idf * (float(tf_weights_nonrelevant[word]) / num_Non_Relevant)
    
    if word in weights_term:
      weights_term[word] = A * weights_term[word] + weights[word]
    elif weights[word] > 0:
      weights_term[word] = weights[word]
    
  return weights_term  
  
  
# Given parameters Alpha, Beta and Gamma (coefficients to weight the original query and the centroids of the tfidf vectors of the relevant and nonrelevant results respectively) a the sets of relevant and nonrelevant documents, this function returns what the new vector would be in Rocchio's algorithm. RelevantFraction here is simply the precision reached in this round (i.e. the relevant fraction of results) 
def get_new_query_vector(query, weights, maxV = 2):
  m = 0
  query_vectors = []
  new_terms = []
  
  
  for value in sorted(weights, key=weights.get, reverse=True):
    query_vectors.append(value)
    if value in query:
      continue
    new_terms.append(value)
    m = m + 1
    if (m >= maxV):
      break

  
  for value in query:
    if not value in query_vectors:
      query_vectors.append(value)
  #sort words in the new vector by highest to lowest weights. This returns a list of tuples, where the first entry in each tuple is the word and the second is the weight.
    
    #newQueryVector[key] = alpha * value

  return query_vectors, new_terms

#Order the old query (passed as a defaultdict, as created in get_query_tfidf) to pass to the next function, as an ordered list of tuples.

#Add the highest weighted term in the newQuery that is not already in the oldQuery to the next query. Order the next query according to weights in the new query (as computed in the get_new_query_vector function with Rocchio's algorithm). This returns the ordered list of query terms to be passed to the buildUrl function.
def order_next_query(query, results, num_Relevant, num_Non_Relevant):
  
  indexing_docs, doc_inverted = get_idf_dictionary(results)
  

  weights = implemented_rocchio(query, indexing_docs, doc_inverted, num_Relevant, num_Non_Relevant)
  
  query_vectors, new_terms = get_new_query_vector(query, weights)
  
  return query_vectors, new_terms


#############################

def search(key, precision, query):
    
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
        if (len(results) < MAX_DISPLAY):
            print "Error: The number of results are less than as required by the problem statement = %d, exiting.." % len(results)
            with open(PRINT_PATH, 'a') as f: # Print to transcript
                f.write("Error: Total number of results = %d, exiting..\n" % len(results))
            break
        print "Total number of results = %d\n" % len(results)
        with open(PRINT_PATH, 'a') as f: # Print to transcript
            f.write("Total number of results = %d\n" % len(results))
        num_Items = 0
        num_Relevant = 0
        num_Non_Relevant = 0
        

        print "Iteration: " + str(iter_no)
        print "Bing Search Results:"
        print "Please follow as Y/y for relevant results, N/n for irrelevant results <any other> = quit"
        with open(PRINT_PATH, 'a') as f: # Print to transcript
            f.write("Iteration: " + str(iter_no) + "\n")
            f.write("Bing Search Results:\n")
            f.write("Please follow as Y/y for relevant results, N/n for irrelevant results\n")
        
        # Get the relevance of the document from the user feedback
        for result in results:
            result[ID] = num_Items
            num_Items += 1
            setFormattedResults(result, num_Items)
            relevant = raw_input("Relevant (Y/N)?")
            with open(PRINT_PATH, 'a') as f: # Print to transcript
                f.write("Relevant (Y/N)?" + relevant + "\n")
            if relevant == 'Y' or relevant == 'y':
                result['relevant'] = True
                num_Relevant += 1
            elif relevant == 'N' or relevant == 'n':
                result['relevant'] = False
                num_Non_Relevant += 1
            else:
                print "Invalid input, exiting...\n!"
                with open(PRINT_PATH, 'a') as f: # Print to transcript
                    f.write("Invalid input, exiting...\n!")
                return
        print 'FEEDBACK SUMMARY'
        with open(PRINT_PATH, 'a') as f: # Print to transcript
            f.write("FEEDBACK SUMMARY\n")
        # if no relevant results exit
        if (num_Relevant <= 0):
            print "Error: No relevant results from user feedback, exiting...\n"
            with open(PRINT_PATH, 'a') as f: # Print to transcript
                f.write("Error: No relevant results from user feedback, exiting...\n")
            return
    
        print "Precision " + str(float(num_Relevant)/MAX_DISPLAY)
        with open(PRINT_PATH, 'a') as f: # Print to transcript
            f.write("Precision " + str(float(num_Relevant)/MAX_DISPLAY) + "\n")
        # if precision of results is less than target precision do query expansion
        if float(num_Relevant)/MAX_DISPLAY < precision:
            print "Still below the desired precision of  " + str(precision)
            with open(PRINT_PATH, 'a') as f: # Print to transcript
                f.write("Still below the desired precision of  " + str(precision) + "\n")
            query, augmentedTerms = order_next_query(query, results, num_Relevant, num_Non_Relevant)
            print "Strings added to the query to refine results" + str(augmentedTerms)
            with open(PRINT_PATH, 'a') as f: # Print to transcript
                f.write("Strings added to the query to refine results" + str(augmentedTerms) + "\n")
        else:
            print "Desired Precision Acquired. Program Exiting"
            with open(PRINT_PATH, 'a') as f: # Print to transcript
                f.write("Desired Precision Acquired. Program Exiting\n")
            return
        iter_no = iter_no + 1

def precisionValidate(precision):
    # Validate whether the precision@10 is a float between 0 and 1
    try:
        f = float(precision)
        if (0 <= f and f <= 1):
            return True
        else:
            return False
    except ValueError:
        return False
    
if __name__ == "__main__":
    # Entry point, does some initial parameter checking
    if len(sys.argv) != 4:
        print "Input in the following manner: python main.py <bingKey> <precision> <query>"
        sys.exit(1)
    bingAccountKey = sys.argv[1]
    precision = float(sys.argv[2])
    query = sys.argv[3]

    if not precisionValidate(precision):
        print "Precision must be between 0 and 1"
        sys.exit(1)
        
    queryArray = query.split();
    #Start the search and query expansion routine
    search(bingAccountKey, precision, queryArray)