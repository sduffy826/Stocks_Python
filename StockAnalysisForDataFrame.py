import numpy as np
import pandas as pd
import datetime
import sys

import StockClass 
import stockUtils as stockUtils
import utils as utils

# This does the work to perform the analysis
def analysisForDF(dataframe,filePrefix,numDaysOfSMA=-1):  
  recCount = 0
  endDate  = str(datetime.date.today())
  for index, row in dataframe.iterrows():
    # Pull fields from dataframe
    account    = row['Account']
    aSymbol    = row['Ticker']
    status     = row['Status']
    shares     = row['Shares']
    investment = row['Value']
    statusDate = row['StatusDate']

    # Instantiate object    
    stockObj = StockClass.Stock(aSymbol)
    date1, date2 = stockObj.getHistoryWindow()
    
    # print('Ticker: {0} date1:{1}: type(date1):{2}'.format(aSymbol,date1,type(date1)))
    if date1 != '' and date1 > statusDate:
      daysDelta = utils.daysBetween(date1, statusDate)
      if daysDelta > 10:
        print('**** Gap in data for ticker: {0}  statusDate: {1}   stockHistoryDate: {2},  Will not analyze!!'.format(aSymbol, statusDate, date1))
        date1 = ''

    if date1 == '':
      print("No data for ticker: {0}".format(aSymbol))
      # referenced in more than just that routine.
      valuationSummary = pd.DataFrame(stockObj.summaryRecord,index=[0])
      valuationSummary.loc[0,'StartDate']         = str(statusDate)
      valuationSummary.loc[0,'InitialInvestment'] = investment
      valuationSummary.loc[0,'ShortName']         = 'No Data Available'
      # Empty df for sample
      valuationSample  = pd.DataFrame()
    else:
      if date1 > statusDate:    
        print("WARNING  Ticker: {0} statusDate: {1} less than stock history date of {2}".format(aSymbol,statusDate,date1))

      # Args: window, initialInvestment, boolForRecordForEachDay, numDaysOfSimpleMovingAverage
      valuationSample, valuationSummary = stockObj.calculateValuation(str(statusDate), endDate, investment, False, numDaysOfSMA)
    
    recCount = recCount + 1

    # Add columns from input dataframe
    valuationSummary['Account'] = account
    valuationSummary['Status']  = status
    valuationSummary['Shares']  = shares
    if recCount == 1: # First record processed just sets allData to summary data, otherwise we'd append        
      allData = valuationSummary.copy()
    else:
      allData = pd.concat([allData, valuationSummary], ignore_index=True)
    del valuationSummary
    del valuationSample
    del stockObj
  
  if recCount > 0:  
    allData.to_csv(stockUtils.getValuationFileName(filePrefix,endDate))
  else:
    print('no data collected')

# ------------------------------------------------------------------------------
#   M A I N   L I N E
# ------------------------------------------------------------------------------
if __name__ == "__main__":
  # If they passed arguments then use them
  if len(sys.argv) >= 2:
    dataframe  = sys.argv[1]
    fileprefix = sys.argv[2]
    if len(sys.arv) >= 3:
      smaDays = sys.argv[3]
      analysisForDF(dataframe,fileprefix,smaDays)
    else:
      analysisForDF(dataframe,fileprefix) 
    print('Used arguments from command line')
  else:
    print("Pass dataframe, fileprefix, optional SMA numdays")  