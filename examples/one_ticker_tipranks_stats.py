from mlstocks.tipranks import download_stats_tipranks
from mlstocks.yahoo_finance import download_stats_yahoo, download_history_yahoo

ticker='AAPL'

# --- Download statistics
basic_stats, all_stats = download_stats_tipranks(ticker)

print('----------- Basic stats')
print(basic_stats)


print('----------- Advanced stats')
print('NOTE: printing would take too much space') 
print('Access the variable `all_stats` as a dictionary.') 
print('The variable has an extra `find` method to look for keys')
print('The example below shows how to use find to look for `momentum`')
res = all_stats.find('momentum')
print('12 month momentum: ', all_stats['tipranksStockScore']['twelveMonthsMomentum'])


