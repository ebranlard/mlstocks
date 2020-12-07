import pandas as pd
import numpy as np
import os  

from mlstocks.tools.clean_exceptions import *
from mlstocks.symbol import Symbol
from mlstocks.crisis import get_crisis_data
from mlstocks.stats import last3y, current_price
from mlstocks.stats import crisis_stats, history_stats, sp500_comp_stats


def download_stats(ticks, columns=None, df=None, sources=['yahoo','tipranks'], nThreads=5, nTries=5, calc_history_stats=True):
    """ 
    Downloads statistics for a list of tickers and store it into a pandas DataFrame
    If a list of columns is provided, the columns are used to set the order of the columns

    nThreads: number of threads used to speed up the download. 
           Aborting requires closing the terminal or creating a file named ABORT


    """
    from mlstocks.tools.tictoc import Timer
    import random
    #import threading
    #import concurrent.futures
    from multiprocessing.pool import ThreadPool as Pool

    # --- Create a dataframe
    if df is None:
        df=pd.DataFrame()
        df['Ticker']=[t.strip().upper() for t in ticks]
    if columns is not None:
        for k in columns:
            if k not in df.columns:
                df[k]=np.nan

    # --- S&P 500 data used for various metrics
    sp500_crisis2008 = get_crisis_data('^GSPC', 2008)
    sp500_crisis2020 = get_crisis_data('^GSPC', 2020)
    sp500_1y, sp500_2y, sp500_3y, sp500_L2y, sp500_32y,_ = last3y(tick='^GSPC')

    # Shuffling, in case the user stop, we download different data every time
    I = list(np.arange(len(ticks)))
    random.shuffle(I)
    problematic_tickers=[]

    # --- Creating a thread for each ticker
    def process_one_ticker(it, iit=1):
        tick=ticks[it]
        if os.path.exists('ABORT'):
            print('ABORT File found')
            return
        print('{:3d}/{:3d} {:15.15s} '.format(iit+1,len(ticks),tick))
        symb = Symbol(tick)
        # --- Download stats, and store in table
        for source in sources:
            with Timer(tick + ' Download Stats {}'.format(source)):
                symb.download_stats(sources=[source], nTries=nTries)

        # --- Get historical market data
        if calc_history_stats:
            with Timer(tick + ' Donwload History'):
                # NOTE: this is stored in _history and hence affects "actions"= "dividends" "splits"
                history = symb.download_history(period="5y" , interval='1d' )

        # --- Store stats in table
        #with Timer(tick + ' Store Stats'):
        info = symb.stats
        sError=''
        if columns is not None:
            for key in columns:
                if key in info.keys():
                    df.loc[it,key] = info[key]
                else:
                    info[key]=np.nan
                    sError+= key+', '
            #if len(sError)>0:
            #    print('Missing keys:',sError)
        else:
            for key in info.keys():
                df.loc[it,key] = info[key]

        if calc_history_stats and len(history)<=0:
            print('[FAIL] No time data')
            problematic_tickers.append(tick)
            return
        if symb.failedStats==len(sources):
            problematic_tickers.append(tick)

        # --- Time history metrics
        if calc_history_stats:
            #with Timer(tick + ' Compute Metrics'):
            # --- Current price
            vNow = current_price(tick, symb.stats, history)
        
            # --- Performance against S&P500 during 2008 and 2020 crises
            cr_stats = crisis_stats(tick, sp500_crisis2008, sp500_crisis2020, criteriaCrisis= 2)
            if columns is None:
                for k,v in cr_stats.items():
                    df.loc[it,k] = v
            else:
                for k,v in cr_stats.items():
                    if k in df.columns:
                        df.loc[it,k] = v

            # --- Performance against S&P500 last year
            sp_stats = sp500_comp_stats(history, sp500_1y, sp500_32y)
            if columns is None:
                for k,v in sp_stats.items():
                    df.loc[it,k] = v
            else:
                for k,v in sp_stats.items():
                    if k in df.columns:
                        df.loc[it,k] = v

            # --- Rel diff today versus last week/month/year stat
            hstats = history_stats(history, vNow)
            if columns is None:
                for k,v in hstats.items():
                    df.loc[it,k] = v
            else:
                for k,v in hstats.items():
                    if k in df.columns:
                        df.loc[it,k] = v

    if nThreads==1:
        # --- Simple loop over tickers
        for iit,it in enumerate(I):
             process_one_ticker(it, iit)
    else:
        # --- Loop over tickers using a parallel pool
        pool = Pool(nThreads)
        for iit,it in enumerate(I):
            pool.apply_async(process_one_ticker, (it,iit))
        pool.close()
        pool.join()

    if len(problematic_tickers)>0:
        problematic_tickers=list(set(problematic_tickers))
        problematic_tickers.sort()
        print('Problem with the following tickers:', problematic_tickers)

    return df

