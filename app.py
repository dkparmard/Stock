import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Indian Stock Screener", page_icon="📈", layout="wide")

st.title("📈 Indian Stock Screener (50/100 SMA + Trend Filter)")

st.write("Enter NSE stock symbols (comma separated, e.g. RELIANCE.NS, TCS.NS, INFY.NS)")

symbols_input = st.text_input("Stock Symbols", "RELIANCE.NS,TCS.NS,INFY.NS")
lookback = st.number_input("Lookback bars (0 = only today)", min_value=0, value=0, step=1)

def fetch_and_screen(symbol, recent):
    try:
        df = yf.download(symbol, period="6mo", interval="1d")
        if df.empty:
            return None

        # Moving Averages
        df["SMA50"] = df["Close"].rolling(50).mean()
        df["SMA100"] = df["Close"].rolling(100).mean()
        df["SMA20"] = df["Close"].rolling(20).mean()
        df["EMA8"] = df["Close"].ewm(span=8, adjust=False).mean()

        # Conditions
        df["golden_cross"] = df["SMA50"] > df["SMA100"]
        df["cond_trend"] = (df["SMA20"] > df["SMA50"]) & (df["EMA8"] > df["SMA20"])

        if recent == 0:  # Only check last day
            last = df.iloc[-1]

            gc = last["golden_cross"].item() if pd.notna(last["golden_cross"]) else False
            trend = last["cond_trend"].item() if pd.notna(last["cond_trend"]) else False

            if gc and trend:
                return {"Symbol": symbol, "Date": df.index[-1].date(), "Close": float(last["Close"])}
        else:  # Check last N bars
            df_recent = df.tail(recent)
            df_recent = df_recent[df_recent["golden_cross"] & df_recent["cond_trend"]]
            if not df_recent.empty:
                rows = []
                for idx, row in df_recent.iterrows():
                    rows.append({"Symbol": symbol, "Date": idx.date(), "Close": float(row["Close"])})
                return rows

        return None
    except Exception as e:
        st.error(f"Error for {symbol}: {e}")
        return None

if st.button("🔍 Run Screener"):
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    results = []

    for sym in symbols:
        row = fetch_and_screen(sym, lookback)
        if row:
            if isinstance(row, list):
                results.extend(row)
            else:
                results.append(row)

    if results:
        df_results = pd.DataFrame(results)
        st.success("✅ Stocks found!")
        st.dataframe(df_results)
    else:
        st.warning("⚠️ No stocks matched the conditions.")
