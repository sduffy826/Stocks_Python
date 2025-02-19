import os
import pandas as pd

import utils
import dataframeUtils as dataframeUtils
import stockUtils as stockUtils
import StockAnalysisForDataFrame as stockAnalysisForDataFrame

# ----------------------------------------------------------------------------------------------------------------------
# Main purpose of this is to generate a summaryValuation spreadsheet for stock transaction data; beneficial if you want
# to see how sold assets compare to purchased ones.  It can also generate summaryValuation based on a portfolio
# spreadsheet but that doesn't seem as valuable unless it's and old portfolio file and want to see what current 
# valuation might be (you should know value of recent portfolio data).
# Worth noting, the code uses the value (Net Amount or Current Value) to determine shares on starting window, it does this 
# because sometimes the date of transaction is a settlement date and there may not be stock data for it.  The 'Shares' 
# from the data file will be output (far right) and you can compare it with 'SharesPurchased', the main deltas I've
# seen are usually from aqquisitions, just be aware of it.
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# The transaction file should be csv (comman separated), line 1 should be column headers with
# columns below; the order of columns doesn't matter and it can have more columns that listed but
# it must have them (also interviening whitespace is removed so FromAcct and From Acct would be ok)
#      Stock Symbol,FromAcct,Date of Trade,Transaction,Shares,Net Amount
# The code uses 'Date of Trade' as the starting date to pull data from
#
# The portfolio file (also csv format), should have header in line1 and have minimum columns:
#      Account Name, Symbol, Quantity, Current Value
# The 'portfolioDate' variable you set will be used as the starting date to pull from (read below) 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# To run this you should:
#   1) set variable 'procTransaction' to True or False (True it'll do transactions, False it'll do portfolio)
#   2) make sure the 'transactionFile', 'portfolioFile', and 'portfolioDate' variables are correct
#   3) set 'removeIfNoTicker' to False
#   4) run the program, if there are tickers that you don't have data for it'll create file 'getTickerData.symbols'
#        that filename is in the variable 'getsymFile'
#   5) review console output, if there were tickers you need continue below, otherwise you have your analysis
#        a) update YFinanceProcessHistory so the symbol file it points to the one you want ('getTickerData.symbols')
#        b) run YFinanceProcessHistory
#        c) redo from step 4, if it still lists tickers but you want to bypass them go to step 3, change it to True
#              and proceed with remaining steps
# ----------------------------------------------------------------------------------------------------------------------


# Return a dataframe of portfolio data, this also should be passed the
# date that the portfolio data was pulled.  note: it is assumed that there will be
# some data in the file, if not an exception will be thrown since you're trying
# to return dtRecFrame and it won't exist
def getPortfolioData(portfolioFile,dateStringToUse='2011-10-18'):
  df = utils.readCSV(portfolioFile)
  dataframeUtils.stripSpaceInCols(df) # Trim column names
  numRecs = 0
  dtRec   = {}
  for index, row in df.iterrows():    
    if pd.isna(row['Symbol']) == False: # Got data
      dtRec['Account'] = row['AccountName']
      dtRec['Ticker']  = row['Symbol'].strip().lower()
      dtRec['Status']  = 'Own'      
      if pd.isna(row['Quantity']) == False:
        dtRec['Shares'] = utils.convertToNumIfPossible(row['Quantity'])
      else:
        dtRec['Shares'] = utils.convertToNumIfPossible(row['CurrentValue']) # If no shares then use the current value... probably cash

      dtRec['Value']      = utils.convertToNumIfPossible(row['CurrentValue'])
      dtRec['StatusDate'] = utils.getDateFromISOString(dateStringToUse)
      if numRecs == 0:
        dtRecFrame = pd.DataFrame(dtRec,index=[0])
      else:
        dtRecFrame = pd.concat([dtRecFrame, pd.DataFrame([dtRec])], ignore_index=False)
      numRecs = numRecs + 1
  dtRecFrame.reset_index(drop=True, inplace=True) # Reset index
  return dtRecFrame

# Return a dataframe of transaction data; note: it is assumed that there will be
# some data in the file, if not an exception will be thrown since you're trying
# to return dtRecFrame and it won't exist
def getTransactionData(transactionFile):
  df = utils.readCSV(transactionFile)
  dataframeUtils.stripSpaceInCols(df) # Trim column names
  numRecs = 0
  dtRec   = {}
  for index, row in df.iterrows():    
    if pd.isna(row['StockSymbol']) == False and row['StockSymbol'].strip() != '?': # Got data
      dtRec['Account']    = row['FromAcct']
      dtRec['Ticker']     = row['StockSymbol'].strip().lower()
      dtRec['Status']     = row['Transaction']
      dtRec['Shares']     = utils.convertToNumIfPossible(row['Shares'])      
      dtRec['Value']      = utils.convertToNumIfPossible(row['NetAmount'])
      dtRec['StatusDate'] = utils.getDateFromLongUSA(row['DateofTrade'])      
      if numRecs == 0:
        dtRecFrame = pd.DataFrame(dtRec,index=[0])
      else:
        dtRecFrame = pd.concat([dtRecFrame, pd.DataFrame([dtRec])], ignore_index=False)
      numRecs = numRecs + 1
  dtRecFrame.reset_index(drop=True, inplace=True) # Reset index
  return dtRecFrame

# Print some of the dataframe data, defaults to 5 records but can be overridden
def printSomeData(dataframe,numrecs=5):      
  for index, row in dataframe.iterrows():
    if index < numrecs:
      print(index,row['Account'],row['Ticker'],row['Status'],row['Shares'],row['Value'],row['StatusDate'])

# -----------------------------------------------------------------------------------------------------------
# Mainline, We'll either process transactions or the portfolio data (based on procTransaction)
# -----------------------------------------------------------------------------------------------------------
procTransaction = True

transactionFile = 'transactions.csv'

portfolioFile   = 'Portfolio_Positions_Feb-03-2025.csv'
portfolioDate   = '2025-02-03'

removeIfNoTicker = False  # Run first time with False, this will identify missing symbols 
                          # After pulling those you may want to turn this True to remove any symbols
                          # that you don't want to process (i.e. because things like 'cash' or really old
                          # tickers might be in the file, and you can't pull stock data for them)

getsymFile = 'getTickerData.symbols'
if removeIfNoTicker == False: # We are potentially going to create the file below
  if utils.fileExists(getsymFile):
    os.remove(getsymFile)

if procTransaction:
  theFile   = transactionFile
  outPrefix = 'transaction'
  if utils.fileExists(theFile):
    df = getTransactionData(theFile)
  else:
    print("Transaction file: {0} does not exist".format(theFile))
else:
  theFile   = portfolioFile  
  outPrefix = 'portfolio'
  if utils.fileExists(theFile):
    df = getPortfolioData(theFile,portfolioDate)
  else:
    print("Portfolio file: {0} does not exist".format(theFile))

# For testing, print some dataframe data, we give it # of recs to print, otherwise will get 5 recs
if 1 == 0:
  printSomeData(df,10)


# Check if have data for all the ticker symbols, we'll write all
# tickers needing data to getTickerData.symbols, note I added the
# logic for removeInvalidTickers since cash (other tickers) may
# be present and we want to continue processing, by having the removeInvalidTickers
# on then they will be removed from the dataframe.
# You should run the code with the flag False first, review results and
# then (possibly) turn it on
tickerListWithoutData = stockUtils.checkHasData(df, removeIfNoTicker)
if len(tickerListWithoutData) > 0 and removeIfNoTicker == False:
  with open(getsymFile, 'w') as f:
    for line in tickerListWithoutData:
      f.write('\n{0}'.format(line))
  print('\nMissing Ticker Data for data below, symbols written to: {0}'.format(getsymFile))
  print(tickerListWithoutData) 
else:
  print('We have ticker data for all the symbols, performing analysis')
  stockAnalysisForDataFrame.analysisForDF(df,outPrefix)
