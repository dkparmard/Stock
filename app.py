import requests
import pandas as pd
import yfinance as yf
import ta
from bs4 import BeautifulSoup

def fetch_nifty50_tickers():
    """
    Scrape Wikipedia for current NIFTY 50 tickers, return a list
    of tickers with '.NS' appended for Yahoo Finance.
    """
    url = "https://en.wikipedia.org/wiki/NIFTY_50"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.find("table", {"class": "wikitable sortable"})
    tickers = []
    if not table:
        raise ValueError("Could not find constituents table on Wikipedia page")

    # The “Symbol” column has tickers without suffix
    for row in table.find_all("tr")[1:]:  # skip header row
        cols = row.find_all("td")
        if len(cols) < 2:  # skip malformed rows
            continue
        symbol = cols[1].text.strip()  # The symbol is in the 2nd column (0-based index 1)
        if symbol:
            # Append .NS for Yahoo Finance NSE data
            yf_symbol = f"{symbol}.NS"
            tickers.append(yf_symbol)
    return tickers

def check_condition(latest):
    """
    Given latest row of data with the computed indicators,
    check if:
      - EMA8 and SMA5 are between EMA44 and SMA50
      - Close > EMA8 (bullish)
    Return strength % or None
    """
    lower = min(latest["EMA44"], latest["SMA50"])
    upper = max(latest["EMA44"], latest["SMA50"])
    cond_between = (lower < latest["EMA8"] < upper) and (lower < latest["SMA5"] < upper)
    cond_bull = latest["Close"] > latest["EMA8"]
    if cond_between and cond_bull:
        strength_pct = ((latest["Close"] - latest["EMA8"]) / latest["EMA8"]) * 100
        return round(strength_pct, 4)
    return None

def scan_nifty50():
    # Step 1: get current constituents
    tickers = fetch_nifty50_tickers()
    print(f"Fetched {len(tickers)} tickers from Wikipedia: {tickers[:5]} ...")

    results = []
    for tk in tickers:
        try:
            df = yf.download(tk, period="6mo", interval="1d", progress=False)
            if df.shape[0] < 50:
                continue  # not enough data yet

            # compute indicators
            df["EMA8"] = ta.trend.ema_indicator(df["Close"], window=8)
            df["EMA44"] = ta.trend.ema_indicator(df["Close"], window=44)
            df["SMA5"] = df["Close"].rolling(window=5).mean()
            df["SMA50"] = df["Close"].rolling(window=50).mean()

            latest = df.iloc[-1]
            # Check for NaNs
            needed = ["EMA8","EMA44","SMA5","SMA50","Close"]
            if any(pd.isna(latest[col]) for col in needed):
                continue

            strength = check_condition(latest)
            if strength is not None:
                results.append({
                    "Ticker": tk,
                    "Close": round(latest["Close"], 2),
                    "EMA8": round(latest["EMA8"], 2),
                    "SMA5": round(latest["SMA5"], 2),
                    "EMA44": round(latest["EMA44"], 2),
                    "SMA50": round(latest["SMA50"], 2),
                    "Strength_%": round(strength, 2),
                })
        except Exception as e:
            print(f"Error with {tk}: {e}")

    results_df = pd.DataFrame(results)
    if results_df.empty:
        print("No NIFTY50 stocks meet the condition today.")
    else:
        results_df = results_df.sort_values(by="Strength_%", ascending=False).reset_index(drop=True)
        print("Stocks meeting your criteria (sorted by strength):")
        print(results_df)

    return results_df

if __name__ == "__main__":
    scan_nifty50()
