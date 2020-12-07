import pandas as pd
import numpy as np
from mlstocks.excel_table import ExcelTable

import unittest

class Test(unittest.TestCase):
    def test_excel_table(self):

        outFile = '_Test.xlsx'
        df = pd.DataFrame(columns=['A','B','C','D','E'], data=np.eye(5))
        
        xls = ExcelTable(outFile, df=df, sheetname='TestSheet') 

        # --- Styling (NOTE: buggy for now when changing the same column multiple times)
        # Width
        xls.defaultColumnWidth(5)
        xls.columnWidth(['A','D'], colWidth=40, center=True)
        # Borders
        xls.verticalBorders(leftBorderCols=['B'], rightBorderCols=['C','E'])
        # Format
        xls.formatPercentage(['A'])

        # Conditional
        xls.conditionalFormatGoodBelow('A', 1)
        xls.conditionalFormatGoodAbove('B', -1)
        xls.conditionalFormat3NumValues('C', -1, 0, 1)

        xls.urlValues('E',['a','b','c','d','e'], ['a','b','c','d','e'])

        xls.write()

if __name__=='__main__':
    unittest.main()
