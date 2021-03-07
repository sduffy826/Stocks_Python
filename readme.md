# Stock related routines

This has some code I developed to save stock data and also perform analysis.  I originally
was planning on storing all the data in MySql tables but after doing some of the work I 
changed direction and started using the 'Files' instead.  That section of code is the 
newest.  You can still use/enhance the other code as you see fit.

## Broken into various types: Http, MySql and Files (Files is newest)

### Http Version (This made http calls to a server which did the work)
- httpStockSymbol.py - CRUD routines for StockSymbol table
- httpStockAttributesForDay - CRUD for the StockAttributesForDay table

### MySql Version
- **NOTE** Dependent on MySqlCommon directory, see readme in that project 
- mySqlStockSymbol.py - CRUD routines for StockSymbol table
- **Also Note** I moved away from this and was just keeping data in csv files for analysis... quicker
  than accessing database... may pick this up again but for now it's shelved... look at the 
  description below for more info on the 'latest' stuff
- Also, I didn't write the code for StockAttributesForDay yet... using the http code to do crud

### Files (latest code)
<p><strong>Note</strong> Most of the files have 'test' logic in them (i.e. you can easily test the routines in 
   stockUtils.py even though it's designed to be called externally.... just look hear the
   bottom of the file)</p>

<h4>Code overview</h4>   
<dl>
  <dt><strong>StockAnalysis.py</strong></dt>
    <dd>This is the <strong>main routine of interest</strong>, it will calculate the valuation
        for all the stocks you are interested in.  The variable fileWithSymbols
        has a list of the files you want to process (each having a list of
        ticker symbols).  Note the useCommonDateWindow will determine if all
        the stocks will have a common window (start/end) or will use the date
        you specified (common window is applicable when stock doesn't have
        historical data based on the window you wanted..).  Also note that the
        startWindow, endWindow variables should reflect the window you want
        to do for analysis.  It will output a csv file with the name
        summaryValuations_yyyy-mm-dd_yyyy-mm-dd.csv (the yyyy-mm-dd's are
        the start/end window).  fyi: filename set in stockUtils-getSummaryValuationFileName()</dd>

  <dt><strong>StockClass.py</strong></dt>
    <dd>Class to encapsulate the Stock attributes for a particular symbol.  It 
        relies on data in the CSV files, it doesn't pull from any external
        source.  It has methods to:
        <ul>
          <li><strong>calculateValuation(...)</strong> calculates what the value of a stock would be if you held 
                                                       it for window, this is <strong>VERY USEFUL</strong></li>
          <li><strong>getFilteredMultiplierForDate(...)</strong> returns the split multiplier for a date, this uses 
                                                                 the window from the date passed in up to the ending date
                                                                 of the history data</li>
          <li><strong>getHistoryActionData(...)</strong> returns dataframe with the first and last row of the dataframe
                                                         passed in as well as all the dividends and splits in that
                                                         dataframe... it drops dupes (in case first or last record
                                                         was a split or dividend event))</li>
          <li><strong>getHistoryDataFrameByRange(...)</strong> returns the history data for a particular
                                                               window (passed in)</li>
          <li><strong>getHistoryWindow()</strong> returns the window for the history data (start/end dates)</li>
          <li><strong>getMultiplierForDate(...)</strong> helper method, returns split multiplier for given 
                                                         date/split type; not meant to be called directly use
                                                         getFilteredMultiplierForDate() or getSplitMultiplierForDate()</li>
          <li><strong>getSplitMultiplierForDate(...)</strong> returns the split multiplier that should be used for 
                                                              the date passed in.  Uses splits from this date thru 
                                                              the ending window of the history data to calculate it 
                                                              (i.e. if splits 2:1 3:1 2:1 have occured since then 
                                                              the split multiplier is 12)</li>
          <li><strong>getTrueHistoryDataFrameByRange(...)</strong> returns a copy of the 'trueHistoryDataFrame'
                                                                    for the given window.  Note: the trueHistoryDataFrame 
                                                                    has the values for that date adjusted (by split amt) 
                                                                    to represent what the 'real' prices where on that date.</li>
          <li><strong>initXXX(...)</strong> there are a bunch of 'init' methods to initialize various attributes
                                            related ot the stock... the splitMultiplier, dividendDataFrame, historyDataFrame,
                                            trueHistoryDataFrame, splitDataFrame, listOfSplitRange...</li>
          <li><strong>writeDataFrame(...)</strong> helper method, writes the dataframe passed in to the filename
            also passed in.</li>
    </dd>

  <dt><strong>stockUtils.py</strong></dt>
    <dd>Common utilities,
      <ul>
        <li><strong>appendLogDates(...)</strong> This will write the arguments to a history log file, that
                                                 file is useful as it shows what the start and end date
                                                 that was used for the last yahoo stock pull</li>
        <li><strong>getDividendFileName(...)</strong> Returns the name of the file that has the dividends for
                                                      the particular ticker symbol passed in</li>
        <li><strong>getHistoryFileName(...)</strong> Returns the name of the file that has the historical
                                                     prices for the ticker passed in</li>
        <li><strong>getHistoryLogFileName()</strong> Returns the name of the log file that shows when the last
                                                     history data was pulled.</li>
        <li><strong>getLogStartEndDate(...)</strong> Returns the start and end date of the last entry in the log
                                                     file... this is the start/end window of the history
                                                     data that was pulled.</li>
        <li><strong>getSplitFileName(...)</strong> Returns the name of the file that contains the split information
                                                   for the ticker symbol passed in.</li>
        <li><strong>getSummaryValuationFileName(...)</strong> Returns the name of the summary valuations file, this is 
                                                              the file created via StockAnalysis</li></ul>
    </dd>

  <dt><strong>stockVars.py</strong></dt>
    <dd>Global variables</dd>
  
  <dt><strong>YFinanceClass</strong></dt>
    <dd>Creates 'ticker' object.  It uses 'yfinance' to get data from yahoo and has methods to provide
        this data.  Methods are:
        <ul>
          <li><strong>getCalendar()</strong> Gets next event earnings etc</li>
          <li><strong>getInfo()</strong> has a ton of info about the ticker, look at test section
                                        to do a trial run to see what's returned</li>
          <li><strong>getInstitutionalHolders()</strong> Get institutional holders, cols: index, holder, 
                                                        shares, date reported, % Out, Value</li>
          <li><strong>getOptionChain(...)</strong> Get option chain for a specific expiration date 
                                                  (date is string isodate yyyy-mm-dd)</li>
          <li><strong>getOptions()</strong> Get option expirations</li>
          <li><strong>getRecommendations()</strong> Get recommendations</li>
          <li><strong>getShortName()</strong> Returns shortname (wrapper for ...getInfo()['shortName'])
          <li><strong>saveDivSplit()</strong> Saves the dividends and splits to data file (uses stockUtils to
                                              get destination name</li>
          <li><strong>saveHist()</strong> Saves the stock historical prices to a data file (uses stockUtils also)</li>
        </ul>
    </dd>

  <dt><strong>testPython</strong></dt>
    <dd>Just 'test/playground' code, left just for info/play :)</dd>

  <dt><strong>utils</strong></dt>
    <dd>Utility routines (not specific to stocks).  Methods are:
        <ul>
          <li><strong>getDateFromISOString(isoDateString)</strong> Return date object for the iso date string
                                                                   passed in</li>
        </ul>
    </dd>
    
  <dt><strong>YFinanceProcessHistory</strong></dt>
    <dd>This program <strong>pulls the yahoo stock information</strong> (historical prices,
        dividends and splits) and writes the data to csv files.  Variable 'fileWithSymbols' represents 
        the name of the file with the tickers to pull.  Note: Most of the work is done in the 
        YFinanceClass routine.</dd>
</dl>


<h3>Notes/Test Drive</h3>
<ul>
  <li><strong>The data directory</strong> is defined as global variable in stockVars.py, you obviously need to re-pull
    data if you change this.  The <strong>analysis output directory</strong> is also defined in stockVars.py</li>
  <li><strong>Make sure</strong> the directories specified above exist on your machine</li>
  <li><strong>Names of data/output files</strong>: program stockUtils.py gives the programs the names of the data files, both
    on creation (YFinanceClass) and on reading.  If you want to change it just modify stockUtils.py and re-pull data (YFinanceProcessHistory); you're then ready to do analysis (StockAnalysis)</li>
  <li><strong>Getting data from yahoo</strong>
    <ul>
      <li>Have a file that contains the symbols you want to pull (i.e. All.symbols), the first word in each record
          should be the ticker, the data after that is ignored (down the road can change to reflect # of shares or
          purchase/sell transactions etc...)</li>
      <li>Make sure variable <strong>fileWithSymbols</strong> (in YFinanceProcessHistory.py) has the name of 
          the file you created/updated</li>
      <li>Run <strong>YFinanceProcessHistory.py</strong>, it will pull the data and store the results in the 
          stockVars.py-pathToAnalysis directory</li>      
    </ul>    
  </li>
  
  <li><strong>Doing analysis</strong> (example)
    <ul>
      <li><strong>Update StockAnalysis.py</strong>
        <ul>
          <li>Have variable <strong>fileWithSymbols</strong> point to the file that has a list of 
              the symbols you want to analyze</li>
          <li>Set variable <strong>useCommonDateWindow</strong> to reflect how you want to treat the window of
              dates for each stock... if your trying to compare end of date valuations then you probably want
              all dates to align, if calculated average compound rate (see below) then they don't have to align</li>
          <li>Set the 'startWindow, endWindow' variables to be the window you want to analyze</li>
        </ul>
      </li>
       <li><strong>Run StockAnalysis.py</strong>, afterward look at the output file created, will be in the 
        stockVars.py-pathToAnalysis directory  (see note below on compound rate)</li>
    </ul>   
  </li>

  <li><strong>Calculating the compound growth rate</strong> good to see the avg annual growth over timespan.
    I manually added values to the output generated from the StockAnalysis program.  The description below
    shows what I did.
    <p>The table below shows the columns you need to add to the spreadsheet in question.  This was
       very valuable in my analysis, once you've done this in one spreadsheet just copy/paste
       the formulas into a new one (but u know that)
       <br/>Note: you could consolidate these cols, but I used four cols to make it easy to see what
      I'm doing</p>
    <table>
      <tr>
        <th>ColName</th>
        <th>Formula</th>
        <th>Notes</th>
      </tr>
      <tr>
        <td>DateDiff</td>   <td>=datedif(startDateColumn,endDateColumn,"d")/365</td>  <td>Years (as real #)</td>
      </tr>
      <tr>
        <td>OneOverDateDiff</td>  <td>=1/DateDiff</td>  <td></td> 
      </tr>
      <tr>
        <td>EndValueOverStartValue</td>  <td>=EndingValueColumn/StartingValueColumn</td> 
                                            <td>If using summary csv file may be column O divided by column D</td>
      </tr>
      <tr>
        <td>CompoundGrowthRate</td>  <td>=Power(EndValueOverStartValue,OneOverDateDiff)-1</td>  <td>What u want :)</td>      
      </tr>
     </table>    
  </li>
</ul>
  
