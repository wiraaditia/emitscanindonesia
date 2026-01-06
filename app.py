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

# --- CONFIG DASHBOARD ---
st.set_page_config(page_title="EmitScan Indonesia", page_icon="favicon.png", layout="wide")

# --- CUSTOM CSS STOCKBIT STYLE ---
# --- CUSTOM CSS PREMIUM DARK STYLE ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Reset & Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0b0e11 !important; /* Deep dark background */
        color: #e0e0e0 !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #15191e !important;
        border-right: 1px solid #2d343c;
    }
    
    /* Main Container */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    /* Metrics / Cards */
    div[data-testid="stMetric"] {
        background-color: #1e2329;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #2d343c;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 12px !important;
        color: #848e9c !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
        color: #f0b90b !important; /* Binance Yellow for contrast */
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #2962ff; /* TradingView Blue */
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #1e53e5;
        box-shadow: 0 2px 8px rgba(41, 98, 255, 0.4);
    }
    
    /* Table Styling */
    [data-testid="stCheck"] { color: #848e9c; }
    
    div[data-testid="stDataFrame"] {
        border: none !important;
    }
    
    /* Dataframe Header */
    thead tr th {
        background-color: #15191e !important;
        color: #848e9c !important;
        font-size: 13px !important;
        border-bottom: 1px solid #2d343c !important;
    }
    
    /* Dataframe Cells */
    tbody tr td {
        background-color: #0b0e11 !important;
        color: #eaecef !important;
        font-size: 13px !important;
        border-bottom: 1px solid #2d343c !important;
    }
    
    /* News Feed Styles */
    .news-card {
        background-color: #15191e;
        border: 1px solid #2d343c;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .news-title {
        font-size: 14px;
        font-weight: 600;
        color: #eaecef;
        margin-bottom: 8px;
        text-decoration: none;
    }
    .news-title:hover {
        color: #2962ff;
    }
    
    .news-meta {
        font-size: 11px;
        color: #848e9c;
    }
    
    /* Sentiment Badges */
    .badge-bullish {
        background-color: rgba(0, 230, 118, 0.15);
        color: #00e676;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        border: 1px solid rgba(0, 230, 118, 0.3);
    }
    
    .badge-bearish {
        background-color: rgba(255, 82, 82, 0.15);
        color: #ff5252;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        border: 1px solid rgba(255, 82, 82, 0.3);
    }

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
            pbv = stock.info.get('priceToBook', 0)
        except: 
            pbv = 0
        return hist, pbv
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
    hist, pbv = data
    
    curr_price = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2]
    chg_pct = ((curr_price - prev_close) / prev_close) * 100
    
    curr_vol = hist['Volume'].iloc[-1]
    avg_vol = hist['Volume'].mean()
    vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 0
    
    ma5 = hist['Close'].tail(5).mean()
    ma20 = hist['Close'].tail(20).mean()
    
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
# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("## 📊 Screener Filters")
    
    # Ticker Selection
    chart_options = ["COMPOSITE"] + [t.replace('.JK', '') for t in TICKERS]
    st.selectbox("Select Ticker:", chart_options, key="ticker_selector")
    
    # Timeframe Selection
    timeframe_map = {
        "Daily": "D", "Weekly": "W", "Monthly": "M",
        "4 Hours": "240", "1 Hour": "60", "30 Minutes": "30", "5 Minutes": "5"
    }
    if 'chart_timeframe' not in st.session_state: st.session_state.chart_timeframe = "Daily"
    st.selectbox("Timeframe:", list(timeframe_map.keys()), key="chart_timeframe")
    
    st.markdown("---")
    
    # Action Buttons
    if st.button("RUN SCREENER", type="primary", use_container_width=True):
        st.session_state.run_screener = True
        st.session_state.active_tab = "🔬 Research & News"
    
    if st.button("CLEAR RESULTS", use_container_width=True):
        st.session_state.scan_results = None
        st.rerun()
        
    st.markdown("---")
    
    # Status Indicators
    st.caption(f"Last Update: {st.session_state.get('last_update', '-')}")
    st.caption(f"Assets: {len(TICKERS)} Stocks")

# --- MAIN LAYOUT ---

# --- MAIN LAYOUT ---

# Programmatic Navigation (Custom Tabs)
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📈 Market Dashboard"

# Custom CSS for Radio Buttons to look like Tabs
st.markdown("""
<style>
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    div.row-widget.stRadio > div > label {
        background-color: #1e2329;
        padding: 10px 20px;
        border-radius: 8px;
        border: 1px solid #2d343c;
        cursor: pointer;
        transition: all 0.2s;
        font-weight: 600;
        color: #848e9c;
    }
    div.row-widget.stRadio > div > label:hover {
        background-color: #2d343c;
        color: #e0e0e0;
    }
    div.row-widget.stRadio > div > label[data-baseweb="radio"] {
        background-color: transparent;
    }
    /* Hide the default radio circle */
    div.row-widget.stRadio div[role="radio"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Navigation Control
current_tab = st.radio(
    "", 
    ["📈 Market Dashboard", "🔬 Research & News"], 
    key="active_tab", 
    label_visibility="collapsed"
)

if current_tab == "📈 Market Dashboard":
    # Top Header & Metrics
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown("### 📈 Market Overview")
    with c2:
        st.metric("IHSG", "7,350.12", "+0.45%")
    with c3:
        st.metric("Sentiment", "BULLISH", "Strong Inflow")
    
    # Chart Section (Full Width)
    current_symbol = st.session_state.ticker_selector
    current_tf_code = timeframe_map[st.session_state.chart_timeframe]
    tv_symbol = "IDX:COMPOSITE" if current_symbol == "COMPOSITE" else f"IDX:{current_symbol}"
    
    st.components.v1.html(
    f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": 500,
        "symbol": "{tv_symbol}",
        "interval": "{current_tf_code}",
        "timezone": "Asia/Jakarta",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """,
    height=500,
)

st.write("") # Spacer

st.write("") 

# --- SCANNER LOGIC ---
if 'scan_results' not in st.session_state:
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
            st.success(f"Scan Completed. Found {len(st.session_state.scan_results[st.session_state.scan_results['Status'] != 'HOLD'])} potential assets.")
        else:
            st.warning("No data fetched or no match found.")
            st.session_state.scan_results = None

# --- DISPLAY RESULTS FROM STATE ---
# --- DISPLAY LOGIC ---
if current_tab == "🔬 Research & News":
    # 1. Check Data Availability
    if st.session_state.scan_results is None:
        st.info("Silakan jalankan 'RUN SCREENER' di sidebar terlebih dahulu untuk melihat data riset.")
    else:
        df = st.session_state.scan_results
        
        # 2. TABLE SECTION (FULL WIDTH)
        st.markdown("### 📋 Screened Stocks Result")
        
        # Highlight Function
        def format_row(row):
            color = ''
            if 'STRONG BUY' in row['Status']: color = 'background-color: rgba(0, 230, 118, 0.1)'
            elif 'WATCHLIST' in row['Status']: color = 'background-color: rgba(255, 193, 7, 0.1)'
            return [color] * len(row)

        # Display Options
        st.dataframe(
            df.style.apply(format_row, axis=1).format({
                "Price": "Rp {:,.0f}", 
                "Change %": "{:+.2f}%", 
                "Vol Ratio": "{:.1f}x",
                "PBV": "{:.2f}x"
            }), 
            use_container_width=True,
            column_order=["Ticker", "Status", "Price", "Change %", "Vol Ratio", "PBV", "MA Trend", "Sentiment"],
            height=500
        )
        
        st.caption("Tip: Klik tombol 'Load Chart' di tab Research untuk analisis per saham.")
        st.markdown("---")
        df = st.session_state.scan_results
        st.markdown("### 📰 AI News & Deep Analysis")
        
        # Use Expander for each stock to keep UI clean
        for i, row in df.iterrows():
            if row['Status'] != 'HOLD': 
                with st.expander(f"{row['Ticker']} - {row['Status']} ({row['Sentiment']})", expanded=False):
                    # Layout: 2 Columns (News vs Analysis)
                    c_news, c_analysis = st.columns([1, 1])
                    
                    with c_news:
                        st.markdown("#### 📰 Latest News")
                        # Main Headline
                        st.info(f"**Headline**: {row['Headline']}")
                        
                        # Sentiment Bar
                        score = row['Sentiment Score']
                        st.progress(score / 100.0, text=f"Sentiment Score: {score}/100")
                        
                        # Timeline
                        if row['News List']:
                            for news_item in row['News List'][:3]:
                                st.caption(f"{news_item.get('source','').upper()} • {news_item.get('date','')}")
                                st.markdown(f"[{news_item.get('title')}]({news_item.get('link')})")
                                st.markdown("---")
                                
                        st.button(f"📈 Load Chart: {row['Ticker']}", key=f"btn_{i}", on_click=set_ticker, args=(row['Ticker'],))

                    with c_analysis:
                        st.markdown("#### 🤖 AI Analysis")
                        st.write(row['Analysis'])
                        
                        st.markdown("#### 📊 Key Indicators")
                        k1, k2, k3 = st.columns(3)
                        k1.metric("Trend", row['MA Trend'])
                        k2.metric("Vol Ratio", f"{row['Raw Vol Ratio']:.1f}x")
                        k3.metric("PBV", f"{row['Raw PBV']:.2f}x")
                        
                        # Recommendation
                        if 'STRONG BUY' in row['Status']:
                            st.success("**RECOMMENDATION: BUY**\n\nTrend Bullish + High Volume + Positive Sentiment.")
                        else:
                            st.warning("**RECOMMENDATION: WATCH**\n\nMonitor for breakout or volume confirmation.")

# Footer
st.markdown("""
<br><br>
<div style="text-align: center; color: #666; font-size: 12px;">
    &copy; 2026 EmitScan Indonesia. Data provided by Yahoo Finance (Delayed 15m). <br>
    Developed by <strong style="color: #00c853">Wira Aditia</strong> | <a href="https://instagram.com/wiirak_" style="color: #00c853; text-decoration: none;">@wiirak_</a>
</div>
""", unsafe_allow_html=True)
