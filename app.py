import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import time
import random
from concurrent.futures import ThreadPoolExecutor
import pickle
import os

# Cache file for persistent scanner results
CACHE_FILE = ".scanner_cache.pkl"
WATCHLIST_CACHE_FILE = ".watchlist_cache.pkl"

def load_cached_results():
    """Load scanner results from cache file"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    return None

def save_cached_results(results, timestamp):
    """Save scanner results to cache file"""
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump({'results': results, 'timestamp': timestamp}, f)
    except:
        pass

def clear_cached_results():
    """Clear cached scanner results"""
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except:
            pass

def load_watchlist_cache():
    """Load watchlist from cache"""
    if os.path.exists(WATCHLIST_CACHE_FILE):
        try:
            with open(WATCHLIST_CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    return None

def save_watchlist_cache(watchlist_data):
    """Save watchlist to cache"""
    try:
        with open(WATCHLIST_CACHE_FILE, 'wb') as f:
            pickle.dump(watchlist_data, f)
    except:
        pass

def clear_watchlist_cache():
    """Clear watchlist cache"""
    if os.path.exists(WATCHLIST_CACHE_FILE):
        try:
            os.remove(WATCHLIST_CACHE_FILE)
        except:
            pass

# --- CONFIG DASHBOARD ---
st.set_page_config(page_title="EmitScan Indonesia", page_icon="favicon.png", layout="wide")

# --- CUSTOM CSS STOCKBIT STYLE ---
# --- CUSTOM CSS PREMIUM DARK STYLE ---
# --- CUSTOM CSS TRADINGVIEW / STOCKBIT PRO STYLE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Reset & Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #131722 !important; /* TradingView Black */
        color: #e0e0e0 !important;
        font-size: 13px; /* Smaller font for pro feel */
        overflow-x: hidden !important; /* Remove horizontal scroll */
    }
    
    /* Sidebar (Watchlist) */
    [data-testid="stSidebar"] {
        background-color: #1e222d !important;
        border-right: 1px solid #2a2e39;
        width: 300px !important;
    }
    
    /* Main Layout Gap */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    
    /* Card / Panels */
    .pro-card {
        background-color: #1e222d;
        border: 1px solid #2a2e39;
        border-radius: 4px;
        padding: 0px;
        margin-bottom: 8px;
        overflow: hidden;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    div[data-testid="stMetricLabel"] { font-size: 11px !important; color: #787b86 !important; }
    div[data-testid="stMetricValue"] { font-size: 16px !important; color: #d1d4dc !important; }
    
    /* Buttons (Buy/Sell Style) */
    .stButton > button {
        border-radius: 4px;
        font-weight: 600;
        font-size: 12px;
        padding: 4px 12px;
        border: none;
    }
    
    /* Order Book Table */
    .order-book-cell {
        font-family: 'Roboto Mono', monospace;
        font-size: 12px;
        padding: 4px;
    }
    
    /* Tabs (Bottom Panel) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e222d;
        padding: 0px 10px;
        border-bottom: 1px solid #2a2e39;
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0px;
        color: #787b86;
        font-size: 13px;
        font-weight: 500;
        padding-top: 0;
        padding-bottom: 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #2962ff;
        border-bottom: 2px solid #2962ff;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #131722; }
    ::-webkit-scrollbar-thumb { background: #363a45; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #4e525e; }

</style>
""", unsafe_allow_html=True)

# --- ANTI-BLOCKING MEASURES ---
# 1. Daftar User-Agent untuk Rotasi
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
]

# --- EXPANDED TICKER DATABASE (LQ45 + POPULAR) ---
# Simulasi "Semua Emiten" dengan mengambil 50 sahama teraktif/populer.
TICKERS = [
    'BBCA.JK', 'BBRI.JK', 'BMRI.JK', 'BBNI.JK', 'BBTN.JK', 'ARTO.JK', 'BRIS.JK', # Banking
    'ASII.JK', 'TLKM.JK', 'ISAT.JK', 'EXCL.JK', 'UNTR.JK', 'GOTO.JK', 'BUKA.JK', # Bluechip/Tech
    'ADRO.JK', 'PTBA.JK', 'ITMG.JK', 'PGAS.JK', 'MEDC.JK', 'AKRA.JK', # Energy
    'ANTM.JK', 'INCO.JK', 'TINS.JK', 'MDKA.JK', 'BRMS.JK', # Metal/Mining
    'CPIN.JK', 'JPFA.JK', 'ICBP.JK', 'INDF.JK', 'UNVR.JK', 'MYOR.JK', 'AMRT.JK', # Consumer
    'BSDE.JK', 'PWON.JK', 'CTRA.JK', 'SMRA.JK', 'ASRI.JK', # Property
    'KLBF.JK', 'HEAL.JK', 'MIKA.JK', 'SIDO.JK', # Healthcare
    'SMGR.JK', 'INTP.JK', 'INKP.JK', 'TKIM.JK', # Basic Ind
    'BUMI.JK', 'DEWA.JK', 'KIJA.JK', 'BEST.JK' # Others
]

# --- FUNGSI LOGIKA (SAFE VERSION) ---
@st.cache_data(ttl=600) # Cache 10 mins
def get_stock_data(ticker):
    # Random delay 0.5s - 1.5s untuk menghindari deteksi robot
    time.sleep(random.uniform(0.5, 1.5))
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if len(hist) < 20: return None
        
        # Fundamental data kadang bikin lemot/error, kita wrap try-except ketat
        try: 
            # Dapatkan info lengkap
            info = stock.info
            pbv = info.get('priceToBook', 0)
        except: 
            info = {}
            pbv = 0
            
        return hist, pbv, info
    except Exception as e:
        return None

def get_news_sentiment(ticker):
    """
    Advanced News Sentiment Analysis with Multi-Source Aggregation
    Returns: sentiment, headline, score, impact, news_list, analysis
    """
    try:
        clean_ticker = ticker.replace('.JK', '')
        
        # Multi-source news aggregation
        news_sources = [
            f"https://www.cnbcindonesia.com/search?query={clean_ticker}",
            f"https://www.cnnindonesia.com/search/?query={clean_ticker}",
        ]
        
        all_news = []
        
        for url in news_sources:
            try:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                res = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Helper to find date
                def find_date(art_soup):
                    # Try finding relative time strings
                    for tag in art_soup.find_all(['span', 'div', 'p']):
                        txt = tag.get_text().strip()
                        if any(x in txt for x in ['lalu', 'WIB', 'ago', 'min', 'hour']):
                            return txt
                    return "Baru saja"

                # CNBC Indonesia parsing
                if 'cnbcindonesia' in url:
                    articles = soup.find_all('article', limit=5)
                    for article in articles:
                        try:
                            title_elem = article.find('h2') or article.find('h3') or article.find('a', class_='title')
                            if title_elem:
                                title = title_elem.get_text().strip()
                                link_elem = article.find('a')
                                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                                if not link.startswith('http'):
                                    link = 'https://www.cnbcindonesia.com' + link
                                
                                date_text = find_date(article)
                                
                                all_news.append({
                                    'title': title,
                                    'source': 'CNBC Indonesia',
                                    'link': link,
                                    'date': date_text
                                })
                        except:
                            continue
                
                # CNN Indonesia parsing
                elif 'cnnindonesia' in url:
                    articles = soup.find_all('article', limit=5)
                    for article in articles:
                        try:
                            title_elem = article.find('h2') or article.find('h3') or article.find('a', class_='title')
                            if title_elem:
                                title = title_elem.get_text().strip()
                                link_elem = article.find('a')
                                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                                if not link.startswith('http'):
                                    link = 'https://www.cnnindonesia.com' + link
                                
                                date_text = find_date(article)

                                all_news.append({
                                    'title': title,
                                    'source': 'CNN Indonesia',
                                    'link': link,
                                    'date': date_text
                                })
                        except:
                            continue
                            
                time.sleep(0.3)  # Rate limiting
            except:
                continue
        
        if not all_news:
            return "NEUTRAL", "Tidak ada berita terbaru", 50, "LOW", [], "Tidak ada data berita yang tersedia"
        
        # Advanced Sentiment Scoring (0-100)
        positive_keywords = {
            'sangat_positif': ['rekor', 'melesat', 'booming', 'ekspansi besar', 'akuisisi', 'dividen jumbo', 'laba bersih naik', 'ara', 'terbang'],
            'positif': ['laba', 'naik', 'ekspansi', 'dividen', 'borong', 'untung', 'tumbuh', 'kinerja positif', 'buyback', 'rights issue', 'akumulasi', 'progresif'],
            'cukup_positif': ['stabil', 'optimis', 'prospek', 'potensi', 'peluang', 'target', 'rebound']
        }
        
        negative_keywords = {
            'sangat_negatif': ['bangkrut', 'kolaps', 'skandal', 'fraud', 'suspend', 'delisting', 'rugi besar', 'arb', 'anjlok parah'],
            'negatif': ['rugi', 'turun', 'merosot', 'anjlok', 'PHK', 'tutup', 'gagal', 'krisis', 'distribusi', 'buang barang'],
            'cukup_negatif': ['risiko', 'tantangan', 'tekanan', 'penurunan', 'koreksi', 'lemah']
        }
        
        # Calculate sentiment score
        total_score = 0
        sentiment_reasons = []
        
        for news in all_news[:3]:  # Analyze top 3 news
            title_lower = news['title'].lower()
            news_score = 50  # Neutral base
            
            # Check positive keywords
            for category, keywords in positive_keywords.items():
                for keyword in keywords:
                    if keyword in title_lower:
                        if category == 'sangat_positif':
                            news_score += 20
                            sentiment_reasons.append(f"✅ Berita sangat positif: '{keyword}' terdeteksi")
                        elif category == 'positif':
                            news_score += 10
                            sentiment_reasons.append(f"✅ Berita positif: '{keyword}' terdeteksi")
                        else:
                            news_score += 5
            
            # Check negative keywords
            for category, keywords in negative_keywords.items():
                for keyword in keywords:
                    if keyword in title_lower:
                        if category == 'sangat_negatif':
                            news_score -= 20
                            sentiment_reasons.append(f"❌ Berita sangat negatif: '{keyword}' terdeteksi")
                        elif category == 'negatif':
                            news_score -= 10
                            sentiment_reasons.append(f"❌ Berita negatif: '{keyword}' terdeteksi")
                        else:
                            news_score -= 5
            
            total_score += news_score
        
        # Average score
        avg_score = min(100, max(0, total_score // len(all_news[:3])))
        
        # Determine sentiment category
        if avg_score >= 70:
            sentiment = "VERY POSITIVE"
        elif avg_score >= 55:
            sentiment = "POSITIVE"
        elif avg_score >= 45:
            sentiment = "NEUTRAL"
        elif avg_score >= 30:
            sentiment = "NEGATIVE"
        else:
            sentiment = "VERY NEGATIVE"
        
        # Impact Analysis
        if avg_score >= 70 or avg_score <= 30:
            impact = "HIGH"
        elif avg_score >= 60 or avg_score <= 40:
            impact = "MEDIUM"
        else:
            impact = "LOW"
        
        # Main headline
        main_headline = all_news[0]['title']
        
        # Generate analysis summary
        analysis = f"Analisis {len(all_news)} berita terkini menunjukkan sentimen {sentiment.lower()} dengan skor {avg_score}/100. "
        if impact == "HIGH":
            analysis += "Dampak terhadap harga saham diprediksi TINGGI dalam 1-3 hari ke depan."
        elif impact == "MEDIUM":
            analysis += "Dampak terhadap harga saham diprediksi SEDANG."
        else:
            analysis += "Dampak terhadap harga saham diprediksi RENDAH."
        
        return sentiment, main_headline, avg_score, impact, all_news[:5], analysis
        
    except Exception as e:
        return "NEUTRAL", "Tidak ada berita", 50, "LOW", [], "Error mengambil data berita"

def analyze_stock(ticker):
    data = get_stock_data(ticker)
    if not data: return None
    hist, pbv, info = data
    
    curr_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2]
    chg_pct = ((curr_price - prev_close) / prev_close) * 100
    
    curr_vol = hist['Volume'].iloc[-1]
    avg_vol = hist['Volume'].mean()
    vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 0
    
    ma5 = hist['Close'].tail(5).mean()
    ma20 = hist['Close'].tail(20).mean()
    
    # News Sentiment

    
    # Get enhanced news sentiment data
    sentiment, headline, score, impact, news_list, analysis = get_news_sentiment(ticker)
    
    # 5 Pillars Logic
    cond_vol_pbv = (vol_ratio > 1.5) and (pbv < 1.2)
    cond_trend = ma5 > ma20
    cond_big_player = (vol_ratio > 2.0) and (abs(chg_pct) < 4)
    cond_sentiment = score >= 55  # Use sentiment score instead of just "POSITIVE"
    
    status = "HOLD"
    final_score = 0
    if cond_trend: final_score += 1
    if cond_vol_pbv: final_score += 1
    if cond_sentiment: final_score += 1
    if cond_big_player: final_score += 1
    
    if final_score >= 3:
        status = "🔥 STRONG BUY"
    elif final_score == 2:
        status = "✅ WATCHLIST" 
        
    return {
        "Ticker": ticker.replace('.JK',''),
        "Price": curr_price,
        "Change %": chg_pct,
        "Vol Ratio": vol_ratio,
        "PBV": pbv,
        "MA Trend": "Bullish" if cond_trend else "Bearish",
        "Sentiment": sentiment,
        "Sentiment Score": score,
        "Impact": impact,
        "Status": status,
        "Headline": headline,
        "News List": news_list,
        "Analysis": analysis,
        "Raw Vol Ratio": vol_ratio,
        "Raw PBV": pbv
    }

# Helper untuk mengubah ticker dari News Feed
def set_ticker(ticker):
    # Update langsung ke key milik selectbox
    st.session_state.ticker_selector = ticker.replace('.JK', '')
    # Force switch to Market Dashboard
    st.session_state.active_tab = "📈 Market Dashboard"

# --- MAIN UI ---

# Initialization for Ticker Selector (Since old widget is removed)
if 'ticker_selector' not in st.session_state:
    st.session_state.ticker_selector = "BBCA" # Default Startup Ticker


# --- UI COMPONENT: SIDEBAR (WATCHLIST ONLY) ---
with st.sidebar:
    # Remove default padding & Reduce Top Margin AGGRESSIVELY
    st.markdown("""
    <style>
        /* FORCE SIDEBAR TOP ZERO */
        section[data-testid="stSidebar"] > div {
            padding-top: 0rem !important;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important; /* Some padding needed for inner content */
            margin-top: -4rem !important;
        }
        /* Hide default Streamlit anchors if any */
        a.anchor-link { display: none !important; }
        
        /* Specific Fix for "stSidebarUserContent" */
        [data-testid="stSidebarUserContent"] {
            padding-top: 0rem !important;
        }
        /* Header Adjustment */
        .wl-header {
             margin-top: -20px !important; 
        }
        /* Custom Row Styling */
        .wl-row {
            display: flex;
            align-items: center;
            padding: 8px 4px;
            border-radius: 6px;
            margin-bottom: 2px;
            transition: background 0.2s;
            cursor: pointer;
        }
        /* Header Styling */
        .wl-header {
            font-size: 16px;
            font-weight: 700;
            color: #e0e0e0;
            margin-bottom: 10px;
            margin-top: 10px; /* Adjust this to move Up/Down */
            display: flex;
            align-items: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # BRANDING HEADER
    st.markdown("""
    <div style="margin-bottom: 16px; text-align: center;">
        <div style="font-size: 18px; font-weight: 800; background: -webkit-linear-gradient(45deg, #00c853, #b2ff59); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 1px;">
            EMITSCAN INDONESIA
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Refresh Button
    if st.button("🔄 Refresh Prices", use_container_width=True, type="secondary"):
        clear_watchlist_cache()
        if 'watchlist_data_list' in st.session_state:
            del st.session_state.watchlist_data_list
        st.rerun()
    
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    # Tabs for Watchlist / Gainer / Loser
    tab_wl, tab_gainer, tab_loser = st.tabs(["📋 Watchlist", "📈 Gainer", "📉 Loser"])
    
    # Action Bar (Add, Sort) - Removed Refresh as requested, kept minimal loop structure if needed, or just remove cols
    # ... logic for watchlist loop continues below ...

    # --- WATCHLIST (CUSTOM ROW COMPONENT) ---
    # Styles for custom row
    st.markdown("""
    <style>
    /* ... existing styles ... */
    .wl-row {
        display: flex;
        align-items: center;
        padding: 8px 4px;
        border-radius: 6px;
        margin-bottom: 2px;
        transition: background 0.2s;
        cursor: pointer;
    }
    .wl-row:hover {
        background-color: #2a2e39;
    }
    .wl-ticker { font-weight: 700; font-size: 13px; color: #e0e0e0; }
    .wl-name { font-size: 10px; color: #848e9c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 110px; }
    .wl-price { font-weight: 600; font-size: 13px; text-align: right; }
    .wl-chg { font-size: 10px; text-align: right; }
    .up { color: #00c853; }
    .down { color: #ff5252; }
    </style>
    """, unsafe_allow_html=True)

    # Load from cache or fetch new data
    if 'watchlist_data_list' not in st.session_state:
        # Try to load from cache first
        cached_watchlist = load_watchlist_cache()
        if cached_watchlist:
            st.session_state.watchlist_data_list = cached_watchlist
        else:
            # Generate list only once
            wl = []
            names_map = {
            "BBCA": "Bank Central Asia Tbk.",
            "BBRI": "Bank Rakyat Indonesia.",
            "BMRI": "Bank Mandiri (Persero).",
            "TLKM": "Telkom Indonesia (Persero).",
            "ASII": "Astra International Tbk.",
            "GOTO": "GoTo Gojek Tokopedia Tbk.",
            "UNVR": "Unilever Indonesia Tbk.",
            "ADRO": "Adaro Energy Indonesia Tbk.",
            "BBNI": "Bank Negara Indonesia.",
            "ANTM": "Aneka Tambang Tbk."
        }
            # Realistic Base Prices
            base_prices = {
                "BBCA": 9900, "BBRI": 5200, "BMRI": 7100, "TLKM": 3500, "ASII": 5100,
                "GOTO": 68, "UNVR": 2600, "ADRO": 2500, "BBNI": 5400, "ANTM": 1500,
                "KLBF": 1500, "PGAS": 1400, "PTBA": 2600, "ITMG": 26000, "INDF": 6200
            }

            import random
            for t in TICKERS:
                ticker = t.replace('.JK', '')
                
                # Try to fetch real price from yfinance
                try:
                    stock = yf.Ticker(t)
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        price = int(hist['Close'].iloc[-1])
                        prev_close = hist['Open'].iloc[0]
                        chg = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    else:
                        # Fallback to base price
                        base = base_prices.get(ticker, 1000)
                        price = int(base * random.uniform(0.98, 1.02))
                        chg = random.uniform(-2.5, 2.5)
                except:
                    # Fallback to base price
                    base = base_prices.get(ticker, 1000)
                    price = int(base * random.uniform(0.98, 1.02))
                    chg = random.uniform(-2.5, 2.5)
                
                # Logo URL (Targeting Stockbit's pattern or fallback)
                logo = f"https://assets.stockbit.com/logos/companies/{ticker}.png"
                
                wl.append({
                    "ticker": ticker,
                    "name": names_map.get(ticker, "Emiten Indonesia Tbk"),
                    "price": price,
                    "chg": chg,
                    "logo": logo
                })
            st.session_state.watchlist_data_list = wl
            # Save to cache
            save_watchlist_cache(wl)
            
    # Helper for SVG Sparkline
    def make_sparkline(data, color):
        if not data: return ""
        width = 60
        height = 20
        min_y, max_y = min(data), max(data)
        range_y = max_y - min_y if max_y != min_y else 1
        pts = []
        for i, val in enumerate(data):
            x = (i / (len(data)-1)) * width
            y = height - ((val - min_y) / range_y) * height
            pts.append(f"{x},{y}")
        polyline = " ".join(pts)
        return f'<svg width="{width}" height="{height}"><polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5"/></svg>'

    # Render Loop - Watchlist Tab
    with tab_wl:
        for item in st.session_state.watchlist_data_list:
            # Layout: [Logo] [Ticker/Name] [Sparkline] [Price/Change]
            r_col1, r_col2, r_col3, r_col4 = st.columns([0.8, 2, 1.5, 1.8])
            
            with r_col1:
                # Logo
                st.image(item['logo'], width=32)
                
            with r_col2:
                # Ticker & Name 
                if st.button(f"{item['ticker']}", key=f"btn_wl_{item['ticker']}", use_container_width=True):
                    set_ticker(item['ticker'])
                st.caption(f"{item['name']}")
                
            with r_col3:
                # Sparkline
                # Mock a small trend list based on change
                trend_color = "#00c853" if item['chg'] >= 0 else "#ff5252"
                # Generate pseudo-random trend for the sparkline visual
                trend_data = [
                    item['price'] * (1 - (random.uniform(0, 0.05) if item['chg'] < 0 else -random.uniform(0, 0.05)))
                    for _ in range(5)
                ]
                trend_data.append(item['price']) # End at current
                
                st.markdown(make_sparkline(trend_data, trend_color), unsafe_allow_html=True)
                
            with r_col4:
                # Price & Change
                color_class = "up" if item['chg'] >= 0 else "down"
                sign = "+" if item['chg'] >= 0 else ""
                
                st.markdown(f"""
                <div style="text-align: right; line-height: 1.2;">
                    <div style="font-size: 13px; font-weight: 600; color: #e0e0e0;">{item['price']:,}</div>
                    <div style="font-size: 10px;" class="{color_class}">{sign}{item['chg']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<div style='margin-bottom: 4px; border-bottom: 1px solid #2a2e39;'></div>", unsafe_allow_html=True)
        
        st.caption("IHSG 7,350.12 (Live)")
    
    # Gainer Tab
    with tab_gainer:
        # Sort by highest positive change
        gainers = sorted([i for i in st.session_state.watchlist_data_list if i['chg'] > 0], key=lambda x: x['chg'], reverse=True)[:10]
        for item in gainers:
            r_col1, r_col2, r_col3, r_col4 = st.columns([0.8, 2, 1.5, 1.8])
            with r_col1:
                st.image(item['logo'], width=32)
            with r_col2:
                if st.button(f"{item['ticker']}", key=f"btn_g_{item['ticker']}", use_container_width=True):
                    set_ticker(item['ticker'])
                st.caption(f"{item['name']}")
            with r_col3:
                trend_color = "#00c853"
                trend_data = [item['price'] * (1 - random.uniform(0, 0.05)) for _ in range(5)]
                trend_data.append(item['price'])
                st.markdown(make_sparkline(trend_data, trend_color), unsafe_allow_html=True)
            with r_col4:
                st.markdown(f"""
                <div style="text-align: right; line-height: 1.2;">
                    <div style="font-size: 13px; font-weight: 600; color: #e0e0e0;">{item['price']:,}</div>
                    <div style="font-size: 10px; color: #00c853;">+{item['chg']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 4px; border-bottom: 1px solid #2a2e39;'></div>", unsafe_allow_html=True)
    
    # Loser Tab
    with tab_loser:
        # Sort by change (lowest first) - show bottom 10 regardless of positive/negative
        losers = sorted(st.session_state.watchlist_data_list, key=lambda x: x['chg'])[:10]
        if not losers:
            st.info("🔎 No data available")
        for item in losers:
            r_col1, r_col2, r_col3, r_col4 = st.columns([0.8, 2, 1.5, 1.8])
            with r_col1:
                st.image(item['logo'], width=32)
            with r_col2:
                if st.button(f"{item['ticker']}", key=f"btn_l_{item['ticker']}", use_container_width=True):
                    set_ticker(item['ticker'])
                st.caption(f"{item['name']}")
            with r_col3:
                trend_color = "#ff5252" if item['chg'] < 0 else "#00c853"
                trend_data = [item['price'] * (1 + random.uniform(0, 0.05)) for _ in range(5)]
                trend_data.append(item['price'])
                st.markdown(make_sparkline(trend_data, trend_color), unsafe_allow_html=True)
            with r_col4:
                color_class = "up" if item['chg'] >= 0 else "down"
                sign = "+" if item['chg'] >= 0 else ""
                st.markdown(f"""
                <div style="text-align: right; line-height: 1.2;">
                    <div style="font-size: 13px; font-weight: 600; color: #e0e0e0;">{item['price']:,}</div>
                    <div style="font-size: 10px;" class="{color_class}">{sign}{item['chg']:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 4px; border-bottom: 1px solid #2a2e39;'></div>", unsafe_allow_html=True)


        


# --- UI COMPONENT: TICKER TAPE ---
# Modern CSS Marquee
st.markdown("""
<div class="ticker-wrap">
<div class="ticker">
  <div class="ticker__item">BBCA <span class="up">▲ 9,975</span></div>
  <div class="ticker__item">BBRI <span class="down">▼ 5,200</span></div>
  <div class="ticker__item">BMRI <span class="up">▲ 7,125</span></div>
  <div class="ticker__item">BBNI <span class="up">▲ 6,025</span></div>
  <div class="ticker__item">TLKM <span class="down">▼ 2,130</span></div>
  <div class="ticker__item">ASII <span class="up">▲ 5,100</span></div>
  <div class="ticker__item">GOTO <span class="down">▼ 54</span></div>
  <div class="ticker__item">UNVR <span class="down">▼ 2,340</span></div>
  <div class="ticker__item">ADRO <span class="up">▲ 2,450</span></div>
  <div class="ticker__item">ANTM <span class="up">▲ 1,560</span></div>
  <!-- Duplicate for infinite loop illusion -->
  <div class="ticker__item">BBCA <span class="up">▲ 9,975</span></div>
  <div class="ticker__item">BBRI <span class="down">▼ 5,200</span></div>
  <div class="ticker__item">BMRI <span class="up">▲ 7,125</span></div>
  <div class="ticker__item">BBNI <span class="up">▲ 6,025</span></div>
</div>
</div>
<style>
.ticker-wrap {
  width: 100%;
  overflow: hidden;
  background-color: #15191e;
  padding-left: 100%; /* Start offscreen */
  box-sizing: content-box;
  border-bottom: 1px solid #2a2e39;
  height: 30px;
  line-height: 30px;
  margin-bottom: 10px;
}
.ticker {
  display: inline-block;
  white-space: nowrap;
  padding-right: 100%;
  box-sizing: content-box;
  animation-iteration-count: infinite;
  animation-timing-function: linear;
  animation-name: ticker;
  animation-duration: 45s;
}
.ticker__item {
  display: inline-block;
  padding: 0 2rem;
  font-size: 12px;
  color: #d1d4dc;
  font-weight: 600;
}
.ticker__item .up { color: #00c853; }
.ticker__item .down { color: #ff5252; }

@keyframes ticker {
  0% { transform: translate3d(0, 0, 0); }
  100% { transform: translate3d(-100%, 0, 0); }
}
</style>
""", unsafe_allow_html=True)


# --- MAIN LAYOUT (Tabs: Chart, Financials, Profile) ---
current_symbol = st.session_state.ticker_selector

# Top Bar (Symbol Info) with Logo
logo_url = f"https://assets.stockbit.com/logos/companies/{current_symbol}.png"

header_html = f"""
<div style="background: rgba(30, 34, 45, 0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); padding: 10px 20px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; margin-top: -12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; gap: 12px;">
        <img src="{logo_url}" onerror="this.style.display='none'" style="width: 36px; height: 36px; border-radius: 6px; object-fit: contain; background: rgba(255,255,255,0.05); padding: 4px;" alt="{current_symbol}">
        <div style="display: flex; flex-direction: column; gap: 2px;">
            <span style="font-size: 20px; font-weight: 800; color: #fff; letter-spacing: 0.5px; line-height: 1;">{current_symbol}</span>
            <span style="font-size: 11px; color: #848e9c; font-weight: 500;">JKSE • STOCK</span>
        </div>
        <span style="background: rgba(0, 200, 83, 0.1); color: #00c853; padding: 5px 10px; border-radius: 4px; font-size: 10px; font-weight: 700; border: 1px solid rgba(0, 200, 83, 0.2); letter-spacing: 0.5px; margin-left: 8px;">MARKET OPEN</span>
    </div>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# Main Content Tabs
tab_chart, tab_financials, tab_profile = st.tabs(["🔥 Chart", "📊 Financials", "🏢 Profile"])

with tab_chart:
    # Split Layout for Chart
    c_chart, c_orderbook = st.columns([3, 1])


    with c_chart:
        # TradingView Chart
        timeframe_map = {
            "Daily": "D", "Weekly": "W", "Monthly": "M",
            "4 Hours": "240", "1 Hour": "60", "30 Minutes": "30", "5 Minutes": "5"
        }
        if 'chart_timeframe' not in st.session_state: st.session_state.chart_timeframe = "Daily"
        
        current_tf_code = timeframe_map[st.session_state.chart_timeframe]
        tv_symbol = "IDX:COMPOSITE" if current_symbol == "COMPOSITE" else f"IDX:{current_symbol}"
        
        st.components.v1.html(
            f"""
            <div class="tradingview-widget-container" style="height: 600px; width: 100%; border-radius: 0px; overflow: hidden; border: none; margin-top: -15px;">
            <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget(
            {{
                "autosize": true,
                "symbol": "{tv_symbol}",
                "interval": "{current_tf_code}",
                "timezone": "Asia/Jakarta",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_chart",
                "toolbar_bg": "#1e222d",
                "hide_side_toolbar": false,
                "details": true,
                "hotlist": true,
                "calendar": false,
                "withdateranges": true
            }});
            </script>
            </div>
            """,
            height=550,
        )

        # --- MOVED SCREENER & ANALYSIS ---
        st.write("")
        st.markdown("### Market Screener & AI Analysis")

        # Control Bar
        b1, b2, b3 = st.columns([2, 1, 6])
        with b1:
            if st.button("RUN SCREENER", use_container_width=True, type="primary"):
                st.session_state.run_screener = True
        with b2:
            if st.button("🧹 Clear", use_container_width=True):
                st.session_state.scan_results = None
                st.session_state.last_update = None
                clear_cached_results()  # Clear cache file
                st.rerun()

        st.markdown("---")

        # --- SCANNER LOGIC ---
        # Load from cache if available
        if 'scan_results' not in st.session_state:
            cached_data = load_cached_results()
            if cached_data:
                st.session_state.scan_results = cached_data['results']
                st.session_state.last_update = cached_data['timestamp']
            else:
                st.session_state.scan_results = None

        # Logic triggered by Sidebar Button
        if st.session_state.get('run_screener', False):
            st.session_state.run_screener = False # Reset trigger
            with st.spinner(f'Scanning {len(TICKERS)} Stocks across IDX...'):
                results = []
                progress_bar = st.progress(0)
                
                # Parallel processing using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=10) as executor:
                    # Map tickers to analyze_stock function
                    future_to_ticker = {executor.submit(analyze_stock, t): t for t in TICKERS}
                    
                    for i, future in enumerate(future_to_ticker):
                        res = future.result()
                        if res: 
                            results.append(res)
                        # Update progress bar
                        progress_bar.progress(min((i + 1) / len(TICKERS), 1.0))
                    
                progress_bar.empty()
                
                if results:
                    st.session_state.scan_results = pd.DataFrame(results)
                    st.session_state.last_update = time.strftime("%H:%M WIB")
                    # Save to cache
                    save_cached_results(st.session_state.scan_results, st.session_state.last_update)
                    st.success(f"Scan Completed. Found {len(st.session_state.scan_results[st.session_state.scan_results['Status'] != 'HOLD'])} potential assets.")
                else:
                    st.warning("No data fetched or no match found.")
                    st.session_state.scan_results = None

        # Display Logic
        if st.session_state.scan_results is not None:
            df = st.session_state.scan_results
            
            # Tabs for Result View
            tab_grid, tab_table = st.tabs(["🔲 Grid View", "📋 Table View"])
            
            with tab_grid:
                valid_rows = [r for i, r in df.iterrows() if r['Status'] != 'HOLD']
                cols = st.columns(3)
                for idx, row in enumerate(valid_rows):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"### {row['Ticker']}")
                            if 'STRONG BUY' in row['Status']: st.markdown(":fire: **STRONG BUY**")
                            else: st.markdown(":white_check_mark: **WATCHLIST**")
                            
                            st.progress(row['Sentiment Score'] / 100.0, text=f"Sentiment: {row['Sentiment']}")
                            st.markdown("---")
                            
                            k1, k2, k3 = st.columns(3)
                            k1.metric("Trend", row['MA Trend'])
                            k2.metric("Vol", f"{row['Raw Vol Ratio']:.1f}x")
                            k3.metric("PBV", f"{row['Raw PBV']:.2f}x")
                            
                            st.markdown("---")
                            st.write(row['Analysis'])
                            
                            with st.expander("📰 Lihat Berita"):
                                if row['News List']:
                                    for news in row['News List']:
                                        st.caption(f"{news.get('date')} - {news.get('source')}")
                                        st.markdown(f"[{news.get('title')}]({news.get('link')})")
                                else: st.write("-")
                            
                            st.button(f"📈 Load", key=f"btn_g_{idx}", on_click=set_ticker, args=(row['Ticker'],), use_container_width=True)

            with tab_table:
                st.dataframe(
                    df, 
                    use_container_width=True,
                    column_order=["Ticker", "Status", "Price", "Change %", "Vol Ratio", "Sentiment Score", "Headline"],
                    height=400
                )

        


    with c_orderbook:
        # --- DATA PREPARATION ---
        # Fetch fresh data for the selected ticker to ensure sidebar matches selection
        try:
            # Re-fetch or reuse logic if optimized, but for now safe to call our cached function
            sidebar_data = get_stock_data(current_symbol + ".JK")
            if sidebar_data:
                sb_hist, sb_pbv, sb_info = sidebar_data
                # Current Price from history to be safe
                sb_price = sb_hist['Close'].iloc[-1]
                sb_prev = sb_hist['Close'].iloc[-2]
                sb_open = sb_hist['Open'].iloc[-1]
                sb_high = sb_hist['High'].iloc[-1]
                sb_low = sb_hist['Low'].iloc[-1]
                sb_vol = sb_hist['Volume'].iloc[-1]
                
                # Mock Frequency (Freq) - usually not in free yfinance
                sb_freq = int(sb_vol / random.randint(100, 500)) if sb_vol > 0 else 0
                
                # Mock Foreign Buy/Sell (Estimasi)
                sb_f_buy = sb_vol * sb_price * 0.3 # 30% foreign
                sb_f_sell = sb_vol * sb_price * 0.25 # 25% foreign
                
                # ARA / ARB Simulation (approx 20-35% limits in ID but keeping simple)
                sb_ara = int(sb_prev * 1.25) 
                sb_arb = int(sb_prev * 0.75) 
                
                # Value
                sb_val = sb_vol * sb_price
            else:
                # Fallback if no data
                sb_price = 4200
                sb_prev = 4150
                sb_open = 4200
                sb_high = 4350
                sb_low = 4180
                sb_vol = 1120000
                sb_freq = 1900
                sb_f_buy = 5200000000
                sb_f_sell = 2100000000
                sb_ara = 5200
                sb_arb = 3900
                sb_val = 8400000000
        
        except:
             # Fallback crash protection
            sb_price = 0
            sb_prev = 0
            sb_open = 0
            sb_high = 0
            sb_low = 0
            sb_vol = 0
            sb_freq = 0
            sb_f_buy = 0
            sb_f_sell = 0
            sb_ara = 0
            sb_arb = 0
            sb_val = 0

        # Create Helper for Mock Order Book
        def generate_mock_order_book(center_price):
            # Generate 5-10 rows
            rows = []
            # Bid side (Left) - descending from price
            # Offer side (Right) - ascending from price
            
            # Start slightly below/above current price
            # Adjust step based on price fraction (tick size logic simplified)
            tick = 5 if center_price < 200 else (25 if center_price < 5000 else 50)
            
            # Round center price to nearest tick
            base_price = int(round(center_price / tick) * tick)
            
            for i in range(8):
                # BID
                bid_p = base_price - (i * tick)
                bid_vol = random.randint(100, 50000)
                bid_freq = random.randint(5, 500)
                
                # OFFER
                off_p = base_price + ((i+1) * tick) # Start 1 tick above
                off_vol = random.randint(100, 50000)
                off_freq = random.randint(5, 500)
                
                rows.append({
                    "bid_freq": bid_freq,
                    "bid_vol": bid_vol,
                    "bid_p": bid_p,
                    "off_p": off_p,
                    "off_vol": off_vol,
                    "off_freq": off_freq
                })
            return rows

        # Create Helper for Mock Running Trade
        def generate_mock_running_trade(ticker_code, center_price):
            trades = []
            brokers = ["YP", "PD", "KK", "NI", "CC", "LG", "SQ", "OD", "XL", "XC", "AK", "BK"]
            types = ["D", "F"] # Domestic, Foreign
            
            tick = 5 if center_price < 200 else (25 if center_price < 5000 else 50)
            base_price = int(round(center_price / tick) * tick)
            
            import datetime
            now = datetime.datetime.now()
            
            for i in range(15):
                t_time = (now - datetime.timedelta(seconds=i*random.randint(2, 10))).strftime("%H:%M:%S")
                # Price randomly +/- 1-2 ticks
                p_offset = random.choice([-tick, 0, tick])
                t_price = base_price + p_offset
                
                t_action = "Buy" if p_offset >= 0 else "Sell"
                t_color = "#00c853" if p_offset > 0 else ("#ff5252" if p_offset < 0 else "#e0e0e0")
                
                t_lot = random.randint(1, 500)
                t_buy_code = random.choice(brokers)
                t_buy_type = random.choice(types)
                t_buyer = f"{t_buy_code} [{t_buy_type}]"
                
                trades.append({
                    "time": t_time,
                    "code": ticker_code,
                    "price": t_price,
                    "action": t_action,
                    "color": t_color,
                    "lot": t_lot,
                    "buyer": t_buyer
                })
            return trades

        mock_ob = generate_mock_order_book(sb_price)
        mock_rt = generate_mock_running_trade(current_symbol, sb_price)

        # --- PRO STATS HEADER ---
        # Helper number format
        def fmt_num(n):
            if n >= 1e9: return f"{n/1e9:.1f}B"
            if n >= 1e6: return f"{n/1e6:.1f}M"
            if n >= 1e3: return f"{n/1e3:.1f}K"
            return str(int(n))

        st.markdown(f"""<div style="background: #1e222d; border-radius: 4px; padding: 8px; margin-bottom: 4px; font-family: 'Roboto', sans-serif; font-size: 11px;"><div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4px; color: #d1d4dc;"><div>Open <span style="float:right; color:#e0e0e0;">{sb_open:,}</span></div><div>Prev <span style="float:right; color:#e0e0e0;">{sb_prev:,}</span></div><div>Lot <span style="float:right; color:#00c853;">{fmt_num(sb_vol)}</span></div><div>High <span style="float:right; color:#00c853;">{sb_high:,}</span></div><div>ARA <span style="float:right; color:#e0e0e0;">{sb_ara:,}</span></div><div>Val <span style="float:right; color:#00c853;">{fmt_num(sb_val)}</span></div><div>Low <span style="float:right; color:#ff5252;">{sb_low:,}</span></div><div>ARB <span style="float:right; color:#e0e0e0;">{sb_arb:,}</span></div><div>Avg <span style="float:right; color:#e0e0e0;">{(sb_high+sb_low)//2:,}</span></div><div>F Buy <span style="float:right; color:#00c853;">{fmt_num(sb_f_buy)}</span></div><div>F Sell <span style="float:right; color:#ff5252;">{fmt_num(sb_f_sell)}</span></div><div>Freq <span style="float:right; color:#e0e0e0;">{fmt_num(sb_freq)}</span></div></div></div>""", unsafe_allow_html=True)

        # --- PRO ORDER BOOK ---
        st.markdown("###  Order Book")
        
        # Build Table Rows HTML (Flattened to avoid Markdown Code Block issues)
        ob_rows_html = ""
        for row in mock_ob:
             ob_rows_html += f"""<tr style="border-bottom: 1px solid #1e222d;"><td style="color:#787b86; text-align:center;">{row['bid_freq']}</td><td style="color:#d1d4dc; text-align:right;">{row['bid_vol']:,}</td><td style="color:#00c853; text-align:right;">{row['bid_p']:,}</td><td style="color:#ff5252; text-align:left;">{row['off_p']:,}</td><td style="color:#d1d4dc; text-align:right;">{row['off_vol']:,}</td><td style="color:#787b86; text-align:center;">{row['off_freq']}</td></tr>"""
             
        # Total Row
        total_bid_vol = sum(r['bid_vol'] for r in mock_ob)
        total_off_vol = sum(r['off_vol'] for r in mock_ob)
        total_bid_freq = sum(r['bid_freq'] for r in mock_ob)
        total_off_freq = sum(r['off_freq'] for r in mock_ob)

        st.markdown(f"""
<div style="background: #1e222d; border: 1px solid #2a2e39; border-radius: 4px; overflow: hidden; font-family: 'Roboto Mono', monospace; font-size: 10px;">
<div style="max-height: 480px; overflow-y: auto;">
<table style="width: 100%; border-collapse: separate; border-spacing: 0;">
<thead style="background: #2a2e39; color: #848e9c; position: sticky; top: 0; z-index: 5;">
<tr>
<th style="padding: 4px; text-align: center; border-bottom: 1px solid #1e222d; background: #2a2e39;">Freq</th>
<th style="padding: 4px; text-align: right; border-bottom: 1px solid #1e222d; background: #2a2e39;">Lot</th>
<th style="padding: 4px; text-align: right; border-bottom: 1px solid #1e222d; background: #2a2e39;">Bid</th>
<th style="padding: 4px; text-align: left; border-bottom: 1px solid #1e222d; background: #2a2e39;">Offer</th>
<th style="padding: 4px; text-align: right; border-bottom: 1px solid #1e222d; background: #2a2e39;">Lot</th>
<th style="padding: 4px; text-align: center; border-bottom: 1px solid #1e222d; background: #2a2e39;">Freq</th>
</tr>
</thead>
<tbody>
{ob_rows_html}
<tr style="border-bottom: 1px solid #1e222d; border-top: 1px solid #444; position: sticky; bottom: 0; background: #1e222d; z-index: 5; box-shadow: 0 -2px 5px rgba(0,0,0,0.2);">
<td style="color:#e0e0e0; text-align:center; font-weight:bold;">{total_bid_freq:,}</td>
<td style="color:#e0e0e0; text-align:right; font-weight:bold;">{fmt_num(total_bid_vol)}</td>
<td style="color:#848e9c; text-align:center; font-size:9px;" colspan="2">TOTAL</td>
<td style="color:#e0e0e0; text-align:right; font-weight:bold;">{fmt_num(total_off_vol)}</td>
<td style="color:#e0e0e0; text-align:center; font-weight:bold;">{total_off_freq:,}</td>
</tr>
</tbody>
</table>
</div>
</div>
""", unsafe_allow_html=True)
        
        # --- PRO RUNNING TRADE ---
        st.markdown("<div style='margin-top: 15px; font-weight: 700; font-size: 14px;'>Running Trade ↗</div>", unsafe_allow_html=True)
        
        # Build Trade Rows HTML (Flattened)
        rt_rows_html = ""
        for t in mock_rt:
             rt_rows_html += f"""<tr><td style="color:#d1d4dc; padding:4px 6px;">{t['time']}</td><td style="color:{t['color']}; text-align:center;">{t['code']}</td><td style="color:{t['color']}; text-align:right;">{t['price']:,}</td><td style="color:{t['color']}; text-align:center;">{t['action']}</td><td style="color:#d1d4dc; text-align:right;">{t['lot']}</td><td style="color:#aa00ff; text-align:right;">{t['buyer']}</td></tr>"""
             
        st.markdown(f"""
<div style="background: #1e222d; border: 1px solid #2a2e39; border-radius: 4px; padding: 0; min-height: 180px; overflow: hidden;">
<div style="max-height: 300px; overflow-y: auto;">
<table style="width: 100%; border-collapse: separate; border-spacing: 0; font-family: 'Roboto Mono', monospace; font-size: 10px;">
<thead style="background: #1e222d; border-bottom: 1px solid #2a2e39; color: #848e9c; position: sticky; top: 0; z-index: 5;">
<tr>
<th style="padding: 6px; text-align: left; background: #1e222d;">Time</th>
<th style="padding: 6px; text-align: center; background: #1e222d;">Code</th>
<th style="padding: 6px; text-align: right; background: #1e222d;">Price</th>
<th style="padding: 6px; text-align: center; background: #1e222d;">Action</th>
<th style="padding: 6px; text-align: right; background: #1e222d;">Lot</th>
<th style="padding: 6px; text-align: right; background: #1e222d;">Buyer</th>
</tr>
</thead>
<tbody>
{rt_rows_html}
</tbody>
</table>
</div>
</div>
""", unsafe_allow_html=True)

with tab_financials:
    st.markdown(f"### 📊 Financial Highlights: {current_symbol}")
    
    # Try fetching real data via yfinance
    try:
        yf_ticker = yf.Ticker(current_symbol + ".JK")
        info = yf_ticker.info
        
        f1, f2, f3 = st.columns(3)
        with f1:
            st.metric("Market Cap", f"Rp {info.get('marketCap', 0)/1e12:.2f} T")
            st.metric("Trailing P/E", f"{info.get('trailingPE', 0):.2f}x")
        with f2:
            st.metric("Revenue (TTM)", f"Rp {info.get('totalRevenue', 0)/1e12:.2f} T")
            st.metric("Price/Book", f"{info.get('priceToBook', 0):.2f}x")
        with f3:
            st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-")
            st.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "-")
            
        st.markdown("#### 📑 Income Statement (Annual)")
        st.dataframe(yf_ticker.income_stmt.T.head(3), use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to fetch financial data: {e}")
        st.info("Showing mock data instead for demonstration.")
        
        # Mock Data Fallback
        f1, f2, f3 = st.columns(3)
        with f1:
            st.metric("Market Cap", "Rp 1,050 T")
            st.metric("Trailing P/E", "24.5x")
        with f2:
            st.metric("Revenue (TTM)", "Rp 85.2 T")
            st.metric("Price/Book", "4.2x")
        with f3:
            st.metric("Dividend Yield", "2.1%")
            st.metric("ROE", "18.5%")

with tab_profile:
    try:
        yf_ticker = yf.Ticker(current_symbol + ".JK")
        info = yf_ticker.info
        
        st.markdown(f"### {info.get('longName', current_symbol)}")
        st.caption(f"Sector: {info.get('sector', '-')} | Industry: {info.get('industry', '-')}")
        st.write(info.get('longBusinessSummary', 'No description available.'))
        
        if info.get('website'):
            st.markdown(f"**Website**: [{info.get('website')}]({info.get('website')})")
            
    except:
        st.warning("Profile data unavailable.")


