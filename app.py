import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Indian Stock Screener", layout="wide")

st.title("📈 Indian Stock Screener (50/100 SMA + Trend Filter)")

# -------------------------
# Fetch & Screen Function
# -------------------------
def fetch_and_screen(symbol: str, recent: int = 0):
    try:
        df = yf.download(symbol, period="400d", interval="1d", auto_adjust=True, progress=False)
    except Exception as e:
        st.error(f"❌ Failed to fetch {symbol}: {e}")
        return None

    if df.empty or len(df) < 110:
        return None

    close = df["Close"]
    df["SMA20"] = close.rolling(20).mean()
    df["SMA50"] = close.rolling(50).mean()
    df["SMA100"] = close.rolling(100).mean()
    df["EMA8"] = close.ewm(span=8, adjust=False).mean()

    # conditions with safe fillna
    df["golden_cross"] = ((df["SMA50"] > df["SMA100"]) &
                          (df["SMA50"].shift(1) <= df["SMA100"].shift(1))).fillna(False)
    df["cond_trend"] = ((df["SMA20"] > df["SMA50"]) &
                        (df["EMA8"] > df["SMA20"])).fillna(False)

    if recent == 0:
        last = df.iloc[-1]

        gc = bool(last["golden_cross"]) if pd.notna(last["golden_cross"]) else False
        trend = bool(last["cond_trend"]) if pd.notna(last["cond_trend"]) else False

        if gc and trend:
            return {"Symbol": symbol, "Date": df.index[-1].date(), "Close": float(last["Close"])}

    else:
        tail = df.tail(recent + 1)
        hits = tail[(tail["golden_cross"] == True) & (tail["cond_trend"] == True)]
        if not hits.empty:
            last_hit = hits.iloc[-1]
            return {"Symbol": symbol, "Date": hits.index[-1].date(), "Close": float(last_hit["Close"])}

    return None


# -------------------------
# Streamlit UI
# -------------------------
symbols_input = st.text_area(
    "Enter NSE stock symbols (comma separated, e.g. RELIANCE.NS, TCS.NS, INFY.NS)",
    "RELIANCE.NS,TCS.NS,INFY.NS"
)

recent = st.number_input("Lookback bars (0 = only today)", min_value=0, max_value=30, value=0, step=1)

if st.button("▶️ Run Screener"):
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]

    results = []
    for sym in symbols:
        row = fetch_and_screen(sym, recent)
        if row:
            results.append(row)

    if results:
        df_results = pd.DataFrame(results)
        st.success(f"✅ {len(df_results)} stocks matched the criteria")
        st.dataframe(df_results, use_container_width=True)
    else:
        st.warning("⚠️ No stocks matched the criteria.")
