import yfinance as yf
import pandas as pd

#Building a function to get the mag 7 stock price data.

#Inputs: Put in a start date in 'YYYY-MM-DD' format
#Delta: Input a interval time. Values can range from:
#['1m','2m','5m','15m','30m','60m','90m','1h','1d','5d','1wk','1mo','3mo']

def get_mag7_prices(start_date: str, delta: str = '1d') -> pd.DataFrame:
    while delta in ['1m','2m','5m','15m','30m','60m','90m','1h','1d','5d','1wk','1mo','3mo']:
        try:
            present = pd.Timestamp.now().strftime('%Y-%m-%d')
            mag_7 = ["GOOGL", "AMZN", "AAPL", "META", "MSFT", "NVDA", "TSLA"]
            mag_history = yf.Tickers(mag_7).history(start=start_date, end=present)
            mag_history = mag_history.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index(level=1)
            
            #ADDING volatility to my stock prices and 
            mag_history['Daily Volatility'] = mag_history.groupby('Ticker').agg(
            volatility=('Close', 'pct_change'))
            
            return mag_history
        except ValueError:
            print(f'Please type in a valid period: {delta}')


#A more general fucntion where you can get the stock data for any publicly traded company on yahoo finance

#Creating a function where we get the statistics for a particular stock
def creating_df(dictionary, comp_ticker):
    variables = set()
    firm = yf.Ticker(comp_ticker).get_info()
    
    for i in dictionary.keys():
        for j in dictionary[i]:
            variables.add(j)
        
    metrics_df = dict()
        
    for variable in variables:
        try:
            metrics_df[variable] = [firm[variable]]
        except KeyError:
            metrics_df[variable] = pd.NA

            
    metrics_df = pd.DataFrame.from_dict(metrics_df)
        

    metric_to_category = {metric: category for category, metrics in dictionary.items() for metric in metrics}

        # Filter the mapping to only include metrics present in the dataframe
    filtered_mapping = {metric: metric_to_category[metric] for metric in metrics_df.columns if metric in metric_to_category}

        # Create a multi-level index based on the mapping
    multi_index = pd.MultiIndex.from_tuples(
    [(filtered_mapping[metric], metric) for metric in metrics_df.columns if metric in filtered_mapping],
    names=["Category", "Metric"])

        # Reorganize the dataframe
    sorted_metrics = [metric for category, metric in multi_index]  # Extract sorted metric names
    df_multi_indexed = metrics_df[sorted_metrics].copy()
    df_multi_indexed.columns = multi_index
    return df_multi_indexed.T.sort_index(axis=0)


#This is the main function to interact with. If a user wants to receive the stats from a company, they should call this function.
def get_metrics(comp_ticker: str, type='all'):
    #We create two different instances based on what the user prioritizes. If they only want the finacial data, we'll seperate that for them. Repeat for trading data.
    financial_highlights = {
    'Fiscal Year': ['lastFiscalYearEnd', 'mostRecentQuarter'],
    'Summary': ['marketCap', 'enterpriseValue', 'trailingPE', 'forwardPE', 'priceToSalesTrailing12Months','priceToBook','enterpriseToRevenue', 'enterpriseToEbitda'],
    'Profitability': ['profitMargins', 'operatingMargins'],
    'Management Effectiveness': ['returnOnAssets', 'returnOnEquity'],
    'Income Statement': ['totalRevenue','revenuePerShare', 'revenueGrowth', 'grossProfits', 'ebitda', 'earningsQuarterlyGrowth'],
    'Balance Sheet': ['totalCash', 'totalCashPerShare', 'totalDebt', 'debtToEquity', 'currentRatio','bookValue'],
    'Cash Flow Statement': ['operatingCashflow', 'freeCashflow']
}
    trading_highlights = {
    'Stock Price History': ['beta', '52WeekChange', 'SandP52WeekChange', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'fiftyDayAverage', 'twoHundredDayAverage'],
    'Share Statistics': ['averageVolume', 'averageVolume10days', 'sharesOutstanding', 'impliedSharesOutstanding', 'floatShares', 'heldPercentInsiders', 'heldPercentInstitutions', 'sharesShort', 'shortRatio', 'shortPercentOfFloat', 'sharesPercentSharesOut', 'sharesShort'],
    'Dividends & Splits': ['dividendRate', 'dividendYield', 'trailingAnnualDividendRate', 'trailingAnnualDividendYield', 'payoutRatio', 'lastDividendValue','exDividendDate', 'lastSplitFactor', 'lastSplitDate']
}
    
    if type == 'financial':
        return creating_df(financial_highlights, comp_ticker)
    
    elif type == 'trading':
        return creating_df(trading_highlights, comp_ticker)
    
    #We'll assume our base is if the user does not change anything
    else:       
        #If type is all, then we want all available data that we could get from the yahoo finance statistics page
        whole = financial_highlights | trading_highlights
        return creating_df(whole, comp_ticker)
 




    
    

#Volatility

#One week volatility = 
#One month volaitility


#get_volatility(delta, ticker)


# Seperate
#Average volume one month and week =
# get_volume(delta, ticker)

#Average one volatility from past month?



class Trading:
    def __init__(self, comp_ticker):
        self.ticker = comp_ticker
        
    
    def stock_price(self, start_date: str,  delta: str  = '1d') -> pd.DataFrame:
        present = pd.Timestamp.now().strftime('%Y-%m-%d')
        return yf.Ticker(self.ticker).history(start=start_date,end=present, interval=delta).sort_index(ascending=False)
    
    
    
    
    def monthly_avg_volume(self, offset: int) -> pd.DataFrame:
        #Getting volume data
        present = pd.Timestamp.now()
        start_date = present - pd.DateOffset(months=offset)
        
        volume = self.stock_price(start_date=start_date)['Volume'].reset_index()
        
        #Getting month and year to group by MoM
        volume['Month'] = volume.Date.dt.month
        volume['Year'] = volume.Date.dt.year
        
        #Aggregating and calculating mean for every month
        average = volume.groupby(['Month', 'Year']).agg(
            avg_volume = ('Volume', 'mean')
        ).reset_index()
        
        return average
    
    
    
    
    def trading_metrics(self, type='trading') -> pd.DataFrame:
        trading_highlights = {
        'Stock Price History': ['beta', '52WeekChange', 'SandP52WeekChange', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'fiftyDayAverage', 'twoHundredDayAverage'],
        'Share Statistics': ['averageVolume', 'averageVolume10days', 'sharesOutstanding', 'impliedSharesOutstanding', 'floatShares', 'heldPercentInsiders', 'heldPercentInstitutions', 'sharesShort', 'shortRatio', 'shortPercentOfFloat', 'sharesPercentSharesOut', 'sharesShort'],
        'Dividends & Splits': ['dividendRate', 'dividendYield', 'trailingAnnualDividendRate', 'trailingAnnualDividendYield', 'payoutRatio', 'lastDividendValue','exDividendDate', 'lastSplitFactor', 'lastSplitDate']}
        return creating_df(trading_highlights, self.ticker)
