# Common (global) variables
import datetime

urlEndpoint = 'http://localhost:8080'

# Path to where the data files are stored
pathToData  = './data'

# Path to where the analysis files are written
pathToAnalysis = './output'

one_day = datetime.timedelta(days=1)

# How many days in the moving average, this is default value used in StockClass, it can be
# overriden during analysis (by passing a different value in StockAnalysis... and will be ignored if StockAnalysis
# passes a -1)
movingAverageNumDays = 5