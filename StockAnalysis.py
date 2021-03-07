import numpy as np
import pandas as pd
import random
import time

import StockClass 
import stockUtils as stockUtils

# Read the text file passed in, it should represent stock symbols where the first
# word is the stock symbol
def readSymbolFile(filename):
  rtnList = []
  with open(filename, "r") as f:
    for aLine in f.readlines():
      if len(aLine.strip()) > 0:
        symbol = aLine.strip().split(' ')[0] # Just take the first word, it's the ticker symbol
        rtnList.append(symbol)
  return rtnList

# Delay for a bit
def waitABit(theMsg=''):
  minDelay = 3
  maxDelay = 20
  delayInSeconds = random.randint(minDelay,maxDelay)
  print("  {0} delay for: {1} seconds".format(theMsg, delayInSeconds))
  time.sleep(delayInSeconds)

# ------------------------------------------------------------------------------
#   M A I N   L I N E
# ------------------------------------------------------------------------------
# Define array that has a list of the filenames we should process, each of those
# files has a list of ticker symbols in it.
# fileWithSymbols = ['All.symbols','All_unowned.symbols']
# fileWithSymbols = ['All_subset.symbols']
fileWithSymbols = ['one.symbol']

# If var below is true then the start and ending window will be common amounst all
# the stocks, so if you wanted to use 1/1/1990->1/1/2021 but one of the stocks
# didn't have history till 1/1/2000 then the window for all stocks will be 1/1/2000
# forward.  
useCommonDateWindow = True
# useCommonDateWindow = False

# Set window for anlysis, NOTE: we'll override if history doesn't exist for it
startWindow, endWindow = '2013-01-20','2017-01-19' # Obama second term
startWindow, endWindow = '2017-01-20','2021-01-19' # Trump term (should probably do 3 yr compare)
startWindow, endWindow = '2009-01-20','2013-01-19' # Obama first term
startWindow, endWindow = '2017-01-20','2020-02-19' # Trump till covid 3 years 1 month
startWindow, endWindow = '2009-01-20','2012-02-19' # Obama first term 3 years 1 month

# startWindow, endWindow = '2020-01-20','2021-01-19' # Current Year
# startWindow, endWindow = '2016-03-01','2021-02-28' # 5 years prior to Covid
#startWindow, endWindow = '2011-03-01','2021-02-28' # 10 years prior to Covid
#startWindow, endWindow = '2020-03-16','2021-02-28' # Since covid low to now
startWindow, endWindow = '2003-12-31','2020-11-20' # Window to compare my results to web

listOfObjects = {}
listOfSymbols = []

# build array of all the symbols
print('Reading symbol file(s)')
for symbolFile in fileWithSymbols:
  fSymbols = readSymbolFile(symbolFile)
  listOfSymbols.extend(fSymbols)

# Initialize objects for each symbol and check window
print('Initializing stock objects')
for aSymbol in listOfSymbols:
  print('  {0}'.format(aSymbol))
  listOfObjects[aSymbol] = StockClass.Stock(aSymbol)
  date1, date2 = listOfObjects[aSymbol].getHistoryWindow()
  if str(date1) > startWindow and useCommonDateWindow:    
    startWindow = str(date1)
    print("Window start changed to {0} due to stock symbol: {1}".format(startWindow, aSymbol))
  if str(date2) < endWindow and useCommonDateWindow:    
    endWindow = str(date2)
    print("Window end changed to {0} due to stock symbol: {1}".format(endWindow, aSymbol))

# Now process the valuation for each of the stocks
recCount = 0
allData  = pd.DataFrame()
for aSymbol in listOfSymbols:
  valuationSample, valuationSummary = listOfObjects[aSymbol].calculateValuation(startWindow, endWindow, 1000, False)
  recCount = recCount + 1
  if recCount == 1: # First record processed just sets allData to summary data, otherwise we'd append
    del allData
    allData = valuationSummary.copy()
  else:
    allData = allData.append(valuationSummary)
  del valuationSummary
  del valuationSample
  waitABit('Created object for: {0}'.format(aSymbol))

if recCount > 0:  
  allData.to_csv(stockUtils.getSummaryValuationFileName(startWindow,endWindow))
else:
  print('no data collected')
