import stockVars as gv
import stockUtils as stockUtils
import utils as utils
import StockClass

# import numpy as np
import pandas as pd
import time

# Class to encapsulate the Stock attributes for a particular symbol
# This class relies on information written to CSV files, it does not
# pull any data from external resources (i.e. yahoo)
# Note: the dates from the history datapull are in a log file, see
#       below for more info
class Stock:

  DEBUGIT        = False
  SHOWCAPGAINMSG = False  # Message saying turned off mergeCapitalGains

  def __init__(self, tickerSymbol):
    # Mutual funds have capital gains that are treated like dividends... the var below will merge
    # them into the dividend value... which you almost certainly want
    # NOTE: the value may be changed if the CapitalGains column does not exist
    self.mergeCapitalGains = True 

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

    # Init summary record, put it in separate method so value is available in other routines (than
    # just 'calculateValuation')
    self.initSummaryRecord()

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
  #              BOD and EOD calculations, they could be different if the last date in the window is an
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

    # The summary record was initialized in constructor, set initialInvestment here,
    # other values are set in the loop; we return this dictionary converted to a dataframe
    self.summaryRecord['InitialInvestment'] = initialInvestment

    bodShares = -1
    for index, row in actionTrueHistoryFrame.iterrows():
      # the 'R' on end of vars is for the reinvested dividend version      
      closeDivisor = row['Close'] if row['Close'] > 0 else 1
      if pd.isna(row['CloseSMA']):  # Check for NaN or null, if so use close value
        # if self.DEBUGIT:
        print("Found NAN for close divisor, using Close, ticker: {0} date: {1}".format(self.ticker,str(row['Date'])))
        closeSMADivisor = closeDivisor
      else:
        closeSMADivisor = row['CloseSMA'] if row['CloseSMA'] > 0 else 1
      if bodShares < 0:
        if useSMA:
          bodShares = initialInvestment / closeSMADivisor
        else:
          bodShares = initialInvestment / closeDivisor
        bodSharesR                            = bodShares 
        self.summaryRecord['StartDate']       = str(row['Date'])
        self.summaryRecord['SharesPurchased'] = bodShares

      self.summaryRecord['EndDate'] = str(row['Date'])

      dividendAmount  = bodShares * row['Dividend']
      dividendAmountR = bodSharesR * row['Dividend']
      dividendShares  = dividendAmountR / closeDivisor
      
      splitShares  = bodShares * row['Split']
      splitSharesR = bodSharesR * row['Split']        
        
      if splitShares > 0: # If split occurred we calc eod differently
        eodShares  = splitShares
        eodSharesR = splitSharesR + dividendShares 
      else:
        eodShares  = bodShares
        eodSharesR = bodSharesR + dividendShares

      if useSMA:
        valuation  = bodShares * row['CloseSMA']
        valuationR = (bodSharesR + dividendShares) * row['CloseSMA']        
      else:
        valuation  = bodShares * row['Close']
        valuationR = (bodSharesR + dividendShares) * row['Close']        
      
      # First show without reinvestment, then with it
      actionTrueHistoryFrame.loc[index,['BOD Shares']]                = bodShares   # Start Of Day shares
      actionTrueHistoryFrame.loc[index,['DividendAmount']]            = dividendAmount
      actionTrueHistoryFrame.loc[index,['EOD Value']]                 = valuation   # End Of Day valuation
      actionTrueHistoryFrame.loc[index,['SplitShares']]               = splitShares
      actionTrueHistoryFrame.loc[index,['EOD Shares']]                = eodShares

      actionTrueHistoryFrame.loc[index,['BOD Shares w/Reinvest']]     = bodSharesR 
      actionTrueHistoryFrame.loc[index,['DividendAmount w/Reinvest']] = dividendAmountR
      actionTrueHistoryFrame.loc[index,['DividendShares']]            = dividendShares
      actionTrueHistoryFrame.loc[index,['EOD Value w/Reinvest']]      = valuationR
      actionTrueHistoryFrame.loc[index,['SplitShares w/Reinvest']]    = splitSharesR
      actionTrueHistoryFrame.loc[index,['EOD Shares w/Reinvest']]     = eodSharesR

      # Sum the required fields for the summary record
      self.summaryRecord['DividendAmount']            = self.summaryRecord['DividendAmount'] + dividendAmount
      self.summaryRecord['DividendAmount w/Reinvest'] = self.summaryRecord['DividendAmount w/Reinvest'] + dividendAmountR
      self.summaryRecord['DividendShares']            = self.summaryRecord['DividendShares'] + dividendShares

      bodShares  = eodShares # Set value for next date
      bodSharesR = eodSharesR

    if len(actionTrueHistoryFrame) > 0:
      lastPos = actionTrueHistoryFrame.index[-1]
    else:
      print('No data in actionTrueHistoryFrame, ticker: {0}'.format(self.ticker))
      return pd.DataFrame(), pd.DataFrame()

    # Assign values in the summary dictionary
    self.summaryRecord['BOD Shares'] = actionTrueHistoryFrame.loc[lastPos,['BOD Shares']].values[0]    
    self.summaryRecord['EOD Value']  = actionTrueHistoryFrame.loc[lastPos,['EOD Value']].values[0]
    
    growthPct = 100 * (actionTrueHistoryFrame.loc[lastPos,['EOD Value']].values[0] - initialInvestment) / initialInvestment
    self.summaryRecord['EOD Value Pct Change'] = growthPct
    
    self.summaryRecord['EOD Shares']            = actionTrueHistoryFrame.loc[lastPos,['EOD Shares']].values[0]
    self.summaryRecord['BOD Shares w/Reinvest'] = actionTrueHistoryFrame.loc[lastPos,['BOD Shares w/Reinvest']].values[0]      
    self.summaryRecord['EOD Value w/Reinvest']  = actionTrueHistoryFrame.loc[lastPos,['EOD Value w/Reinvest']].values[0]
    
    # totInvestment = initialInvestment + summaryRecord['DividendAmount w/Reinvest']
    # The growthPct below is based on initial investment... if you want it based on total investment initialInvestment (div+initial) then
    # uncomment value above and use it instead of 'initialInvestment'... note this makes Pct lower; I left it based
    # on initial investment since that's really what I am in for and the dividend is really taken out of the 
    # stock price.
    growthPct = 100 * (actionTrueHistoryFrame.loc[lastPos,['EOD Value w/Reinvest']].values[0] - initialInvestment) / initialInvestment
    self.summaryRecord['EOD Value w/Reinvest Pct Change'] = growthPct
    
    self.summaryRecord['EOD Shares w/Reinvest'] = actionTrueHistoryFrame.loc[lastPos,['EOD Shares w/Reinvest']].values[0]

    # Convert dictionary to a dataframe   
    summaryRecordDataFrame = pd.DataFrame(self.summaryRecord,index=[0])

    # Return both dataframes, actionTrueHistoryFrame has a line item for each 'action' date and summaryRecordDataFrame
    # has just the one record... thought being you can collect all summary records for different stocks and then
    # perform some analysis on them
    return actionTrueHistoryFrame, summaryRecordDataFrame

  # -----------------------------------------------------------------------------------------------
  # Helper to calculate cost basis (also returns dividend revenue).  It does this pretending an initial
  # purchase of $1,000.00, it then calculates what it would be worth at the 'endingDate'; from there you
  # get a growth per dollar (gpd).  Using the gpd, you can calculate what your original cost basis is (totalInvestmentValue/gpd).
  # It also returns dpv which is dividendPerValue (dividends/endingValue), from that the caller can
  # determine dividends and subsequently what the original investment was and shares, see how it's used
  # in getCostBasis, should be clear :)
  # -----------------------------------------------------------------------------------------------
  def getCostBasisHelper(self, startDate, endingDate = "", initialInvestment = 1000, reinvestDividend = True):

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
    gpd        = totalValue / totalInvestment
    dpv        = totalDivInvestment / totalValue
    cbRec = {"Ticker": self.ticker, "StartDate": initialDate, "InitialInvestment": initialInvestment, "InitSharePrice": initialSharePrice,
             "InitialShares": initialShares, "EndingDate": finalDate, "DividendInvestment": totalDivInvestment,
             "TotalInvestment": totalInvestment, "EndingSharePrice": finalClose, "EndingShares": shares, "EndingValue":  totalValue,
             "GPD": gpd, "DPV": dpv }
    cbRecFrame = pd.DataFrame(cbRec,index=[0])

    return cbRecFrame

  # -----------------------------------------------------------------------------------------------
  # Return the cost basis for a 'startDate', it also returns the number of shares you had on that
  # date.  You can pass in the date to use as the ending window, otherwise it'll use the ending date
  # of the data.  currentInvestment represents the value of the stock for 'endingDate'; you can also
  # indicate whether you were doing dividend reinvestment or not... defaults to True.
  # Note: I used 10k as the default initial investment for the helper call; did this just as a good
  # number, you could pass in currentInvestment... wouldn't change results since we really use gpd
  # and initSharePrice from that call.  fyi: using 10k should alleviate roundoff errors if currentInvestment
  # was really small or really large.
  # -----------------------------------------------------------------------------------------------
  def getCostBasis(self, startDate, endingDate = "", currentInvestment = 1000, reinvestDividend = True):
    dataRec = self.getCostBasisHelper(startDate, endingDate, initialInvestment=10000, reinvestDividend=reinvestDividend)
    if self.DEBUGIT == True: # Show dataframe from the helper
      print(dataRec)
      print('To get your cost basis (cb), cb = investmentValue / gpd (from cost basis calc), seel below')

    costBasisAmt      = currentInvestment / dataRec.loc[0,['GPD']].values[0]
    dividendsInvested = currentInvestment * dataRec.loc[0,['DPV']].values[0]
    origInvest        = costBasisAmt - dividendsInvested
    origShares        = origInvest / dataRec.loc[0,['InitSharePrice']].values[0]
    return origShares, origInvest, costBasisAmt
 
  # --------------------------------------------------------------------------------------
  # Get dates for cost basis.  This is useful if you have a cost basis but don't know when
  # you acquired security; this will give you dates possible... within a pct of accuracy
  # The args:  costBasis ------------- The cost basis you want to find
  #            sharesOwned ----------- The shares you own on 'lastDateOwnedSecurity'
  #            lastDateOwnedSecurity - The ending date you owned security, this is optional
  #                                      if you don't pass it it'll use the last date we
  #                                      have data for.
  #            accuracyNeeded --------- The accuracy you want, defaults to 95% but can use
  #                                       value between 0.0 and 1.0 exclusive
  #            reinvestedDividend ----- Boolean to indicate whether you were doing dividend
  #                                       reinvestment
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

    # dumDate = utils.getDateFromISOString('2020-01-01')

    # Init vars
    totalDividends = 0.0
    dividendAmt    = 0.0
    splitShares    = 0.0
    firstTime      = True
    dtRec = {"Ticker": self.ticker, "CostBasis": costBasis, "sharesStartedWith": sharesOwned, "OrigPricePerShare" : costBasis/sharesOwned,
             "endDateOwned": eDate.strftime("%Y-%m-%d"), "accuracyTested": accuracyNeeded, "reinvestedDividend": reinvestedDividend,
             "Date": "", "Accuracy": 0, "SharesOwned":  0, "PricePerShare": 0, "Valuation": 0, "TotDividends": 0}

    numRecs = 0
    for index, row in tempData.iterrows():      
      if row['Date'] <= eDate:
        if firstTime: # Init for first value
          firstTime = False
          if (row['Dividend'] > 0.0 and reinvestedDividend == True):
            dividendAmt = shares * row['Dividend']
          if row['Split'] > 0:
            splitShares = shares/row['Split']
        
        # Calculate value and cost basis for this record
        theValue     = row['Close'] * shares
        theCostBasis = theValue + totalDividends
        
        # if row['Date'] >= dumDate:
        #   print('date: {0} shares: {1} value: {2} totDvidends: {3} costBasis: {4}'.format(row['Date'], shares, theValue, totalDividends, theCostBasis))

        if theCostBasis >= lowBasisRange and theCostBasis <= highBasisRange:
          dtRec["Date"] = row["Date"]
          dtRec["Accuracy"] = theCostBasis/costBasis
          dtRec["SharesOwned"] = shares
          dtRec["PricePerShare"] = row["Close"]
          dtRec["Valuation"] = theValue
          dtRec["TotDividends"] = totalDividends
          if numRecs == 0:
            dtRecFrame = pd.DataFrame(dtRec,index=[0])
          else:
            dtRecFrame = pd.concat([dtRecFrame, pd.DataFrame([dtRec])], ignore_index=False)
          numRecs = numRecs + 1

        # We now adjust the shares for the next day thru the loop (basically the shares at the start of this day,
        #  before we adjusted for split/dividends)
        if splitShares != 0.0:
          shares = splitShares
        else:
          shares = shares - dividendAmt/row['Close']

        # Calculate the dividend amount for the day, we use this to keep track of totalDividends
        dividendAmt = 0.0
        if (row['Dividend'] > 0.0 and reinvestedDividend == True):
          dividendAmt = shares * row['Dividend']

        # Calculate what the shares were prior to the split
        splitShares = 0.0
        if row['Split'] > 0:
          splitShares = shares/row['Split']

        totalDividends = totalDividends + dividendAmt

    if numRecs == 0:
      dtRecFrame = pd.DataFrame(dtRec,index=[0])

    return dtRecFrame

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
            if key.lower() != 'date':  # Ignore header line 
              if key in rtnDict:
                rtnDict[key] = rtnDict[key] + float(value)
              else:
                rtnDict[key] = float(value)
          except:
            print("Exception on getDividendsAndCapGainFromFile, ignored line: {0}".format(aLine))
    except Exception as ex:
      print("Exception {0} trying to read: {1}  file ignored".format(ex,infile))
    
    return rtnDict

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
  # Get the value for a given key from the tickerInfo data
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
    return self.getMultiplierForDate(theDate,2)

  # -----------------------------------------------------------------------------------------------
  # Return the maximum split multiplier for a given date, this could be beyond the ending data window
  #   left in code for future use but not sure if ever will be
  # -----------------------------------------------------------------------------------------------
  def getSplitMaxMultiplierForDate(self, theDate):
    return self.getMultiplierForDate(theDate,3)

  # -----------------------------------------------------------------------------------------------
  # Get the start/end date of the history data
  # -----------------------------------------------------------------------------------------------
  def getTickerInfo(self):
    return self.tickerInfo

  # -----------------------------------------------------------------------------------------------
  # Get Column from TrueHistoryDataFrame for a date
  # -----------------------------------------------------------------------------------------------
  def getTrueHistoryDataFieldForDate(self, theDate, colName):
    tempFrame = self.trueHistoryDataFrame[(self.trueHistoryDataFrame['Date']==theDate)]
    if tempFrame.empty == False:
      if colName in tempFrame:
        return tempFrame[colName].values[0]
    return None

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
    if self.mergeCapitalGains == True:
      self.dividendDataFrame = self.initDividendCapGainHelper()
    else:
      infile                 = stockUtils.getDividendFileName(self.ticker)
      self.dividendDataFrame = pd.read_csv(infile)    

    '''
    print('-------------------------------------------')
    print(self.dividendDataFrame)    
    print('-------------------------------------------')
    '''
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
  #                                (Date, Open, High, Low, Close, AdjustedClose, Volume, Dividend, Split, SplitMultiplier, SplitMaxMultiplier)
  #                                The SplitMultiplier is the value used in adjusting open, high, low, close, adjustedclose, dividend.  I put
  #                                splitmaxmultiplier in dataframe in case you want it down the road
  # -----------------------------------------------------------------------------------------------
  def initHistoryDataFrame(self):    
    infile                = stockUtils.getHistoryFileName(self.ticker)
    self.historyDataFrame = pd.read_csv(infile)    

    # Make the ISODate string a date
    self.historyDataFrame['Date'] = self.historyDataFrame['Date'].apply(utils.getDateFromISOString)

    # Check that Capital Gains column exists... rename if it does and turn off flag if it doesn't
    if ("Capital Gains" in self.historyDataFrame.columns):
      self.historyDataFrame.rename(columns = {"Capital Gains":"CapitalGains"}, inplace=True)
    else:
      self.mergeCapitalGains = False
      if self.SHOWCAPGAINMSG:
        print("Turned off mergeCapitalGains for: {0}".format(self.ticker))

    # Rename column
    self.historyDataFrame.rename(columns = {'Adj Close'     : 'AdjustedClose', 
                                            'Dividends'     : 'AdjustedDividend',
                                            'Stock Splits'  : 'Split'}, inplace=True) 
    # Some old files don't have these columns, add them if necessary (will prevent exception thrown)    
    if ('AdjustedDividend' not in self.historyDataFrame.columns):
      self.historyDataFrame['AdjustedDividend'] = 0  # 
    if ('Split' not in self.historyDataFrame.columns):
      self.historyDataFrame['Split'] = 0  
        
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
    self.trueHistoryDataFrame['SplitMultiplier']    = self.trueHistoryDataFrame['Date'].apply(self.getSplitMultiplierForDate)
    self.trueHistoryDataFrame['SplitMaxMultiplier'] = self.trueHistoryDataFrame['Date'].apply(self.getSplitMaxMultiplierForDate)
    self.trueHistoryDataFrame['Open']          = self.trueHistoryDataFrame['Open'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['High']          = self.trueHistoryDataFrame['High'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['Low']           = self.trueHistoryDataFrame['Low'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['Close']         = self.trueHistoryDataFrame['Close'] * self.trueHistoryDataFrame['SplitMultiplier']
    self.trueHistoryDataFrame['AdjustedClose'] = self.trueHistoryDataFrame['AdjustedClose'] * self.trueHistoryDataFrame['SplitMultiplier']

    # Merge the capital gains into the dividend value (mutual funds work this way)
    if self.mergeCapitalGains == True:
      self.trueHistoryDataFrame['Dividend'] = (self.trueHistoryDataFrame['Dividend'] + self.trueHistoryDataFrame['CapitalGains']) * self.trueHistoryDataFrame['SplitMultiplier']
    else:
      self.trueHistoryDataFrame['Dividend'] = self.trueHistoryDataFrame['Dividend'] * self.trueHistoryDataFrame['SplitMultiplier']
    
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
  #   splitMultiplier - calculate how many shares you'd have by 'self.endDate' if purchased in a window
  #                       this is also used in calculating values and dividends to come up with 'true'
  #                       values for a date
  #   splitMaxMultiplier  - how many shares you'd have today if you used the max split end window (which
  # #                         could be past self.endDate
  #   self.listOfSplitRange - [windowStartDate, windowEndDate, splitMultiplier, splitMaxMultiplier], so 
  #                             ['2018-11-01', '2020-01-09', 5, 10] means that shares you acquired between
  #                             11/1/2018 thru 1/9/2020 would be worth 5 shares on self.endDate, the 10 is
  #                             the number you'd have today (this is only when self.endDate is less than
  #                             latest split date)
  # -----------------------------------------------------------------------------------------------
  def initSplitRange(self):
    self.listOfSplitRange = [] 
    if not self.splitDataFrame.empty:
      self.splitDataFrame.sort_values('Date', ascending=False, inplace=True)
      splitMaxMult = 1
      splitMult    = 1
      dumbDict     = {}
      for index, row in self.splitDataFrame.iterrows(): 
        theDate      = row['Date']      
        splitAmt     = row['Split']
        splitMaxMult = splitMaxMult * splitAmt
        if theDate <= self.endDate: 
          splitMult = splitMult * splitAmt        
        dumbDict[theDate] = [splitMult, splitMaxMult]
        
      # Reset sort ascending
      self.splitDataFrame.sort_values('Date', ascending=True, inplace=True)
      
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
  # Initialize the summary record
  # -----------------------------------------------------------------------------------------------
  def initSummaryRecord(self):
    # The summary record we'll build in calculate valuation, it was put here so it could be
    # referenced in more than just that routine.
    self.summaryRecord = {'Ticker'                          : self.ticker,                     
                          'StartDate'                       : '',
                          'InitialInvestment'               : 0.0,
                          'SharesPurchased'                 : 0,
                          'EndDate'                         : '',
                          'BOD Shares'                      : 0,      
                          'DividendAmount'                  : 0, 
                          'EOD Value'                       : 0,
                          'EOD Value Pct Change'            : 0.0,
                          'EOD Shares'                      : 0,
                          'BOD Shares w/Reinvest'           : 0,
                          'DividendAmount w/Reinvest'       : 0,
                          'DividendShares'                  : 0,
                          'EOD Value w/Reinvest'            : 0,
                          'EOD Value w/Reinvest Pct Change' : 0.0,
                          'EOD Shares w/Reinvest'           : 0,
                          'ShortName'                       : self.getKeyValue('shortName'),
                          'QuoteType'                       : self.getKeyValue('quoteType')}
    
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
  
  theSymbol = 'psx'
  theSymbol = 'acsdx'
  theSymbol = 'viac'
  theSymbol = 'vsmix'
  theSymbol = 'aapl'

  stockObj = StockClass.Stock(theSymbol)
  print('Processing symbol: {0}'.format(theSymbol))
  
  # Show Ticker Info
  if 1 == 0:
    print(type(stockObj.tickerInfo),stockObj.tickerInfo)

  # Show split
  if 1 == 0:
    print('Split values below')
    for index, row in stockObj.splitDataFrame.iterrows(): 
      print("Index: {0}  Date: {1}  Split Amount: {2}".format(index, row['Date'], row['Split']))
    
    print('listOfSplitRange values below')
    for aRow in stockObj.listOfSplitRange:
      print(str(aRow))
 
  # Show dividends
  if 1 == 0:
    print('Dividend values below')
    for index, row in stockObj.dividendDataFrame.iterrows(): 
      print("Index: {0}  Date: {1}  AdjDiv: {2} RealDiv: {3}".format(index, row['Date'], row['AdjustedDividend'], row['DateDividend']))
  
  # Test utility to show splits for a particular date
  if 1 == 0:
    theDate = utils.getDateFromISOString('1993-01-01')
    print('SplitMultiplier for {0}: {1}'.format(str(theDate),stockObj.getSplitMultiplierForDate(theDate)))
    print('SplitMaxMultiplier for {0}: {1}'.format(str(theDate),stockObj.getSplitMaxMultiplierForDate(theDate)))
  
  # Show how to calc elapsed time (not related to stock object, but had for testing)
  if 1 == 0:
    tt1 = time.time()
    # Do something here...
    time.sleep(1.5)   
    tt2 = time.time()
    print('Elapsed is: {0}'.format(tt2 - tt1))

  # Write out the true history dataframe
  if 1 == 0:
    stockObj.writeDataFrame(stockObj.trueHistoryDataFrame,'aaplTrueHistoryDataFrame.csv')

  # Output true history, action history, stock history for particular date range
  if 1 == 0:
    sd, ed = '2009-01-20', '2013-01-19'
    sd, ed = '2009-01-20','2012-02-19'
    sd, ed = '1998-01-01', '1999-06-01'
    sd, ed = '1990-01-01', '2024-02-26'
    sd, ed = '2018-12-02', '2021-12-01'
    sd, ed = '1993-06-01', '1993-07-01'
    sd, ed = '2020-02-01', '2025-11-08'

    sDate = utils.getDateFromISOString(sd)
    eDate = utils.getDateFromISOString(ed)
    trueHistoryFrame = stockObj.getTrueHistoryDataFrameByRange(sDate,eDate)
    stockObj.writeDataFrame(trueHistoryFrame, '{0}TrueHistory_{1}_{2}.csv'.format(theSymbol,sd,ed))

    actionTrueHistoryFrame = stockObj.getHistoryActionData(trueHistoryFrame)
    stockObj.writeDataFrame(actionTrueHistoryFrame, '{0}ActionHistory_{1}_{2}.csv'.format(theSymbol,sd,ed))
    
    historyFrame = stockObj.getHistoryDataFrameByRange(sDate,eDate)
    stockObj.writeDataFrame(historyFrame, '{0}History_{1}_{2}.csv'.format(theSymbol,sd,ed))
   
    print('Look at CSV files written for true,action,history dataframes')    
    
    # See it on console too?
    if 1 == 1:
      print('True history data frame')
      print(trueHistoryFrame)
      print()
      print('Action history data frame')
      print(actionTrueHistoryFrame)
      print()
      print('History data frame')
      print(historyFrame)

  # Calculate valuations for a date range
  if 1 == 0:
    sd, ed = '2011-10-12','2021-10-11'
    sd, ed = '1998-01-01', '1999-06-01'
    sd, ed = '2014-11-30', '2022-10-05'
    sd, ed = '2010-03-22', '2025-02-06'
    sd, ed = '2020-08-07', '2020-09-03'
    sd, ed = '2017-12-22', '2025-02-12'
    smaNumDays = 5 # Typically used 5 but during testing don't want it (-1 signifies that)

    # Returns valuation dataframe and a summary record dataframe.
    #   Args: pass in window (startDate, endDate) , initialInvestmentAmount, boolForRecordForEachDay, #DaysForSimpleMovingAverage (-1 if don't want)    
    
    tickerValu, tickerSumm = stockObj.calculateValuation(sd, ed, 2654.22, False, numdaysInSimpleMovingAverage=smaNumDays) 

    stockObj.writeDataFrame(tickerValu, '{0}Valuation_{1}_{2}.csv'.format(theSymbol,sd,ed))
    stockObj.writeDataFrame(tickerSumm, '{0}ValuationSummary_{1}_{2}.csv'.format(theSymbol,sd,ed))

  # Calculate valuations for a date range
  if 1 == 0:
    sd, ed = '2020-08-07', '2020-08-31'  # Dividend on start, .205, Split on end date 4 for 1
    sd, ed = '2020-08-07', '2020-09-01'  # Dividend on start, .205, Split the day before on 8/31 4 for 1
    smaNumDays = -1 # Typically used 5 but during testing don't want it (-1 signifies that)

    # Returns valuation dataframe and a summary record dataframe.
    #   Args: pass in window (startDate, endDate) , initialInvestmentAmount, boolForRecordForEachDay, #DaysForSimpleMovingAverage (-1 if don't want)    
    
    tickerValu, tickerSumm = stockObj.calculateValuation(sd, ed, 1000.0, True, numdaysInSimpleMovingAverage=smaNumDays) 

    stockObj.writeDataFrame(tickerValu, '{0}Valuation_{1}_{2}.csv'.format(theSymbol,sd,ed))
    stockObj.writeDataFrame(tickerSumm, '{0}ValuationSummary_{1}_{2}.csv'.format(theSymbol,sd,ed))


  # Calculate cost basis
  if 1 == 0:
    theDate = '1990-06-14'
    theDate = '2014-11-30'
    
    theDate            = '2020-01-01'
    theEndDateOverride = '2025-02-06'
    endDateValue       = 3132.12

    shares, origInvest, costBasisAmt = stockObj.getCostBasis(theDate, theEndDateOverride, currentInvestment=endDateValue,reinvestDividend=True)
    print('{0} investment: ${1:.2f} buying {2:.2f} shares, currentValue: ${3} has costBasis: ${4:.2f}'.format(theDate,origInvest,shares,endDateValue,costBasisAmt))
    
  # Get the date for a cost basis
  if 1 == 0:    
    # Args to below: costbasis, sharesowned, datelastowned, accuracy (default 95%) dividendreinvestment (default True)
    costBasis          = 5885.58
    sharesOwned        = 392
    dateLastOwned      = '2025-02-06'
    accuracy           = .99
    dividendReinvested = True
    dateOfBasis = stockObj.getDatesForCostBasis(costBasis, sharesOwned, dateLastOwned, accuracy, dividendReinvested) # ,accuracyNeeded = 0.95, reinvestedDividend = True)
    print(dateOfBasis)

  # Example below gets the unadjusted (actual) closing price of a stock on a given date
  if 1 == 1:
    theDateStr = '2021-08-24'
    theDateStr = '2015-01-02'
    theCol     = 'Close'
    theDate    = utils.getDateFromISOString(theDateStr)
    
    theValue = stockObj.getTrueHistoryDataFieldForDate(theDate, theCol)
    print('{0} for {1} is: {2}'.format(theCol, theDateStr, theValue))

  print('\n\n\nDone processing symbol: {0}'.format(theSymbol))

  print('Short name is: {0}'.format(stockObj.getKeyValue('shortName')))