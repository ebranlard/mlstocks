from mlstocks.tipranks import download_stats_tipranks
from mlstocks.yahoo_finance import download_stats_yahoo, download_history_yahoo

import unittest

class Test(unittest.TestCase):
    def test_yahoo_stats(self):
        ticker='AAPL'
        # --- Download statistics
        basic_stats, all_stats = download_stats_tipranks(ticker)
        #print(basic_stats)

        self.assertEqual(basic_stats['TR_quoteType'],'stock')
        self.assertEqual(basic_stats['TR_longName'], 'Apple')

if __name__=='__main__':
    unittest.main()
