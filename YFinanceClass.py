import datetime
import yfinance as yf
from pandas_datareader import data as pdr
# import random
# import time
import pandas as pd
import numpy as np 

import stockUtils as stockUtils

# -----------------------------------------------------------------------------------------------------------------------------------
# Change log
# -----------------------------------------------------------------------------------------------------------------------------------
# 2024-02-19 yfinance changed the way it returns dates, now they're form yyyy-mm-dd 00:00:00-timzoneDelta (yyyy-mm-dd 00:00:00-05:00)
#            I changed the .to_csv calls to add date_format='%Y-%m-%d' so that I only get the iso date
# -----------------------------------------------------------------------------------------------------------------------------------
class YahooFinance:

  DEBUGIT  = False
  ONE_DAY  = datetime.timedelta(days=1)
  MIN_DATE = '1970-01-01'

  def __init__(self, tickerSymbol):
    yf.pdr_override()

    self.ticker     = tickerSymbol
    self.tickerData = yf.Ticker(self.ticker)

    # Get the dates from the last history pull and update 'self...'
    # sDate, eDate = stockUtils.getLogStartEndDate()
    # self.startDate = utils.getDateFromISOString(sDate)
    # self.endDate   = utils.getDateFromISOString(eDate)

  # Get next event earnings etc...
  def getCalendar(self):
    return self.tickerData.calendar

  # Get ticker info
  def getInfo(self):
    return self.tickerData.info

  # Get institutional holders, cols: index, holder, shares, date reported, % Out, Value
  def getInstitutionalHolders(self):
    return self.tickerData.institutional_holders 

  # Get option chain for a specific expiration date (date is string isodate yyyy-mm-dd)
  def getOptionChain(self, yyyy_mm_dd):
    return self.tickerData.option_chain(yyyy_mm_dd)

  # Get option expirations
  def getOptions(self):
    return self.tickerData.options

  # Get the recommendations, cols: datetime, firm, to grade (i.e. buy), from grade action 
  def getRecommendations(self):
    return self.tickerData.recommendations

  # Get ticker short name (we pull it from info)
  def getShortName(self):
    theInfo = self.getInfo()
    return theInfo['shortName']

  # Save the dividends and the split information to a file  
  def saveDivSplit(self):
    outFile = stockUtils.getDividendFileName(self.ticker)
    data    = self.tickerData.dividends
    data.to_csv(outFile,date_format='%Y-%m-%d')  

    outFile = stockUtils.getSplitFileName(self.ticker)
    data    = self.tickerData.splits
    data.to_csv(outFile,date_format='%Y-%m-%d')

    outFile = stockUtils.getCapGainFileName(self.ticker)
    data    = self.tickerData.capital_gains
    data.to_csv(outFile,date_format='%Y-%m-%d')  


  # Save the information about the stock (the dictionary returned from getInfo)
  def saveInfo(self):
    infoFile = stockUtils.getInfoFileName(self.ticker)
    stockUtils.saveDictionary(self.getInfo(),infoFile)

  # Get the historical data and save it to a file
  def saveHist(self):
    today = str(datetime.date.today())[:10]
    
    # Get history and turn off the auto_adjust (it would adjust open, high, low, close)
    # Note leave auto_adjust false.... if true then you don't get the adjusted_close column of data
    # and the close column is really the adjusted close
    historyDF  = self.tickerData.history(start=YahooFinance.MIN_DATE,end=today,auto_adjust=False)
    outFile    = stockUtils.getHistoryFileName(self.ticker)
    historyDF.to_csv(outFile,date_format='%Y-%m-%d')
    stockUtils.appendLogDates(YahooFinance.MIN_DATE, today, 'Log created on {0}'.format(str(datetime.datetime.now())))
    

# ===============================================================================================
#  T E S T I N G
# ===============================================================================================
if __name__ == "__main__":

  # Get stock object
  yFinanceObj = YahooFinance('vsmix')
  
  # Show short name
  if 1 == 1:
    print('Symbol: {0}  Shortname: {1}'.format(yFinanceObj.ticker, yFinanceObj.getShortName()))

  # Show ticker info
  if 1 == 1:
    dictValue = yFinanceObj.getInfo()
    print('Symbol: {0} info elements below'.format(yFinanceObj.ticker))
    for key, value in dictValue.items():
      print("  key: {0:30s} value: {1}".format(key,value))
  
  # Save history
  if 1 == 1:
    yFinanceObj.saveHist()
    print('Symbol: {0} saved'.format(yFinanceObj.ticker))
    
  # Save dividends/splits/capital gains
  if 1 == 1:
    yFinanceObj.saveDivSplit()
    print('Symbol: {0} saved div/split/cap gains'.format(yFinanceObj.ticker))
      