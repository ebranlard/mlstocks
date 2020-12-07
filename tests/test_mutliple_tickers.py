import pandas as pd
import os
import time

from mlstocks.excel_table import ExcelTable
from mlstocks.symbol_list import download_stats
from mlstocks.utils import *

import unittest

class Test(unittest.TestCase):
    def test_yahoo_stats(self):
        # --- Parameters
        nThreads=2   # Number of therads used to download data
        nTries=2     # Number of retry if download of data fail
        sheetName='Portfolio' #  Name of sheet forExcel output
        outFile = '_DummpyExampleStats.xlsx'  # Excel output file
        ticks  = ['AAPL','SPY']

        # --- Select column and column order
        # For a full list of available columns see the examples for "one ticker"
        columns=[]
        columns += ['longName','country','currentPrice','expenseRatio']  # Basic company info

        df = download_stats(ticks, columns, nThreads=nThreads, nTries=nTries, calc_history_stats=False)
        print(df)

        # --- Write to Excel
        xls = ExcelTable(outFile, df=df, sheetname=sheetName)
        xls.conditionalFormatBadAbove('expenseRatio',  0.5)
        xls.urlValues('Ticker',[t for t in df['Ticker']], ['https://finance.yahoo.com/quote/{:s}?p={:s}'.format(t,t) for t in df['Ticker']])
        # --- Write and laucnh 
        xls.write()

if __name__=='__main__':
    unittest.main()
