# This program is responsible to pull the yahoo stock information (historical prices,
# dividends and splits).  Variable 'fileWithSymbols' represents the name of the file
# with the tickers to pull.  Note: Most of the work is done in the YFinanceClass routine.
import random
import time

import YFinanceClass as yfc

# Process all the stock files
def procHistoryAndDividendsToFile(fileOfSymbols):
  minDelay = 3
  maxDelay = 30
  maxDivDelay = 5

  listOfSymbols = readSymbolFile(fileOfSymbols)
  for aSymbol in listOfSymbols:
    print("Processing: {0}".format(aSymbol))
    finObj = yfc.YahooFinance(aSymbol)
    finObj.saveHist()

    # Save the key/value pairs associated with this stock
    finObj.saveInfo()
      
    delayInSeconds = random.randint(minDelay,maxDelay)
    print("  history delay for: {0} seconds".format(delayInSeconds))
    time.sleep(delayInSeconds)

    finObj.saveDivSplit()
    del finObj

    delayInSeconds = random.randint(minDelay,maxDivDelay)
    print("  div/split delay for: {0} seconds".format(delayInSeconds))
    time.sleep(delayInSeconds)
  
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

fileWithSymbols = 'All.symbols'
fileWithSymbols = 'All_unowned.symbols'
fileWithSymbols = 'All.symbols'
fileWithSymbols = 'All_owned.symbols'
fileWithSymbols = 'one.symbol'

# Read symbol file and show symbols... just a debug step 
if 1 == 0:
  theSymbols = readSymbolFile(fileWithSymbols)
  for aSym in theSymbols:
    print("Symbol: {0}".format(aSym))

# Get the history, dividend and split information and write to files
if 1 == 1:
  procHistoryAndDividendsToFile(fileWithSymbols)