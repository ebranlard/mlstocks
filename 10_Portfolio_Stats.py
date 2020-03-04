import xlsxwriter
import yfinance as yf
import os

from mlstocks.symbol import *
import mlstocks.symbol
import pandas as pd
import os
import shutil
from datetime import date, timedelta
import weio
try:
    from pybra.clean_exceptions import *
except:
    pass

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# --- parameters
InFile  = 'Portfolio.xlsx'
OutFile = 'PortfolioTickerOnly_Stats.xlsx'
# InFile  = None
# OutFile = 'PortfolioTickerOnly_Stats_Small.xlsx'
ColNameExtraShort = ['Dividends','Index','Note','Crisis','International','Quality','LongTerm','Expense Ratio']
ColNameExtraLong = ['longName']
SheetName='Portfolio'
bDownloadInfo=True
# --------------------------------------------------------------------------------}
# --- Option for monitored stocks 
# --------------------------------------------------------------------------------{
Mode          = 'Monitor'    # Monitor/Portfolio
Mode          = 'Portfolio'  # Monitor/Portfolio

MRelDiffCrit=4
YRelDiffCrit=3

# --- Derived params
day_start     = (date.today()-timedelta(days=3*365)).strftime("%Y-%m-%d") 
day_end       = date.today().strftime("%Y-%m-%d")
Folder        = '_'+Mode+'/'

# --- Read portfolio
# xls=weio.read(InFile)
# df=xls.data[next(iter(xls.data)]

if InFile:
    # --- Read in an excel file
    df= pd.read_excel(InFile, sheet_name=SheetName);
    df=df.replace(r'^\s*$', 'XXX', regex=True) # replace empty field
    df = df.filter(['Ticker', 'Type'])
    ticks     = df['Ticker'].values
    types     = df['Type'].values
else:
    # --- Create data frame from list of ticks
#     ticks=['ICLN','NPI.TO','RNW.TO','BLX.TO','PEGI','CSIQ','JKS','DNNGY','AMT','T','CSCO','GLW','CCI','ERIC','INTC','NOK','NXP','AMBA','APPN','ACLS','AAXN','WIFI','CRNT','GNRC','MVIS','QRVO','SWKS','TMUS','S','TSM','ACLS','INSG','IOTS','DGII']
    ticks=['XLK','VGT','XLC','XLE','XLV','XLRE','XLP','SMH','SOXX','PTF','XSD','FTEC','SKYY','VGT']
    df=pd.DataFrame()
    df['Ticker']=ticks
    types = ticks
    types[:] = 'Stocks'
# # --- Perform selection
# if Mode.find('Monitor')>=0:
#     df=df[df['Note'].str.find('M')>=0 ] # select monitor
# elif Mode.find('NotBought')>=0:
#     df=df[df['Note']!='B']          # we select things we didn't buy already
# elif Mode.find('Portfolio')>=0:
#     # we select all
#     pass
# 
# # ---
# notes     = (df['International'].map(str)+'_'+df['Dividend'].map(str)+'_'+df['Note'].map(str) +'_'+df['Crisis'].map(str) + '_' + df['LongTerm'].map(str)).values
# 
# # --- All you need for script below is:
# # ticks     = ['AAPL','GOOG']
# # day_start = '2019-10-28'
# # day_end   = '2019-10-31'
# # notes = None
# 
# # --- Less likely parameters
# ForceDownload = True
# # ForceDownload = False
# Interval      = '1d' # 1d
# 
# # --------------------------------------------------------------------------------}
# # ---  Main Script
# # --------------------------------------------------------------------------------{
# dfList=pd.DataFrame()
# dfList['Tick']=''
# dfList['Company']=''
# dfList['Type'] = ''
# dfList['Note'] = ''
# dfList['MRelDiff'] =0
# dfList['YRelDiff'] =0
# 
# dfList['YIncr.']    = 0
# dfList['YRelMean'] = 0
# dfList['YRat']     = 0
# dfList['YRat2']    = 0
# dfList['YGood']    = False
# dfList['Filename']=''
# 
# ISel=['Tick','Company','Type','Note','MRelDiff','YRelDiff','YIncr.','YRelMean','YRat','YGood']
# 
# 
KeysInfo=dict()
KeysInfo['Company']  = ['longName','country','fullTimeEmployees','industry','sector']
KeysInfo['Market']   = ['quoteType','exchange']
KeysInfo['Recomm']   = ['numberOfAnalystOpinions','targetLowPrice', 'currentPrice', 'targetMeanPrice', 'targetHighPrice', 'recommendationMean']
KeysInfo['Div']      = ['dividendYield' ,'trailingAnnualDividendYield' ,'trailingAnnualDividendRate' ,'yield' ,'ytdReturn']
KeysInfo['Metrics']  = ['trailingPE' ,'forwardPE' ,'forwardEps' ,'trailingEps']
KeysInfo['Risk']     = ['morningStarOverallRating', 'morningStarRiskRating','profitMargins', 'beta']
KeysInfo['Earnings'] = ['earningsQuarterlyGrowth']
KeysInfo['Price']    = ['open','dayLow','dayHigh']
# previousClose        166.17
# regularMarketDayLow
# regularMarketDayHigh
# regularMarketOpen    167.42
# regularMarketPreviousClose    167.42
KeysInfo['52'] = ['twoHundredDayAverage', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow']
KeysInfo['Unknown'] = ['bookValue','enterpriseToEbitda' ,'enterpriseToRevenue' ,'payoutRatio' ,'pegRatio' ,'priceHint' ,'shortRatio']


KeyMetrics = [                       'RecRating_M','RecPrice_M','WRelDiff_M','MRelDiff_M','YRelDiff_M', 'YIncr_M','YRat_M','YRelMean_M']
KeyPoints  = ['Total'   ,'RecConf_P','RecRating_P','RecPrice_P','WRelDiff_P','MRelDiff_P','YRelDiff_P', 'YIncr_P','YRat_P','YRelMean_P']


# --- Adding columns to dataframe (only if not already present)
for kk in KeyPoints:
    if kk not in df.columns:
        df[kk]=np.nan
for kk in KeyMetrics:
    if kk not in df.columns:
        df[kk]=np.nan
for k in KeysInfo.keys():
    for kk in KeysInfo[k]:
        if kk not in df.columns:
            df[kk]=''

# --- Functions for point system
def pointAboveCriteria(val,crit_half,crit):
    if isinstance(val, (int, float, complex)):
        if val >= crit:
            return 1
        elif val >= crit_half:
            return 0.5
        else:
            return 0
    else:
        return np.nan
def pointBelowCriteria(val,crit_half,crit):
    if isinstance(val, (int, float, complex)):
        if val <= crit:
            return 1
        elif val <= crit_half:
            return 0.5
        else:
            return 0
    else:
        return np.nan



# --- Loop on tickers
for it,tick in enumerate(ticks):
    if types[it].strip() in ['EQUITY','Stocks']:
        def setKey(key1,key2=None):
            if key2 is None:
                key2=key1
            if key2 in info.keys():
                df.loc[it,key1] = info[key2]
                return ''
            else:
                info[key2]=np.nan
                return key2+', '

        try:

            tick=tick.strip()
            print('{:3d}/{:3d} {:15.15s} '.format(it+1,len(ticks),tick))
            symb = yf.Ticker(tick)
            # --- Info
            info = symb.info
            sError=''
            for k in KeysInfo.keys():
                for kk in KeysInfo[k]:
                    sError+=setKey(kk)
            if len(sError)>0:
                print('Missing keys:',sError)

            # --- Get historical market data
            # NOTE: this is stored in _history and hence affects "actions"= "dividends" "splits"
            years = symb.history(period="5y" , interval='1d' )
            month = symb.history(period="1mo", interval='90m')
            day   = symb.history(period="1d" , interval='1m' )
            month.index=month.index.astype('datetime64[ns]')
            years.index=years.index.astype('datetime64[ns]')

            # --- Get financials
            # Total Revenue              1.25843e+11  1.1036e+11  9.6571e+10  9.1154e+10
            # Net Income  ("Eranings")     3.924e+10  1.6571e+10  2.5489e+10  2.0539e+10
            # Research Development        1.6876e+10  1.4726e+10  1.3037e+10  1.1988e+10
            #if len(fn)>0:
            #    fn=symb.financials
            #    import pdb; pdb.set_trace()
            #    #fn.columns=['Y4','Y3','Y2','Y1']

            #    qf=symb.quarterly_financials
            #    qf.columns=['Q4','Q3','Q2','Q1']
            #    print(fn)
            #    print('Quarterly')
            #    print(qf)

            # --------------------------------------------------------------------------------}
            # --- Metrics and Points
            # --------------------------------------------------------------------------------{
            # 
            # --- How is the stock price compare to the analyst estimate
            # The number of analysits opinion is important
            try:
                confFactor = pointAboveCriteria(info['numberOfAnalystOpinions'], 2, 4)
                df.loc[it,'RecConf_P'] = confFactor
                current = info['currentPrice']
                pmin    = info['targetLowPrice']
                pmax    = info['targetHighPrice']
                pmean   = info['targetMeanPrice']
                howFarIsTheMean = pmean/current 
                df.loc[it,'RecPrice_M'] = howFarIsTheMean
                df.loc[it,'RecPrice_P'] = howFarIsTheMean*2                  # <<<< IMPORTANT
            except:
                print('[FAIL] No recommended price')
                pass
            try:
                Rating = info['recommendationMean'] # between 1 and 5
                df.loc[it,'RecRating_M'] = Rating 
                df.loc[it,'RecRating_P'] = pointAboveCriteria((5-Rating)/4, 0.5, 0.75)*2 # <<<< IMPORTANT
            except:
                print('[FAIL] No mean recommendation')
                pass

            # ---  Earnings


            # --- Current price
            today = date.today()
            vNow = info['currentPrice']
            if vNow==np.nan:
                #iToday     = month.index.get_loc(pd.to_datetime(date.today()                   ), method='nearest')
                print('[FAIL] No current price')

            if len(month)<=0:
                print('[FAIL] No time data')
            else:
                # --- Week discount
                iLastWeek  = month.index.get_loc(pd.to_datetime(date.today()-timedelta(days=7)), method='nearest')
                vLastWeek  = month['Close'].values[iLastWeek]
                WRelDiff = np.around((vNow-vLastWeek)/vLastWeek*100,2)
                df.loc[it,'WRelDiff_M'] = WRelDiff
                df.loc[it,'WRelDiff_P'] = pointAboveCriteria(-WRelDiff, 2.5, 5)

                # --- Last month discont
                iLastMonth = month.index.get_loc(pd.to_datetime(date.today()-timedelta(days=31)), method='nearest')
                vLastMonth = month['Close'].values[iLastMonth]
                MRelDiff   = np.around((vNow-vLastMonth)/vLastMonth*100,2) # MRelDiff [%]
                df.loc[it,'MRelDiff_M'] = MRelDiff
                df.loc[it,'MRelDiff_P'] = pointAboveCriteria(-MRelDiff, 2.5, 5)

            #     # --- Year discount
                iLastYear = years.index.get_loc(pd.to_datetime(date.today()-timedelta(days=365)), method='nearest')
                vLastYear = years['Close'].iloc[iLastYear]
                YRelDiff = np.around((vNow-vLastYear)/vLastYear*100,2)
                df.loc[it,'YRelDiff_M'] = YRelDiff
                df.loc[it,'YRelDiff_P'] = pointAboveCriteria(-YRelDiff, 2.5, 5)

                # --- Computing Year stats
                # NOTE: 
                #  You want increase quite above 2
                #  You want LastRat<<<0.5
                #  You want Mean>10 and < 3000
                m1y  = today- timedelta(days=1*365)
                m2y  = today- timedelta(days=2*365)
                m3y  = today- timedelta(days=3*365)
                data1y  = years['Close'][ years.index > str(m1y)]
                data2y  = years['Close'][(years.index > str(m2y)) & (years.index <= str(m1y))]
                data3y  = years['Close'][(years.index > str(m3y)) & (years.index <= str(m2y))]
                dataL2y = years['Close'][ years.index > str(m2y)]

                ref=np.mean(data3y)
                if np.isnan(ref):
                    ref=years['Close'][0]

                # --- How much increase over the years
                YIncr = np.around(np.mean(data1y)/ref,2) # how much increase compared to 2y ago. We want >>1 ,a stock doing goo
                df.loc[it,'YIncr_M'] = YIncr
                df.loc[it,'YIncr_P'] = pointAboveCriteria(YIncr,1,2)

                vmin  = np.min(data1y)
                vmean = np.mean(data1y)

                YRelMean = np.around((vNow-vmean)/vmean      ,2) # How are we now  compared to the year mean. We probably want this to be negative, we buy lower than the year mean
                YRat     = np.around((vNow-vmin)/(vmean-vmin),2) #How do we compare to the mean. 1=we are like the mean, >1 we are above it, <<1 we are very close to the min
                df.loc[it,'YRelMean_M']= YRelMean
                df.loc[it,'YRat_M'    ]= YRat
                df.loc[it,'YRelMean_P']= pointBelowCriteria( YRelMean, -0.1,  -0.2)
                df.loc[it,'YRat_P'    ]= pointBelowCriteria( YRat    ,  0.3 ,  0.5)

                # --- Total points 
                Points = [df.loc[it,c] for c in KeyPoints[1:]]
                df.loc[it,'Total'] =  np.nansum(Points)
                print(df.loc[it,'Total'], Points)
        except:
            print('>>>>>>>>>>>>>>>>>> ERROR')

# 
# def copygood(dfGood,folder):
#     FirstFile = dfGood['Filename'].values[0]
#     parent=os.path.join(os.path.dirname(FirstFile),folder)
#     if os.path.exists(parent):
#         try:
#             shutil.rmtree(parent)
#         except:
#             print('[FAIL] Removing directory '+parent)
#             pass
#     try:
#         os.makedirs(parent)
#     except:
#         print('[FAIL] Creating directory '+parent)
#         pass
#     for fn in dfGood['Filename'].values:
#         newfile = os.path.join(parent,os.path.basename(fn))
#         shutil.copyfile(fn,newfile)
# 
# 
# 
# 
# 
# 
# dfList.to_csv('PortfolioMonitor_{}.csv'.format(Mode),sep=',',index=False)
# dfList=dfList.sort_values(['MRelDiff'],ascending=False)
# print('')
# print('------------------------------------------------------------')
# print('>>> All:')
# print('')
# print(dfList[ISel])
# print('')
# 
# 
# 
# 
# 
# dfList=dfList.sort_values(['YRelDiff'],ascending=False)
# dfGood=dfList[dfList['YRelDiff']<-YRelDiffCrit]
# if len(dfGood)>0:
#     print('------------------------------------------------------------')
#     print('')
#     print('>>> Decreased more than {:.1f}% in the last year'.format(YRelDiffCrit))
#     print('')
#     print(dfGood[ISel])
#     copygood(dfGood,'_Year')
#     print('')
# 
# 
# dfList=dfList.sort_values(['MRelDiff'],ascending=False)
# dfGood=dfList[dfList['MRelDiff']<-MRelDiffCrit]
# if len(dfGood)>0:
#     print('------------------------------------------------------------')
#     print('')
#     print('>>> Decreased more than {:.1f}% in the last month'.format(MRelDiffCrit))
#     print('')
#     print(dfGood[ISel])
#     copygood(dfGood,'_Month')
#     print('')
# 
# dfList=dfList.sort_values(['YRelMean'],ascending=False)
# dfGood=dfList[dfList['YGood']]
# if len(dfGood)>0:
#     print('------------------------------------------------------------')
#     print('')
#     print('>>> Satisfy the year criteria')
#     print('')
#     print(dfGood[ISel])
#     copygood(dfGood,'_GoodYear')
#     print('')
# 
# 
# 




# --------------------------------------------------------------------------------}
# --- Write to Excel
# --------------------------------------------------------------------------------{
print(df.columns.values)

def colRange(iCol):
    nRows     = len(df)
    ColLetter = xlsxwriter.utility.xl_col_to_name(iCol)
    xlsRange =  '{:s}1:{:s}{:d}'.format(ColLetter,ColLetter,nRows+1)
    return xlsRange



writer = pd.ExcelWriter(OutFile, engine='xlsxwriter')
# Convert the dataframe to an XlsxWriter Excel object.
df.to_excel(writer, sheet_name=SheetName, index=False)
workbook  = writer.book
worksheet = writer.sheets[SheetName]

# --- Creating a "table"
nCols= len(df.columns)
nRows= len(df)
ColLetter=  xlsxwriter.utility.xl_col_to_name(nCols-1)
xlsRange = 'A1:'+'{:s}{:d}'.format(ColLetter,nRows+1)
worksheet.add_table(xlsRange, {'header_row': True, 'columns':[{'header':v} for v in df.columns.values]})

# --- Styling
# https://xlsxwriter.readthedocs.io/format.html
header_format = workbook.add_format({'text_wrap': True, 'bold': True, 'align':'left'})
worksheet.set_row(0, 60, header_format)

# Changing borders
borderfmt = workbook.add_format()   # {'border': 5})
borderfmt.set_right(5)
ColNames=list(df.columns.values)
for k in KeysInfo:
    worksheet.set_column(colRange(ColNames.index(KeysInfo[k][-1] )),20,borderfmt)

# --- Column width
# Default column width
for ColLetter in [xlsxwriter.utility.xl_col_to_name(i) for i in np.arange(len(df.columns))]:
    worksheet.set_column(ColLetter+':'+ColLetter, 5)
# Making some columns shorter
IValid=[ColNames.index(c) for c in ColNameExtraShort if c in ColNames]
for ColLetter in [xlsxwriter.utility.xl_col_to_name(i) for i in IValid]:
    worksheet.set_column(ColLetter+':'+ColLetter, 2)
# Making some columns longer
IValid=[ColNames.index(c) for c in ColNameExtraLong if c in ColNames]
for ColLetter in [xlsxwriter.utility.xl_col_to_name(i) for i in IValid]:
    worksheet.set_column(ColLetter+':'+ColLetter, 50)

# for ColLetter in [xlsxwriter.utility.xl_col_to_name(ColNames.index(c)) for c in KeysCompany]]:
#     worksheet.set_column(ColLetter+':'+ColLetter, 20, color_fmt)
# color_fmt = workbook.add_format({'bg_color': 'red'})
# for ColLetter in [xlsxwriter.utility.xl_col_to_name(ColNames.index(c)) for c in KeysRecomm]:
#     worksheet.set_column(ColLetter+':'+ColLetter, 20, color_fmt)


# # Account info columns (set size)
# # Total formatting
# total_fmt = workbook.add_format({'align': 'right', 'num_format': '$#,##0', 'bold': True, 'bottom':6})
# # Total percent format
# total_percent_fmt = workbook.add_format({'align': 'right', 'num_format': '0.0%', 'bold': True, 'bottom':6})


# --- Conditional formatting
# worksheet.conditional_format('B2:B8', {'type': '3_color_scale'})

# Highlight the top 5 values in Green
#worksheet.conditional_format(color_range, {'type': 'top', 'value': '5', 'format': format2})
## Highlight the bottom 5 values in Red
#worksheet.conditional_format(color_range, {'type': 'bottom', 'value': '5', 'format': format1})
writer.save()



# --------------------------------------------------------------------------------}
# --- Open Excel
# --------------------------------------------------------------------------------{
cmdLaunch='start "" "{:s}"'.format(OutFile)
os.system(cmdLaunch)
