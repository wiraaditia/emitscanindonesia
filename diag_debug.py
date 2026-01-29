
import yfinance as yf
import pandas as pd

def check(t):
    print(f"--- Checking {t} ---")
    data = yf.download(t, period="5d", interval="5m", progress=False)
    print(f"Columns: {data.columns}")
    
    if isinstance(data.columns, pd.MultiIndex):
        print("MultiIndex detected")
        print("Level 0:", data.columns.get_level_values(0).unique())
        try:
             print("Level 1:", data.columns.get_level_values(1).unique())
        except: pass
        
        # Simulating app logic
        if 'Close' in data.columns.get_level_values(0):
             print("Flattening using Level 0")
             data.columns = data.columns.get_level_values(0)
             
    if 'Close' in data.columns:
        print(f"Last Price: {data['Close'].iloc[-1]}")
        print(data['Close'].tail())
    else:
        print("No Close column found")

tickers = ["DMMX.JK", "DCII.JK", "MLPT.JK", "MCAS.JK"]
for t in tickers:
    check(t)
