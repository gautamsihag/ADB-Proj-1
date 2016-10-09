import urllib2
import base64
import json
from collections import defaultdict
import re

query = []
bingUrl = 'https://api.datamarket.azure.com/Bing/Search/Web?Query=%27gates%27&$top=10&$format=json'
#Provide your account key here (it should be read in from command line)
accountKey = 'LKoZpTSATH/5vI43rWKM828iGcJq4vgOe9F2k7sGSug'

accountKeyEnc = base64.b64encode(accountKey + ':' + accountKey)
headers = {'Authorization': 'Basic ' + accountKeyEnc}
req = urllib2.Request(bingUrl, headers = headers)
response = urllib2.urlopen(req)
content = response.read()
#content contains the json response from Bing. 
content = json.loads(content)
#parses content as json.
results = content['d']['results']
#drills down to the results.
for result in results:
  print(result['Title'])
  print('\n')
  print(result['Description'])
  print('\n')
  print(result['Url']) 
  relevant = raw_input('Relevant? (Y/N): ')
  result['Relevant'] = relevant
#for each result returned, get user relevance feedback. Store this in a new field ("Relevance") in the dictionary of results.

#This function to calculate precision. If the query returns fewer than 10 results, we will set the precision to 0 so the program stops:
def get_precision(results):
  precision = 0.0
  if len(results) < 10:
    return precision
  else:
    for result in results:
      if result['Relevant'] == 'Y' or 'y':
        precision = precision + .1 
    return precision

#This function to compare precision from this iteration to target precision
# 3 options: 1) There are fewer than 10 results, there are no relevant results. In this case we stop. 2) Precision is greater than zero but less than the target. In this case, we create an expanded query. 3) Precision is equal to or greater than the target. In this case we stop.  
#This function returns True for case 2 and False for the other cases. 
def compare_precision(precision, target):
  if precision > 0 and precision < target:
    return True
  else:
    return False
  
#This function takes the ordered list of query terms and returns the bingUrl to be used to query the API 
def build_URL(query):
  query = '+'.join(query)
  return 'https://api.datamarket.azure.com/Bing/Search/Web?Query=%27'+query+'%27&$top=10&$format=json'

#Get dictionary where key is the term and the value is the number of documents in the relevant results in which the term appears. We include the list of query words as input to create the dictionary. 
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
  
  return doc_inverted, indexing_docs


#returns a tfidf vector given a result (in json)
def get_tf_idf_vector(document):
  wordList = document['Description'].lower()
  wordList = re.sub(r'[^\w\s]','',wordList)
  wordList = wordList.split()  
  tfVector = defaultdict(float)
  for word in wordList:
    tfVector[word] += 1.0
  tfidfVector = defaultdict(float)
  for key, value in tfVector.iteritems():
    tfidfVector[key] = (float(value) / float(len(wordList))) / float(docCount[key])    
  return tfidfVector
 

#get vectors for a set of results, save each vector to its result (as an entry in the dictionary)
def get_vectors(documents):
  for document in documents:
    document['tfidfVector'] = get_tf_idf_vector(document)

# get a tfidf vector for the list of query words. Return as a new dictionary. We assume that the user does not input repeated words (and the program ensures that expanded queries will not include repeated words).
def get_query_tfidf(queryList):
  tfidfVector = defaultdict(float)
  for word in query:
    tfidfVector[word] = (1.0 / float(len(query))) / float(docCount[word])  
  return tfidfVector

# Given parameters Alpha, Beta and Gamma (coefficients to weight the original query and the centroids of the tfidf vectors of the relevant and nonrelevant results respectively) a the sets of relevant and nonrelevant documents, this function returns what the new vector would be in Rocchio's algorithm. RelevantFraction here is simply the precision reached in this round (i.e. the relevant fraction of results) 
def get_new_query_vector(weights, query, maxV = 2):
  newQueryVector = defaultdict(float)
  m = 0
  query_vectors = []
  new_terms = []
  for value in query:
    if not value in query_vectors:
      query_vectors.append(value)
  #sort words in the new vector by highest to lowest weights. This returns a list of tuples, where the first entry in each tuple is the word and the second is the weight.
  for value in sorted(weights, key = weights.get, reverse = True):
    query_vectors.append(value)
    if value in query:
      continue
    new_terms.append(value)
    m = m + 1
    if (m >= maxV):
      break
  
    #newQueryVector[key] = alpha * value

  return new_terms, query_vectors

#Order the old query (passed as a defaultdict, as created in get_query_tfidf) to pass to the next function, as an ordered list of tuples.
def order_old_query(query):
  oldQueryVector = sorted(query.iteritems(), key=lambda (k,v): v, reverse=True)
  return oldQueryVector

#Add the highest weighted term in the newQuery that is not already in the oldQuery to the next query. Order the next query according to weights in the new query (as computed in the get_new_query_vector function with Rocchio's algorithm). This returns the ordered list of query terms to be passed to the buildUrl function.
def order_next_query(query, results, num_Relevant, num_Non_Relevant):
  nextQuery = []
  doc_inverted, indexing_docs = get_idf_dictionary(results)
  
  j = 0
  for i in range(len(query)):
    if query[i][0] == query[j][0]:
      nextQuery.append(query[i][0])
      j+=1
    elif query[i][1] = query[j][1]:
      nextQuery.append(query[i][0])
    elif len(query) < 1 + len(nextQuery):
      nextQuery.append(query[j][0])
  
  weights = implemented_rocchio(query, indexing_docs, doc_inverted, num_Relevant, num_Non_Relevant)
  
  new_terms, query_vectors = get_new_query_vector(weights, query)
  
  return new_terms, query_vectors
 


