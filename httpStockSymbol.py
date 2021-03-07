import requests
import stockVars as gv 
import json

# Delete stock symbol, returns http status code from the call
def deleteStockSymbol(_tickerSymbol):
  theUrl     = gv.urlEndpoint + "/symbols/{0}".format(_tickerSymbol)
    
  response = requests.delete(theUrl)
  return response.status_code

# Get all the stock symbols on file, return a dictionary with them
def getStockSymbols():
  theUrl   = gv.urlEndpoint + "/symbols"
  response = requests.get(theUrl)
  body     = response.json()
  return stockSymbolMapToDict(body)
  
# Return one symbol (as dictionary value) 
def getStockSymbol(_ticker):
  theUrl   = gv.urlEndpoint + "/symbols/{0}".format(_ticker)
  response = requests.get(theUrl)
  body     = response.json() 
  return stockSymbolMapToDict(body)

# Insert a record, return the http status code from the call
def insertStockSymbol(_dictRecord):
  headers    = { 'content-type': 'application/json' }
  theUrl     = gv.urlEndpoint + "/symbols/"
  postBody   = json.dumps(stockSymbolDictToMap(_dictRecord))
  
  response = requests.post(theUrl, data=postBody, headers=headers)  
  return response.status_code

# Helper to convert the dictionary record to the map
def stockSymbolDictToMap(dictRecord):
  dict2Return = {}
  if len(dictRecord) > 0:
    for theKey, theValue in dictRecord.items():
      dict2Return['tickerSymbol'] = theKey
      dict2Return['companyName']  = theValue
      break
  return dict2Return

# Helper to convert the data returned from http to a dictionary of values, 
# this handles getting a list or a dictionary (dictionary is passed in 
# when only one record was returned from call).
def stockSymbolMapToDict(theMap):
  dict2Return = {}
  
  # If arg is a dictionary convert it to a list 
  if isinstance(theMap,dict):
    theMap = [theMap.copy()]

  for aRow in theMap:
    theKey              = aRow['tickerSymbol']
    theValue            = aRow['companyName']
    dict2Return[theKey] = theValue
  return dict2Return


# Update record record, return status code
def updateStockSymbol(_dictRecord):
  headers  = { 'content-type': 'application/json' }
  theUrl   = gv.urlEndpoint + "/symbols/"
  postBody = json.dumps(stockSymbolDictToMap(_dictRecord))
  
  response = requests.put(theUrl, data=postBody, headers=headers)
  return response.status_code

# ------------------------------------------------------------------------------------
#   T E S T I N G
# ------------------------------------------------------------------------------------
if __name__ == "__main__":
  # Test - get all stock symbols
  if 1 == 1:
    allSymbols = getStockSymbols() 
    for aKey in allSymbols:
      print("ticker: {0}  name: {1}".format(aKey,allSymbols[aKey]))
  
  # Test - get one symbol
  if 1 == 0:
    oneSymbol = getStockSymbol('GOOG') 
    for aKey in oneSymbol:
      print("ticker: {0}  name: {1}".format(aKey,oneSymbol[aKey]))

  # Test - insert symbol
  if 1 == 0:
    aSymbol = {"VOO" : "Voo Company Name"}
    insertStockSymbol(aSymbol)

  # Test - update company name for symbol
  if 1 == 0:
    aSymbol = {"GOOG" : "Google"}
    updateStockSymbol(aSymbol)

  # Test - delete symbol
  if 1 == 0:
    statusCode = deleteStockSymbol('VO4')
    print("Status code from the delete: {0}".format(statusCode))