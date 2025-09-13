import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(page_title="📊 NIFTY50 Screener & Backtester", layout="wide")
st.title("📊 NIFTY50 Screener & Backtester")
st.caption("Strategy: EMA8 & SMA5 between EMA44 & SMA50 and Close > EMA8")

# -----------------------
# NIFTY50 Ticker List
# -----------------------
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

# -----------------------
# Backtesting Function
# -----------------------
def backtest_nifty50(period="1y"):
    tickers = fetch_nifty50_tickers()
    data = yf.download(tickers, period=period, interval="1d", group_by="ticker", progress=False)
    results = []

    for ticker in tickers:
        try:
            df = data[ticker]
            if df.empty:
                continue

            # Compute Indicators
            df["EMA8"] = df["Close"].ewm(span=8, adjust=False).mean()
            df["EMA44"] = df["Close"].ewm(span=44, adjust=False).mean()
            df["SMA5"] = df["Close"].rolling(window=5).mean()
            df["SMA50"] = df["Close"].rolling(window=50).mean()
            df = df.dropna()

            for i in range(len(df) - 1):  # avoid last row (no next-day close)
                row = df.iloc[i]
                ema8, ema44, sma5, sma50, close = map(float, [row["EMA8"], row["EMA44"], row["SMA5"], row["SMA50"], row["Close"]])

                # Strategy Condition
                if (
                    min(ema44, sma50) < ema8 < max(ema44, sma50)
                    and min(ema44, sma50) < sma5 < max(ema44, sma50)
                    and close > ema8
                ):
                    next_close = df.iloc[i+1]["Close"]
                    next_return = (next_close - close) / close * 100

                    results.append({
                        "Date": df.index[i].strftime("%Y-%m-%d"),
                        "Ticker": ticker,
                        "Close": round(close, 2),
                        "Next_Day_Close": round(next_close, 2),
                        "Next_Day_Return(%)": round(next_return, 2)
                    })

        except Exception as e:
            st.warning(f"⚠️ {ticker} skipped: {e}")

    return pd.DataFrame(results)

# -----------------------
# Run Backtest
# -----------------------
if st.button("📈 Backtest Strategy (1 Year)"):
    with st.spinner("⏳ Running backtest on NIFTY50..."):
        bt_df = backtest_nifty50(period="1y")

    if bt_df.empty:
        st.error("No signals found for the selected period.")
    else:
        st.success(f"{len(bt_df)} signals generated ✅")
        st.dataframe(bt_df, use_container_width=True)

        # Performance Summary
        st.subheader("📊 Strategy Performance Summary")
        total_signals = len(bt_df)
        avg_return = bt_df["Next_Day_Return(%)"].mean()
        win_rate = (bt_df["Next_Day_Return(%)"] > 0).mean() * 100

        st.write(f"**Total Signals:** {total_signals}")
        st.write(f"**Win Rate:** {win_rate:.2f}%")
        st.write(f"**Average Next-Day Return:** {avg_return:.2f}%")

        # -----------------------
        # Equity Curve Plot
        # -----------------------
        bt_df_sorted = bt_df.sort_values("Date")
        bt_df_sorted["Cumulative_Return(%)"] = bt_df_sorted["Next_Day_Return(%)"].cumsum()

        st.subheader("📈 Equity Curve (Cumulative Returns %)")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(bt_df_sorted["Date"], bt_df_sorted["Cumulative_Return(%)"], label="Strategy Cumulative Return")
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Return (%)")
        ax.legend()
        ax.grid()
        st.pyplot(fig)
