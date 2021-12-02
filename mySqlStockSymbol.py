import sys
import os

DEBUGIT = False

from addMySqlToPath import *
import mySqlRoutines as mySql 

# Delete record by it's ticker symbol, return number of records deleted
def deleteByTickerSymbol(tickerSymbol):
  recsAffected = 0
  mySql.init()
  if mySql.DEBUGIT:
    print("mySqlStockSymbol-deleteByTickerSymbol ticker: {0}".format(tickerSymbol))

  theStmt = """delete from corti.stock_symbol where ticker_symbol=%s"""
  if mySql.doUpdate:   
    mySql.cursor.execute(theStmt,(tickerSymbol, ))
    recsAffected = mySql.cursor.rowcount
    mySql.connection.commit()
  return recsAffected

# This returns a list where each row is a map containing the stock_symbol record
def getAllExistingStockSymbols():
  mySql.init()
  theStmt = """select * from corti.stock_symbol order by ticker_symbol"""
  mySql.cursor.execute(theStmt)
  listOfDictOfValues = mySql.cursor.fetchall()
  mySql.connection.commit()
  if mySql.DEBUGIT:
    print("getAllExistingStockSymbos")
    for aRow in listOfDictOfValues:
      print(str(aRow))
  return listOfDictOfValues

# Return dictionary where key is ticker and row has the company name
# NOTE: This is really the routine you want to call to get dictionary of
# values for tickers, passing no arg gives all tickers, passing one will
# return just that record
def getDictOfSymbols(_tickerSymbol=""):
  if len(_tickerSymbol) > 0:
    theList = getSingleStockSymbol(_tickerSymbol)
  else:
    theList = getAllExistingStockSymbols()
  theDict = {}
  for aRow in theList:
    theKey = aRow["ticker_symbol"]
    theValue = aRow["company_name"]
    theDict[theKey] = theValue
  return theDict

# This returns a list (should only be list of 1) where each row is a map containing 
# the stock_symbol record... note: use the getDictOfSymbols routine, it'll return
# the dictionary for the one record (it calls this routine)
def getSingleStockSymbol(_tickerSymbol):
  if mySql.DEBUGIT:
    print("mySqlStockSymbol-getSingleStockSymbol arg: {0}".format(_tickerSymbol))
  
  mySql.init()
  theStmt = """select * from corti.stock_symbol where ticker_symbol=%s"""
  mySql.cursor.execute(theStmt,(_tickerSymbol,))
  listOfDictOfValues = mySql.cursor.fetchall()
  mySql.connection.commit()
    
  return listOfDictOfValues

# Insert record into the table, return record count of record inserted
# NOTE: this routine shouldn't be called directly.. use the updateStockSymbolRecord
#       routine... it'll call this one if an insert is applicable
def insertStockSymbolRecord(_tickerSymbol, _stockName):
  recsAffected = 0
  mySql.init()

  theStmt = """insert into corti.stock_symbol (ticker_symbol, company_name) \
                          values(%s, %s)"""
  if mySql.DEBUGIT:
    print("mySqlStockSymbol-insertStockSymbolRecord: {0}".format(theStmt))

  if mySql.doUpdate:
    mySql.cursor.execute(theStmt,(_tickerSymbol, _stockName))
    recsAffected = mySql.cursor.rowcount
    mySql.connection.commit()    
  return recsAffected

# Update record based on args in, NOTE: this routine handles inserts and upates so it
# is the routine that should be called for both (don't call insert... directly)
def updateStockSymbolRecord(_ticker, _symbolName):
  recsAffected = 0

  dictOfData = getDictOfSymbols(_ticker)
  if len(dictOfData) > 0:
    if dictOfData[_ticker] == _symbolName:
      if mySql.DEBUGIT:
        print("mySqlStockSymbol-updateStockSymbolRecord, no update necessary")

      recsAffected = 1 # We don't need to do update but make it look like we did
    else:
      mySql.init()
      theStmt = """update corti.stock_symbol set company_name=%s where ticker_symbol=%s"""
      if mySql.DEBUGIT:
        print("mySqlStockSymbol-updateStockSymbolRecord: {0}".format(theStmt))

      if mySql.doUpdate:
        mySql.cursor.execute(theStmt,(_symbolName, _ticker))
        recsAffected = mySql.cursor.rowcount
        mySql.connection.commit()
  else:
    recsAffected = insertStockSymbolRecord(_ticker, _symbolName)
  return recsAffected

# ------------------------------------------------------------------------------------
#   T E S T I N G
# ------------------------------------------------------------------------------------
if __name__ == "__main__":
  listOfEverything = getAllExistingStockSymbols()
  listOfSymbols    = getDictOfSymbols()
  for aRow in listOfEverything:
    print(str(aRow))
  print("\n\n")

  for key in listOfSymbols:
    print("key: {0} value: {1}".format(key,listOfSymbols[key]))

  # Delete by ticker
  if 1 == 0:
    numDeleted = deleteByTickerSymbol('FOO')
    print("Number of records deleted: {0}".format(numDeleted))

  # This is for inserts and updates
  if 1 == 0:
    updateStockSymbolRecord("GOOG","Google")

  mySql.cleanup()

