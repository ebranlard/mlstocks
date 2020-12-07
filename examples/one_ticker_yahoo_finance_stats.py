from mlstocks.yahoo_finance import download_stats_yahoo, download_history_yahoo
from mlstocks.stats import history_stats, sp500_comp_stats, crisis_stats

ticker='AAPL'


# --- Download statistics
basic_stats, all_stats = download_stats_yahoo(ticker, True)

# Print basic stats
print('----------- Basic stats')
print(basic_stats)

# Look for some keys in the more advanced "all_stats"
print('----------- Example looking for more info in all_stats')
print('NOTE: printing would take too much space') 
print('Access the variable `all_stats` as a dictionary.') 
print('The variable has an extra `find` method to look for keys')
print('The example below shows how to use find to look for `beta`')
all_stats.find('beta')
print('beta:', all_stats['info']['beta'])


# --- Download time history
history = download_history_yahoo(ticker, period="5y", interval="1d")
# print(df)


print('----------- Historical data stats')
print('Relative difference in price, current day, 3last days, week, month, year')
hstats = history_stats(history, basic_stats['currentPrice'])
print(hstats)


print('----------- Performances wrt S&P500')
print('Relative difference in price, current day, 3last days, week, month, year')
sp_stats = sp500_comp_stats(history)
print(sp_stats)

print('----------- Performances wrt S&P500 during 2008 and 2020 crises')
cr_stats = crisis_stats(ticker)
print(cr_stats)






