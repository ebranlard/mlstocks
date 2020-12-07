from mlstocks.symbol import Symbol
import unittest

class Test(unittest.TestCase):
    def test_symbol(self):
        ticker='AMZN'
        # --- Download statistics from multiple sources
        symb = Symbol(ticker)
        symb.download_stats(sources=['yahoo','tipranks'])

        self.assertEqual(symb.stats['country'],'United States')

if __name__=='__main__':
    unittest.main()
