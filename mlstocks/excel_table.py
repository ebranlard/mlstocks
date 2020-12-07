import xlsxwriter
import numpy as np
import pandas as pd
import os



class ExcelTable(object):
    """
    Class to ease the writing of pandas DataFrames to and Excel file.
        Assumes one dataframe per sheet
        DataFrames are converted to Excel tables
        Different formatting options are provided:
          - borders
          - column width
          - conditional formatting

    Author: E. Branlard

    # For more styling options see
    https://xlsxwriter.readthedocs.io/format.html

    """

    def __init__(self, outFile, sheetname='Sheet1', df=None):
        
        # Creting writer
        self.filename  = outFile
        self.writer    = pd.ExcelWriter(outFile, engine='xlsxwriter')
        self.workbook  = self.writer.book

        # --- Creating some reusable Styles
        # Alignement
        self._centerfmt = self.workbook.add_format({'align':'center'})   # {'border': 5})
        # Borders
        self._borderfmt_last = self.workbook.add_format()   # {'border': 5})
        self._borderfmt_last.set_right(1)
        self._borderfmt_first = self.workbook.add_format()   # {'border': 5})
        self._borderfmt_first.set_left(1)
        # Number format
        self._percent_fmt = self.workbook.add_format({'num_format': '0.0%'})
        #self._total_fmt = workbook.add_format({'align': 'right', 'num_format': '$#,##0', 'bold': True, 'bottom':6})
        # For conditional formatting
        self._format_bad  = self.workbook.add_format({'bg_color':   '#FFC7CE', 'font_color': '#9C0006'}) # Light red fill with dark red text.
        self._format_mid  = self.workbook.add_format({'bg_color':   '#FFEB9C', 'font_color': '#9C6500'}) # Light yellow fill with dark yellow text.
        self._format_good = self.workbook.add_format({'bg_color':   '#C6EFCE', 'font_color': '#006100'}) # Green fill with dark green text.

        if df is not None:
            self.addDataFrame(df, sheetname)

    def write(self):
#         try:
        self.writer.save()
#         except:
#             print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
#             print('!!! Excel file {} is likely locked'.format(self.filename))
#             print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
#             print('Close the file and then type `continue`')
#             import pdb; pdb.set_trace()
#             self.writer.save()

    def launch(self):
        """ Open Excel file (after it has been written) """
        print('Opening Excel file: {}'.format(self.filename))
        cmdLaunch='start "" "{:s}"'.format(self.filename)
        os.system(cmdLaunch)

    def addDataFrame(self, df, sheetname):
        """ """
        # Store info about dataframe
        self.ColNames=list(df.columns.values)
        self.nCols= len(df.columns)
        self.nRows= len(df)

        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(self.writer, sheet_name=sheetname, index=False)
        self.worksheet = self.writer.sheets[sheetname]

        # --- Creating a "table"
        ColLetter=  xlsxwriter.utility.xl_col_to_name(self.nCols-1)
        xlsRange = 'A1:'+'{:s}{:d}'.format(ColLetter,self.nRows+1)
        self.worksheet.add_table(xlsRange, {'header_row': True, 'columns':[{'header':v} for v in df.columns.values]})

        # Styling Header 
        header_format = self.workbook.add_format({'text_wrap': True, 'bold': True, 'align':'left'})
        self.worksheet.set_row(0, 80, header_format)

        # Default column width
        self.defaultColumnWidth()


    # --------------------------------------------------------------------------------}
    # --- Styling options 
    # --------------------------------------------------------------------------------{
    def verticalBorders(self, leftBorderCols=[], rightBorderCols=[]):
        """ add vertical borders on the right or left of some columns"""
        def colRange(iCol):
            ColLetter = xlsxwriter.utility.xl_col_to_name(iCol)
            xlsRange =  '{:s}1:{:s}{:d}'.format(ColLetter,ColLetter,self.nRows+1)
            return xlsRange

        for c in leftBorderCols:
            self.worksheet.set_column(colRange(self.ColNames.index(c)),None,self._borderfmt_first)
        for c in rightBorderCols:
            self.worksheet.set_column(colRange(self.ColNames.index(c)),None,self._borderfmt_last)

    def defaultColumnWidth(self, colWidth=20):
        """ set column width for the entire table"""
        ColLetterStart=xlsxwriter.utility.xl_col_to_name(0) 
        ColLetterEnd  =xlsxwriter.utility.xl_col_to_name(self.nCols)
        self.worksheet.set_column(ColLetterStart+':'+ColLetterEnd, colWidth)

    def columnWidth(self, cols=[], colWidth=20, center=False):
        """ set column width for a list of column names """
        # --- Column width
        IValid=[self.ColNames.index(c) for c in cols if c in self.ColNames]
        for ColLetter in [xlsxwriter.utility.xl_col_to_name(i) for i in IValid]:
            if center:
                self.worksheet.set_column(ColLetter+':'+ColLetter, colWidth, self._centerfmt)
            else:
                self.worksheet.set_column(ColLetter+':'+ColLetter, colWidth)

    def formatPercentage(self, cols=[]):
        """ set the numerical format of some columns to % """
        IValid=[self.ColNames.index(c) for c in cols if c in self.ColNames]
        for ColLetter in [xlsxwriter.utility.xl_col_to_name(i) for i in IValid]:
            self.worksheet.set_column(ColLetter+':'+ColLetter, None, self._percent_fmt)


    def conditionalFormat(self, colName,formatDict):
        """ 
        Set conditinoal formatting on a given column

        Examples of formatDict:
        {'type': 'cell', 'criteria':'>=', 'value':value, 'format':self._format_good}
        {'type': '3_color_scale','min_value':-50, 'mid_value':0, 'max_value':50,'min_type':'num','mid_type':'num','max_type':'num'}
         
        """
        iCol = self.ColNames.index(colName)
        if iCol>=0:
            ColLetter = xlsxwriter.utility.xl_col_to_name(iCol)
            xlsRange =  '{:s}2:{:s}{:d}'.format(ColLetter,ColLetter,self.nRows+1)
            self.worksheet.conditional_format(xlsRange, formatDict)
        else:
            print('[WARN] Column not found:',colName)

    def conditionalFormatGoodBelow(self, colName, value, strict=True):
        eq='' if strict else '='
        self.conditionalFormat(colName, {'type': 'cell', 'criteria':'<'+eq, 'value':value, 'format':self._format_good})

    def conditionalFormatBadBelow(self, colName, value, strict=True):
        eq='' if strict else '='
        self.conditionalFormat(colName, {'type': 'cell', 'criteria':'<'+eq, 'value':value, 'format':self._format_bad})

    def conditionalFormatGoodAbove(self, colName, value, strict=True):
        eq='' if strict else '='
        self.conditionalFormat(colName, {'type': 'cell', 'criteria':'>'+eq, 'value':value, 'format':self._format_good})

    def conditionalFormatBadAbove(self, colName, value, strict=True):
        eq='' if strict else '='
        self.conditionalFormat(colName, {'type': 'cell', 'criteria':'>'+eq, 'value':value, 'format':self._format_bad})

    def conditionalFormatGoodIfEqual(self, colName, value, strict=True):
        self.conditionalFormat(colName, {'type': 'cell', 'criteria':'==', 'value':value, 'format':self._format_good})

    def conditionalFormatBadIfEqual(self, colName, value, strict=True):
        self.conditionalFormat(colName, {'type': 'cell', 'criteria':'==', 'value':value, 'format':self._format_bad})



    def conditionalFormat3NumValues(self, colName, min_value, mid_value, max_value):
        self.conditionalFormat(colName, { 'type': '3_color_scale','min_value':min_value, 'mid_value':mid_value, 'max_value':max_value, 'min_type':'num', 'mid_type':'num', 'max_type':'num'})
 

    def urlValues(self, colName, values, links) :
        """ Insert URL instead of values for a given column """
        iCol = self.ColNames.index(colName)
        colLetter = xlsxwriter.utility.xl_col_to_name(iCol)
        for i, link in enumerate(links):
            self.worksheet.write_url('{:s}{:d}'.format(colLetter, i+2), link, string=values[i])

if __name__ == '__main__':
    outFile = 'Test.xlsx'

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

    xls.launch()





