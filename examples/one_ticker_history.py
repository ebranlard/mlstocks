""" 
plot the price history of a given ticker

"""
from mlstocks.symbol import Symbol

ticker='AMZN'

# --- Download different periods
symb = Symbol(ticker)

# Download one year
df  = symb.download_history(period  = '1y', interval = '1d')

# Download a given period
df2 = symb.download_history(ts_start = '2020-03-01', ts_end = '2020-05-01', interval = '1d')


# --- Plot
import matplotlib.pyplot as plt
fig,ax = plt.subplots(1, 1, sharey=False, figsize=(6.4,4.8)) # (6.4,4.8)
fig.subplots_adjust(left=0.12, right=0.95, top=0.95, bottom=0.11, hspace=0.20, wspace=0.20)
ax.plot(df.index,  df['Close'].values,  '--', label='one year')
ax.plot(df2.index, df2['Close'].values, '-',  label='given period')
ax.set_xlabel('Time')
ax.set_ylabel('Closing price [$]')
ax.legend()
ax.tick_params(direction='in')
plt.show()





