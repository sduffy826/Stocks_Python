import stockVars as gv
import stockUtils as stockUtils
import utils as utils
import StockClass

import numpy as np
import pandas as pd
import time

# Class to encapsulate the Stock attributes for a particular symbol
# This class relies on information written to CSV files, it does not
# pull any data from external resources (i.e. yahoo)
# Note: the dates from the history datapull are in a log file, see
#       below for more info
class Stock:

  DEBUGIT           = False

  # Mutual funds have capital gains that are treated like dividends... the var below will merge
  # them into the dividend value... which you almost certainly want
  MERGECAPITALGAINS = True 

  def __init__(self, tickerSymbol):
    self.ticker    = tickerSymbol

    # Get the dates from the last history pull and update 'self...'
    sDate, eDate   = stockUtils.getLogStartEndDate()
    self.startDate = utils.getDateFromISOString(sDate)
    self.endDate   = utils.getDateFromISOString(eDate)
    
    self.histStartDate = ''
    self.histEndDate   = ''
    self.SMADays       = -1 # Holds the number of days used in simple moving average calculation
    
    # Init dictionary 'tickerInfo' with key/values from yahoo
    self.initTickerInfo()
    
    # Init split data
    self.initSplitDataFrame()
    self.initSplitRange()

    # Init history data, this will populate self.historyDataFrame and self.trueHistoryDataFrame
    self.initHistoryDataFrame()

    # Init dividend data, will populate self.dividendDataFrame
    self.initDividendDataFrame()

  # -----------------------------------------------------------------------------------------------
  # This calculates the valuation for a given period and initial investment amount.  It's good
  # for things like 'what would 1k invest in apple starting on yyyy-mm-dd be worth on a given
  # end date'  
  # It will return two dataframes:
  #   firstOne - has the valuation calculation for multiple dates, if the optional parm (recordForEachDay
  #              is true you get a record for each date, if not then you get records for the start date,
  #              end date, and all dates that had actions (dividends or splits).
  #   second --- you get a 'summary' dataframe that only has one record (idea is you can use this and summary
  #              records from other stocks and perform analysis on them).  NOTE: if wondering why you have
  #              SOD and EOD calculations, they could be different if the last date in the window is an
  #              action date.
  # Note: it calculates valuation with and without doing dividend reinvestment
  # Note 2021-10-12: Added logic to use simple moving average on close date to flatten out the
  #                  potential spikes that may influence your analysis, if the last arg is
  #                  passed then it'll be used in the calculation for starting shares and valuation
  # -----------------------------------------------------------------------------------------------
  def calculateValuation(self, startDate, endDate, initialInvestment, recordForEachDay=False, numdaysInSimpleMovingAverage=-1):
    sDate = utils.getDateFromISOString(startDate)
    eDate = utils.getDateFromISOString(endDate)

    useSMA = False
    if numdaysInSimpleMovingAverage != -1:
      # Need to calc simple moving average before trimming down to the window we want
      self.initSimpleMovingAverage(numdaysInSimpleMovingAverage)
      useSMA = True

    # Get history with the 'true' values for each date
    trueHistoryFrame = self.getTrueHistoryDataFrameByRange(sDate,eDate)
    
    if recordForEachDay == False:
      # Get the action dates for the dataframe above, this gives us the start/end records
      # and each record with a dividend or stock split
      actionTrueHistoryFrame = self.getHistoryActionData(trueHistoryFrame)
    else:
      actionTrueHistoryFrame = trueHistoryFrame.copy()
      print('Be Patient...')

    # The summary record we'll build... we turn this into a dataframe for the return value,
    # as you can see almost all values are set while looping thru the data or at the end
    # it's mainly here so you can see what values are collected
    summaryRecord = {'Ticker'                          : self.ticker,                     
                     'StartDate'                       : '',
                     'InitialInvestment'               : initialInvestment,
                     'SharesPurchased'                 : 0,
                     'EndDate'                         : '',
                     'SOD Shares'                      : 0,      
                     'DividendAmount'                  : 0, 
                     'EOD Value'                       : 0,
                     'EOD Value Pct Change'            : 0.0,
                     'EOD Shares'                      : 0,
                     'SOD Shares w/Reinvest'           : 0,
                     'DividendAmount w/Reinvest'       : 0,
                     'DividendShares'                  : 0,
                     'EOD Value w/Reinvest'            : 0,
                     'EOD Value w/Reinvest Pct Change' : 0.0,
                     'EOD Shares w/Reinvest'           : 0,
                     'ShortName'                       : self.getKeyValue('shortName'),
                     'QuoteType'                       : self.getKeyValue('quoteType')}

    sodShares = -1
    for index, row in actionTrueHistoryFrame.iterrows():
      # the 'R' on end of vars is for the reinvested dividend version      
      closeDivisor = row['Close'] if row['Close'] > 0 else 1
      if pd.isna(row['CloseSMA']):  # Check for NaN or null, if so use close value
        # if self.DEBUGIT:
        print("Found NAN for close divisor, using Close, ticker: {0} date: {1}".format(self.ticker,str(row['Date'])))
        closeSMADivisor = closeDivisor
      else:
        closeSMADivisor = row['CloseSMA'] if row['CloseSMA'] > 0 else 1
      if sodShares < 0:
        if useSMA:
          sodShares = initialInvestment / closeSMADivisor
        else:
          sodShares = initialInvestment / closeDivisor
        sodSharesR                       = sodShares 
        summaryRecord['StartDate']       = str(row['Date'])
        summaryRecord['SharesPurchased'] = sodShares

      summaryRecord['EndDate'] = str(row['Date'])

      dividendAmount  = sodShares * row['Dividend']
      dividendAmountR = sodSharesR * row['Dividend']
      dividendShares  = dividendAmountR / closeDivisor
      
      splitShares  = sodShares * row['Split']
      splitSharesR = sodSharesR * row['Split']        
        
      if splitShares > 0: # If split occurred we calc eod differently
        eodShares  = splitShares
        eodSharesR = splitSharesR + dividendShares 
      else:
        eodShares  = sodShares
        eodSharesR = sodSharesR + dividendShares

      if useSMA:
        valuation  = sodShares * row['CloseSMA']
        valuationR = (sodSharesR + dividendShares) * row['CloseSMA']        
      else:
        valuation  = sodShares * row['Close']
        valuationR = (sodSharesR + dividendShares) * row['Close']        
      
      # First show without reinvestment, then with it
      actionTrueHistoryFrame.loc[index,['SOD Shares']]                = sodShares   # Start Of Day shares
      actionTrueHistoryFrame.loc[index,['DividendAmount']]            = dividendAmount
      actionTrueHistoryFrame.loc[index,['EOD Value']]                 = valuation   # End Of Day valuation
      actionTrueHistoryFrame.loc[index,['SplitShares']]               = splitShares
      actionTrueHistoryFrame.loc[index,['EOD Shares']]                = eodShares

      actionTrueHistoryFrame.loc[index,['SOD Shares w/Reinvest']]     = sodSharesR 
      actionTrueHistoryFrame.loc[index,['DividendAmount w/Reinvest']] = dividendAmountR
      actionTrueHistoryFrame.loc[index,['DividendShares']]            = dividendShares
      actionTrueHistoryFrame.loc[index,['EOD Value w/Reinvest']]      = valuationR
      actionTrueHistoryFrame.loc[index,['SplitShares w/Reinvest']]    = splitSharesR
      actionTrueHistoryFrame.loc[index,['EOD Shares w/Reinvest']]     = eodSharesR

      # Sum the required fields for the summary record
      summaryRecord['DividendAmount']            = summaryRecord['DividendAmount'] + dividendAmount
      summaryRecord['DividendAmount w/Reinvest'] = summaryRecord['DividendAmount w/Reinvest'] + dividendAmountR
      summaryRecord['DividendShares']            = summaryRecord['DividendShares'] + dividendShares

      sodShares  = eodShares # Set value for next date
      sodSharesR = eodSharesR

    if len(actionTrueHistoryFrame) > 0:
      lastPos = actionTrueHistoryFrame.index[-1]
    else:
      print('No data in actionTrueHistoryFrame, ticker: {0}'.format(self.ticker))
      return pd.DataFrame(), pd.DataFrame()

    # Assign values in the summary dictionary
    summaryRecord['SOD Shares'] = actionTrueHistoryFrame.loc[lastPos,['SOD Shares']].values[0]    
    summaryRecord['EOD Value']  = actionTrueHistoryFrame.loc[lastPos,['EOD Value']].values[0]
    
    growthPct = 100 * (actionTrueHistoryFrame.loc[lastPos,['EOD Value']].values[0] - initialInvestment) / initialInvestment
    summaryRecord['EOD Value Pct Change'] = growthPct
    
    summaryRecord['EOD Shares']            = actionTrueHistoryFrame.loc[lastPos,['EOD Shares']].values[0]
    summaryRecord['SOD Shares w/Reinvest'] = actionTrueHistoryFrame.loc[lastPos,['SOD Shares w/Reinvest']].values[0]      
    summaryRecord['EOD Value w/Reinvest']  = actionTrueHistoryFrame.loc[lastPos,['EOD Value w/Reinvest']].values[0]
    
    # totInvestment = initialInvestment + summaryRecord['DividendAmount w/Reinvest']
    # The growthPct below is based on initial investment... if you want it based on total investment initialInvestment (div+initial) then
    # uncomment value above and use it instead of 'initialInvestment'... note this makes Pct lower; I left it based
    # on initial investment since that's really what I am in for and the dividend is really taken out of the 
    # stock price.
    growthPct = 100 * (actionTrueHistoryFrame.loc[lastPos,['EOD Value w/Reinvest']].values[0] - initialInvestment) / initialInvestment
    summaryRecord['EOD Value w/Reinvest Pct Change'] = growthPct
    
    summaryRecord['EOD Shares w/Reinvest'] = actionTrueHistoryFrame.loc[lastPos,['EOD Shares w/Reinvest']].values[0]

    # Convert dictionary to a dataframe   
    summaryRecordDataFrame = pd.DataFrame(summaryRecord,index=[0])

    # Return both dataframes, actionTrueHistoryFrame has a line item for each 'action' date and summaryRecordDataFrame
    # has just the one record... thought being you can collect all summary records for different stocks and then
    # perform some analysis on them
    return actionTrueHistoryFrame, summaryRecordDataFrame

  # -----------------------------------------------------------------------------------------------
  # Return the cost basis for the stock (with dividend revinue).  It does this pretending an initial
  # purchase of $1,000.00, to get the growth per dollar (GPD) just divide that number by 1000.
  # If you have your current valuation of your stock then divide it by (GPD) to come up with what
  # your original cost basis is.
  # -----------------------------------------------------------------------------------------------
  def getCostBasis(self, startDate, endingDate = "", initialInvestment = 1000, reinvestDividend = True):   

    sDate = utils.getDateFromISOString(startDate)
    if endingDate == "":
      eDate = self.endDate 
    else:
      eDate = utils.getDateFromISOString(endingDate)

    trueHistoryFrame = self.getTrueHistoryDataFrameByRange(sDate,eDate)
    
    actionTrueHistoryFrame = self.getHistoryActionData(trueHistoryFrame)
    
    totalInvestment    = initialInvestment
    totalDivInvestment = 0
    initialDate        = ""
    initialSharePrice  = 0
    finalDate          = ""
    finalClose         = 0
    shares, initialShares = -1, -1
    for index, row in actionTrueHistoryFrame.iterrows():
      divNum = row['Close'] if row['Close'] > 0 else 1
      if shares < 0:  # First time thru loop
        initialShares     = initialInvestment / divNum
        shares            = initialShares
        initialDate       = row['Date']
        initialSharePrice = row['Close']

      if (row['Dividend'] > 0.0 and reinvestDividend == True):
        divInvestment      = shares * row['Dividend']
        shares             += divInvestment/divNum  
        totalInvestment    += divInvestment
        totalDivInvestment += divInvestment

      if row['Split'] > 0.0:
        shares = shares * row['Split']
      finalDate  = row['Date']
      finalClose = row['Close']

    totalValue = shares * finalClose
    cbRec = {"Ticker": self.ticker, "StartDate": initialDate, "InitialInvestment": initialInvestment, "InitSharePrice": initialSharePrice,
             "InitialShares": initialShares, "EndingDate": finalDate, "DividendInvestment": totalDivInvestment,
             "TotalInvestment": totalInvestment, "EndingSharePrice": finalClose, "EndingShares": shares, "EndingValue":  totalValue}
    cbRecFrame = pd.DataFrame(cbRec,index=[0])

    return cbRecFrame

  # --------------------------------------------------------------------------------------
  # Get dates for cost basis.  This is useful if you have a cost basis but don't know when
  # you acquired security; this will give you dates possible... within a pct of accuracy
  # The args should be obvious :)
  # --------------------------------------------------------------------------------------
  def getDatesForCostBasis(self, costBasis, sharesOwned, lastDateOwnedSecurity = "", accuracyNeeded = 0.95, reinvestedDividend = True):
    shares = sharesOwned

    if accuracyNeeded <= 0.0 or accuracyNeeded >= 1.0:
      raise Exception("accuracy should be number < 1 (i.e. .95 means you want 95% accuracy)")
    
    lowBasisRange  = costBasis * accuracyNeeded
    highBasisRange = costBasis / accuracyNeeded 

    # Get ending date the person has security... if they didn't provide it use last date on file
    if lastDateOwnedSecurity == "":
      eDate = self.endDate
    else:
      eDate = utils.getDateFromISOString(lastDateOwnedSecurity)
    
    # We could use get range with earliest start and eDate but most likely it's the same as below so
    # we didn't bother... most overhead with this is skipping data till get to eDate... minimal
    tempData = self.trueHistoryDataFrame.copy()
    tempData.sort_values('Date', ascending=False, inplace=True)

    dtRec = {"Ticker": self.ticker, "CostBasis": costBasis, "sharesStartedWith": sharesOwned, "OrigPricePerShare" : costBasis/sharesOwned,
             "endDateOwned": eDate.strftime("%Y-%m-%d"), "accuracyTested": accuracyNeeded, "reinvestedDividend": reinvestedDividend,
             "Date": "", "Accuracy": 0, "SharesOwned":  0, "PricePerShare": 0, "Valuation": 0}

    numRecs = 0
    for index, row in tempData.iterrows():
      if row['Date'] <= eDate:
        theValue = row['Close'] * shares
        if theValue >= lowBasisRange and theValue <= highBasisRange:
          dtRec["Date"] = row["Date"]
          dtRec["Accuracy"] = theValue/costBasis
          dtRec["SharesOwned"] = shares
          dtRec["PricePerShare"] = row["Close"]
          dtRec["Valuation"] = theValue
          if numRecs == 0:
            dtRecFrame = pd.DataFrame(dtRec,index=[0])
          else:
            dtRecFrame = pd.concat([dtRecFrame, pd.DataFrame([dtRec])], ignore_index=False)
          numRecs = numRecs + 1
                
        # Calculate what the shares where before dividend reinvestment, formula is (shares*price)/(price+div amt)
        # we only adjust shares if doing dividend reinvestment and the record date is <= date we had stock
        if (row['Dividend'] > 0.0 and reinvestedDividend == True):
          shares = (shares * row['Close']) / (row['Close'] + row['Dividend'])

        # Calculate shares before split
        if row['Split'] > 0:
          shares = shares/row['Split']

    if numRecs == 0:
      dtRecFrame = pd.DataFrame(dtRec,index=[0])

    return dtRecFrame

  # -----------------------------------------------------------------------------------------------
  # Return the filtered multiplier for a given date (remember filtered mutliplier only calcs splits
  # up until self.endDate)
  # -----------------------------------------------------------------------------------------------
  def getFilteredMultiplierForDate(self, theDate):
    return self.getMultiplierForDate(theDate,2)

  # ----------------------------------------------------------------------------------------------
  # Return a new dataframe with the first and last row of the dataframe passed in, and all the
  # records that have a dividend or a split... you can use this to derive valulation over a period
  # ----------------------------------------------------------------------------------------------
  def getHistoryActionData(self, dataframe):
    if len(dataframe) > 0:  # Check that there is data
      newDataFrame1 = dataframe.iloc[[0, -1]]  # Get first and last record
      newDataFrame2 = dataframe[(dataframe['Dividend'] > 0.0) | (dataframe['Split'] > 0.0)]
      # rtnDataFrame  = newDataFrame1.append(newDataFrame2)  ## Deprecated so had to change to concat
      rtnDataFrame  = pd.concat([newDataFrame1, newDataFrame2]) 
      rtnDataFrame.sort_values('Date', ascending=True, inplace=True)
      return rtnDataFrame.drop_duplicates() # Remove dupes.. could be if first or last record is div/split
    else:
      return dataframe.copy()

  # -----------------------------------------------------------------------------------------------
  # Get a copy of the 'historyDataFrame' for the date range passed in
  # -----------------------------------------------------------------------------------------------
  def getHistoryDataFrameByRange(self, startDate, endDate):
    return self.historyDataFrame[(self.historyDataFrame['Date']>=startDate) & (self.historyDataFrame['Date']<=endDate)]

  # -----------------------------------------------------------------------------------------------
  # Get the start/end date of the history data
  # -----------------------------------------------------------------------------------------------
  def getHistoryWindow(self):
    return self.histStartDate, self.histEndDate

  # -----------------------------------------------------------------------------------------------
  # Get the start/end date of the history data
  # -----------------------------------------------------------------------------------------------
  def getKeyValue(self,keyName):
    if keyName in self.tickerInfo:
      return self.tickerInfo[keyName]
    else:
      return None

  # -----------------------------------------------------------------------------------------------
  # Return the split multiplier for a given date
  # -----------------------------------------------------------------------------------------------
  def getMultiplierForDate(self, theDate, index2Grab):
    rtnValue = 1
    for aRow in self.listOfSplitRange:
      if theDate >= aRow[0] and theDate <= aRow[1]:
        return aRow[index2Grab]
    return rtnValue

  # -----------------------------------------------------------------------------------------------
  # Return the split multiplier for a given date
  # -----------------------------------------------------------------------------------------------
  def getSplitMultiplierForDate(self, theDate):
    return self.getMultiplierForDate(theDate,3)

  # -----------------------------------------------------------------------------------------------
  # Get the start/end date of the history data
  # -----------------------------------------------------------------------------------------------
  def getTickerInfo(self):
    return self.tickerInfo

  # -----------------------------------------------------------------------------------------------
  # Get a copy of the 'trueHistoryDataFrame' for the date range passed in
  # -----------------------------------------------------------------------------------------------
  def getTrueHistoryDataFrameByRange(self, startDate, endDate):
    return self.trueHistoryDataFrame[(self.trueHistoryDataFrame['Date']>=startDate) & (self.trueHistoryDataFrame['Date']<=endDate)]

  # -----------------------------------------------------------------------------------------------
  # Little helper that takes a date and adjustedDividend amount and
  #   returns what the actual dividend was (multiplies by split multiplier)
  # -----------------------------------------------------------------------------------------------
  def initDividendHelper(self, theDate, adjustedDividend):
    multiplier = self.getSplitMultiplierForDate(theDate)
    return multiplier * adjustedDividend 

  # -------------------------------------------------------------------------------------------------
  # Return dictionary for dividends or capital gain values, they are read in from the file passed in.
  # The key is date (iso), value is dividend or cap gain amount (as floating point value)
  # -------------------------------------------------------------------------------------------------
  def getDividendsAndCapGainFromFileHelper(self,infile):
    rtnDict = {}
    try:
      with open(infile) as filePtr:
        for aLine in filePtr:
          try:
            (key, value) = aLine.split(',')                 
            if key in rtnDict:
              rtnDict[key] = rtnDict[key] + float(value)
            else:
              rtnDict[key] = float(value)
          except:
            print("Exception on getDividendsAndCapGainFromFile, ignored line: {0}".format(aLine))
    except Exception as ex:
      print("Exception {0} trying to read: {1}  file ignored".format(ex,infile))
    
    return rtnDict

  # ---------------------------------------------------------------------------------------------------------
  # Helper to merge the dividends and capital gains, it will return a dataframe with 'Date','Dividends' values
  # ---------------------------------------------------------------------------------------------------------
  def initDividendCapGainHelper(self):
    divDict = self.getDividendsAndCapGainFromFileHelper(stockUtils.getDividendFileName(self.ticker))
    capDict = self.getDividendsAndCapGainFromFileHelper(stockUtils.getCapGainFileName(self.ticker))
    
    # We have the dictionaries... merge values from capDict into divDict
    for key, value in capDict.items():
      if key in divDict:
        divDict[key] = divDict[key] + value
      else:
        divDict[key] = value
    
    rtnFrame = pd.DataFrame(divDict.items(),columns=['Date','Dividends'])
    rtnFrame.sort_values('Date', ascending=True, inplace=True)
    return rtnFrame
  
  # -----------------------------------------------------------------------------------------------
  # Initialize following:
  #    self.dividendDataFrame - dataframe has 'Date'     - Date of split, it's a dtype of Date
  #                                           'Dividend' - The dividend amount
  # -----------------------------------------------------------------------------------------------
  def initDividendDataFrame(self):    
    if Stock.MERGECAPITALGAINS == True:
      self.dividendDataFrame = self.initDividendCapGainHelper()
    else:
      infile                 = stockUtils.getDividendFileName(self.ticker)
      self.dividendDataFrame = pd.read_csv(infile)    

    print('-------------------------------------------')
    print(self.dividendDataFrame)    
    print('-------------------------------------------')
    if len(self.dividendDataFrame) > 0:     
      # Make the ISODate string a date
      self.dividendDataFrame['Date'] = self.dividendDataFrame['Date'].apply(utils.getDateFromISOString)
      
      # Rename column
      self.dividendDataFrame.rename(columns = {'Dividends':'AdjustedDividend'}, inplace=True) 
      
      # Calculate the 'real dividend' amount
      self.dividendDataFrame['DateDividend'] = self.dividendDataFrame.apply(lambda theRow: self.initDividendHelper(theRow.Date, theRow.AdjustedDividend), axis=1)
      
      # Sort ascending by date
      self.dividendDataFrame.sort_values('Date', ascending=True, inplace=True)
      
      if Stock.DEBUGIT:
        print('In initDividendDataFrame for ticker: {0} data below'.format(self.ticker))
        print(self.dividendDataFrame)

    return

  # -----------------------------------------------------------------------------------------------
  # Initialize following:
  #  self.historyDataFrame - dataframe has the following elements (Date, Open, High, Low, Close, AdjustedClose, Volume, AdjustedDividend, Split)
  #                            the 'AdjustedDivided' is the dividend/SplitMultiplier
  #  self.trueHistoryDataFrame - dataframe has the history values above mutliplied by the appropriate split multplier (SplitMultiplier), cols are
  #                                (Date, Open, High, Low, Close, AdjustedClose, Volume, Dividend, Split, SplitMultiplier, FilterMultiplier)
  #                                The SplitMultiplier is the value used in adjusting open, high, low, close, adjustedclose, dividend.  I put
  #                                filtermultiplier in dataframe in case you want it down the road
  # -----------------------------------------------------------------------------------------------
  def initHistoryDataFrame(self):    
    infile                = stockUtils.getHistoryFileName(self.ticker)
    self.historyDataFrame = pd.read_csv(infile)    

    # Make the ISODate string a date
    self.historyDataFrame['Date'] = self.historyDataFrame['Date'].apply(utils.getDateFromISOString)

    # Rename column
    self.historyDataFrame.rename(columns = {'Adj Close'     : 'AdjustedClose', 
                                            'Dividends'     : 'AdjustedDividend',
                                            'Stock Splits'  : 'Split',
                                            'Capital Gains' : 'CapitalGains'}, inplace=True) 
        
    # Sort ascending by date
    self.historyDataFrame.sort_values('Date', ascending=True, inplace=True)
    
    # Set the start/end date range of the history data
    if len(self.historyDataFrame) > 0:
      lastPos = self.historyDataFrame.index[-1]
      self.histStartDate = self.historyDataFrame.loc[0,['Date']].values[0]
      self.histEndDate   = self.historyDataFrame.loc[lastPos,['Date']].values[0]

    # Calculate the actual values for the individual dates (these are values multiplied by split multiplier)
    self.trueHistoryDataFrame = self.historyDataFrame.copy()
    self.trueHistoryDataFrame.rename(columns = {'AdjustedDividend' : 'Dividend'}, inplace=True)

    # Add the split multiplier columns then adjust each of the other cols
    self.trueHistoryDataFrame['SplitMultiplier'] = self.trueHistoryDataFrame['Date'].apply(self.getSplitMultiplierForDate)
    self.trueHistoryDataFrame['FiltMultilier']   = self.trueHistoryDataFrame['Date'].apply(self.getFilteredMultiplierForDate)
    self.trueHistoryDataFrame['Open']          = self.trueHistoryDataFrame['Open'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['High']          = self.trueHistoryDataFrame['High'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['Low']           = self.trueHistoryDataFrame['Low'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['Close']         = self.trueHistoryDataFrame['Close'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['AdjustedClose'] = self.trueHistoryDataFrame['AdjustedClose'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['Dividend']      = self.trueHistoryDataFrame['Dividend'] * self.trueHistoryDataFrame['SplitMultiplier']
    
    # Init simple moving average
    self.initSimpleMovingAverage()
 
    # Example if you wanted to call with a lambda expression, but above is probably quicker :)
    #  self.trueHistoryDataFrame.apply(lambda theRow: (theRow.Open * theRow.SplitMult),axis=1)
    if Stock.DEBUGIT:
      print('In initHistoryDataFrame for ticker: {0} data below'.format(self.ticker))
      print(self.historyDataFrame.head())
   
      print('trueHistoryDataFrame below')
      print(self.trueHistoryDataFrame.head())
      print(self.trueHistoryDataFrame.tail())
 
    return

  # -----------------------------------------------------------------------------------------------
  # Initialize the simple moving average, this will be column 'CloseSMA', we'll use that to flatten
  #   the spikes that could occur and inflate/deflate analysis we're doing.
  # Note: it'll only recalculate when number of days changed
  # -----------------------------------------------------------------------------------------------    
  def initSimpleMovingAverage(self,numDays=gv.movingAverageNumDays):
    # Calculate the simple moving average for the 'close'... this will help flatten spikes  
    if numDays != self.SMADays:      
      self.trueHistoryDataFrame['CloseSMA'] = self.trueHistoryDataFrame.loc[:,'Close'].rolling(window=numDays).mean()
      self.SMADays = numDays    
    
    return

  # -----------------------------------------------------------------------------------------------
  # Initialize following:
  #    self.splitDataFrame - dataframe has 'Date'  - Date of split, it's a dtype of Date
  #                                        'Split' - Float for split amount
  # -----------------------------------------------------------------------------------------------
  def initSplitDataFrame(self):    
    infile              = stockUtils.getSplitFileName(self.ticker)
    self.splitDataFrame = pd.read_csv(infile)    

    if len(self.splitDataFrame) > 0:
      # Make the ISODate string a date
      self.splitDataFrame['Date'] = self.splitDataFrame['Date'].apply(utils.getDateFromISOString)

      # Rename column
      self.splitDataFrame.rename(columns = {'Stock Splits':'Split'}, inplace=True) 
          
      # Sort ascending by date
      self.splitDataFrame.sort_values('Date', ascending=True, inplace=True)

      if Stock.DEBUGIT:
        print('In initSplitDataFrame for ticker: {0} data below'.format(self.ticker))
        print(self.splitDataFrame)

    return

  # -----------------------------------------------------------------------------------------------
  # Initialize the splitRange list, this allows you to use following columns:
  #   filterMultiplier - calculate how many shares you'd have by 'self.endDate' if purchased in a window
  #   splitMultiplier  - how many shares you'd have today if you purchased between window - note we also
  #                        need this value to calculate 'real' dividend amount
  #    self.listOfSplitRange - [windowStartDate, windowEndDate, filteredMultiplier, splitMultiplier], so 
  #                              ['2018-11-01', '2020-01-09', 5, 10] means that shares you acquired between
  #                              11/1/2018 thru 1/9/2020 would be worth 5 shares on self.endDate, the 10 is
  #                              the number you'd have today
  # -----------------------------------------------------------------------------------------------
  def initSplitRange(self):
    self.splitDataFrame.sort_values('Date', ascending=False, inplace=True)
    splitMult  = 1
    filterMult = 1
    dumbDict = {}
    for index, row in self.splitDataFrame.iterrows(): 
      theDate   = row['Date']      
      splitAmt  = row['Split']
      splitMult = splitMult * splitAmt
      if theDate <= self.endDate: 
        filterMult = filterMult * splitAmt
      dumbDict[theDate] = [filterMult, splitMult]
      
    # Reset sort ascending
    self.splitDataFrame.sort_values('Date', ascending=True, inplace=True)

    self.listOfSplitRange = [] 
    # Build list where each row is a list of [startDate, endDate, splitMultiplier]
    # the give any date (between start/end) we can determine the split factor
    lowDate = self.startDate
    for index, row in self.splitDataFrame.iterrows():
      theDate = row['Date']
      aRecord = [lowDate, theDate, dumbDict[theDate][0], dumbDict[theDate][1]]
      self.listOfSplitRange.append(aRecord)
      lowDate = theDate + gv.one_day

    # Add last record
    aRecord = [lowDate, utils.getDateFromISOString('2999-12-31'), 1, 1]  # last record has split multipliers of 1
    self.listOfSplitRange.append(aRecord)
    return

  # -----------------------------------------------------------------------------------------------
  # Initialize a dictionary with the ticker info (returned from yahoo's getInfo method)
  # -----------------------------------------------------------------------------------------------
  def initTickerInfo(self):    
    infile          = stockUtils.getInfoFileName(self.ticker)
    self.tickerInfo = stockUtils.loadDictionary(infile)
    return

  def writeDataFrame(self, dataframe, outputFile):
    dataframe.to_csv(outputFile)
    return

# ===============================================================================================
#  T E S T I N G
# ===============================================================================================
if __name__ == "__main__":
  # Get stock object
  theSymbol = 'aapl'
  theSymbol = 'psx'
  theSymbol = 'vsmix'
  stockObj = StockClass.Stock(theSymbol)
  print('Processing symbol: {0}'.format(theSymbol))
  
  # Show split
  if 1 == 0:
    print('Split values below')
    for index, row in stockObj.splitDataFrame.iterrows(): 
      print("Index: {0}  Date: {1}  Split Amount: {2}".format(index, row['Date'], row['Split']))
    
    print('listOfSplitRange values below')
    for aRow in stockObj.listOfSplitRange:
      print(str(aRow))
 
  # Show dividends
  if 1 == 1:
    print('Dividend values below')
    for index, row in stockObj.dividendDataFrame.iterrows(): 
      print("Index: {0}  Date: {1}  AdjDiv: {2} RealDiv: {3}".format(index, row['Date'], row['AdjustedDividend'], row['DateDividend']))
  
  # Test utility to show splits for a particular date
  if 1 == 0:
    theDate = utils.getDateFromISOString('1993-01-01')
    print('SplitMultiplier for {0}: {1}'.format(str(theDate),stockObj.getSplitMultiplierForDate(theDate)))
    print('FilteredMultiplier for {0}: {1}'.format(str(theDate),stockObj.getFilteredMultiplierForDate(theDate)))
  
  # Show how to calc elapsed time (not related to stock object, but had for testing)
  if 1 == 0:
    tt1 = time.time()
    # Do something here...
    time.sleep(1.5)   
    tt2 = time.time()
    print('Elapsed is: {0}'.format(tt2 - tt1))

  if 1 == 0:
    stockObj.writeDataFrame(stockObj.trueHistoryDataFrame,'aaplTrueHistoryDataFrame.csv')

  # history filtered and action history records
  if 1 == 0:
    sd, ed = '2009-01-20', '2013-01-19'
    sd, ed = '2009-01-20','2012-02-19'
    sd, ed = '1998-01-01', '1999-06-01'
    sd, ed = '1990-01-01', '2024-02-26'

    sDate = utils.getDateFromISOString(sd)
    eDate = utils.getDateFromISOString(ed)
    trueHistoryFrame = stockObj.getTrueHistoryDataFrameByRange(sDate,eDate)
    stockObj.writeDataFrame(trueHistoryFrame, '{0}TrueHistory_{1}_{2}.csv'.format(theSymbol,sd,ed))

    actionTrueHistoryFrame = stockObj.getHistoryActionData(trueHistoryFrame)
    stockObj.writeDataFrame(actionTrueHistoryFrame, '{0}ActionHistory_{1}_{2}.csv'.format(theSymbol,sd,ed))
    
    print('True history data frame filtered')
    print(trueHistoryFrame)
    print()
    print('History data frame filtered')
    historyFrame = stockObj.getHistoryDataFrameByRange(sDate,eDate)
    stockObj.writeDataFrame(historyFrame, '{0}History_{1}_{2}.csv'.format(theSymbol,sd,ed))
    print(historyFrame)

  # Calculate valuations
  if 1 == 1:
    sd, ed = '2011-10-12','2021-10-11'
    sd, ed = '1998-01-01', '1999-06-01'
    sd, ed = '2011-10-18', '2022-10-05'
    # sd, ed = '2015-09-25','2020-09-30'
    # Returns valuation dataframe and a summary record dataframe.
    #   Args: pass in window (startDate, endDate) , initialInvestmentAmount, boolTrueForDividendReinvestment, #DaysForSimpleMovingAverage (-1 if don't want)    
    
    tickerValu, tickerSumm = stockObj.calculateValuation(sd, ed, 5636.07, True, -1)
    stockObj.writeDataFrame(tickerValu, '{0}Valuation_{1}_{2}.csv'.format(theSymbol,sd,ed))
    stockObj.writeDataFrame(tickerSumm, '{0}ValuationSummary_{1}_{2}.csv'.format(theSymbol,sd,ed))

  # Calculate cost basis
  if 1 == 1:
    theDate = '1990-06-14'
    theDate = '2011-10-18'
    initInvestment = 5636.07
    costBasis = stockObj.getCostBasis(theDate)
    print(costBasis)
    costBasis = stockObj.getCostBasis(theDate,'',False)  # Don't do divident reinvestment calculation
    print(costBasis)
    costBasis = stockObj.getCostBasis(theDate, '2022-10-05', initInvestment)
    print(costBasis)
    
    desc = 'To get cost basis, if initialInvestment = 1k, for your amount: costBasis = (yourAmount*1000)/EndingValue (from cost basis calc)'
    print(desc)
    
  # Get the date for a cost basis
  if 1 == 1:    
    dateOfBasis = stockObj.getDatesForCostBasis(61899.78, 190.256, "", 0.99, True) # ,accuracyNeeded = 0.95, reinvestedDividend = True)
    print(dateOfBasis)

  print('\n\n\nDone processing symbol: {0}'.format(theSymbol))

  print('Short name is: {0}'.format(stockObj.getKeyValue('shortName')))