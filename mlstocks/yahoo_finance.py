"""

Methods to access yahoo finance data:
    - download_history_yahoo: download price history
    - download_stats_yahoo: download misc statistics


Inspired by yfinance see:
    https://github.com/ranaroussi/yfinance/

"""
import time 
import datetime
import requests 
import pandas as pd
import numpy as np
import re
try:
    import ujson as json
except ImportError:
    import json as json
try:
    from .utils   import SearchableDict
except:
    SearchableDict=dict()
from . exceptions import EmptyDataException


_base_url   = 'https://query1.finance.yahoo.com'
_scrape_url = 'https://finance.yahoo.com/quote'

# --------------------------------------------------------------------------------}
# ---  
# --------------------------------------------------------------------------------{
def download_history_yahoo(ticker, period="5y", interval="1d", ts_start=None, ts_end=None):
    """
    Download history price data from yahoo finance.
    time range is either sepcified using `period` or `ts_start` and `ts_end`

    ticker: str
        Ticker symbol, e.g. 'AAPL'
    period : str
        Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,5y,10y,ytd,max
        Either Use period parameter or use start and end
    interval : str
        Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        Intraday data cannot extend last 60 days
    ts_start: str
        Download start date string (YYYY-MM-DD) or _datetime.
        Default is 1900-01-01
    ts_end: str
        Download end date string (YYYY-MM-DD) or _datetime.
        Default is now
    """
    # --- figuring out ts_start and ts_end based on period
    if ts_start or period is None or period.lower() == "max":
        if ts_start is None:
            ts_start = -2208988800
        elif isinstance(ts_start, datetime.datetime):
            ts_start = int(time.mktime(ts_start.timetuple()))
        else:
            ts_start = int(time.mktime(
                time.strptime(str(ts_start), '%Y-%m-%d')))
        if ts_end is None:
            ts_end = int(time.time())
        elif isinstance(ts_end, datetime.datetime):
            ts_end = int(time.mktime(ts_end.timetuple()))
        else:
            ts_end = int(time.mktime(time.strptime(str(ts_end), '%Y-%m-%d')))

        params = {"period1": ts_start, "period2": ts_end}
    else:
        period = period.lower()
        params = {"range": period}

    params["interval"] = interval.lower()
    params["includePrePost"] = False

    # 1) fix weired bug with Yahoo! - returning 60m for 30m bars
    if params["interval"] == "30m":
        params["interval"] = "15m"
    # Getting data from json
    url = "{}/v8/finance/chart/{}".format(_base_url, ticker)
    data = requests.get(url=url, params=params)
    if "Will be right back" in data.text:
        raise RuntimeError("*** YAHOO! FINANCE IS CURRENTLY DOWN! ***\n"
                           "Our engineers are working quickly to resolve "
                           "the issue. Thank you for your patience.")
    data = data.json()

    # Work with errors
    err_msg = "No data found for this date range, symbol may be delisted"
    if "chart" in data and data["chart"]["error"]:
        return empty_df()
    elif "chart" not in data or data["chart"]["result"] is None or \
            not data["chart"]["result"]:
        return empty_df()

    # parse quotes
    try:
        quotes = parse_quotes(data["chart"]["result"][0])
    except Exception:
        raise Exception('Failed parsing quote')

    # 2) fix weired bug with Yahoo! - returning 60m for 30m bars
    if interval.lower() == "30m":
        quotes2 = quotes.resample('30T')
        quotes = pd.DataFrame(index=quotes2.last().index, data={
            'Open': quotes2['Open'].first(),
            'High': quotes2['High'].max(),
            'Low': quotes2['Low'].min(),
            'Close': quotes2['Close'].last(),
            'Adj Close': quotes2['Adj Close'].last(),
            'Volume': quotes2['Volume'].sum()
        })
    quotes = auto_adjust(quotes)
    quotes['Volume'] = quotes['Volume'].fillna(0).astype(np.int64)
    quotes.dropna(inplace=True)

    # combine
    df = quotes

    # index eod/intraday
    df.index = df.index.tz_localize("UTC").tz_convert(data["chart"]["result"][0]["meta"]["exchangeTimezoneName"])

    if params["interval"][-1] == "m":
        df.index.name = "Datetime"
    else:
        df.index = pd.to_datetime(df.index.date)
        df.index.name = "Date"
    return df

# --------------------------------------------------------------------------------}
# ---  
# --------------------------------------------------------------------------------{
def download_stats_yahoo(ticker, financials=False, holders=False):
    """ 
    Download statistics from a given symbol

    returns
       stats: dictionary with simple stats data

       all_stats: a dictionary of dictionaries with keys:
       all_stats['info']            # info on the stock, e.g:
       all_stats['calendar']        # events
       all_stats['earnings']        # earnings
       all_stats['recommendations'] # recommendations
       all_stats['raw_data']        # raw json data downloaded

    if `financials` is true, the following is also donwloaded (more expensive):
        all_stats['cashflow']            # cashflow
        all_stats['balancesheet']        # balancesheet
        all_stats['financials']          # financials
        all_stats['raw_data_financials'] # raw json data downloaded


    """
    fundamentals          = False
    info                  = None
    sustainability        = None
    recommendations       = None
    major_holders         = None
    institutional_holders = None
    isin                  = None
    calendar              = None
    expirations           = {}
    earnings              = { "yearly": empty_df(), "quarterly": empty_df()}
    financials            = { "yearly": empty_df(), "quarterly": empty_df()}
    balancesheet          = { "yearly": empty_df(), "quarterly": empty_df()}
    cashflow              = { "yearly": empty_df(), "quarterly": empty_df()}

    def cleanup(data):
        df = pd.DataFrame(data).drop(columns=['maxAge'])
        for col in df.columns:
            df[col] = np.where(
                df[col].astype(str) == '-', np.nan, df[col])

        df.set_index('endDate', inplace=True)
        try:
            df.index = pd.to_datetime(df.index, unit='s')
        except ValueError:
            df.index = pd.to_datetime(df.index)
        df = df.T
        df.columns.name = ''
        df.index.name = 'Breakdown'

        df.index = camel2title(df.index)
        return df

    # --------------------------------------------------------------------------------}
    # --- Main symbol page
    # --------------------------------------------------------------------------------{
    # get info and sustainability
    url = '{:s}/{:s}'.format(_scrape_url, ticker)
    data = get_json(url)

    # Added by manu
    # Added by manu
    #findkey(data, 'expenseratio')

    # holders
    if holders:
        try: # Added by manu
            url = "{}/{}/holders".format(_scrape_url, ticker)
            holders = pd.read_html(url)
            self._major_holders = holders[0]
            self._institutional_holders = holders[1]
            if 'Date Reported' in self._institutional_holders:
                self._institutional_holders['Date Reported'] = pd.to_datetime(self._institutional_holders['Date Reported'])
            if '% Out' in self._institutional_holders:
                self._institutional_holders['% Out'] = self._institutional_holders['% Out'].str.replace('%', '').astype(float)/100
        except:
            pass

    # sustainability
    d = {}
    if isinstance(data.get('esgScores'), dict):
        for item in data['esgScores']:
            if not isinstance(data['esgScores'][item], (dict, list)):
                d[item] = data['esgScores'][item]

        s = pd.DataFrame(index=[0], data=d)[-1:].T
        s.columns = ['Value']
        s.index.name = '%.f-%.f' % (
            s[s.index == 'ratingYear']['Value'].values[0],
            s[s.index == 'ratingMonth']['Value'].values[0])

        sustainability = s[~s.index.isin(['maxAge', 'ratingYear', 'ratingMonth'])]

    # info 
    info = {}
    items = ['summaryProfile', 'summaryDetail', 'quoteType',
             'defaultKeyStatistics', 'assetProfile','financialData','fundProfile']
    for item in items:
        if isinstance(data.get(item), dict):
            info.update(data[item])

    try: # added by Manu
        info['regularMarketPrice'] = info['regularMarketOpen']
    except:
        pass
    # Calendar / events
    try:
        cal = pd.DataFrame(data['calendarEvents']['earnings'])
        cal['earningsDate'] = pd.to_datetime(cal['earningsDate'], unit='s')
        calendar = cal.T
        calendar.index = camel2title(self._calendar.index)
        calendar.columns = ['Value']
    except Exception:
        pass
    # analyst recommendations
    try:
        rec = pd.DataFrame(data['upgradeDowngradeHistory']['history'])
        rec['earningsDate'] = pd.to_datetime(rec['epochGradeDate'], unit='s')
        rec.set_index('earningsDate', inplace=True)
        rec.index.name = 'Date'
        rec.columns = camel2title(rec.columns)
        recommendations = rec[['Firm', 'To Grade', 'From Grade', 'Action']].sort_index()
    except Exception:
        pass

    all_stats=SearchableDict()
    all_stats['raw_data']        = data
    all_stats['info']            = info
    all_stats['calendar']        = calendar
    all_stats['earnings']        = earnings
    all_stats['recommendations'] = recommendations

    # --------------------------------------------------------------------------------}
    # --- Financial details: Cashflow, balance sheets, financials, earnings
    # --------------------------------------------------------------------------------{
    # get fundamentals
    if financials:
        data = get_json(url+'/financials')

        # generic patterns
        for key in (
            (cashflow, 'cashflowStatement', 'cashflowStatements'),
            (balancesheet, 'balanceSheet', 'balanceSheetStatements'),
            (financials, 'incomeStatement', 'incomeStatementHistory')
        ):
            item = key[1] + 'History'
            if isinstance(data.get(item), dict):
                key[0]['yearly'] = cleanup(data[item][key[2]])
            item = key[1]+'HistoryQuarterly'
            if isinstance(data.get(item), dict):
                key[0]['quarterly'] = cleanup(data[item][key[2]])

        # Earnings
        if isinstance(data.get('earnings'), dict):
            earnings = data['earnings']['financialsChart']
            df = pd.DataFrame(earnings['yearly']).set_index('date')
            df.columns = camel2title(df.columns)
            df.index.name = 'Year'
            earnings['yearly'] = df
            df = pd.DataFrame(earnings['quarterly']).set_index('date')
            df.columns = camel2title(df.columns)
            df.index.name = 'Quarter'
            earnings['quarterly'] = df

        # Store in dict
        all_stats['cashflow']            = cashflow
        all_stats['balancesheet']        = balancesheet
        all_stats['financials']          = financials
        all_stats['raw_data_financials'] = data

    # --------------------------------------------------------------------------------}
    # --- Filling up some simple stats
    # --------------------------------------------------------------------------------{
    basic_stats = SearchableDict()
    stats_from_info  =['longName','industry','sector','country','fullTimeEmployees','quoteType']
    stats_from_info +=['numberOfAnalystOpinions','targetLowPrice', 'currentPrice', 'targetMeanPrice', 'targetHighPrice', 'recommendationMean','targetMeanGainFromCurrent']
    stats_from_info +=['beta','trailingEps','yield', 'expenseRatio', 'dividendYield' ,'trailingAnnualDividendYield' ,'trailingAnnualDividendRate','ytdReturn','trailingPE' ,'forwardPE' ,'forwardEps']
    stats_from_info +=['morningStarOverallRating', 'morningStarRiskRating','profitMargins'] #, 'beta']
    stats_from_info +=['earningsQuarterlyGrowth']
    stats_from_info +=['open','dayLow','dayHigh']
    for key in stats_from_info:
        try:
            basic_stats[key] = info[key]
        except:
            basic_stats[key] = np.nan
    try:
        basic_stats['expenseRatio'] = info['feesExpensesInvestment']['annualReportExpenseRatio']*100
    except:
        pass
    try:
        current = info['currentPrice']
        pmean   = info['targetMeanPrice']
        basic_stats['targetMeanGainFromCurrent'] = np.around((min(pmean/current, 2)-1)*100.0, 1)
    except:
        basic_stats['targetMeanGainFromCurrent'] = np.nan

    return basic_stats, all_stats


# --------------------------------------------------------------------------------}
# --- Helpers 
# --------------------------------------------------------------------------------{
# --------------------------------------------------------------------------------}
# --- Utils  (see yfinance/utils.py)
# --------------------------------------------------------------------------------{
def empty_df(index=[]):
    empty = pd.DataFrame(index=index, data={
        'Open': np.nan, 'High': np.nan, 'Low': np.nan,
        'Close': np.nan, 'Adj Close': np.nan, 'Volume': np.nan})
    empty.index.name = 'Date'
    return empty

def parse_quotes(data):
    """ convert json data to a dataframe """
    timestamps = data["timestamp"]
    ohlc       = data["indicators"]["quote"][0]
    volumes    = ohlc["volume"]
    opens      = ohlc["open"]
    closes     = ohlc["close"]
    lows       = ohlc["low"]
    highs      = ohlc["high"]
    adjclose = closes
    if "adjclose" in data["indicators"]:
        adjclose = data["indicators"]["adjclose"][0]["adjclose"]
    quotes = pd.DataFrame({"Open": opens,
                            "High": highs,
                            "Low": lows,
                            "Close": closes,
                            "Adj Close": adjclose,
                            "Volume": volumes})
    quotes.index = pd.to_datetime(timestamps, unit="s")
    quotes.sort_index(inplace=True)
    return quotes

def auto_adjust(data):
    """ Adjust Open/High/Low/Close prices based on Adj Close price """
    df = data.copy()
    ratio = df["Close"] / df["Adj Close"]
    df["Adj Open"] = df["Open"] / ratio
    df["Adj High"] = df["High"] / ratio
    df["Adj Low"]  = df["Low"] / ratio

    df.drop(["Open", "High", "Low", "Close"], axis=1, inplace=True)

    df.rename(columns={
        "Adj Open": "Open", "Adj High": "High",
        "Adj Low": "Low", "Adj Close": "Close"
    }, inplace=True)

    df = df[["Open", "High", "Low", "Close", "Volume"]]
    return df[["Open", "High", "Low", "Close", "Volume"]]


def get_json(url, proxy=None):
    html = requests.get(url=url, proxies=proxy).text
    if "QuoteSummaryStore" not in html:
        raise EmptyDataException()

    json_str = html.split('root.App.main =')[1].split('(this)')[0].split(';\n}')[0].strip()
    data_all = json.loads(json_str)
    data=data_all['context']['dispatcher']['stores']['QuoteSummaryStore']

    # adde by manu
    # useful to find a variable in the json hierarchy
    #findkey(data_all,'expenseratio')

    # return data
    new_data = json.dumps(data).replace('{}', 'null')
    new_data = re.sub(r'\{[\'|\"]raw[\'|\"]:(.*?),(.*?)\}', r'\1', new_data)
    return_dict = SearchableDict(json.loads(new_data))
#     print(return_dict)
    return return_dict

def camel2title(o):
    return [re.sub("([a-z])([A-Z])", "\g<1> \g<2>", i).title() for i in o]


