import datetime
import os
import pandas as pd

# Convert string to number if possible, string can be currency, float or int format
def convertToNumIfPossible(argIn):
  if isinstance(argIn,str):
    temp = argIn.strip().replace('$','')     
    if temp.replace('.','').isnumeric():
      if '.' in temp:
        return float(temp)
      else:
        return int(temp)
    else:
      return temp
  else:
    return argIn

# Return days between two date objects
def daysBetween(date1, date2):
  return abs((date2-date1).days)

# Return boolean if file exists
def fileExists(fileAndPath):
  return os.path.exists(fileAndPath)

# Return date object from an ISO date string (yyyy-mm-dd)
def getDateFromISOString(isoDateString):
  return datetime.date(*map(int, isoDateString.split('-')))

# Return date object from an long usa date string (mm/dd/yyyy)
def getDateFromLongUSA(longUSADateString):  
  return datetime.datetime.strptime(longUSADateString,'%m/%d/%Y').date()

# Read the csv file passed in and return a dataframe with the data, the first
# line in the file should be the header (line=0)
def readCSV(filename):
  dataframe = pd.read_csv(filename,header=0)
  return dataframe

# ------------------------------------------------------------------------------
#  T E S T I N G
# ------------------------------------------------------------------------------
if __name__ == "__main__":
  date1 = getDateFromISOString('2020-02-01')
  date2 = getDateFromLongUSA('2/12/2025')

  print('date1: {0}  date2: {1}  daysBetween: {2}'.format(date1, date2, daysBetween(date1, date2)))
  
  print("\nfileExists('utils.py') returned: {0}".format(fileExists('utils.py')))
  print("fileExists('utilZ.py') returned: {0}".format(fileExists('utilZ.py')))
