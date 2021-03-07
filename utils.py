import datetime

# Return date object
def getDateFromISOString(isoDateString):
  return datetime.date(*map(int, isoDateString.split('-')))

# ------------------------------------------------------------------------------
#  T E S T I N G
# ------------------------------------------------------------------------------
if __name__ == "__main__":
  print(getDateFromISOString('2020-02-01'))
  