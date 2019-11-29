from mlstocks.symbol import *
import pandas as pd
from pybra.clean_exceptions import *
import os
from datetime import date, timedelta
import weio

# # 
day_start = None
day_end   = None

Mode='Random'
Mode='Portfolio'



# ---

if Mode=='Random':
    df = pd.read_csv('./_data/symbol_lists/yahoo_all.csv')
    # random_subset = df.sample(n=3)
    # print(len(df))
    df=df[(df['Type']=='NMS') |  (df['Type']=='NYQ') |  (df['Type']=='PNK')]
    # print(len(df))

    # Index(['Ticker', 'Name', 'Exchange', 'exchangeDisplay', 'Type', 'TypeDisplay']
    TICKS=df['Ticker']
    NAMES=df['Name']
    bBad = NAMES==TICKS
    TICKS=TICKS[~bBad]

    WrongTickFile='_data/symbol_lists/WrongTicks.csv'
    if os.path.exists(WrongTickFile):
        df = pd.read_csv(WrongTickFile)
        WrongTicks=df['Ticker']
        print('Number of Wrong ticks  :',len(WrongTicks))
        nTicks=len(TICKS)
        TICKS=TICKS[~TICKS.isin(WrongTicks)]
        print('Number of ticks removed:',nTicks-len(TICKS))
        WrongTicks=WrongTicks.tolist()
    else:
        WrongTicks=[]
    nWrong=len(WrongTicks)

    DoneTickFile='_data/symbol_lists/DoneTicks.csv'
    if os.path.exists(DoneTickFile):
        df = pd.read_csv(DoneTickFile)
        DoneTicks=df['Ticker']
        print('Number of Done ticks  :',len(DoneTicks))
        nTicks=len(TICKS)
        TICKS=TICKS[~TICKS.isin(DoneTicks)]
        print('Number of ticks removed:',nTicks-len(TICKS))
        DoneTicks=DoneTicks.tolist()
    else:
        DoneTicks=[]
    nDone=len(DoneTicks)

    TICKS=df['Ticker'].sample(7000)

elif Mode=='Portfolio':
    di=weio.read('Portfolio.xlsx').toDataFrame()
    df=di[next(iter(di))]
    print(df.columns)
    #df=df[df['Note']!='B']
    # ---
    TICKS=df['Ticker']
    names=df['Name']
    WrongTicks=None
    DoneTicks=None
# 
# TICKS=['FSLR','NFLX','DOGEF','BASFY','EDIT','GCTAF','NTLA','OC','UBER']



dfList=pd.DataFrame()
dfList['ID']=list(np.arange(len(TICKS)))
dfList['nDays']=0
dfList['Meanm3Y']=0
dfList['Meanm2Y']=0
dfList['Meanm1Y']=0
dfList['Increase']=0
dfList['Last']=0
dfList['LastRelMean']=0
dfList['MeanRel']=0
dfList['LastRel']=0
dfList['LastAbs']=0
dfList['LastAbs2']=0
dfList['LastRat']=0
dfList['LastRat2']=0
dfList['Ticks']=''

for it,tick in enumerate(TICKS):
    if WrongTicks is not None and len(tick)>12:
        WrongTicks.append(tick)
        continue
    if tick.find(' ')<=0 and tick[0]!='^' and tick.find('.')<0 :
        print('{:6d}/{:6d} {:12s} '.format(it,len(TICKS),tick))#,len(DoneTicks),len(WrongTicks)))
        symb=Symbol(tick)
        symb.download(day_start = day_start, day_end=day_end)
        if len(symb.data)<=1:
            if WrongTicks is not None:
                WrongTicks.append(tick)
        else:
            if DoneTicks is not None:
                DoneTicks.append(tick)
            # Computing stats
            today = date.today()
            m1y  = today- timedelta(days=1*365)
            m2y  = today- timedelta(days=2*365)
            m3y  = today- timedelta(days=3*365)
            data1y = symb.data['Close'][ symb.data.index  > str(m1y)]
            data2y = symb.data['Close'][(symb.data.index > str(m2y)) & (symb.data.index <= str(m1y))]
            data3y = symb.data['Close'][(symb.data.index > str(m3y))  & (symb.data.index <= str(m2y))]

            dataL2y = symb.data['Close'][symb.data.index > str(m2y)]


            dfList.loc[it,'nDays'  ]= len(symb.data)
            dfList.loc[it,'Meanm1Y']=np.mean(data1y)
            dfList.loc[it,'Meanm2Y']=np.mean(data2y)
            dfList.loc[it,'Meanm3Y']=np.mean(data3y)
            ref=np.mean(data3y)
            if np.isnan(ref):
                ref=symb.data['Close'][0]

            # NOTE: 
            #  You want increase quite above 2
            #  You want LastRat<<<0.5
            #  You want Mean>10 and < 3000
            dfList.loc[it,'Increase']=np.mean(data1y)/ref # how much increase compared to 2y ago. We want >>1 ,a stock doing goo

            vmin  = np.min(data1y)
            vmax  = np.max(data1y)
            vmean = np.mean(data1y)
            vLast=symb.data['Close'][-1]

            dfList.loc[it,'Last'       ]=vLast
            dfList.loc[it,'LastRelMean']= (vLast-vmean)/vmean  # How are we now  compared to the year mean. We probably want this to be negative, we buy lower than the year mean
            dfList.loc[it,'MeanRel'    ]= (vmean-vmin)/(vmax-vmin) # how is the mean, compared to the min-max range. 
            dfList.loc[it,'LastRel'    ]= (vLast-vmean)/(vmax-vmin) # How are we compared to the mean, in the min-max range. Probably best to be negative (we are below the mean)
            dfList.loc[it,'LastAbs'    ]= (vLast-vmin)/(vmax-vmin)-(vmean-vmin)/(vmax-vmin) # In the min-max range how are we compared to the mean. Positive, we are currently above. We probably want negative values
            dfList.loc[it,'LastRat'    ]= (vLast-vmin)/(vmean-vmin) #How do we compare to the mean. 1=we are like the mean, >1 we are above it, <<1 we are very close to the min

            vmin  = np.min(dataL2y)
            vmax  = np.max(dataL2y)
            vmean = np.mean(dataL2y)
            dfList.loc[it,'LastAbs2']= (vLast-vmin)/(vmax-vmin)-(vmean-vmin)/(vmax-vmin)
            dfList.loc[it,'LastRat2']= (vLast-vmin)/(vmean-vmin)
            dfList.loc[it,'Ticks'   ]= tick
    else:
        if WrongTicks is not None:
            WrongTicks.append(tick)

# print(dfList)
# import pdb
# pdb.set_trace()

dfList['Meanm3Y'     ]=np.around(dfList['Meanm3Y'     ],2)
dfList['Meanm2Y'     ]=np.around(dfList['Meanm2Y'     ],2)
dfList['Meanm1Y'     ]=np.around(dfList['Meanm1Y'     ],2)
dfList['Increase'    ]=np.around(dfList['Increase'    ],2)
dfList['Last'        ]=np.around(dfList['Last'        ],2)
dfList['LastRelMean' ]=np.around(dfList['LastRelMean' ],2)
dfList['MeanRel'     ]=np.around(dfList['MeanRel'     ],2)
dfList['LastRel'     ]=np.around(dfList['LastRel'     ],2)
dfList['LastAbs'     ]=np.around(dfList['LastAbs'     ],2)
dfList['LastAbs2'    ]=np.around(dfList['LastAbs2'    ],2)
dfList['LastRat'     ]=np.around(dfList['LastRat'     ],2)
dfList['LastRat2'    ]=np.around(dfList['LastRat2'    ],2)











dfList=dfList[dfList['nDays']>400]

dfList.to_csv('Portfolio_Stats_{}.csv'.format(Mode),sep=',',index=False)

