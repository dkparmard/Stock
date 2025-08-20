### NSE 50/100 Crossover + Trend Filter

Filters Indian stocks where:
1. 50-SMA crosses above 100-SMA **on the signal bar**
2. 20-SMA > 50-SMA
3. 8-EMA > 20-SMA

```bash
pip install pandas yfinance
python screen_india_ma.py --symbols RELIANCE.NS TCS.NS INFY.NS
# or
python screen_india_ma.py --file tickers.txt
# include signals in the last 3 bars
python screen_india_ma.py --recent 3 --file tickers.txt
