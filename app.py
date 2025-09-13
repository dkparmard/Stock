import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import streamlit as st

# ---------- Fetch NIFTY50 tickers ----------
@st.cache_data(ttl=3600)
def fetch_nifty50_tickers():
    url = "https://en.wikipedia.org/wiki/NIFTY_50"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table", {"class": "wikitable sortable"})
    tickers = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        symbol = cols[1].text.strip()
        if symbol:
            tickers.append(f"{symbol}.NS")
    return tickers

# ---------- Indicator & Condition ----------
def check_condition(df):
    latest = df.iloc[-1]
    lower = min(latest["EMA44"], latest["SMA50"])
    upper = max(latest["EMA44"], latest["SMA50"])
    cond_between = (lower < latest["EMA8"] < upper) and (lower < latest["SMA5"] < upper)
    cond_bull = latest["Close"] > latest["EMA8"]
    if cond_between and cond_bull:
        strength_pct = ((latest["Close"] - latest["EMA8"]) / latest["EMA8"]) * 100
        return round(strength_pct, 2)
    return None

def scan_nifty50():
    tickers = fetch_nifty50_tickers()
    results = []
    progress_bar = st.progress(0)
    for i, tk in enumerate(tickers):
        try:
            df = yf.download(tk, period="6mo", interval="1d", progress=False)
            if df.shape[0] < 50:
                continue

            # Calculate EMAs and SMAs using pandas
            df["EMA8"] = df["Close"].ewm(span=8, adjust=False).mean()
            df["EMA44"] = df["Close"].ewm(span=44, adjust=False).mean()
            df["SMA5"] = df["Close"].rolling(window=5).mean()
            df["SMA50"] = df["Close"].rolling(window=50).mean()

            latest = df.iloc[-1]
            if any(pd.isna(latest[col]) for col in ["EMA8", "EMA44", "SMA5", "SMA50", "Close"]):
                continue

            strength = check_condition(df)
            if strength is not None:
                results.append({
                    "Ticker": tk,
                    "Close": round(latest["Close"], 2),
                    "EMA8": round(latest["EMA8"], 2),
                    "SMA5": round(latest["SMA5"], 2),
                    "EMA44": round(latest["EMA44"], 2),
                    "SMA50": round(latest["SMA50"], 2),
                    "Strength_%": strength,
                })
        except Exception as e:
            st.write(f"Error with {tk}: {e}")
        progress_bar.progress((i + 1) / len(tickers))
    return pd.DataFrame(results)

# ---------- Streamlit UI ----------
st.title("📊 NIFTY50 Screener (No External TA Library)")
st.markdown("**Condition:** EMA8 & SMA5 between EMA44 & SMA50 + Close > EMA8")

if st.button("🔎 Scan Now"):
    with st.spinner("Fetching & scanning NIFTY50 stocks..."):
        df = scan_nifty50()
        if df.empty:
            st.warning("No stocks meet the condition today.")
        else:
            df = df.sort_values(by="Strength_%", ascending=False).reset_index(drop=True)
            st.success(f"Found {len(df)} matching stocks")
            st.dataframe(df, use_container_width=True)
