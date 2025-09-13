import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="NIFTY50 Screener", page_icon="📊", layout="centered")
st.title("📊 NIFTY50 Screener (No External TA Library)")
st.markdown("**Condition:** EMA8 & SMA5 between EMA44 & SMA50 + Close > EMA8")

# ------------------------------------------
# 1️⃣ Function to fetch Nifty 50 tickers
# ------------------------------------------
@st.cache_data
def fetch_nifty50_tickers():
    url = "https://www1.nseindia.com/content/indices/ind_nifty50list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()  # raise error if request fails
    df = pd.read_csv(pd.compat.StringIO(r.text))
    return [symbol + ".NS" for symbol in df["Symbol"].tolist()]

# ------------------------------------------
# 2️⃣ Function to scan stocks
# ------------------------------------------
def scan_nifty50():
    tickers = fetch_nifty50_tickers()
    results = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="6mo", interval="1d")
            if df.empty:
                continue

            # Calculate indicators
            df["EMA8"] = df["Close"].ewm(span=8, adjust=False).mean()
            df["EMA44"] = df["Close"].ewm(span=44, adjust=False).mean()
            df["SMA5"] = df["Close"].rolling(window=5).mean()
            df["SMA50"] = df["Close"].rolling(window=50).mean()

            if len(df) < 50:
                continue  # not enough data

            # ✅ Take latest values only
            ema8 = df["EMA8"].iloc[-1]
            ema44 = df["EMA44"].iloc[-1]
            sma5 = df["SMA5"].iloc[-1]
            sma50 = df["SMA50"].iloc[-1]
            close = df["Close"].iloc[-1]

            # ✅ Safe condition check
            if (ema8 > ema44) and (ema8 < sma50) and (sma5 > ema44) and (sma5 < sma50) and (close > ema8):
                results.append(ticker)

        except Exception as e:
            st.write(f"⚠️ Error with {ticker}: {e}")

    return results

# ------------------------------------------
# 3️⃣ Streamlit UI
# ------------------------------------------
if st.button("🔍 Scan Now"):
    with st.spinner("Scanning NIFTY50 stocks..."):
        stocks = scan_nifty50()
    if stocks:
        st.success(f"✅ {len(stocks)} stocks matched the condition")
        st.write(stocks)
    else:
        st.warning("No stocks matched the condition.")
