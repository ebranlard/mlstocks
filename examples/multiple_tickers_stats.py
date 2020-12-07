import pandas as pd
import os
import time

from mlstocks.excel_table import ExcelTable
from mlstocks.symbol_list import download_stats
from mlstocks.utils import *

# --- Parameters
nThreads=5   # Number of therads used to download data
nTries=2     # Number of retry if download of data fail
sheetName='Portfolio' #  Name of sheet forExcel output
outFile = 'ExampleStats.xlsx'  # Excel output file
ticks  = ['AAPL','TSLA','AMZN','MSFT','AA','UAL','CVS']  

# --- Select column and column order
# For a full list of available columns see the examples for "one ticker"
columns=[]
columns += ['longName','industry','sector','country','fullTimeEmployees','quoteType','currentPrice']  # Basic company info
columns += ['International','Dividend','Dividends','expenseRatio']  #  
columns += ['numberOfAnalystOpinions','recommendationMean','targetMeanGainFromCurrent'] # Yahoo finance, price recommendation
columns += ['TR_numberOfAnalystOpinions','TR_targetMeanGainFromCurrent','TR_targetMeanGainFromCurrent_Best','TR_score_raw', 'TR_consensus_raw','TR_percentOfBuy'] # Tipranks recommendation/ score
columns += ['priceChange_today','priceChange_3days','priceChange_week','priceChange_month','priceChange_year'] # Change of price (current vs old)
columns += ['TR_insidersActivity_last3MonthsSum','TR_hedgeFundActivity_trend','TR_bloggerSentiment']      # Tipranks 
columns += ['TR_fundamentals_assetGrowth','TR_technicals_SMA_20_200','TR_technicals_twelveMonthsMomentum']
columns += ['relSP500_year_I','yield','dividendYield']

# Excel Output options
colNameExtraShort = ['Dividend','International']
colNameExtraLong  = ['longName']
colNameRightBorders  = ['currentPrice','expenseRatio','targetMeanGainFromCurrent','TR_percentOfBuy','priceChange_year']


# --------------------------------------------------------------------------------}
# --- Downloading stats to a dataframe 
# --------------------------------------------------------------------------------{
try:
    df = download_stats(ticks, columns, nThreads=nThreads, nTries=nTries)
except:
    raise
    print('>>> Something wrong happened in loop')


# --------------------------------------------------------------------------------}
# --- Compute extra data and store in dataframe
# --------------------------------------------------------------------------------{
# --- Convenient replacements
df['country']   = standardizeCountry(df['country'])
df['sector']    = standardizeSector(df['sector'])
df['quoteType'] = standardizeQuoteType(df['quoteType'])
import warnings
warnings.filterwarnings('ignore')
df['TR_insidersActivity_last3MonthsSum'] = np.sign(df['TR_insidersActivity_last3MonthsSum'].values)

# Blurring the notion of dividends and yields
df['dividendYield'] = np.around(100 * replaceEmptyStringsAndNA(df['dividendYield'], 0), 1)
df['yield']         = np.around(100 * replaceEmptyStringsAndNA(df['yield']        , 0) ,1)
bStock   =df['quoteType'].values=='stock'
bNotStock=df['quoteType'].values!='stock'
df.loc[bStock   ,'Dividends'] = df.loc[bStock,'dividendYield']
df.loc[bNotStock,'Dividends'] = df.loc[bNotStock,'yield']
df['Dividend'] = ['D' if v>=3 else '' for v in df['Dividends']]
try:
    df.drop(['dividendYield','yield'], 1, inplace=True)
except:
    pass
# International flag
df['International'] = [''  if (v=='USA' or len(v)==0) else 'I' for v in df['country']]

# --------------------------------------------------------------------------------}
# --- Write to Excel
# --------------------------------------------------------------------------------{
xls = ExcelTable(outFile, df=df, sheetname=sheetName)
# --- Styling (NOTE: buggy for now when changing the same column multiple times)
# Borders
xls.verticalBorders(leftBorderCols=colNameRightBorders)
# Width
xls.defaultColumnWidth(5)
xls.columnWidth(colNameExtraShort, colWidth=2, center=True)
xls.columnWidth(colNameExtraLong, colWidth=30)
# Format
#xls.formatPercentage(['A'])
# Conditional formatting
xls.conditionalFormatGoodBelow('priceChange_3days'       ,-6, strict=False)
xls.conditionalFormatGoodBelow('priceChange_today'       ,-5, strict=False)
xls.conditionalFormatGoodBelow('priceChange_week'        ,-6, strict=False)
xls.conditionalFormatGoodBelow('priceChange_month'       ,-4, strict=False)
xls.conditionalFormatGoodBelow('priceChange_year'        ,-3, strict=False)
xls.conditionalFormatGoodAbove('Dividends'                 ,3)
xls.conditionalFormatGoodBelow('recommendationMean'     ,  2.2)
xls.conditionalFormat3NumValues('TR_score_raw'  , 1,7,10)
xls.conditionalFormatGoodAbove('TR_percentOfBuy',   70)
xls.conditionalFormatGoodAbove('TR_consensus_raw',  4)

xls.conditionalFormatBadBelow('numberOfAnalystOpinions'   ,5)
xls.conditionalFormatBadBelow('TR_numberOfAnalystOpinions',5)
xls.conditionalFormatBadIfEqual('TR_technicals_SMA_20_200',  '"Negative"')
xls.conditionalFormatBadIfEqual('TR_hedgeFundActivity_trend',  '"Decreased"')
xls.conditionalFormatBadBelow('TR_fundamentals_assetGrowth',  0)
xls.conditionalFormatBadAbove('expenseRatio',  0.5)

xls.conditionalFormatGoodIfEqual('TR_bloggerSentiment',  '"Very Bullish"')
xls.conditionalFormat3NumValues('TR_insidersActivity_last3MonthsSum', -1 ,  0  ,  1 )

xls.conditionalFormat3NumValues('relSP500_year_I'          , -50 ,  0  ,  50 )

xls.conditionalFormat3NumValues('targetMeanGainFromCurrent'        ,-5,15,35)
xls.conditionalFormat3NumValues('TR_targetMeanGainFromCurrent'     ,-5,15,35)
xls.conditionalFormat3NumValues('TR_targetMeanGainFromCurrent_Best',-5,15,35)

# Insert URL for tickers
xls.urlValues('Ticker',[t for t in df['Ticker']], ['https://finance.yahoo.com/quote/{:s}?p={:s}'.format(t,t) for t in df['Ticker']])
# --- Write and laucnh 
xls.write()
xls.launch()
