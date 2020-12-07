""" 
Plot the price history of two tickers against each other.

"""
from mlstocks.stats import rel_comparison_plot_tick
from mlstocks.crisis import get_crisis_ts
import matplotlib.pyplot as plt


ticker='AMZN'

# Relative difference of prices between S&P 500 and AMZN over the last 6 month
ax = rel_comparison_plot_tick('^GSPC', ticker,  period='1y', interval='1d')
ax.set_title('Last six month')

# Relative difference of prices between S&P 500 and AMZN during 2008 crisis
ts_start, ts_end = get_crisis_ts(year = 2008)
ax = rel_comparison_plot_tick('^GSPC', ticker,  ts_start=ts_start, ts_end=ts_end, interval='1d')
ax.set_title('2008 crisis')

plt.show()

