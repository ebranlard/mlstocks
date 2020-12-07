from mlstocks.yahoo_finance import download_stats_yahoo, download_history_yahoo
from mlstocks.stats import history_stats, sp500_comp_stats, crisis_stats

import unittest

class Test(unittest.TestCase):
    def test_yahoo_stats(self):
        ticker='AAPL'

        # --- Download statistics
        basic_stats, all_stats = download_stats_yahoo(ticker, True)

        self.assertEqual(basic_stats['country'],'United States')

    def test_yahoo_history(self):
        ticker='AAPL'

        ## --- Download time history
        history = download_history_yahoo(ticker, period="1y", interval="1d")
        print(len(history))
        self.assertTrue(len(history)>220)
        #print(df)
        #print('----------- Historical data stats')
        #print('Relative difference in price, current day, 3last days, week, month, year')
        #hstats = history_stats(history, basic_stats['currentPrice'])
        #print(hstats)
        #print('----------- Performances wrt S&P500')
        #print('Relative difference in price, current day, 3last days, week, month, year')
        #sp_stats = sp500_comp_stats(history)
        #print(sp_stats)

        #print('----------- Performances wrt S&P500 during 2008 and 2020 crises')
        #cr_stats = crisis_stats(ticker)
        #print(cr_stats)


if __name__=='__main__':
    unittest.main()
