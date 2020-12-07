import pandas as pd
import os
import time

from mlstocks.symbol import *
from mlstocks.stats import *
from mlstocks.excel_table import ExcelTable
from mlstocks.utils import *
from mlstocks.symbol_list import download_stats
from datetime import date, timedelta

from mlstocks.tools.tictoc import Timer
from mlstocks.tools.clean_exceptions import *
from mlstocks.ticker_lists import tickLF, tickL5

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# --- Parameters
nThreads=10  # Number of therads used to download data
nTries=2     # Number of retry if download of data fail
sheetName='Portfolio' #  Name of sheet forExcel output

# --- Option 1
InFile  = 'Portfolio.xlsx'; outFile = 'Portfolio_FullStats.xlsx'
# InFile  = 'Portfolio2.xlsx'; outFile = 'Portfolio2_FullStats.xlsx'
# --- Option 2
# InFile  = None; outFile = 'Selection_FullStats.xlsx'
# ticks  = ['ACER','TSLA','AMZN','MSFT','AA','UAL','CVS']
# ticks  = ['CUK']
# # ticks  = tickL5
# ticks = ['ACER', 'ACH', 'ACWV', 'AGRO', 'AMBO', 'AMK', 'ANFI', 'ARNC', 'ATV', 'AXGT', 'BASFY', 'BBAX', 'BBCA', 'BBEU', 'BBJP', 'BBL', 'BEDU', 'BITA', 'BLX.TO', 'BMA', 'BND', 'BNDX', 'BO.CO', 'BRFS', 'BRK-A', 'BRK-B', 'BSBR', 'CABGY', 'CAN', 'CANG', 'CBD', 'CCM', 'CDXC', 'CELG', 'CEPU', 'CGA', 'CHL', 'CHT', 'CHU', 'CIG', 'CIUEX', 'CLIX', 'CMCM', 'CNF', 'CNYA', 'CO', 'CPHI', 'CPL', 'CSTM', 'CTK', 'CTL', 'CUK', 'CUSDX', 'CUSUX', 'CYD', 'DARE', 'DIA', 'DL', 'DLPH', 'DNNGY', 'DODLX', 'DOGEF', 'DPSGY', 'DUSA', 'DVYA', 'DWX', 'EBIX', 'EBR', 'EDN', 'EMQQ', 'EROS', 'EVH', 'EWA', 'EWT', 'EWZ', 'FENG', 'FKUQX', 'FNI', 'FOJCF', 'FSAGX', 'FSPSX', 'FTEC', 'FXAIX', 'FXY', 'GAIN', 'GCGMF', 'GCTAF', 'GHG', 'GLD', 'GLDM', 'GLTR', 'GNNDY', 'GOL', 'GOVT', 'GSH', 'GSL', 'GTIP', 'GTX', 'HAUD', 'HKIB', 'HMC', 'HSBC', 'HYMB', 'IAC', 'IAU', 'ICLN', 'IDV', 'IEF', 'IGBH', 'IGOV', 'IGSB', 'IHF', 'IHG', 'IOO', 'IOTS', 'IRS', 'IVV', 'IX', 'IYR', 'JEIQX', 'JMEI', 'JP', 'KB', 'KEP', 'KNSA', 'KRYS', 'KT', 'LAIX', 'LEGN', 'LEJU', 'LFC', 'LINX', 'LITB', 'LK', 'LN', 'LND', 'LOWE.VI', 'LPL', 'LQD', 'LVHI', 'LVL', 'LXFR', 'MBB', 'MCHI', 'MFG', 'MFGP', 'MMYT', 'MOGU', 'MSC', 'MSYPX', 'MTILX', 'MUFG', 'NE', 'NEW', 'NFC', 'NGG', 'NMR', 'NSRGY', 'NTP', 'NVGS', 'NXP', 'OIBRQ', 'OROCF', 'PAM', 'PDBAX', 'PEGI', 'PPDF', 'PSO', 'PTF', 'PTR', 'PUK', 'QQQ', 'QWLD', 'RAPT', 'RBS', 'RELX', 'RENN', 'REZ', 'RHHBY', 'RNW.TO', 'RUBI', 'RYB', 'S', 'SAMG', 'SBGL', 'SCHD', 'SCHZ', 'SCPE', 'SDIV', 'SDRL', 'SFUN', 'SHI', 'SHY', 'SID', 'SKM', 'SKYY', 'SLV', 'SMFG', 'SMH', 'SOGO', 'SOXX', 'SPHD', 'SPLB', 'SPXC', 'SPY', 'STG', 'SUZ']
# ticks=['AMZN','TSLA']


# --- Read portfolio
if InFile:
    # --- Read in an excel file
    df_in= pd.read_excel(InFile, sheet_name=sheetName);
    df_in=df_in.replace(r'^\s*$', 'XXX', regex=True) # replace empty field
    df_in = df_in.filter(['Ticker', 'Type','Note']) # Keeping only few columns
    ticks = df_in['Ticker'].values
    # Duplicates warning
    ticklist=[t.strip().lower() for t in ticks]
    duplicates=set([t.upper() for t in ticklist if ticklist.count(t) > 1])
    if len(duplicates)>0:
        duplicates=list(duplicates)
        duplicates.sort()
        print('>>> Duplicates: ',duplicates)
        raise Exception('Remove duplicates first')


# --- Select column and column order
columns=[]
columns += ['longName','industry','sector','country','fullTimeEmployees','quoteType'] 
columns += ['International','Dividend','Crisis','Dividends','Note','Fav','expenseRatio','beta','trailingEps'] 
columns += ['Total']
columns += ['outperformSP500_year','recentUnderperformSP500']
columns += ['numberOfAnalystOpinions','recommendationMean','targetMeanGainFromCurrent']  # Yahoo finance, price recommendation
columns += ['TR_numberOfAnalystOpinions','TR_targetMeanGainFromCurrent','TR_targetMeanGainFromCurrent_Best','TR_score_raw', 'TR_consensus_raw','TR_percentOfBuy'] 
columns += ['priceChange_today','priceChange_3days','priceChange_week','priceChange_month','priceChange_year'] # Change of price (current vs old)
columns += ['Year_P','ratio_thisYear_3yearsAgo','ratio_currentPrice_YMin','ratio_currentPrice_YMean']
columns += ['TR_insidersActivity_last3MonthsSum','TR_hedgeFundActivity_trend','TR_bloggerSentiment']
columns += ['TR_fundamentals_assetGrowth','TR_technicals_SMA_20_200','TR_technicals_twelveMonthsMomentum']
columns += ['targetLowPrice','TR_targetLowPrice', 'currentPrice', 'targetMeanPrice','TR_targetMeanPrice', 'targetHighPrice','TR_targetHighPrice']
columns += ['yield', 'dividendYield' ,'trailingAnnualDividendYield' ,'trailingAnnualDividendRate'  ,'ytdReturn']
columns += ['outperformSP500_crises']
#columns += ['trailingPE' ,'forwardPE' ,'forwardEps' ]
#columns += ['morningStarOverallRating', 'morningStarRiskRating','profitMargins'] 
#columns += ['earningsQuarterlyGrowth']
#columns += ['open','dayLow','dayHigh']
#columns += ['twoHundredDayAverage', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow']
#columns += ['bookValue','enterpriseToEbitda' ,'enterpriseToRevenue' ,'payoutRatio' ,'pegRatio' ,'priceHint' ,'shortRatio']
columns += ['relSP500_year', 'relSP500_year_I', 'relSP500_year23', 'relSP500_year23_I', 'relSP500_crisis08', 'relSP500_crisis08_I', 'relSP500_crisis20' , 'relSP500_crisis20_I']

# Excel Output options
colNameExtraShort = ['Dividend','Index','Note','Crisis','International','Quality','LongTerm','Expense Ratio','Fav','outperformSP500_year','recentUnderperformSP500']
colNameExtraLong  = ['longName']
colNameRightBorders  = ['quoteType','trailingEps','targetMeanGainFromCurrent','TR_percentOfBuy','priceChange_year','TR_bloggerSentiment','ratio_currentPrice_YMean']
# colNameRightBorders  += ['ytdReturn','profitMargins','dayHigh','fiftyTwoWeekLow','shortRatio','relSP500_crisis20_I']


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
for it in np.arange(len(df)):
    tick = df.loc[it,'Ticker']
    if tick in tickLF:
        df.loc[it,'Fav'] = 1
    else:
        df.loc[it,'Fav'] = 0
    # --- Metrics "Points"
    #df.loc[it,'WDel_P']     = pointAboveCriteria(-df.loc[it,'priceChange_week'], 2.5, 5)
    #df.loc[it,'MDel_P']     = pointAboveCriteria(-df.loc[it,'priceChange_month'], 2.5, 5)
    #df.loc[it,'YDel_P']     = pointAboveCriteria(-df.loc[it,'priceChange_year'], 2.5, 5)
    #df.loc[it,'YIncr_P']    = pointAboveCriteria(df.loc[it,'ratio_thisYear_3yearsAgo'],1,2)
    #df.loc[it,'YRelMean_P'] = pointBelowCriteria( df.loc[it,'ratio_currentPrice_YMean'], -0.1,  -0.2)
    #df.loc[it,'YRat_P'    ] = pointBelowCriteria( df.loc[it,'ratio_currentPrice_YMin'] ,  0.3 ,  0.5)
    #df.loc[it,'EstPrice_P'] = (info['targetMeanGainFromCurrent']/100+1)*2                  # <<<< IMPORTANT
    #df.loc[it,'RecRating_P'] = pointAboveCriteria((5-Rating)/4, 0.5, 0.75)*2 # <<<< IMPORTANT
    # --- Total points 
    #Points = [df.loc[it,c] for c in KeyPoints if c in df.columns]
    #df.loc[it,'Total'] =  np.nansum(Points)

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

# --- Criteria
df['Year_P']   = [1 if b else 0 for b in  (df['ratio_currentPrice_YMin']<0.5) & (df['ratio_currentPrice_YMean']<-0.2)  & (df['ratio_thisYear_3yearsAgo']>2)]
df['Crisis']   = ['C' if v==1 else '' for v in df['outperformSP500_crises']]
try:
    df.drop(['outperformSP500_crises'], 1, inplace=True)
except:
    pass


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
xls.conditionalFormatGoodBelow('ratio_currentPrice_YMin' ,0.5      , strict=False)
xls.conditionalFormatGoodBelow('ratio_currentPrice_YMean',-0.2     , strict=False)
xls.conditionalFormatGoodAbove('ratio_thisYear_3yearsAgo', 2       , strict=False)
# xls.conditionalFormatGoodAbove('relSP500_crisis08_I'     , Crit2008, strict=False)
# xls.conditionalFormatGoodAbove('relSP500_crisis20_I'     , Crit2020, strict=False)
# xls.conditionalFormatGoodAbove('relSP500_crisis08'       , Crit2008, strict=False)
# xls.conditionalFormatGoodAbove('relSP500_crisis20'       , Crit2020, strict=False)
xls.conditionalFormatGoodAbove('recentUnderperformSP500',   0)
xls.conditionalFormatGoodAbove('outperformSP500_year'   ,   0)
xls.conditionalFormatGoodAbove('outperformSP500_last3y' ,   0)
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

# columns += ['TR_numberOfAnalystOpinions','TR_targetMeanGainFromCurrent','TR_targetMeanGainFromCurrent_Best','TR_score_raw', 'TR_consensus_raw','TR_percentOfBuy'] 
# columns += ['TR_insidersActivity_last3MonthsSum','TR_hedgeFundActivity_trend','TR_bloggerSentiment']
# columns += ['TR_fundamentals_assetGrowth','TR_technicals_SMA_20_200','TR_technicals_twelveMonthsMomentum']



xls.conditionalFormat3NumValues('relSP500_year'            , -50 ,  0  ,  50 )
# xls.conditionalFormat3NumValues('relSP500_year_I'          , -50 ,  0  ,  50 )
xls.conditionalFormat3NumValues('relSP500_year23'          , -50 ,  0  ,  50 )
# xls.conditionalFormat3NumValues('relSP500_year23_I'        , -50 ,  0  ,  50 )

xls.conditionalFormat3NumValues('targetMeanGainFromCurrent'        ,-5,15,35)
xls.conditionalFormat3NumValues('TR_targetMeanGainFromCurrent'     ,-5,15,35)
xls.conditionalFormat3NumValues('TR_targetMeanGainFromCurrent_Best',-5,15,35)


xls.conditionalFormat3NumValues('Total'                    , 0   ,  7  ,  15 )
# Insert URL for tickers
xls.urlValues('Ticker',[t for t in df['Ticker']], ['https://finance.yahoo.com/quote/{:s}?p={:s}'.format(t,t) for t in df['Ticker']])
# --- Write and laucnh 
xls.write()
xls.launch()
