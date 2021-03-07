import stockVars as gv

# Append the log dates passed in to the logfile, note we'll only write to log if
# dates differ
def appendLogDates(startDate, endDate, restOfRecord=""):
  sDate = str(startDate)
  eDate = str(endDate)

  sd, ed = getLogStartEndDate()
  if sd != sDate or ed != eDate:
    with open(getHistoryLogFileName(),'a+') as theFile:
      theFile.write("{0} {1} {2}\n".format(sDate,eDate,restOfRecord))
  else:
    if 1 == 0: # Was here during testing, don't need message now :)
      print('Log already has: {0} / {1}'.format(sd,ed))

# Return the filename that has the dividend info
def getDividendFileName(ticker):
  return "{thePath}/{ticker}_Dividends.csv".format(thePath=gv.pathToData,ticker=ticker)

# Return the history filename
def getHistoryFileName(ticker):
  return "{thePath}/{ticker}_History.csv".format(thePath=gv.pathToData,ticker=ticker)

# Return the history log filename, this is the file that has a log of when the
# 'history' stock data was pulled
def getHistoryLogFileName():
  return "{thePath}/historyDataPull.log".format(thePath=gv.pathToData)  

# Get the start end dates from the log file, we return the values from the last record
# on file
def getLogStartEndDate(showFile=False):
  sDate, eDate = '', ''
  with open(getHistoryLogFileName(),'r') as theFile:
    for aLine in theFile:
      theDates = aLine.strip().split(' ')      
      if len(theDates) > 1:
        sDate = theDates[0]
        eDate = theDates[1]
        if showFile:
          print('in getLogStartEndDate, sDate: {0} eDate: {1}'.format(sDate,eDate))
  return sDate, eDate

# Return the filename with the split data
def getSplitFileName(ticker):
  return "{thePath}/{ticker}_Splits.csv".format(thePath=gv.pathToData,ticker=ticker)

# Return name of summaryValuations file (it includes the start/end window)
def getSummaryValuationFileName(startDate, endDate):
  return "{0}/summaryValuations_{1}_{2}.csv".format(gv.pathToAnalysis,startDate,endDate)  

# ------------------------------------------------------------------------------
#  T E S T I N G
# ------------------------------------------------------------------------------
if __name__ == "__main__":
  print(getDividendFileName('msft'))
  print(getHistoryFileName('qqq'))
  print(getSplitFileName('aapl'))
  print(getSummaryValuationFileName('2020-01-02','2021-03-04'))

  if 1 == 0:
    # If want to test appending to log file, but delete record afterward so that
    # you don't mess up the connection between history data and dates of pull
    appendLogDates('2020-01-01','2020-01-15','Log created on 2021-02-09')

  # Get the log record start/end date, passing the optional True parm will
  # tell called routine to show each record in the file
  startDate, endDate = getLogStartEndDate(True)
  print('startDate: {0} endDate: {1}'.format(startDate,endDate))


