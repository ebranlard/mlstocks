import numpy as np
import pandas as pd
from datetime import date, timedelta

from .symbol  import Symbol 
from .utils   import SearchableDict
from .crisis import get_crisis_data


# --------------------------------------------------------------------------------}
# --- Stats from history of price
# --------------------------------------------------------------------------------{
def last3y(df=None, tick=None):
    """ returns last three years of historical price data: 
    ym1: last year
    ym2: year 2 prior 
    ym3: year 3 prior
    ym321: last 3 years
    ym21:  last 2 years
    ym32: years 2 and 3 before 
    """
    if tick is not None:
        # Download last 3 years
        day_start     = (date.today()-timedelta(days=3*365)).strftime("%Y-%m-%d") 
        day_end       = date.today().strftime("%Y-%m-%d")
        symb=Symbol(tick)
        symb.download_history(ts_start=day_start, ts_end=day_end, interval='1d')
        df =symb.history

    today = date.today()
    m1y  = today- timedelta(days=1*365)
    m2y  = today- timedelta(days=2*365)
    m3y  = today- timedelta(days=3*365)
    ym1   = df[ df.index > str(m1y)]  # Last year
    ym2   = df[(df.index > str(m2y)) & (df.index <= str(m1y))]
    ym3   = df[(df.index > str(m3y)) & (df.index <= str(m2y))]
    ym32  = df[(df.index > str(m3y)) & (df.index <= str(m1y))]
    ym21  = df[ df.index > str(m2y)]
    ym321 = df[ df.index > str(m3y)]
    return ym1, ym2, ym3, ym21, ym32, ym321


def history_stats(history, currentPrice, stats=None):
    """
    Compute some historical stats based on historical dataframe of price

    NOTE: for now history should have intervals of 1d and at least 3y of data.

    return a searchable dictionary with keys:
       - priceChange_today: [%] change current day
       - priceChange_3days: [%] change last 3 days
       - priceChange_week:  [%] change last week
       - priceChange_month: [%] change last month
       - priceChange_year:  [%] change last year
    """
    if stats is None:
        stats=SearchableDict()

    history.index = history.index.astype('datetime64[ns]')
    history       = history.loc[~history.index.duplicated(keep = 'first')] # removing duplicate indices
    # Last three years of data
    dfym1, dfym2, dfym3, dfL2y, df32y,_ = last3y(history)

    # --- Rel diff currentPrice versus last week/month/year stat [%]
    # Relative day change
    vLastDays                    = lastdays_value(history,nDays= 1, removeToday = True)
    vLastAvg                     = np.mean(vLastDays.values)
    stats['priceChange_today']   = np.around((currentPrice-vLastAvg)/vLastAvg*100,2)
    # Relative change in the 3 last days
    vLastDays                  = lastdays_value(history,nDays = 3, removeToday = True)
    vLastAvg                   = vLastDays.values[0]                            
    stats['priceChange_3days'] = np.around((currentPrice-vLastAvg)/vLastAvg*100,2)
    # Relative change last week
    vLastWeek                 = lastweek_value(history)
    stats['priceChange_week'] = np.around((currentPrice-vLastWeek)/vLastWeek*100,2)
    # Relative change last months
    vLastMonth                 = lastmonth_value(history)
    stats['priceChange_month'] = np.around((currentPrice-vLastMonth)/vLastMonth*100,2)
    #  Relative change last year
    vLastYear                 = lastyear_value(history)
    stats['priceChange_year'] = np.around((currentPrice-vLastYear)/vLastYear*100,2)

    # --- Computing some ratios stats
    # NOTE: 
    #  You may want ratio_thisyear_3yearsAgo quite above 2 (stock value is increasing a lot)
    #  You may want ratio_current_YMin  <<<0.5  (currently cheamp compared to the mean)
    #  You may want ratio_current_YMean 
    data1y  = dfym1['Close'].values
    if len(data1y)>0:
        vmin  = np.min(data1y)
        vmean = np.mean(data1y)
    else:
        vmin  = np.nan
        vmean = np.nan
    if len(dfym3>0):
        ref = np.mean(dfym3['Close'].values)
    else:
        ref =np.nan
    # --- How much increase over the years
    # how much increase compared to 2y ago. We want >>1 ,a stock doing goo
    stats['ratio_thisYear_3yearsAgo'] =  np.around(vmean/ref,1)

    YRelMean = np.around((currentPrice-vmean)/vmean      ,1) # How are we now  compared to the year mean. May want this to be negative to buy lower than the year mean
    YRat     = np.around((currentPrice-vmin)/(vmean-vmin),1) #How do we compare to the mean. 1=we are like the mean, >1 we are above it, <<1 we are very close to the min
    stats['ratio_currentPrice_YMean']= YRelMean
    stats['ratio_currentPrice_YMin' ]= YRat

    return stats


def crisis_stats(ticker, sp500_crisis2008=None, sp500_crisis2020=None, criteriaCrisis=2, stats=None): # Compute performance during crises """
    """
    Computes stats comparing a ticker price history with SP500 during 2008 and 2020 crises 
    The two prices are normalized by their initial values atthe beginning of the crisis
    Then a relative comparison is performed between the two.

    return a searchable dictionary with keys:
       -  relSP08  : last value percent difference 
       -  relSP08_I: integral value of percent differences
    """
    if stats is None:
        stats=SearchableDict()

    # --- Performance with respect to sp500 in last year and year -3 -2

    # Using S&P500 is none provided
    if sp500_crisis2008 is None:
        sp500_crisis2008 = get_crisis_data('^GSPC', 2008)
    if sp500_crisis2020 is None:
        sp500_crisis2020 = get_crisis_data('^GSPC', 2020)

    # Performance against S&P500 during 2008 financial crisis
    df_crisis2008 = get_crisis_data(ticker, 2008)
    if len(df_crisis2008)>200:
        stats['relSP500_crisis08_I'], stats['relSP500_crisis08'] = rel_comparison(sp500_crisis2008, df_crisis2008)
    else:
        stats['relSP500_crisis08_I'] = np.nan
        stats['relSP500_crisis08']   = np.nan

    #  Performance against S&P500 during 2020 financial crisis
    df_crisis2020 = get_crisis_data(ticker, 2020)
    if len(df_crisis2020)>5:
        stats['relSP500_crisis20_I'], stats['relSP500_crisis20'] = rel_comparison(sp500_crisis2020, df_crisis2020)
    else:
        stats['relSP500_crisis20_I'] = np.nan
        stats['relSP500_crisis20']   = np.nan     

    stats['outperformSP500_crises'] = stats['relSP500_crisis08_I']>criteriaCrisis and stats['relSP500_crisis20_I']>criteriaCrisis

    return stats


def sp500_comp_stats(history, sp500_1y=None, sp500_32y=None, stats=None, criteria=2):
    """
    Computes stats comparing a ticker price history with SP500 during the last 3 years
    
    return a searchable dictionary with keys:
        - 'relSP500_year'   : relative difference end of current year (Ym1=year minus 1)
        - 'relSP500_year_I' : integral value of relative difference during this current year 
        - 'outperformSP500' : Has this stock outperformed the SP500 in the last 3 years?
        - 'recentUnderperformSP500' : Is this stock recently underperforming? 
    """
    if stats is None:
        stats=SearchableDict()

    # Clean inputs are extract/split last 3y of data
    history.index = history.index.astype('datetime64[ns]')
    history       = history.loc[~history.index.duplicated(keep = 'first')] # removing duplicate indices
    # Last three years of data
    df1y, df2y, df3y, dfL2y, df32y,_ = last3y(history)

    # Download S&P500 is no data provided
    if sp500_1y is None:
        sp500_1y, _, _, _, sp500_32y,_ = last3y(tick='^GSPC')

    # Performance against S&P500 last year
    if len(df1y)>200:
        stats['relSP500_year_I'], stats['relSP500_year'] = rel_comparison(sp500_1y, df1y)
    else:
        stats['relSP500_year_I'] = np.nan
        stats['relSP500_year']   = np.nan

    # Performance against S&P500 year-2 and year-3 year
    if len(df32y)>400:
        stats['relSP500_year23_I'], stats['relSP500_year23'] = rel_comparison(sp500_32y, df32y)
    else:
        stats['relSP500_year23_I'] = np.nan
        stats['relSP500_year23']   = np.nan

    # Translate the above into some metrics
    # Has this stock outperformed the SP500 in the last 3 years?
    if (stats['relSP500_year_I']>criteria) and (stats['relSP500_year23_I']>criteria):
        stats['outperformSP500_last3y'] =  1
    else:
        stats['outperformSP500_last3y'] = 0

    # Has this stock outperformed the SP500 this current year
    if (stats['relSP500_year_I']>criteria):
        stats['outperformSP500_year'] =  1
    else:
        stats['outperformSP500_year'] = 0

    # Is this stock recently underperforming? 
    # We say that a stock underperform if it used to beat the SP500 in years -2 -3 
    # but in the last year it has done worse than the SP500.
    # Sometimes a stock that underperform in current year, will outperform in next one if
    # it outperformed in the past.
    if (stats['relSP500_year_I']<-1.0) and (stats['relSP500_year23_I']>0):
        stats['recentUnderperformSP500'] =  1
    else:
        stats['recentUnderperformSP500'] = 0

    return stats




# --------------------------------------------------------------------------------}
# --- Helpers for metrics 
# --------------------------------------------------------------------------------{
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


def rel_comparison(df_ref,df_mes, more_out=False, variable='Close'):
    """ 
    Compute relative comparison of price:
     Integral value, and Last value 

    Prices are normalized to percent point increase compared to the price at t=0

    """
    df_ref = df_ref.filter([variable])
    df_mes = df_mes.filter([variable])
    t1=df_ref.index
    t2=df_mes.index
    p1=df_ref[variable].values
    p2=df_mes[variable].values
    # Normalizing price to percent point increase
    p1=(p1/p1[0]-1)*100 
    p2=(p2/p2[0]-1)*100

    if len(t1)!=len(t2):
        if np.abs(len(t1)-len(t2))>3:
            print('>>> Interpolating time',len(t1),len(t2))
        p2_new = np.interp(t1,t2,p2)
        #if p2_new[-1]!=p2[-1]:
        #    import pcdb; pdb.set_trace()
        #      = '1d' # 1d
        #    raise Exception('Extrapolation wrong')
        p2=p2_new

    x=np.linspace(0,1,len(t1))

    #  Difference
    p3=p2-p1
    Int = np.around(np.trapz(p3, x), 1)
    Last= np.around(p3[-1]         , 1)

    Int  = min(Int, 150)
    Int  = max(Int,-150)
    Last = min(Last, 150)
    Last = max(Last,-150)


    if more_out:
        return Int, Last, x, p1, p2, t1
    else:
        return Int, Last

def rel_comparison_plot_tick(tick1, tick2, ts_start=None, ts_end=None, period=None, interval='1d', variable='Close', ax=None, xDimensionless=False):
    """ 
    Plot relative comparison of two tickers

    Prices are normalized to percent point increase compared to the price at t=0
    """
    #
    symb1 = Symbol(tick1)
    symb2 = Symbol(tick2)
    df1= symb1.download_history(ts_start=ts_start, ts_end=ts_end, period=period, interval=interval)
    df2= symb2.download_history(ts_start=ts_start, ts_end=ts_end, period=period, interval=interval)
    return rel_comparison_plot_df(df1, df2, variable=variable, lb1=tick1, lb2=tick2, ax=ax, xDimensionless=xDimensionless)

def rel_comparison_plot_df(df1, df2, variable='Close', lb1='ref', lb2='other', ax=None, xDimensionless=False):
    """
    Plot two dataframe containing time histories of prices in the column `variable`

    Prices are normalized to percent point increase compared to the price at t=0
    """
    I,L,x,p1,p2,t1 = rel_comparison(df1,df2, more_out=True, variable=variable)
    print('Comparison integral: ',I)
    print('Comparison last    : ',L)

    if not xDimensionless:
        from pandas.plotting import register_matplotlib_converters
        register_matplotlib_converters()
        x=t1

    if ax is None:
        import matplotlib.pyplot as plt
        fig,ax = plt.subplots(1,1)
    ax.plot(x, p1,'k-', label=lb1)
    ax.plot(x, p2,      label=lb2)
    ax.plot(x, p2-p1, '--', label='delta')
    if not xDimensionless:
        ax.set_xlabel('Time')
    else:
        ax.set_xlabel('Dimensionless time [-]')
    ax.set_ylabel('Change in price from period start [%]')
    ax.legend()
    return ax


# --------------------------------------------------------------------------------}
# --- Helpers for price dataframe 
# --------------------------------------------------------------------------------{
# def getTimeIndex(df, ts):
# ts.strftime('%Y-%m-%d')
def current_price(tick, info, history):
    # --- Current price
    vNow = np.nan
    if 'currentPrice' in info:
        vNow = info['currentPrice']
    elif 'TR_currentPrice' in info:
        vNow = info['TR_currentPrice']
    else:
        print('[WARN] {} Current price not found in stats, using history'.format(tick))

    if np.isnan(vNow):
        if len(history)>0:
            # Checking when was the last index
            dt = date.today()-history.index[-1].date()
            if dt>=timedelta(days=2):
                print('[WARN] {} Using an old price:'.format(tick),dt )
            vNow = history.iloc[-1]['Close']
            #print('[FAIL] No current price')
    return vNow

def lastdays_value(df, nDays=3, removeToday=True):
    nDaysWeekend=nDays+5 # we add some days for safety
    iLastDays = df.index.get_loc(pd.to_datetime(date.today()-timedelta(days=nDaysWeekend)), method='nearest')
    values = df['Close'][iLastDays:]
    sToday= date.today().strftime("%Y-%m-%d")
    if removeToday: 
        if sToday in values.index:
            values = values[values.index!=sToday]
    #print('values',values)
    if len(values)>nDays:
        return values[len(values)-nDays:]
    else:
        return values

def lastweek_value(df):
    iLastWeek = df.index.get_loc(pd.to_datetime(date.today()-timedelta(days=7)), method='nearest')
    return df['Close'][iLastWeek]

def lastmonth_value(df):
    iLastMonth = df.index.get_loc(pd.to_datetime(date.today()-timedelta(days=31)), method='nearest')
    return df['Close'][iLastMonth]

def lastyear_value(df):
    iLastYear = df.index.get_loc(pd.to_datetime(date.today()-timedelta(days=365)), method='nearest')
    return df['Close'][iLastYear]

