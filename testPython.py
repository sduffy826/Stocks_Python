import pandas as pd 
import numpy as np

def testDataFrame():
  # create a simple dataframe
  df = pd.DataFrame( {'a':[1,2,3], 'b':[4,5,6]})

  # look at the column names
  print('Original')
  print(df)

  # define a function we will pass
  # our dataframe to that will 
  # change the dataframe some way
  def change_df_col_names(my_df):
      my_df['a'] = my_df['a'] * my_df['a']
      my_df.columns = ['c', 'd']
      return

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