[![Build Status](https://travis-ci.com/ebranlard/mlstocks.svg?branch=master)](https://travis-ci.com/ebranlard/mlstocks)
<a href="https://www.buymeacoffee.com/hTpOQGl" rel="nofollow"><img alt="Donate just a small amount, buy me a coffee!" src="https://warehouse-camo.cmh1.psfhosted.org/1c939ba1227996b87bb03cf029c14821eab9ad91/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f446f6e6174652d4275792532306d6525323061253230636f666665652d79656c6c6f77677265656e2e737667"></a>


#mlstocks

python library to manipulate stock data.

## Features

For a given ticker/symbol (see the examples starting with "one\_ticker" in the folder `examples`)

- Download statistics from yahoo finance (e.g. beta, EPS, recommended price, rating, etc.)
- Download time history from yahoo finance (e.g. 5d, 1y, 5y)
- Download statistics from tipranks (e.g. scrore, recommended price)


For a list of tickers (see the examples starting with "multiple\_tickers" in the folder `examples`):

- Multi-threaded download of the statistics for each tickers from yahoo finance and/or tipranks
- Compute some simple metrics based on time history (e.g. Day change, week change, or performance compared to S&P 500)
- Store the data into a pandas dataframe, and export it to Excel with someconditional formatting


## Installation

```bash
git clone http://github.com/ebranlard/mlstocks
cd mlstocks
python -m pip install -r requirements.txt
python -m pip install -e .
```

Then you can try running the examples in the folder `examples`.




## Ressources
The yahoo finance download was inspired by the project [yfinance](https://github.com/ranaroussi/yfinance/)

Screen stocks using yahoo finance [here](https://finance.yahoo.com/screener)

Monitor the 10y over 2y bond curve [here](https://ycharts.com/indicators/10_2_year_treasury_yield_spread)

Simple scope [here](https://simplywall.st/discover/)


# Contributing
Any contributions to this project are welcome! If you find this project useful, you can also buy me a coffee (donate a small amount) with the link below:


<a href="https://www.buymeacoffee.com/hTpOQGl" rel="nofollow"><img alt="Donate just a small amount, buy me a coffee!" src="https://warehouse-camo.cmh1.psfhosted.org/1c939ba1227996b87bb03cf029c14821eab9ad91/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f446f6e6174652d4275792532306d6525323061253230636f666665652d79656c6c6f77677265656e2e737667"></a>
