from mlstocks.symbol import Symbol

ticker='AMZN'

# --- Download statistics from multiple sources
symb = Symbol(ticker)
symb.download_stats(sources=['yahoo','tipranks'])

print('----------- Basic stats')
print('Failed stats:', symb.failedStats)
print(symb.stats)
# print(basic_stats)

print('----------- Advanced stats')
print('NOTE: printing would take too much space') 
print('Access the variable `all_stats` as a dictionary.') 
print('The variable has an extra `find` method to look for keys')
print('The example below shows how to use find to look for `daylow`')
res = symb.all_stats.find('daylow')
print('Day Low: ', symb.all_stats['info']['dayLow'])

#print(symb.all_stats)
