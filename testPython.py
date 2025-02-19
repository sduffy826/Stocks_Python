import pandas as pd 
import numpy as np
import utils as utils

def testDataFrame():
  # create a simple dataframe
  df = pd.DataFrame( {'a':[1,2,3,4,5,6,7,8,9,10], 'b':[11,12,13,14,15,16,17,18,19,20]})

  currencyDf = pd.DataFrame( {'shares':[101,202,33], 'value':['$505.00','$4040.00','$99.99']})

  # look at the column names
  print('Original')
  print(df)
  print(currencyDf)

  # define a function we will pass
  # our dataframe to that will 
  # change the dataframe some way (we'll square col a and change col names)
  def change_df_col_names(my_df):
      my_df['a'] = my_df['a'] * my_df['a']
      my_df.columns = ['c', 'd', 'sma_c']
      return

  def simple_moving_average(df, numDays=5):
    df['sma_a'] = df.loc[:,'a'].rolling(window=numDays).mean()    
    return

  # Calculage moving average
  simple_moving_average(df)
  print('\nAfter SMA function call, defaults with 5')
  print(df)

  simple_moving_average(df,3)
  print('\nAfter SMA function call with 3')
  print(df)


  # now pass the original dataframe 
  # into the function
  change_df_col_names(df)

  # look at the column names for the
  # original object
  # note that we did not assign the
  # return value of the function to
  # the original variable name,
  # so it is the same reference as
  # before we called the function
  print('\nAfter function call')
  print(df)

  print('\n\nCurrency')
  print(currencyDf)
  currencyDf['value'] = currencyDf['value'].apply(utils.convertToNumIfPossible)
  print(currencyDf)
  print(type(currencyDf.iloc[0]['value']))

  # Referemce amd change individual values
  someDict = {'col1': 5, 'col2': 'John Doe'}
  tempDictDf = pd.DataFrame(someDict,index=[0])
  tempDf     = pd.DataFrame( {'col1':[1,2,3,4,5], 'col2':[11,12,13,14,15]})
  print('printing dataframe values, tempDictDf then tempDf')
  print(tempDictDf)
  print()
  print(tempDf)

  print('\nReference individual items')
  
  print("tempDictDf.loc[0,['col2']]: {0}   Type: {1}".format(tempDictDf.loc[0,'col2'],type(tempDictDf.loc[0,'col2'])))
  print("tempDf.loc[2,['col1']]: {0}   Type: {1}".format(tempDf.loc[2,'col1'],type(tempDf.loc[2,'col1'])))

  print('\nChanged value')
  tempDictDf.loc[0,'col2'] = 'Peter Rooter'  
  print("tempDictDf.loc[0,['col2']]: {0}   Type: {1}".format(tempDictDf.loc[0,'col2'],type(tempDictDf.loc[0,'col2'])))

def testFunc(arg1, arg2=5):
   print('arg1:{0}: arg2:{1}:'.format(arg1,arg2))

# Test arguments
if 1 == 0:
  var2 = None
  testFunc('abc',var2)

if 1 == 1:
  testDataFrame()