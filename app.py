def scan_nifty50():
    tickers = fetch_nifty50_tickers()
    results = []

    for ticker in tickers:
        try:
            df = yf.download(ticker, period="6mo", interval="1d")
            if df.empty:
                continue

            # Calculate indicators
            df["EMA8"]  = df["Close"].ewm(span=8, adjust=False).mean()
            df["EMA44"] = df["Close"].ewm(span=44, adjust=False).mean()
            df["SMA5"]  = df["Close"].rolling(window=5).mean()
            df["SMA50"] = df["Close"].rolling(window=50).mean()

            if len(df) < 50:
                continue

            # ✅ Select last row (scalar values)
            ema8, ema44, sma5, sma50, close = df.iloc[-1][["EMA8","EMA44","SMA5","SMA50","Close"]]

            # ✅ Scalar comparison
            if (ema8 > ema44) and (ema8 < sma50) and (sma5 > ema44) and (sma5 < sma50) and (close > ema8):
                results.append({
                    "Ticker": ticker,
                    "Close": close,
                    "EMA8": ema8,
                    "EMA44": ema44,
                    "SMA5": sma5,
                    "SMA50": sma50
                })

        except Exception as e:
            st.write(f"⚠️ Error with {ticker}: {e}")

    return pd.DataFrame(results)
