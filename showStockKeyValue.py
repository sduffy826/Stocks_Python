import StockClass 

# This is just a simple little program to show a given 'key' value for
# stocks.  It uses the json file for each symbol to get the value... this data
# was retrieved from the Yahoo pull
# Note you can see all the key/value pairs by setting the conditional in the
# mainline... but you probably only want this when running for very few tickers

# Read the text file passed in, it should represent stock symbols where the first
# word is the stock symbol
def readSymbolFile(filename):
  rtnList = []
  with open(filename, "r") as f:
    for aLine in f.readlines():
      if len(aLine.strip()) > 0:
        symbol = aLine.strip().split()[0] # Just take the first word, it's the ticker symbol
        rtnList.append(symbol)
  return rtnList

# ------------------------------------------------------------------------------
#   M A I N   L I N E
# ------------------------------------------------------------------------------
# Define array that has a list of the filenames we should process, each of those
# files has a list of ticker symbols in it.
# fileWithSymbols = ['All.symbols','All_unowned.symbols']
# fileWithSymbols = ['All_subset.symbols']
# fileWithSymbols = ['one.symbol']
fileWithSymbols = ['All_owned.symbols']

listOfObjects = {}
listOfSymbols = []

# build array of all the symbols
print('Reading symbol file(s)')
for symbolFile in fileWithSymbols:
  fSymbols = readSymbolFile(symbolFile)
  listOfSymbols.extend(fSymbols)

# Initialize objects for each symbol and check window
print('Initializing stock objects')
# If only want one symbol then you can do:   listOfSymbols = ['aapl']
for aSymbol in listOfSymbols:  
  listOfObjects[aSymbol] = StockClass.Stock(aSymbol)
  
# Now process each one
for aSymbol in listOfSymbols:
  # print('Ticker: {0}  shortName: {1}'.format(aSymbol,listOfObjects[aSymbol].getKeyValue('shortName')))
  symAndType = '{0},{1}'.format(aSymbol,listOfObjects[aSymbol].getKeyValue('quoteType'))
  shortName  = listOfObjects[aSymbol].getKeyValue('shortName').replace(",",".")
  if 1 == 0:
    print(symAndType)

  # Show all the key/value pairs
  if 1 == 0: 
    theDict = listOfObjects[aSymbol].getTickerInfo()
    for key in theDict:
      print("key: {0}  value: {1}".format(key,theDict[key]))
    # break

  # Show the dividend info... rate and also calculate the rate to do a comparison :)
  if 1 == 1: # Show divided info
    theDict = listOfObjects[aSymbol].getTickerInfo()
    divYield = theDict['dividendYield']
    try:
      prevClose = theDict['previousClose']  # currentPrice didn't work
    except:
      prevClose = -1
    try:
      calcDiv = divYield * prevClose
    except:
      calcDiv = 'n/a'
    
    print("{0},{1} ,dividendRate: ,{2} ,yield: ,{3} ,prevClose: ,{4} ,calcDivRate: ,{5}".format(shortName, symAndType, theDict['dividendRate'], divYield, prevClose, calcDiv))

