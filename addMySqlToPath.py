import sys
import os

# This is a little stub of code to import the common mySql routines.  The
# path for this should be in ../MySqlCommon

# It basically adds '../MySqlCommon' to the search path, this allows you to
# do the imports.  To use your code would typically be coded:
#   from addMySqlToPath import *
#   import mySqlRoutines as mySql
# Note: _parentPath isn't visible but I left mySqlPath visible in case you wanted
#        it.
_parentPath = os.path.dirname(os.getcwd())  # Make this var local
mySqlPath  = _parentPath + '/MySqlCommon'   
sys.path.insert(0, mySqlPath)