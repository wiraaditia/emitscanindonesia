import yfinance as yf
import pandas as pd

tickers = ['BNGA.JK', 'ACES.JK', 'SPTO.JK']
print(f"Checking tickers: {tickers}")

data = yf.download(tickers, period='3mo', group_by='ticker', progress=False)

for t in tickers:
    print(f"\n--- {t} ---")
    hist = data[t]
    print("Tail of data:")
    print(hist.tail(5))
    
    # Check last row specifically
    last_row = hist.iloc[-1]
    print(f"\nLast row values:")
    print(last_row)
    
    # Check if last row is all NaN
    if last_row.isna().all():
        print("ALERT: Last row is entirely NaN!")
    elif last_row.isna().any():
        print("ALERT: Last row contains some NaN values!")
    
    # Try dropping NaNs
    clean_hist = hist.dropna(subset=['Close', 'Volume'])
    if not clean_hist.empty:
        print(f"Cleaned last Close: {clean_hist['Close'].iloc[-1]}")
        print(f"Cleaned last Vol: {clean_hist['Volume'].iloc[-1]}")
    else:
        print("ERROR: Hist is empty after dropping NaNs!")
