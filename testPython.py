import pandas as pd 
import numpy as np

def testDataFrame():
  # create a simple dataframe
  df = pd.DataFrame( {'a':[1,2,3,4,5,6,7,8,9,10], 'b':[11,12,13,14,15,16,17,18,19,20]})

  # look at the column names
  print('Original')
  print(df)

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




testDataFrame()