import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="📊 NIFTY50 Screener", layout="wide")
st.title("📊 NIFTY50 Screener (No External TA Library)")
st.caption("Condition: EMA8 & SMA5 between EMA44 & SMA50 and Close > EMA8")

def fetch_nifty50_tickers():
    return [
        "ADANIENT.NS","ADANIPORTS.NS","APOLLOHOSP.NS","ASIANPAINT.NS","AXISBANK.NS",
        "BAJAJ-AUTO.NS","BAJFINANCE.NS","BAJAJFINSV.NS","BPCL.NS","BHARTIARTL.NS",
        "BRITANNIA.NS","CIPLA.NS","COALINDIA.NS","DIVISLAB.NS","DRREDDY.NS",
        "EICHERMOT.NS","GRASIM.NS","HCLTECH.NS","HDFCBANK.NS","HDFCLIFE.NS",
        "HEROMOTOCO.NS","HINDALCO.NS","HINDUNILVR.NS","ICICIBANK.NS","ITC.NS",
        "INFY.NS","JSWSTEEL.NS","KOTAKBANK.NS","LT.NS","M&M.NS","MARUTI.NS",
        "NTPC.NS","ONGC.NS","POWERGRID.NS","RELIANCE.NS","SBILIFE.NS","SBIN.NS",
        "SUNPHARMA.NS","TCS.NS","TATACONSUM.NS","TATAMOTORS.NS","TATASTEEL.NS",
        "TECHM.NS","TITAN.NS","ULTRACEMCO.NS","UPL.NS","WIPRO.NS"
    ]

def scan_nifty50():
    tickers = fetch_nifty50_tickers()
    results = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty:
                continue

            df["EMA8"] = df["Close"].ewm(span=8, adjust=False).mean()
            df["EMA44"] = df["Close"].ewm(span=44, adjust=False).mean()
            df["SMA5"] = df["Close"].rolling(window=5).mean()
            df["SMA50"] = df["Close"].rolling(window=50).mean()

            # Drop NaN rows so last row has all indicators
            df = df.dropna()
            if df.empty:
                continue

            last = df.iloc[-1]  # ✅ Guaranteed to be a single row
            ema8, ema44, sma5, sma50, close = (
                float(last["EMA8"]),
                float(last["EMA44"]),
                float(last["SMA5"]),
                float(last["SMA50"]),
                float(last["Close"]),
            )

            # ✅ Safe scalar comparisons
            if (
                min(ema44, sma50) < ema8 < max(ema44, sma50)
                and min(ema44, sma50) < sma5 < max(ema44, sma50)
                and close > ema8
            ):
                results.append({
                    "Ticker": ticker,
                    "Close": round(close, 2),
                    "EMA8": round(ema8, 2),
                    "EMA44": round(ema44, 2),
                    "SMA5": round(sma5, 2),
                    "SMA50": round(sma50, 2)
                })
        except Exception as e:
            st.warning(f"⚠️ Error fetching {ticker}: {e}")

    return pd.DataFrame(results)

if st.button("🔎 Scan Now"):
    st.write("⏳ Scanning NIFTY50 stocks...")
    df = scan_nifty50()
    if df.empty:
        st.error("No stocks matched the condition today.")
    else:
        st.success(f"{len(df)} stocks found matching your condition ✅")
        st.dataframe(df, use_container_width=True)
