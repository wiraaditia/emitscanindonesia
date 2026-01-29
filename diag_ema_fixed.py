
import yfinance as yf
import pandas as pd
import time

def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def check_ticker(ticker):
    print(f"Checking {ticker}...")
    try:
        # Test M5
        hist = yf.download(ticker, period="5d", interval="5m", progress=False)
        print(f"  Shape: {hist.shape}")
        
        # Flatten MultiIndex (FIXED LOGIC)
        if isinstance(hist.columns, pd.MultiIndex):
            if 'Close' in hist.columns.get_level_values(0):
                hist.columns = hist.columns.get_level_values(0)
            elif len(hist.columns.levels) > 1 and 'Close' in hist.columns.get_level_values(1):
                hist.columns = hist.columns.get_level_values(1)
            
        if 'Close' not in hist.columns:
            print(f"  No Close column. Columns: {hist.columns}")
            return
            
        ema20 = calculate_ema(hist['Close'], 20).iloc[-1]
        ema50 = calculate_ema(hist['Close'], 50).iloc[-1]
        close = hist['Close'].iloc[-1]
        
        dist = (ema20 - ema50) / close * 100
        print(f"  Close: {close:.2f}, EMA20: {ema20:.2f}, EMA50: {ema50:.2f}, Dist: {dist:.2f}%")
        
    except Exception as e:
        print(f"  Error: {e}")

tickers = ['BBCA.JK', 'GOTO.JK']
for t in tickers:
    check_ticker(t)
