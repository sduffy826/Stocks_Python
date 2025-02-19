import utils as utils
import pandas as pd

# List all the columns in the datafram and their type
def printCols(dataframe):
  idx = 0
  for colname in dataframe.columns:
    print("Column: {0} Index:{1} Type: {2}".format(colname,idx,type(dataframe[colname])))
    idx = idx + 1

# Print out up to 'numrecs' of data, print as a tuple
def printData(dataframe,numrecs=5,showHeader=False):
  if showHeader:
    print(dataframe.columns)
  idx = 0
  for row in dataframe.itertuples():
    if idx < numrecs:
      print(row)
    idx = idx + 1 
    
# Remove any space in the column names
def stripSpaceInCols(dataframe):
  theCols = []
  didChange = False
  for colname in dataframe.columns:
    if colname.count(" ") > 0:
      theCols.append(colname.replace(" ",""))
      didChange = True
    else:
      theCols.append(colname)
  if didChange:
    dataframe.columns = theCols


# Testing some of the routines
if __name__ == "__main__":
  df = utils.readCSV('transactions.csv')
  # Show original column names
  print('Original columns')
  printCols(df)

  stripSpaceInCols(df)
  
  # Show stripped column names
  print('\nColumn names stripped of whitespace')
  printCols(df)

  print('\nDatatypes')
  print(df.dtypes)

  print('\ndf.head(2)')
  print(df.head(2))

  print('\nprintData(df)')
  printData(df)
