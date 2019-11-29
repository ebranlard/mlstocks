import pandas as pd
import os
from datetime import date, timedelta
import numpy as np

import yfinance as yf  

_EVAL=False

NCOL=3


def download_symbol(name,ts_start,ts_end,interval='1d'):
    """
    Wrapper for symbol download
    For now, only Yahoo finance with yfinance supported
    Returns a dataframe
        interval : str
            Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            Intraday data cannot extend last 60 days
    """
    # See https://github.com/ranaroussi/yfinance/blob/master/yfinance/multi.py
    #print(interval)
    df= yf.download(name,ts_start,ts_end, interval=interval, progress=False)
#     print(df)
    #df['Date'] = df.index
    return df


class Symbol:
    """ 

    attributes:
      - data: dataframe with columns:
              -
    
    """
    def __init__(self,name, folder=None, prefix=None, suffix=None):
        self.name=name
        self.data_raw=[]
        self.folder=folder
        self.prefix=prefix
        self.suffix=suffix

    def print(self,s):
        print('>>> {:10s}: {}'.format(self.name,s))

    

    def download(self, day_start=None, day_end=None, force=False, suffix=None, interval='1d'):
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
            if len(self.data)<=1:
                self.print('[WARN] Data exist but with only {} row. Skipping.'.format(len(self.data)))
                doDownload=False
                bOK=False
            elif len(self.data.columns)!=NCOL:
                self.print('[WARN] Wrong number of columns in raw date, removing file')
                self.delete_raw()
                doDownload=True
            else:
                df=self.data
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
                dt_print('Data exist', old_start, old_end, n=len(df))
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
            self.data = download_symbol(self.name, day_start, day_end, interval=interval)
            self.data.drop(['Open','High','Low'], 1, inplace=True)
            if len(self.data.columns)!=NCOL:
                self.print('[FAIL] Downloaded data is erroneous')
                bOK=False
            if len(self.data)>0:
                dt_print('Downloaded',self.data.index[0], self.data.index[-1], len(self.data))
                if doConcat:
                    self.data = pd.concat((df,self.data))
                    self.data.sort_index(inplace=True)
                    self.data=self.data[~self.data.index.duplicated(keep='first')]
                    dt_print('New data',self.data.index[0],self.data.index[-1],len(self.data))
                self.save_raw()
        return bOK


    def save_raw(self):
        #self.print('Saving to '+self.raw_filename)
        #self.data.to_csv(self.raw_filename,sep=',',index=False)
        parent=os.path.dirname(self.raw_filename)
        if not os.path.exists(parent):
            os.makedirs(parent)
        try:
            self.data.to_csv(self.raw_filename,sep=',',index=True)
        except:
            self.print('[FAIL] Problem writing '+self.raw_filename)
            self.data=[]
        
    def load_raw(self):
        try:
            self.data=pd.read_csv(self.raw_filename,sep=',',index_col=0)
            self.data.index = pd.to_datetime(self.data.index)
        except:
            self.print('[FAIL] Problem reading '+self.raw_filename)
            self.delete_raw()
            self.data=[]

        
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
