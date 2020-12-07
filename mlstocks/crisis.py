import numpy as np
import os
from datetime import date

from .symbol import Symbol 

def get_crisis_ts(year=2008):
    """ 
    return time stamp of crisis
    """
    if year==2008:
        ts_start = '2007-10-09'
        ts_end   = '2009-04-01'
    elif year==2020:
        ts_start='2020-02-18'
        ts_end  ='2020-06-01'
    else:
        raise NotImplementedError('Crisis year {} not implemented'.format(year))
    return ts_start, ts_end


def get_crisis_data(tick, crisis_year, df_in=None):
    """
    Download or extract crisis data
    """
    ts_start, ts_end = get_crisis_ts(crisis_year)
    MyDir=os.path.dirname(__file__)

    if df_in is not None:
        df_out = df_in[ df_in.index >= ts_start]
        if ts_end is not None:
          df_out= df_out[ df_out.index <= ts_end]
        #if len(df_out)<=0: 
        #    raise Exception('No data found')
        return df_out
    else:
        # No data provided, download data..
        symb=Symbol(tick, folder=os.path.join(MyDir,'../_{:d}Crisis'.format(crisis_year)))
        symb.download_history(ts_start=ts_start, ts_end=ts_end, interval='1d', saveOnDisk=True, loadOnDisk=True)
        return symb.history

