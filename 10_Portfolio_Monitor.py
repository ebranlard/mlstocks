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

# --------------------------------------------------------------------------------}
# --- Option for monitored stocks 
# --------------------------------------------------------------------------------{
Mode          = 'Monitor'    # Monitor/Portfolio/NotBought
Mode          = 'NotBought'  # Monitor/Portfolio/NotBought 
Mode          = 'Portfolio'  # Monitor/Portfolio/NotBought 

MRelDiffCrit=5
YRelDiffCrit=3

# --- Derived params
day_start     = (date.today()-timedelta(days=3*365)).strftime("%Y-%m-%d") 
day_end       = date.today().strftime("%Y-%m-%d")
Folder        = '_'+Mode+'/'

# --- Read portfolio
di=weio.read('Portfolio.xlsx').toDataFrame()
df=di[next(iter(di))]
df=df.replace(r'^\s*$', 'XXX', regex=True)
print(df.columns)
# --- Perform selection
if Mode.find('Monitor')>=0:
    df=df[df['Note'].str.find('M')>=0 ] # select monitor
elif Mode.find('NotBought')>=0:
    df=df[df['Note']!='B']          # we select things we didn't buy already
elif Mode.find('Portfolio')>=0:
    # we select all
    pass

# ---
ticks     = df['Ticker'].values
companies = df['Name'].values
types     = df['Type'].values
notes     = (df['International'].map(str)+'_'+df['Dividend'].map(str)+'_'+df['Note'].map(str) +'_'+df['Crisis'].map(str) + '_' + df['LongTerm'].map(str)).values

# --- All you need for script below is:
# ticks     = ['AAPL','GOOG']
# day_start = '2019-10-28'
# day_end   = '2019-10-31'
# companies = None
# notes = None
# types = None

# --- Less likely parameters
ForceDownload = True
# ForceDownload = False
Interval      = '1d' # 1d

# --------------------------------------------------------------------------------}
# ---  Main Script
# --------------------------------------------------------------------------------{
dfList=pd.DataFrame()
dfList['Tick']=''
dfList['Company']=''
dfList['Type'] = ''
dfList['Note'] = ''
dfList['MRelDiff'] =0
dfList['YRelDiff'] =0

dfList['YIncr.']    = 0
dfList['YRelMean'] = 0
dfList['YRat']     = 0
dfList['YRat2']    = 0
dfList['YGood']    = False
dfList['Filename']=''

ISel=['Tick','Company','Type','Note','MRelDiff','YRelDiff','YIncr.','YRelMean','YRat','YGood']


# dfList['AbsDiff'] =0
for it,tick in enumerate(ticks):
    print('{:3d}/{:3d}  '.format(it+1,len(ticks)),end='')
    #
    if companies is not None:
        company=('{:15.15s}'.format(str(companies[it]).replace(' ',''))).strip()
    else:
        company=''
    #
    if notes is not None:
        note=str(notes[it]).replace('nan_','').replace('_nan','').strip()
    else:
        note=''
    #
    if types is not None:
        stype=str(types[it]).strip()
    else:
        stype=''

    symb=Symbol(tick, folder=Folder, suffix=company)
    symb.download(day_start = day_start, day_end=day_end, force=ForceDownload, interval=Interval)
    if len(symb.data)>0:

        # --- Basic info
        dfList.loc[it,'Tick']       = tick
        dfList.loc[it,'Company']     = company
        dfList.loc[it,'Type']        = stype
        dfList.loc[it,'Note']        = note
        dfList.loc[it,'Filename']    = symb.raw_filename

        # --- Computing stats
        df = symb.data

        # --- Last month stat
        iLastMonth = df.index.get_loc(pd.to_datetime(date.today()-timedelta(days=31)), method='nearest')
        iToday     = df.index.get_loc(pd.to_datetime(date.today()                   ), method='nearest')
        vLastMonth = df['Close'][iLastMonth]
        vToday     = df['Close'][iToday]
        dfList.loc[it,'MRelDiff'] = np.around((vToday-vLastMonth)/vLastMonth*100,2)

        # --- Computing Year stats
        # NOTE: 
        #  You want increase quite above 2
        #  You want LastRat<<<0.5
        #  You want Mean>10 and < 3000
        iLastYear = df.index.get_loc(pd.to_datetime(date.today()-timedelta(days=365)), method='nearest')
        today = date.today()
        m1y  = today- timedelta(days=1*365)
        m2y  = today- timedelta(days=2*365)
        m3y  = today- timedelta(days=3*365)
        data1y  = df['Close'][ df.index > str(m1y)]
        data2y  = df['Close'][(df.index > str(m2y)) & (df.index <= str(m1y))]
        data3y  = df['Close'][(df.index > str(m3y)) & (df.index <= str(m2y))]
        dataL2y = df['Close'][ df.index > str(m2y)]
        vLastYear = df['Close'][iLastYear]
        dfList.loc[it,'YRelDiff'] = np.around((vToday-vLastYear)/vLastYear*100,2)

        ref=np.mean(data3y)
        if np.isnan(ref):
            ref=df['Close'][0]

        dfList.loc[it,'YIncr.']=np.around(np.mean(data1y)/ref,2) # how much increase compared to 2y ago. We want >>1 ,a stock doing goo

        vmin  = np.min(data1y)
        vmean = np.mean(data1y)
        vLast = df['Close'][-1]

        dfList.loc[it,'YRelMean']= np.around((vLast-vmean)/vmean      ,2) # How are we now  compared to the year mean. We probably want this to be negative, we buy lower than the year mean
        dfList.loc[it,'YRat'    ]= np.around((vLast-vmin)/(vmean-vmin),2) #How do we compare to the mean. 1=we are like the mean, >1 we are above it, <<1 we are very close to the min
        vmin  = np.min(dataL2y)
        vmean = np.mean(dataL2y)
        dfList.loc[it,'YRat2']= np.around((vLast-vmin)/(vmean-vmin),2)

        dfList.loc[it,'YGood'] =  (dfList.loc[it,'YRat']<0.5) & (dfList.loc[it,'YRelMean']<-0.2)  & (dfList.loc[it,'YIncr.']>2)
        


def copygood(dfGood,folder):
    FirstFile = dfGood['Filename'].values[0]
    parent=os.path.join(os.path.dirname(FirstFile),folder)
    if os.path.exists(parent):
        try:
            shutil.rmtree(parent)
        except:
            print('[FAIL] Removing directory '+parent)
            pass
    try:
        os.makedirs(parent)
    except:
        print('[FAIL] Creating directory '+parent)
        pass
    for fn in dfGood['Filename'].values:
        newfile = os.path.join(parent,os.path.basename(fn))
        shutil.copyfile(fn,newfile)






dfList.to_csv('PortfolioMonitor_{}.csv'.format(Mode),sep=',',index=False)
dfList=dfList.sort_values(['MRelDiff'],ascending=False)
print('')
print('------------------------------------------------------------')
print('>>> All:')
print('')
print(dfList[ISel])
print('')





dfList=dfList.sort_values(['YRelDiff'],ascending=False)
dfGood=dfList[dfList['YRelDiff']<-YRelDiffCrit]
if len(dfGood)>0:
    print('------------------------------------------------------------')
    print('')
    print('>>> Decreased more than {:.1f}% in the last year'.format(YRelDiffCrit))
    print('')
    print(dfGood[ISel])
    copygood(dfGood,'_Year')
    print('')


dfList=dfList.sort_values(['MRelDiff'],ascending=False)
dfGood=dfList[dfList['MRelDiff']<-MRelDiffCrit]
if len(dfGood)>0:
    print('------------------------------------------------------------')
    print('')
    print('>>> Decreased more than {:.1f}% in the last month'.format(MRelDiffCrit))
    print('')
    print(dfGood[ISel])
    copygood(dfGood,'_Month')
    print('')

dfList=dfList.sort_values(['YRelMean'],ascending=False)
dfGood=dfList[dfList['YGood']]
if len(dfGood)>0:
    print('------------------------------------------------------------')
    print('')
    print('>>> Satisfy the year criteria')
    print('')
    print(dfGood[ISel])
    copygood(dfGood,'_GoodYear')
    print('')





