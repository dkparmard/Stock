import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(page_title="Indian Stock Screener", layout="wide")

st.title("📈 Indian Stock Screener (50/100 SMA + Trend Filter)")

# ---- User Inputs ----
symbols_input = st.text_input(
    "Enter NSE stock symbols (comma separated, e.g. RELIANCE.NS, TCS.NS, INFY.NS)",
    "RELIANCE.NS"
)

lookback = st.number_input("Lookback bars (0 = only today)", min_value=0, value=0, step=1)

# ---- Function to fetch and screen ----
def fetch_and_screen(symbol, recent=0):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)

        if df.empty:
            return None

        # Moving Averages
        df["SMA50"] = df["Close"].rolling(window=50).mean()
        df["SMA100"] = df["Close"].rolling(window=100).mean()
        df["SMA20"] = df["Close"].rolling(window=20).mean()
        df["EMA8"] = df["Close"].ewm(span=8, adjust=False).mean()

        # Conditions
        df["golden_cross"] = (df["SMA50"] > df["SMA100"])
        df["cond_trend"] = (df["SMA20"] > df["SMA50"]) & (df["EMA8"] > df["SMA20"])

        if recent == 0:  # Only check last day
            gc = bool(df["golden_cross"].iloc[-1])
            trend = bool(df["cond_trend"].iloc[-1])

            if gc and trend:
                return {
                    "Symbol": symbol,
                    "Date": df.index[-1].date(),
                    "Close": float(df["Close"].iloc[-1])
                }
        else:  # Check last N bars
            recent_df = df.tail(recent)
            cond = (recent_df["golden_cross"] & recent_df["cond_trend"])
            cond = cond[cond]  # keep only True rows

            if not cond.empty:
                last_valid = cond.index[-1]
                return {
                    "Symbol": symbol,
                    "Date": last_valid.date(),
                    "Close": float(df.loc[last_valid, "Close"])
                }

    except Exception as e:
        st.error(f"Error for {symbol}: {e}")
    return None

# ---- Run Screener ----
if st.button("🔍 Run Screener"):
    symbols = [s.strip().upper() for s in symbols_input.split(",")]
    results = []

    for sym in symbols:
        row = fetch_and_screen(sym, lookback)
        if row:
            results.append(row)

    if results:
        st.success(f"✅ Found {len(results)} stocks matching conditions")
        df_results = pd.DataFrame(results)
        st.dataframe(df_results)
    else:
        st.warning("⚠️ No stocks matched the conditions.")
