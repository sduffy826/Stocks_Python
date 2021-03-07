import requests
import stockVars as gv 
import json

"""
  "tickerSymbol": "QQQ",
    "stockDate": "2020-03-20",
    "open": "1.01",
    "high": "2.02",
    "low": "0.99",
    "close": "1.50",
    "adjClose": "1.35",
    "volume": "1234"
"""
# Delete stock symbol, returns http status code from the call
def deleteStockAttributes(_tickerSymbol, _isodate):
  theUrl = gv.urlEndpoint + "/stocks/{0}/{1}".format(_tickerSymbol,_isodate)
  print(theUrl)
  response = requests.delete(theUrl)
  return response.status_code


# Get all the data on file
def getAllStockAttributes():
  theUrl   = gv.urlEndpoint + "/stocks"
  response = requests.get(theUrl)
  body     = response.json()
  return body

# Helper to return dictionary for items passed in
def getDictForArgs(tickerSymbol, stockDate, open, high, low, close, adjClose, volume):
  dict2Return = { 'tickerSymbol': tickerSymbol, 
                  'stockDate'   : stockDate,    
                  'open'        : open,         
                  'high'        : high,         
                  'low'         : low,          
                  'close'       : close,       
                  'adjClose'    : adjClose,     
                  'volume'      : volume } 
  return dict2Return

# Get all the stock data for a particular symbol
def getStockAttributesForDayByTicker(_ticker):
  theUrl   = gv.urlEndpoint + "/stocks/{0}".format(_ticker)
  response = requests.get(theUrl)
  body     = response.json() 
  return body 

# Get all the stock data for a particular symbol
def getStockAttributesForDayByTickerAndDate(_ticker, _isodate):
  theUrl   = gv.urlEndpoint + "/stocks/{0}/{1}".format(_ticker,_isodate)
  response = requests.get(theUrl)
  body     = response.json() 
  return body   

# This will convert the list of map elements passed in into a dictionary
# of the form: dict['ticker']['stockdate'] = {'open':nnn, 'close':nnn ...}
# this should make it easier to iterate over the data
def helperListOfDictToSymDictWithDateDict(list2Convert):
  if isinstance(list2Convert,list):
    tempList = list2Convert.copy() # don't want to corrupt arg
  else:
    tempList = [list2Convert] # Wrap to make a list

  dict2Return = {}
  for aRow in tempList:
    ticker = aRow['tickerSymbol']
    if ticker not in dict2Return:
      dict2Return[ticker] = {}
    stockDate = aRow['stockDate']
    del aRow['tickerSymbol'] # Remove values we don't need
    del aRow['stockDate']
    dict2Return[ticker][stockDate] = aRow
  return dict2Return


# Insert or update record, default is insert, return the http status code from the call
def insertOrUpdateStockAttributesForDay(_dictRecord, _mode = "Insert"):
  headers    = { 'content-type': 'application/json' }
  theUrl     = gv.urlEndpoint + "/stocks/"
  postBody   = json.dumps(_dictRecord)
  
  if _mode == "Insert":
    response = requests.post(theUrl, data=postBody, headers=headers)  
  else:
    response = requests.put(theUrl, data=postBody, headers=headers)  
  return response.status_code



# Helper just for dumping out the dictionary that is in form [ticker][stockDate] = {'colName':colValue...}
def zDumpOutSymDict(dict):
  for ticker in dict:
    print("Ticker: {0}".format(ticker))
    for aDate in dict[ticker]:
      print("    Date: {0}  DictRecord: {1}".format(aDate,str(dict[ticker][aDate])))

# ------------------------------------------------------------------------------------
#   T E S T I N G
# ------------------------------------------------------------------------------------
if __name__ == "__main__":
  
  # Test - get all stock symbols
  if 1 == 1:
    allData = getAllStockAttributes() 
    
    # Reformat into dict[ticker][stockdate] = {'colName':value....}
    reformat2Dict = helperListOfDictToSymDictWithDateDict(allData)
    # Show it to the console
    zDumpOutSymDict(reformat2Dict)
    
  # Test - get all stock data for one symbol
  if 1 == 0:
    rtnValue = getStockAttributesForDayByTicker('QQQ') 
    print(str(rtnValue))

    # Reformat into dict[ticker][stockdate] = {'colName':value....}
    reformat2Dict = helperListOfDictToSymDictWithDateDict(rtnValue)
    # Show it to the console
    zDumpOutSymDict(reformat2Dict)

  # Test - get for a symbol on a specific date
  if 1 == 0:
    rtnValue = getStockAttributesForDayByTickerAndDate('XOO','2020-03-20') 
    print(str(rtnValue))

    # Reformat into dict[ticker][stockdate] = {'colName':value....}
    reformat2Dict = helperListOfDictToSymDictWithDateDict(rtnValue)
    # Show it to the console
    zDumpOutSymDict(reformat2Dict)

  # Test - insert a record
  if 1 == 0:
    statusCode = insertOrUpdateStockAttributesForDay(getDictForArgs("QQQ", "2020-03-19", 31.01, 32.02, 3.99, 31.50, 31.35, 2413))
    print('Insert statusCode: {0}'.format(statusCode))

  # Test - update a record
  if 1 == 0:
    dictRecord = getDictForArgs("QQQ", "2020-03-19", 31.31, 32.32, 3.39, 31.35, 31.65, 2443)
    statusCode = insertOrUpdateStockAttributesForDay(dictRecord,"Update")
    print('Update statusCode: {0}'.format(statusCode))

  # Test - delete attributes for symbol/data
  if 1 == 0:
    statusCode = deleteStockAttributes("QQQ", "2020-03-19")    
    print("Delete statusCode: {0}".format(statusCode))
     