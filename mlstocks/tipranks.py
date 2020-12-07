""" 
Simple python API to download tipranks stock info

"""
import requests 
import pandas as pd
import numpy as np
import re
try:
    import ujson as json
except ImportError:
    import json as json
try:
    from .utils   import SearchableDict
except:
    SearchableDict=dict()
from . exceptions import EmptyDataException


_base_url='https://www.tipranks.com/api/stocks/'
#_base_url='https://www.tipranks.com/stocks/'


def download_stats_tipranks(ticker, extra=False, proxy=None):
    """ 
    Download statistics from a given symbol

    returns
       stats: dictionary with simple stats data

       all_stats: a dictionary of dictionaries with keys:
       - TODO
    """
    basic_stats=SearchableDict()

    # News-sentiment
    #_base_url + `getNewsSentiments/?ticker=${symbol.toLowerCase()}&break=${timestamp}`;

    # Price target
    url=_base_url + 'getData/?name={:s}&benchmark=1&period=3'.format(ticker.lower())
    #url=_base_url + '{}/forecast'.format(ticker.lower())

    # Trending stocks
    #config.tipranks.baseUrl + `gettrendingstocks/?daysago=30&which=most&break=${timestamp}`;


    data = get_json(url)
    ptCon = data['ptConsensus']
    hold  = data['portfolioHoldingData']
    cons  = hold['analystConsensus']

    # Industry
    basic_stats['TR_longName']      = data['companyFullName']
    basic_stats['TR_quoteType']     = hold['stockType']
    basic_stats['TR_sector']        = hold['sectorId']
    # --- Current price
    #{'latestDate': '2020-12-04T00:00:00' , 'momentum': 0.8570560534710618}
    # --- Consensus
    # {'period': 3, 'bench': 1, 'priceTarget': 133.67, 'priceTargetCurrency': 1, 'priceTargetCurrencyCode': 'USD', 'high': 150.0, 'low': 100.0},
    # {'period': 0, 'bench': 0, 'priceTarget': 129.22, 'priceTargetCurrency': 1, 'priceTargetCurrencyCode': 'USD', 'high': 150.0, 'low': 75.0}
    if len(ptCon)==2:
        pt=ptCon[1]
        basic_stats['TR_targetLowPrice']  = pt['low']
        basic_stats['TR_currentPrice']    = data['momentum']['latestPrice']
        basic_stats['TR_targetHighPrice'] = pt['high']
        basic_stats['TR_targetMeanPrice'] = pt['priceTarget']
        if pt['period']!=0:
            print(data['ptConsensus'])
            print('>>>> TODO ptCon period not 0')
            import pdb; pdb.set_trace()

    else:
        print(data['ptConsensus'])
        print('>>>> TODO ptCon has not len 2')
        import pdb; pdb.set_trace()
    try:
        basic_stats['TR_targetMeanGainFromCurrent'] = np.around((min(basic_stats['TR_targetMeanPrice']/basic_stats['TR_currentPrice'], 2)-1)*100.0, 1)
        basic_stats['TR_targetMeanGainFromCurrent_Best'] = np.around((min(hold['bestPriceTarget']/basic_stats['TR_currentPrice'], 2)-1)*100.0, 1)
    except:
        basic_stats['TR_targetMeanGainFromCurrent'] = np.nan
        basic_stats['TR_targetMeanGainFromCurrent_Best'] = np.nan
        

    # --- 
    #cons=data['portfolioHoldingData']['bestAnalystConsensus'] # Best performing 
    basic_stats['TR_numberOfAnalystOpinions'] = int(cons['distribution']['buy']+cons['distribution']['hold']+cons['distribution']['sell'])
    if basic_stats['TR_numberOfAnalystOpinions']>0:
        basic_stats['TR_percentOfBuy']            = np.around(cons['distribution']['buy']  / basic_stats['TR_numberOfAnalystOpinions']*100  ,1)
        basic_stats['TR_percentOfHold']           = np.around(cons['distribution']['hold'] / basic_stats['TR_numberOfAnalystOpinions']*100  ,1)
        basic_stats['TR_percentOfSell']           = np.around(cons['distribution']['sell'] / basic_stats['TR_numberOfAnalystOpinions']*100  ,1)
    else:
        basic_stats['TR_percentOfBuy']            = np.nan
        basic_stats['TR_percentOfHold']           = np.nan
        basic_stats['TR_percentOfSell']           = np.nan
    if cons['consensus'] is None:
        cons['consensus']=''
    basic_stats['TR_consensus']     = cons['consensus'].replace('strongbuy','Strong Buy').replace('buy','Moderate Buy').replace('neutral','Hold')
    basic_stats['TR_consensus_raw'] = cons['rawConsensus'] # 1-5   5=strong_buy

    basic_stats['TR_expenseRatio']  = hold['expenseRatio']
    basic_stats['TR_dividendYield'] = hold['dividendYield']

    #  TipRank Score 
    score=data['tipranksStockScore']['score']
    if score is not None:
        if score<4:
            basic_stats['TR_score'] = 'Underperform'
        elif score<=7:
            basic_stats['TR_score'] = 'Neutral'
        elif score<=10:
            basic_stats['TR_score'] = 'Outperform'
    basic_stats['TR_score_raw'] =  score # 1-3=Underperform

    # --- Blogger Sentiment
    blog=data['bloggerSentiment']
    if blog is None:
        blogper=np.nan
        basic_stats['TR_bloggerSentiment'] = ''
    else:
        blogper=float(blog['bullish'])
        if blogper>95: # TODO
            basic_stats['TR_bloggerSentiment'] = 'Very Bullish'
        elif blogper>60:
            basic_stats['TR_bloggerSentiment'] = 'Bullish'
        elif blogper>40:
            basic_stats['TR_bloggerSentiment'] = 'Neutral'
        else:
            basic_stats['TR_bloggerSentiment'] = 'Bearish'
    basic_stats['TR_bloggerSentiment_bullish']=blogper # [%] ~50%"Neutral"  >75% "Bullish"

    # --- Hedge fund activity
    hedge=data['hedgeFundData']
    if hedge is None:
        basic_stats['TR_hedgeFundActivity_sentiment']  = np.nan
        basic_stats['TR_hedgeFundActivity_trendAction']= np.nan
        basic_stats['TR_hedgeFundActivity_trendValue'] = np.nan
        basic_stats['TR_hedgeFundActivity_trend']      = ''
    else:
        basic_stats['TR_hedgeFundActivity_sentiment']  = hedge['sentiment'] #???
        basic_stats['TR_hedgeFundActivity_trendAction']= hedge['trendAction'] #??? 3=Decreased? NO
        basic_stats['TR_hedgeFundActivity_trendValue'] = hedge['trendValue'] #<0 = Decreased?
        basic_stats['TR_hedgeFundActivity_trend']      = 'Decreased' if basic_stats['TR_hedgeFundActivity_trendValue']<0 else 'Increased'
    # {'stockID': 7624, 
    #     'sentiment': 0.188, 
    #     'trendAction': 3,
    #     'trendValue': -37963991.0, # Number of shared decrease last quarter
    # }

    # --- Insider activity, bad if negative
    # TODO divide by total number of shares
    shares = data['insiderslast3MonthsSum']
    if shares <0:
        basic_stats['TR_insidersActivity']='Sold Shares'
    else:
        basic_stats['TR_insidersActivity']='' # <TODO
    #    basic_stats['insidersActivity']='sold shares'
    basic_stats['TR_insidersActivity_last3MonthsSum']=shares     # number of shares sold in the lat 3 month

    # --- News sentiment
    #basic_stats['newsSentiment'] =hold['newsSentiment'] #  seem to be always 0


    # --- Fundamentals
    basic_stats['TR_fundamentals_returnOnEquity']       = data['tipranksStockScore']['returnOnEquity']       # [%]
    basic_stats['TR_fundamentals_assetGrowth']          = data['tipranksStockScore']['assetGrowth']          # [%]
    basic_stats['TR_fundamentals_volatilityLevel']      = data['tipranksStockScore']['volatilityLevelRating']# ???
    # --- Technicals
    try:
        basic_stats['TR_technicals_twelveMonthsMomentum'] = data['tipranksStockScore']['twelveMonthsMomentum']*100 # [%]
    except:
        basic_stats['TR_technicals_twelveMonthsMomentum'] = np.nan
    sma = data['tipranksStockScore']['simpleMovingAverage']
    if sma is None:
        basic_stats['TR_technicals_SMA_20_200'] =  ''
    else:
        if sma>0.5:
            basic_stats['TR_technicals_SMA_20_200'] =  'Positive'# ??? 1.0="Positive" 
        else:
            basic_stats['TR_technicals_SMA_20_200'] =  'Negative' # ??? "Positive" is >0? # TODO
    #'sixMonthsMomentum': 0.0, 'volatilityLevel': 0.0, 
    #'volatilityLevelRating': 2, 
    #'twelveMonthsMomentum': 0.9117, 'simpleMovingAverage': 1.0,

#  - portfolioHoldingData          : {
#          'bestAnalystConsensus': {'consensus': 'strongbuy', 'rawConsensus': 5, 'distribution': {'buy': 22.0, 'hold': 3.0, 'sell': 0.0}},
#          'nextDividendDate': None, 'lastReportedEps': {'date': '2020-10-29T00:00:00', 'company': 'Apple', 'ticker': 'AAPL', 'periodEnding': 'Sep 2020', 'eps': '0.69', 'reportedEPS': '0.73', 'lastEps': '0.76', 'consensus': None, 'bpConsensus': None, 'ratingsAndPT': {'priceTarget': None, 'numBuys': None, 'numHolds': None, 'numSells': None}, 'bpRatingsAndPT': {'priceTarget': None, 'numBuys': None, 'numHolds': None, 'numSells': None}, 'marketCap': 2011651560200, 'sector': 17349, 'stockId': 7624, 'stockTypeId': 1, 'surprise': -0.0547945205479452, 'timeOfDay': 1, 'isConfirmed': True},
#          'nextEarningsReport': {'date': '2021-01-26T00:00:00', 'company': 'Apple', 'ticker': 'AAPL', 'periodEnding': 'Dec 2020', 'eps': '1.39', 'reportedEPS': None, 'lastEps': '1.25', 'consensus': None, 'bpConsensus': None, 'ratingsAndPT': {'priceTarget': None, 'numBuys': None, 'numHolds': None, 'numSells': None}, 'bpRatingsAndPT': {'priceTarget': None, 'numBuys': None, 'numHolds': None, 'numSells': None}, 'marketCap': 2011651560200, 'sector': 17349, 'stockId': 7624, 'stockTypeId': 1, 'surprise': None, 'timeOfDay': 4, 'isConfirmed': False},
#          'priceTarget': 129.22, 
#          'peRatio': 35.1,
#          'hedgeFundSentimentData': {'rating': 3, 'score': 0.188}, 
#          'insiderSentimentData': None, 'bloggerSentimentData': {'ratingIfExists': 1, 'rating': 1, 'bearishCount': 20, 'bullishCount': 98}, 
#          'shouldAddLinkToStockPage': True,
#          'landmarkPrices': 
#              {'yearToDate': {'date': '2020-01-01T00:00:00', 'd': '1/1/20', 'p': 72.78},
#              'threeMonthsAgo': {'date': '2020-09-07T00:00:00', 'd': '7/9/20', 'p': 120.75}, 
#              'yearAgo': {'date': '2019-12-05T00:00:00', 'd': '5/12/19', 'p': 65.83}},

#     # portfolioHoldingData:priceTarget: 129.22 < Average
# 
#     data.find('average')
    #print('prices', len(data['prices']))
    #print('concensus', len(data['consensuses']))
    #print('experts', len(data['experts']))

    return basic_stats, data


def get_json(url, proxy=None):
    html = requests.get(url=url, proxies=proxy).text
    if len(html)==0:
        raise EmptyDataException('Empty data')
    json_dict=json.loads(html)
    return_dict = SearchableDict(json_dict)
    return return_dict

# def get_json(url, proxy=None):
#     html = requests.get(url=url, proxies=proxy).text
#     if "QuoteSummaryStore" not in html:
#         html = requests.get(url=url, proxies=proxy).text
#         if "QuoteSummaryStore" not in html:
#             return {}
# 
#     json_str = html.split('root.App.main =')[1].split('(this)')[0].split(';\n}')[0].strip()
#     data_all = json.loads(json_str)
#     data=data_all['context']['dispatcher']['stores']['QuoteSummaryStore']

#     # return data
#     new_data = json.dumps(data).replace('{}', 'null')
#     new_data = re.sub(r'\{[\'|\"]raw[\'|\"]:(.*?),(.*?)\}', r'\1', new_data)
#     return_dict = json.loads(new_data)
# #     print(return_dict)
#     return return_dict
