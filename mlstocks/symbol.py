import pandas as pd
import os
import numpy as np
import time
from datetime import date, timedelta

from .yahoo_finance import download_stats_yahoo  , download_history_yahoo
from .tipranks      import download_stats_tipranks
from .utils import SearchableDict
from .exceptions import *


class Symbol():
    """ 

    attributes:
      - history: dataframe with columns: # TODO

    main methods
    - download_history_yahoo
    - download_stats_yahoo
    - download_stats_tipranks
    
    """
    def __init__(self, name, folder=None, prefix=None, suffix=None):
        self.name  = name
        self.stats = None
        self.all_stats = None
        self.failedStats=0
        
        # legacy
        self.folder=folder
        self.prefix=prefix
        self.suffix=suffix

    def print(self,s):
        print('>>> {:10s}: {}'.format(self.name,s))

    

    # --------------------------------------------------------------------------------}
    # --- Download stats
    # --------------------------------------------------------------------------------{
    def download_stats(self, sources=['yahoo'], nTries=2, extra=False):
        """ 
        download statistics

        sources: list of sources, e.g. ['yahoo','tipranks']

        """
        if self.stats is None:
            self.stats     = SearchableDict()
            self.all_stats = SearchableDict()

        iTries=0
        if 'yahoo' in sources:
            while iTries<nTries:
                try:
                    basic_stats, all_stats = download_stats_yahoo(self.name, financials=extra)
                    self.stats.update(basic_stats)
                    self.all_stats.update(all_stats)
                    break
                except EmptyDataException:
                    print('[FAIL] {} Error getting yahoo info try {}'.format(self.name, iTries+1))
                    iTries += 1
                    if iTries<nTries:
                        time.sleep(float(iTries))
                    if iTries>=nTries:
                        self.failedStats+=1
        if 'tipranks' in sources:
            if 'quoteType' in self.stats:
                if self.stats['quoteType'].upper() in ['ETF','MF','MUTUALFUND','MUTUAL FUND']:
                    print('[WARN] {} Skipping tipranks for ETF/MF'.format(self.name))
                    return self.stats

            while iTries<nTries:
                try:
                    basic_stats, all_stats = download_stats_tipranks(self.name)
                    self.stats.update(basic_stats)
                    self.all_stats.update(all_stats)
                    break
                except EmptyDataException:
                    print('[FAIL] {} Error getting tipranks info try {}'.format(self.name, iTries+1))
                    iTries += 1
                    if iTries<nTries:
                        time.sleep(float(iTries))
                    if iTries>=nTries:
                        self.failedStats+=1
        return self.stats


    def download_history(self, period=None, ts_start=None, ts_end=None, interval='1d', saveOnDisk=False, loadOnDisk=False, source='yahoo'):
        """ Download time history of a given ticker

        period : str, Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,5y,10y,ytd,max
            Either Use period parameter or use start and end

        ts_start: str, Download start date string (YYYY-MM-DD) or _datetime.
                Default is 1900-01-01

        ts_end: str, Download end date string (YYYY-MM-DD) or _datetime.
                Default is now

        interval : str, Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                Intraday data cannot extend last 60 days
        
        source: str, only 'yahoo' for now

        saveOnDisk: write data to disk 
        loadOnDisk: load data from disk
        """

        doDownload=True
        if loadOnDisk and os.path.exists(self.raw_filename):
            # Load data from disk
            self.load_raw()
            if len(self.history)<=1:
                self.print('[WARN] Data exist but with only {} row. Skipping.'.format(len(self.history)))
                self.delete_raw()
            else:
                doDownload=False
                history=self.history
                old_start = history.index[0]
                old_end   = history.index[-1]

        if doDownload:
            if ts_start is not None:
                ts_start=pd.to_datetime(ts_start)
            if ts_end is not None:
                ts_end  =pd.to_datetime(ts_end)

            # Download data
            if source=='yahoo':
                history = download_history_yahoo(self.name, period=period, ts_start=ts_start, ts_end=ts_end, interval=interval)
            else:
                raise NotImplementedError()

            history.drop(['Open','High','Low'], 1, inplace=True)
            try:
                history.drop(['Adj Close'], 1, inplace=True)
            except:
                pass

        history.index=history.index.astype('datetime64[ns]')
        history = history.loc[~history.index.duplicated(keep='first')] # removing duplicate indices
        self.history=history

        if len(self.history)>0:
            if saveOnDisk:
                self.save_raw()
        return self.history


    # --------------------------------------------------------------------------------}
    # --- Old history download
    # --------------------------------------------------------------------------------{
    def download_history_legacy(self, period=None, day_start=None, day_end=None, force=False, suffix=None, interval='1d', saveOnDisk=True):
        """
        Use yahoo to download history
        """
        bOK=True

        def next_busday(t):
            while not np.is_busday(t.date()):
                t=t+ timedelta(days=1)
            return t
        def prev_busday(t):
            while not np.is_busday(t.date()):
                t=t- timedelta(days=1)
            return t

        def dt_print(prefix,t1,t2,n=None):
            ndays      = (t2-t1).days
            ndays_busy = np.busday_count( t1.date(), t2.date())
            if n:
                self.print('{:12s} from {} to {} - {}/{}/{} days'.format(prefix,t1.strftime("%Y-%m-%d"),t2.strftime("%Y-%m-%d"),n,ndays_busy,ndays))
            else:
                self.print('{:12s} from {} to {} - {}/{} days'.format(prefix,t1.strftime("%Y-%m-%d"),t2.strftime("%Y-%m-%d"),ndays_busy,ndays))


        if day_end is None:
            day_end = date.today().strftime("%Y-%m-%d")
        if day_start is None:
            day_start = '1970-01-01' # TODO

        day_start=pd.to_datetime(day_start)
        day_end  =pd.to_datetime(day_end)

        doDownload=True
        doConcat=False
        if os.path.exists(self.raw_filename) and not force:
            self.load_raw()
            doDownload=False
            if len(self.history)<=1:
                self.print('[WARN] Data exist but with only {} row. Skipping.'.format(len(self.history)))
                doDownload=False
                bOK=False
            else:
                df=self.history
                old_start = df.index[0]
                old_end   = df.index[-1]
                day_start = next_busday(day_start)
                day_end   = prev_busday(day_end)
                if day_start<old_start:
                    pass#print('>>> Skipping previous start day since data already present')
                #    doDownload=True
                #    doConcat=True
                #else:
                if day_start>=old_start:
                    day_start=old_end  + timedelta(days=1)

                if day_end>old_end:
                    doDownload=True
                    doConcat=True
                else: 
                    day_end=old_start  - timedelta(days=1)
                #dt_print('Data exist', old_start, old_end, n=len(df))
                if doDownload:
                    if (day_start-day_end).days==0:
                        doDownload=False
                        doConcat=False
                    elif (day_end-old_end).days<7:
                        self.print('[WARN] Not downloading if less than 7 days missing')
                        doDownload=False
                        doConcat=False

        if doDownload:
            #dt_print('Downloading', day_start, day_end)
            self.history = download_history_yahoo(self.name, ts_start=day_start, ts_end=day_end, interval=interval)
            try:
                self.history.drop(['Adj Close'], 1, inplace=True)
            except:
                pass
            if len(self.history)>0:
                #dt_print('Downloaded',self.history.index[0], self.history.index[-1], len(self.history))
                if doConcat:
                    self.history = pd.concat((df,self.history))
                    self.history.sort_index(inplace=True)
                    self.history=self.history[~self.history.index.duplicated(keep='first')]
                    #dt_print('New data',self.history.index[0],self.history.index[-1],len(self.history))
                if saveOnDisk:
                    self.save_raw()
        return bOK


    def save_raw(self):
        #self.print('Saving to '+self.raw_filename)
        #self.history.to_csv(self.raw_filename,sep=',',index=False)
        parent=os.path.dirname(self.raw_filename)
        if not os.path.exists(parent):
            os.makedirs(parent)
        try:
            self.history.to_csv(self.raw_filename,sep=',',index=True)
        except:
            self.print('[FAIL] Problem writing '+self.raw_filename)
            self.history=[]
        
    def load_raw(self):
        try:
            self.history=pd.read_csv(self.raw_filename,sep=',',index_col=0)
            self.history.index = pd.to_datetime(self.history.index)
        except:
            self.print('[FAIL] Problem reading '+self.raw_filename)
            self.delete_raw()
            self.history=[]

        
    def delete_raw(self):
        if os.path.exists(self.raw_filename):
            os.remove(self.raw_filename)

    @property
    def raw_filename(self):
        if self.suffix is None:
            suffix=''
        else:
            suffix='_'+self.suffix
        if self.folder is None:
            folder='_data/symbols_raw/'
            # we use first letter 
            return os.path.join(os.path.normpath(folder), self.name[0],self.name+suffix+'.csv')
        else:
            return os.path.join(os.path.normpath(self.folder),self.name+suffix+'.csv')
