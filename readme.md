<!--  NOTE NOTE NOTE, to preview this in VSCode hit: ctrl+shift+v  -->

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

<h3>Code overview</h3>   
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
   
  <dt><strong>GenTransactionOrPortfolioAnalysis.py</strong></dt>
    <dd>This is also <strong>very valuable</strong>, the main purpose of this is to generate a 
        summaryValuation spreadsheet for stock transaction data; beneficial if you want to 
        see how sold assets compare to purchased ones. i.e. say you sold 10k of exxon 5 years ago
        and bought 10k worth of amazon, you create a transaction file with both items and you
        can see if you were wise, or a fool.<br/>
        It can also generate summaryValuation based on a portfolio spreadsheet but that doesn't 
        seem as valuable unless it's and old portfolio file and want to see what current 
        valuation might be.
        <br/>There's good comments at the top of the program telling you how to use it, read them</dd>

  <dt><strong>StockAnalysisForDataFrame.py</strong></dt>
    <dd>Really a wrapper/utility, it generates the valuation data for values in a dataframe, this
        is used by the GenTransactionOrPortfolio program.</dd>

  <dt><strong>StockClass.py</strong></dt>
    <dd>Class to encapsulate the Stock attributes for a particular symbol.  It 
        relies on data in the CSV files, it doesn't pull from any external
        source.  It has methods to:
        <ul>
          <li><strong>calculateValuation(...)</strong> calculates what the value of a stock would be if you held 
                                                       it for window, this is <strong>VERY USEFUL</strong></li>
          <li><strong>getCostBasisHelper</strong> Helper method to calculate cost basis, used by getCostBasis</li>
          <li><strong>getCostBasis</strong> Returns the cost basis for a given startingDate, also returns the number
                                            of shares you had on that date; you basicially give it the present day
                                            value of a stock and an indicator whether you do dividend reinvestment
                                            and it'll return the cost basis for the requested date (and shares).
                                            You can also give it the ending date of the value you provide isn't 
                                            'present day'.  Read desc in code, it'll help if this isn't klear.</li>   
          <li><strong>getDatesForCostBasis</strong> Gets you the dates you could have purchased a security.  ie. Say
                                                    you have the cost basis, but you'd like to know when you purchased 
                                                    the security.  This can give you the potential dates.  There are
                                                    args for dividendReinvestment, accuracy desired, ending date you
                                                    owned security.</li>                                                    
          <li><strong>getDividendsAndCapGainFromFileHelper(...)</strong> returns dictionary of dividends or capital gain
                                                                         values from the file passed in.</li>
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
          <li><strong>getKeyValue()</strong> returns value for given key in the 'ticker info data'</li>
          <li><strong>getMultiplierForDate(...)</strong> helper method, returns split multiplier for given 
                                                         date/split type; not meant to be called directly use
                                                         getFilteredMultiplierForDate() or getSplitMultiplierForDate()</li>
          <li><strong>getSplitMultiplierForDate(...)</strong> returns the split multiplier that should be used for 
                                                              the date passed in.  Uses splits from this date thru 
                                                              the ending window of the history data to calculate it 
                                                              (i.e. if splits 2:1 3:1 2:1 have occured since then 
                                                              the split multiplier is 12)</li>
          <li><strong>getSplitMaxMultiplierForDate(...)</strong> returns the maximum split multiplier, this is not currently
                                                                 called anywhere, may come into play down the road (read code
                                                                 if want more info)</li>                     
          <li><strong>getTickerInfo()</strong> returns the tickerInfo object</li>
          <li><strong>getTrueHistoryDataFieldForDate(...)</strong> Get value for a specific column from TrueHistoryDataFrame, 
                                                                   for a specific date</li>
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
        <li><strong>checkHasData(...)</strong>  Takes a dataframe and checks that there's data that's been
                                                pulled for it, optional args to delete tickers that don't have
                                                data.  It returns a list of tickers that don't have data, you
                                                can use that to pull their data</li>
                                                # Return the filename that has the capital gain info (really applicable for mutual funds)
        <li><strong>getCapGainleName(...)</strong> Returns the name of the capital gain file for 
                                                      the particular ticker symbol passed in</li> 
        <li><strong>getDividendFileName(...)</strong> Returns the name of the file that has the dividends for
                                                      the particular ticker symbol passed in</li>
        <li><strong>getHistoryFileName(...)</strong> Returns the name of the file that has the historical
                                                     prices for the ticker passed in</li>
        <li><strong>getHistoryLogFileName()</strong> Returns the name of the log file that shows when the last
                                                     history data was pulled.</li>                                                     
        <li><strong>getInfoFileName(...)</strong> Returns the name of the ticker info file (it's a json format file) for
                                                     the ticker passed in</li>                                                             
        <li><strong>getLogStartEndDate(...)</strong> Returns the start and end date of the last entry in the log
                                                     file... this is the start/end window of the history
                                                     data that was pulled.</li>
        <li><strong>getSplitFileName(...)</strong> Returns the name of the file that contains the split information
                                                   for the ticker symbol passed in.</li>
        <li><strong>getSummaryValuationFileName(...)</strong> Returns the name of the summary valuations file, this is 
                                                              the file created via StockAnalysis</li>
        <li><strong>getValuationFileName(...)</strong> Returns the name of the valuations file, this is 
                                                       the file created via StockAnalysis</li>
        <li><strong>hasData(...)</strong> Returns boolean indicating the existance of history data for the ticker        
                                          passed in</li>                                                              
        <li><strong>loadDictionary(...)</strong> Reads the file passed in and returns a dictionary, the file passed
                                                 in should be a json formatted dictionary</li>
        <li><strong>saveDictionary(...)</strong> Saves the dictionary passed in to a file (also passed in), the file 
                                                 is written in json format</li>                                                
      </ul>                                                              
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
    <dd>Various utility routines (not specific to stocks).</dd>

  <dt><strong>dataframeUtils</strong></dt>
    <dd>Various dataframe utility routines</dd>
    
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
  
  <li><strong>Doing analysis for tickers</strong> (example)
    <ul>
      <li><strong>Update StockAnalysis.py</strong>
        <ul>
          <li>Have variable <strong>fileWithSymbols</strong> point to the file that has a list of 
              the symbols you want to analyze</li>
          <li>Update variable <strong>numDaysOfSMA</strong> to identify if you want to use a simple moving
              average for calculations... this will flatten spikes around the start/end window.  If you 
              don't want to use SMA then set value to -1 (note the value in StockClass is just a default
              to set the value of closeSMA and won't be used if you pass -1; also... it's just set for efficiency
              if the value you have here matches the global value value then it won't have to recalculate
              the sma)</li>
          <li>Set variable <strong>useCommonDateWindow</strong> to reflect how you want to treat the window of
              dates for each stock... if your trying to compare end of date valuations then you probably want
              all dates to align, if calculated average compound rate (see below) then they don't have to align</li>
          <li>Set the 'startWindow, endWindow' variables to be the window you want to analyze (or pass them, see
              'runStockAnalysis' below</li>
        </ul>
      </li>
      <li>Run <strong>StockAnalysis.py (NOTE read next bullet)</strong>, afterward look at the output file created, will be in the 
        stockVars.py-pathToAnalysis directory  (see note below on compound rate)</li>
      <li>Alternately you can run <strong>runStockAnalysis.sh</strong> to run multiple iterations of StockAnalysis.py, this is useful
        when you want to create different windows... i.e. 1, 3, 5 and 10 yr windows; just set the windows
        you want.
        When you're done you'll want to concatenate the output files... I created a little shell in the output directory, it just
        has command 'cat $1 >>merg.csv'.... run it for each output file then open the merg.csv file</li>
      <li>See next block on modifying output</li>
    </ul>   
  </li>

  <li><strong>Doing analysis for sold/purchased securities</strong>
    this is good if you want to see what happened since you sold or bought assets.  Overview is you create
    a transaction file (csv) that has the stock symbol, the transaction (bought/sold etc..), 
    the account, number of shares, value of transaction and the transaction date. The code will
    then perform analysis for each line item using transaction date as a starting point. Note:
    the code can handle a portfolio file also, but I don't find that as valueable as the
    transaction file<br/>
    To do this
    <ul>
      <li>Instead of duplicating instructions, read the comment block at the top of 'GenTransactionOrPortfolioAnalysis.py'</li>
      <li>Do the instructions in that program, it's basically setting variables and running the program</li>
      <li>Once you have output, you'll probably want to add the 'compound growth rate' values, see
          section below.</li>
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
  
<h3>Technotes/tidbits</h3>
<p>fyi: The 'historical' data you get from websites is adjusted, I keep that but also calculate what the 'true' 
   values were on a given date, that's referenced as 'trueHistoryDataFrame' in the StockClass (more below).</p>
<p>I give terse/code examples below, should be obvious</p>   
<ul>
  <li>Most programs have code to be tested/run standalone, look at them.</li>
  <li>The StockClass.py is worth looking at, there are a lot of test blocks that can be run
      to see splits, dividends, 
  <li>stockObj refers to instance of StockClass i.e.<pre>
  stockObj = StockClass.Stock('aapl')</pre></li>
  <li>dates below are python dates, can get via routines in utils like<pre>
  dateVar = utils.getDateFromISOString('2025-02-13')</pre></li>
</ul>

<dl>  
  <dt>Ticker Info</dt>
  <dd>stockObj.tickerInfo - a dictionary with all the ticker info returned from the web service</dd>
  <br/>

  <dt>See true closing price (can use for other fields in dataframe)</dt>
  <dd><pre>
  realClose = stockObj.getTrueHistoryDataFieldForDate(dateVar, 'Close')</pre></dd>

  <br/>
  <dt>Get dataframe with true history data for date range</dt>
    <dd><pre>
  dataframe = stockObj.getTrueHistoryDataFrameByRange(startDate, endDate):</pre></dd>

  <br/>
  <dt>Get the cost basis</dt><dd><pre>
  shares, origInvest, costBasisAmt = stockObj.getCostBasis(dateWantBasisFor, dateOfInvestment, currentInvestment=amount, reinvestDividend=True)</pre>
  fields from dateOfInvestment on are optional<br/>
  dateWantBasisFor - obvious, the data you want the cost basis for<br/>
  dateOfInvestment - ending date of the investment period, if not supplied it will use the last date on file for the stock.<br/>
  currentInvestment - value of your investment on 'dateOfInvestment' (optional and defaults to 1k).<br/> 
  reinvestDividend - boolean identifying if you have dividends reinvested or not, (optional and defaults to True).<br/>
  It returns the shares you started with, your original investment and the cost basis (original
  investment + total dividends reinvested over the term)</dd>

  <br/>
  <dt>Get potential dates of a given cost basis</dt>
  <dd>Sometimes you have a cost basis but want to know when you acquired the stock, this is good for that, since there could be multiple
  dates this returns a dataframe<pre>
  datesDf = stockObj.getDatesForCostBasis(costBasis, sharesOwned, dateLastOwned, accuracyNeeded=.98, reinvestedDividend=False)</pre>
  fields from dateLastOwned on are optional<br/>
  costBasis - is the basis you want to match too<br/>
  sharesOwned - represents the number of shares you owned on 'dateLastOwned'<br/>
  dateLastOwned - the date you last owned security, if not provided it'll use the last date on file<br/>
  accuracyNeeded - the accuracy you want, defaults to 95%<br/>
  reinvestedDividend - boolean identifying if you had dividends reinvested (defaults to True)<br/>
  
  <br/>
  <dt>Calculate valuation (meat of analysis)</dt>
  <dd>This calculates the valuation for a given period and initial investment amount.  It's good
  for things like 'what would 1k invest in apple starting on yyyy-mm-dd be worth on a given end date'<br/>
  Invocation<pre>
  valuesDF, summaryDF = stockObj.calculateValuation(startDate, endDate, investment, recordForEachDay=False, numdaysInSimpleMovingAverage=5)</pre>
  valuesDF - has the valuation calculation for multiple dates, if the optional parm (recordForEachDay is true you get a record for each date, 
    if not then you get records for the start date, end date, and all dates that had actions (dividends or splits).<br/>
  summaryDF - this is a 'summary' dataframe that only has one record (idea is you can use this and summary records from other stocks to
     perform analysis on them). <strong>NOTE:</strong> if wondering why you have BOD and EOD calculations, they could be different if the last date in 
     the window is an action date.<br/>
  Also Note: it calculates valuation with and without doing dividend reinvestment, it's good to see both :)<br/>
  startDate, endDate - represent window that you want to analyze<br/>
  initialInvestment - starting investment amount; I typically use 1000 if I'm going to be analyzing multiple securities<br/>
  recordForEachDay - Optional boolean, defaults to False, see 'valuesDF' description above for logic<br/>
  numdaysInSimpleMovingAverage - Optional int, represents number of days for simple moving average, it defaults to -1 meaning SMA is not applied,
    the SMA smooths out spikes; it uses the prior days values in it's calculation, so if had sma=5 it uses the prior 4 days and the current day
    to derive a value; if looking at the first 4 days (which have no sma) then the closing value is used.<br/><br/>
  <strong>Columns in ValuesDF</strong> (needed to display on multiple lines)<pre>
    Date   Open   High   Low   Close   AdjustedClose   Volume   Dividend   Split   SplitMultiplier   SplitMaxMultiplier   CloseSMA   BOD Shares<br/>
    DividendAmount   EOD Value   SplitShares   EOD Shares   BOD Shares w/Reinvest   DividendAmount w/Reinvest   DividendShares   EOD Value w/Reinvest<br/>
    SplitShares w/Reinvest   EOD Shares w/Reinvest</pre>
  Most should be obvious, of note:<br/>
    SplitMultiplier, SplitMaxMultiplier - see description below for 'True History Dataframe columns'<br/>
    CloseSMA - Is the closing price calculated using simple moving average<br/>
    BOD Shares - The shares you'd have at the beginning of the day<br/>
    DividendAmount - The dividend amount you received (it's your shares owned * dividend issued)<br/>
    EOD Value - End of day value of asset (BOD Shares * (CloseSMA or Close (depending on whether you wanted SMA)))<br/>
    SplitShares - Shares acquired from Splits, without reinvestment (BOD Shares * Split)<br/>
    EOD Shares - Shares you have at end of day<br/>
    BOD Shares w/Reinvest - Shares you had at the beginning of the day if doing dividend reinvestment<br/>
    DividendAmount w/Reinvest- Dividend amount you'd get if you were doing dividend reinvestment<br/>
    DividentShares - Dividend shares you'd get from doing reinvestment<br/>
    EOD Value w/Reinvest - End of day value of your investment when doing dividend reinvestment<br/>
    SplitShares w/Reinvest - Shares you'd have from splits if doing dividend reinvestment<br/>
    EOD Shares w/Reinvestment - End of days shares you'd have with dividend reinvestment<br/>
  <br/>
  <strong>Columns in SummaryDF</strong> (also displayed on multiple lines)<pre>
    Ticker   StartDate   InitialInvestment   SharesPurchased   EndDate   BOD Shares    DividendAmount   EOD Value   EOD Value Pct Change   EOD Shares<br/>
    BOD Shares w/Reinvest   DividendAmount w/Reinvest   DividendShares   EOD Value w/Reinvest   EOD Value w/Reinvest Pct Change   EOD Shares w/Reinvest<br/>
    ShortName   QuoteType</pre>
  Again most are obvious, notes:<br/>
    StartDate, EndDate - Window you're doing analysis on<br/>
    EOD Value Pct Change - It's the growth pct (ending value - start value)/start value<br/>
    ShortName, QuoteType - Come from the web service, it's ticker name (short ver) and type of asset it is<br/>
    You should know the reset based on the previous descriptions<br/>
</dl>

<hr/>
<dl>  
  <dt>History Dataframe columns</dt>
  <dd>This is basically the data pulled from the web, it's got the 'adjusted' values<pre>
   Date   Open   High   Low   Close   AdjustedClose   Volume   AdjustedDividend   Split</pre>
   Date - Date for the values<br/>
   You know what 'Open, High, Low, Close, AdjustedClose, Volume' are<br/>
   AdjustedDividend - Dividend for the date (had been adjusted by for splits)<br/>
   Split - Split for the date<br/></dt>

  <br/>
  <dt>True History Dataframe columns</dt>
  <dd>This has the 'real' values for the date, it is basically the 'history' values multiplied by the SplitMultiplier<pre>
   Date   Open   High   Low   Close   AdjustedClose   Volume   Dividend   Split   SplitMultiplier   SplitMaxMultiplier   CloseSMA</pre>
   Should be obvious what they are, of <strong>note:</strong><br/>
   SplitMultiplier - This is the multiplier used calcuate the 'actual' values, it is all future splits multiplied together (within given
   date range).  To illustrate say on 1/1/2000 there was a split of 4:1, and on 2/1/2000 a split of 3:1.  That means anything you owned
   prior to 1/1 has been adjusted by dividing it by 12 (4*3), for anything between 1/1 and 2/1 it has been divided by 3. If it doesn't 
   make sense think harder (on 12/31 1 share becomes 4 shares on 1/1, on 2/1 it's now 12 shares).<br/>
   SplitMaxMultiplier - For the most part this is the same as SplitMultiplier, the only time it's different is if there's a split
   after the ending window of data you've retrieved (not sure if ever happens but coded to handle).<br/>
   CloseSMA - This is the closing value using a simple moving average</dd>

  <br/>
  <dt>Action History Dataframe columns</dt>
  <dd>This is a subset of the data in 'True History Dataframe'; exactly same columns. It has a record for the start and ending window and also a record
  for each date that a dividend or split has occurred (basically dates of 'action' :))</dd>
</dl>
