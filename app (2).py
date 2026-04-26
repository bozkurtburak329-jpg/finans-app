"""
╔══════════════════════════════════════════════════════════════╗
║  MİDAS KLONU v16.0 · ABD BORSASI (WALL STREET) TERMİNALİ     ║
║  200+ ABD Hissesi, S&P 500 Endeksi, $ Bazlı Tam Simülasyon   ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures
import time

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Wall Street Analiz Terminali",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "market_filter" not in st.session_state:
    st.session_state.market_filter = "TÜMÜ"
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

# ==========================================
# 2. MİDAS DARK TEMA CSS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; background-color: #0B0E11; color: #EAECEF; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

:root {
    --bn-bg:       #0B0E11;
    --bn-card:     #161A1E;
    --bn-card2:    #1E2329;
    --bn-border:   #2B3139;
    --bn-green:    #0ECB81;
    --bn-red:      #F6465D;
    --bn-yellow:   #F0B90B;
    --bn-blue:     #1E90FF;
    --bn-muted:    #848E9C;
    --bn-white:    #EAECEF;
}

.macro-container {
    display: flex; justify-content: space-between; align-items: center;
    background: linear-gradient(135deg, #161A1E 0%, #0F1216 100%);
    border: 1px solid var(--bn-border); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;
}
.bist-box { display: flex; flex-direction: column; border-right: 1px solid var(--bn-border); padding-right: 2rem; min-width: 250px;}
.bist-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem; color: var(--bn-muted); letter-spacing: 0.1em; }
.bist-price { font-size: 2.8rem; font-weight: 800; color: var(--bn-white); line-height: 1.1; }
.bist-chg { font-size: 1.2rem; font-weight: 600; }

.currency-box { display: flex; gap: 2rem; padding-left: 1rem; flex-wrap: wrap;}
.cur-item { display: flex; flex-direction: column; }
.cur-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: var(--bn-muted); }
.cur-price { font-size: 1.5rem; font-weight: 700; color: var(--bn-white); }
.cur-chg { font-size: 0.9rem; font-weight: 600; }

.section-title { font-size: 1.2rem; font-weight: 700; color: var(--bn-white); border-bottom: 1px solid var(--bn-border); padding-bottom: 0.5rem; margin: 2rem 0 1rem 0; }
div.stButton > button { border-radius: 8px; border: 1px solid var(--bn-border); background-color: var(--bn-card2); color: var(--bn-white); font-weight: 600; transition: all 0.2s; }
div.stButton > button:hover { border-color: var(--bn-yellow); color: var(--bn-yellow); }

.bn-card { background-color: var(--bn-card); border-radius: 8px; padding: 1.2rem; border: 1px solid var(--bn-border); margin-bottom: 0.8rem; }
.bn-card-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: var(--bn-muted); text-transform: uppercase; margin-bottom: 0.4rem; }
.bn-card-value { font-size: 1.5rem; font-weight: 700; color: var(--bn-white); }

.forecast-card { background: linear-gradient(135deg, #0D1F12 0%, #0B1A10 100%); border: 1px solid #1B4332; border-radius: 8px; padding: 1.4rem; margin: 0.5rem 0; }
.forecast-card.base { background: linear-gradient(135deg, #0D1525 0%, #0B1220 100%); border-color: #1A3A6B; }
.forecast-card.bear { background: linear-gradient(135deg, #1A0A0D 0%, #160810 100%); border-color: #4A1020; }
.swap-card { background: linear-gradient(135deg, #2A0A10 0%, #160810 100%); border: 1px solid #5C1525; border-left: 4px solid var(--bn-red); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }

[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input { background-color: var(--bn-card2) !important; border: 1px solid var(--bn-border) !important; color: var(--bn-white) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. YARDIMCI FONKSİYONLAR & 200 ABD HİSSESİ
# ==========================================
us_symbols = [
    # Teknoloji & İletişim (Mega Cap)
    "AAPL","MSFT","NVDA","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL","CRM","AMD","INTC","IBM","TXN","QCOM","NFLX","ADBE","NOW","PYPL","CSCO",
    # Yarı İletkenler & Ekipman
    "AMAT","MU","LRCX","ADI","SNPS","CDNS","NXPI","KLAC","MCHP","MPWR","ON","SWKS",
    # Finans & Ödeme
    "JPM","BAC","WFC","C","GS","MS","V","MA","AXP","BLK","SCHW","SPGI","CME","CB","PGR","MMC","AON","ICE","USB","PNC","TFC","COF",
    # Sağlık & İlaç
    "JNJ","UNH","LLY","PFE","ABBV","MRK","TMO","ABT","DHR","BMY","AMGN","CVS","CI","ISRG","SYK","VRTX","ZTS","BDX","BSX","MCK","HUM","EWG","GILD",
    # Tüketim & Perakende
    "WMT","PG","KO","PEP","COST","MCD","NKE","SBUX","TGT","HD","LOW","TJX","PM","MO","MDLZ","CL","KMB","EL","SYY","KHC","DG","ROST",
    # Endüstri & Havacılık & Savunma
    "BA","CAT","HON","LMT","RTX","GE","MMM","DE","UPS","UNP","FDX","CSX","NSC","NOC","GD","ETN","WM","RSG","ITW","PH","PCAR","EMR",
    # Enerji
    "XOM","CVX","COP","SLB","EOG","OXY","MPC","PSX","VLO","WMB","KMI","BKR","HAL","HES","FANG",
    # İletişim & Eğlence & Yazılım
    "T","VZ","CMCSA","DIS","CHTR","TMUS","EA","TTWO","WBD","INTU","FIS","FI","GPN",
    # Otomotiv & Endüstriyel
    "F","GM","MAR","HLT","RCL","CCL","DAL","LUV",
    # Gayrimenkul (REITs)
    "PLD","AMT","EQIX","CCI","PSA","O","SPG",
    # Hammadde & Çeşitli
    "LIN","SHW","APD","ECL","NEM","FCX",
    # Kamu Hizmetleri (Utilities)
    "NEE","DUK","SO","SRE","AEP","D","EXC","XEL","ED","PEG"
]

# Sadece benzersiz olanları tut ve limit koy
us_symbols = list(dict.fromkeys(us_symbols))[:200]
TICKERS_US = {sym: sym for sym in us_symbols}

def fmt_usd(val):
    try:
        if pd.isna(val) or val == 0: return "—"
        return f"${float(val):,.2f}"
    except: return "—"

def format_number(num):
    try:
        val = float(num)
        if pd.isna(val): return "—"
        if val >= 1_000_000_000: return f"${val/1_000_000_000:.2f} B"
        if val >= 1_000_000: return f"${val/1_000_000:.2f} M"
        return f"${val:,.2f}"
    except: return "—"

def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain / loss.replace(0, np.nan)
        return round(float((100 - (100 / (1 + rs))).iloc[-1]), 1)
    except: return np.nan

def compute_macd(series, fast=12, slow=26, signal=9):
    try:
        ema_f = series.ewm(span=fast, adjust=False).mean()
        ema_s = series.ewm(span=slow, adjust=False).mean()
        macd  = ema_f - ema_s
        sig   = macd.ewm(span=signal, adjust=False).mean()
        return float(macd.iloc[-1]), float(sig.iloc[-1]), float((macd - sig).iloc[-1])
    except: return np.nan, np.nan, np.nan

def compute_atr(high, low, close, period=14):
    try:
        pc = close.shift(1)
        tr = pd.concat([high-low,(high-pc).abs(),(low-pc).abs()],axis=1).max(axis=1)
        return float(tr.rolling(period).mean().iloc[-1])
    except: return np.nan

def get_action_signal(rsi, price, sma50):
    if pd.isna(rsi): return "HOLD"
    if rsi < 35 and price > sma50: return "STRONG BUY"
    if rsi < 45: return "BUY"
    if rsi > 70: return "SELL"
    if rsi > 65 and price < sma50: return "STRONG SELL"
    return "HOLD"

def yil_sonu_tahmini(close_series, rsi, macd_hist, price, sma50):
    if len(close_series) < 60: return None
    returns = close_series.pct_change().dropna()
    mu, sigma = float(returns.mean()), float(returns.std())
    n_days = max(1, (datetime(datetime.today().year, 12, 31) - datetime.today()).days)
    
    score = 0.0
    if pd.notna(rsi):
        if rsi < 35: score += 0.4
        elif rsi > 70: score -= 0.4
    if pd.notna(macd_hist): score += 0.3 if macd_hist > 0 else -0.3
    if pd.notna(price) and pd.notna(sma50) and sma50 > 0: score += 0.3 if price > sma50 else -0.3
    
    mu_adj = mu + (score * 0.0008)
    np.random.seed(42)
    sim_returns = np.random.normal(mu_adj, sigma, (n_days, 1000))
    sim_paths = float(price) * np.exp(np.cumsum(sim_returns, axis=0))
    final_prices = sim_paths[-1]
    
    return {
        "bull": float(np.percentile(final_prices, 75)),
        "base": float(np.percentile(final_prices, 50)),
        "bear": float(np.percentile(final_prices, 25))
    }

# ==========================================
# 4. GÜVENLİ (YF.TICKER.HISTORY) VERİ ÇEKME
# ==========================================
def safe_history(ticker, period="1mo"):
    for _ in range(2):
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if not hist.empty and "Close" in hist.columns: return hist
        except: time.sleep(0.2)
    return pd.DataFrame()

def get_price_chg(df):
    if df is not None and not df.empty:
        closes = df["Close"].dropna()
        if len(closes) >= 2:
            c = float(closes.iloc[-1])
            p = float(closes.iloc[-2])
            return {"price": c, "chg": float((c - p) / p * 100)}
    return {"price": 0.0, "chg": 0.0}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_macro_data():
    macro = {}
    
    # S&P 500 ve NASDAQ Endeksleri
    macro["SP500"] = get_price_chg(safe_history("^GSPC", period="1mo"))
    macro["NASDAQ"] = get_price_chg(safe_history("^IXIC", period="1mo"))
    
    # Kurlar ve Altın
    macro["USDTRY"] = get_price_chg(safe_history("TRY=X", period="1mo"))
    macro["EURUSD"] = get_price_chg(safe_history("EURUSD=X", period="1mo"))
    macro["GOLD"] = get_price_chg(safe_history("GC=F", period="1mo"))
    
    return macro

@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    rows = []
    def process_ticker(ticker, name):
        hist = safe_history(ticker, period="3mo")
        if hist.empty or len(hist) < 50: return None
        close = hist["Close"].dropna()
        
        price = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close)>=50 else price
        rsi = compute_rsi(close)
        _, _, macd_h = compute_macd(close)
        
        return {
            "Sembol": name, "Fiyat ($)": price, "Değişim %": float((price - prev) / prev * 100), 
            "RSI": rsi, "MACD_H": macd_h, "Aksiyon": get_action_signal(rsi, price, sma50), "SMA50": sma50
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_US.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def get_detailed_data(ticker: str):
    stock = yf.Ticker(ticker)
    info, valid_news = {}, []
    try: info = stock.info
    except: pass
    hist = safe_history(ticker, period="6mo")
    try:
        for n in stock.news:
            if 'title' not in n or not n['title']: continue
            pub_ts = n.get('providerPublishTime')
            if not pub_ts or pub_ts < 1000000000: continue
            valid_news.append({
                'title': n['title'], 
                'link': n.get('link', f"https://finance.yahoo.com/quote/{ticker}"), 
                'publisher': n.get('publisher', 'Wall Street News'), 
                'date': datetime.fromtimestamp(pub_ts).strftime('%d %B %Y, %H:%M')
            })
    except: pass
    return info, hist, valid_news

@st.cache_data(ttl=60, show_spinner=False)
def get_current_price(ticker: str):
    hist = safe_history(ticker, period="1mo")
    if not hist.empty: return float(hist["Close"].dropna().iloc[-1])
    return 0.0

# ==========================================
# 5. UI RENDER: MAKRO BAR & SEKMELER
# ==========================================
st.markdown('<div class="app-header">ABD Borsası Analiz Terminali</div><div style="color:var(--bn-muted); margin-bottom:1rem; font-size:0.8rem; font-family:monospace;">// WALL STREET · PORTFÖY YÖNETİMİ · YAPAY ZEKA</div>', unsafe_allow_html=True)

macro = fetch_macro_data()

sp500_p = float(macro.get("SP500", {}).get("price", 0.0))
sp500_c = float(macro.get("SP500", {}).get("chg", 0.0))
sp_color = "#0ECB81" if sp500_c >= 0 else "#F6465D"
sp_sign = "+" if sp500_c >= 0 else ""

nasdaq_p = float(macro.get("NASDAQ", {}).get("price", 0.0))
nasdaq_c = float(macro.get("NASDAQ", {}).get("chg", 0.0))

def render_cur(title, key_name, prefix="", suffix=""):
    data = macro.get(key_name, {"price": 0.0, "chg": 0.0})
    p = float(data.get("price", 0.0))
    c = float(data.get("chg", 0.0))
    color = "#0ECB81" if c >= 0 else "#F6465D"
    sign = "+" if c >= 0 else ""
    return f"""<div class="cur-item">
        <div class="cur-title">{title}</div>
        <div class="cur-price">{prefix}{p:,.2f}{suffix}</div>
        <div class="cur-chg" style="color:{color}">{sign}{c:.2f}%</div>
    </div>"""

st.markdown(f"""
<div class="macro-container">
    <div class="bist-box">
        <div class="bist-title">S&P 500 ENDEKSİ</div>
        <div class="bist-price">{sp500_p:,.2f}</div>
        <div class="bist-chg" style="color:{sp_color}">{sp_sign}{sp500_c:.2f}%</div>
    </div>
    <div class="bist-box" style="border-right: none;">
        <div class="bist-title">NASDAQ ENDEKSİ</div>
        <div class="bist-price" style="font-size:2.2rem;">{nasdaq_p:,.2f}</div>
        <div class="bist-chg" style="color:{'#0ECB81' if nasdaq_c >= 0 else '#F6465D'}; font-size:1rem;">{'+' if nasdaq_c >= 0 else ''}{nasdaq_c:.2f}%</div>
    </div>
    <div class="currency-box" style="border-left: 1px solid var(--bn-border);">
        {render_cur("USD/TRY", "USDTRY", "₺")}
        {render_cur("EUR/USD", "EURUSD", "$")}
        {render_cur("ONS ALTIN", "GOLD", "$")}
    </div>
</div>
""", unsafe_allow_html=True)

tab_market, tab_detail, tab_portfolio, tab_recommend = st.tabs([
    "📈 ABD Piyasası", "🔍 Derin Analiz", "📂 Dolar Portföyüm", "🤖 AI Öneri Motoru"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PİYASA GÖRÜNÜMÜ               ║
# ╚══════════════════════════════════════════╝
with tab_market:
    with st.spinner("Wall Street verileri yükleniyor (200 Hisse)..."):
        df_market = fetch_market_data()

    if df_market.empty:
        st.error("Veri çekilemedi. İnternet bağlantınızı kontrol edin.")
    else:
        total_stocks = len(df_market)
        up_stocks = len(df_market[df_market["Değişim %"] > 0])
        down_stocks = len(df_market[df_market["Değişim %"] < 0])

        c1, c2, c3, c4 = st.columns([1, 1, 1, 0.5])
        with c1:
            if st.button(f"📊 Tüm Hisseler ({total_stocks})", use_container_width=True): st.session_state.market_filter = "TÜMÜ"
        with c2:
            if st.button(f"📈 Yükselenler ({up_stocks})", use_container_width=True): st.session_state.market_filter = "YÜKSELENLER"
        with c3:
            if st.button(f"📉 Düşenler ({down_stocks})", use_container_width=True): st.session_state.market_filter = "DÜŞENLER"
        with c4:
            if st.button("🔄 Yenile", use_container_width=True):
                st.cache_data.clear()
                st.session_state.market_filter = "TÜMÜ"
                st.rerun()

        df_filtered = df_market.copy()
        if st.session_state.market_filter == "YÜKSELENLER": df_filtered = df_filtered[df_filtered["Değişim %"] > 0]
        elif st.session_state.market_filter == "DÜŞENLER": df_filtered = df_filtered[df_filtered["Değişim %"] < 0]

        st.markdown(f'<div class="section-title">📋 Piyasa Görünümü ({st.session_state.market_filter})</div>', unsafe_allow_html=True)

        def style_df(df):
            styled = df.style.format({"Fiyat ($)": "${:,.2f}", "Değişim %": "{:+.2f}%", "RSI": "{:.1f}"}, na_rep="—")
            def color_change(val):
                if pd.isna(val): return ''
                return 'color: #00e676; font-weight:bold' if val > 0 else ('color: #ff3d00; font-weight:bold' if val < 0 else 'color: #8E8E93')
            def color_action(val):
                if "BUY" in str(val): return 'color: #00e676; font-weight:bold'
                if "SELL" in str(val): return 'color: #ff3d00; font-weight:bold'
                return 'color: #8E8E93'
            return styled.map(color_change, subset=['Değişim %']).map(color_action, subset=['Aksiyon'])

        st.dataframe(style_df(df_filtered[["Sembol", "Fiyat ($)", "Değişim %", "RSI", "Aksiyon"]]), use_container_width=True, height=500, hide_index=True)


# ╔══════════════════════════════════════════╗
# ║  SEKME 2: DERİN ANALİZ                  ║
# ╚══════════════════════════════════════════╝
with tab_detail:
    st.markdown('<div class="section-title">🔍 Detaylı Analiz & Yapay Zeka Yorumu</div>', unsafe_allow_html=True)
    selected_symbol = st.selectbox("İncelemek istediğiniz ABD hissesini seçin:", sorted(us_symbols), index=us_symbols.index("AAPL") if "AAPL" in us_symbols else 0)
    selected_ticker = selected_symbol

    if selected_ticker:
        info, hist, news = get_detailed_data(selected_ticker)
        if hist.empty or len(hist) < 5:
            st.warning(f"⚠️ {selected_symbol} için yeterli piyasa verisi bulunamadı.")
        else:
            close_data = hist["Close"].dropna()
            curr_p, prev_p = float(close_data.iloc[-1]), float(close_data.iloc[-2])
            chg, chg_p = curr_p - prev_p, ((curr_p - prev_p) / prev_p) * 100
            color_hex, sign = ("#00e676", "+") if chg >= 0 else ("#ff3d00", "")
            
            col1, col2 = st.columns([1.2, 2])
            with col1:
                st.markdown(f"""
                <div class="bn-card" style="height:100%; display:flex; flex-direction:column; justify-content:center;">
                    <h2 style="margin:0; font-size: 2.5rem; color: #FFF;">{selected_symbol}</h2>
                    <div style="font-size: 0.95rem; color: var(--bn-muted); margin-bottom: 1rem;">{info.get('longName', selected_symbol)}</div>
                    <div style="font-size: 3rem; font-weight: 800;">{fmt_usd(curr_p)}</div>
                    <div style="color: {color_hex}; font-size: 1.4rem; font-weight: 700;">{sign}{fmt_usd(chg).replace('$','')} ({sign}{chg_p:.2f}%)</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist.index, y=close_data, mode='lines', 
                    line=dict(color=color_hex, width=2), 
                    fill='tozeroy', fillcolor=f"rgba({0 if chg>=0 else 255}, {200 if chg>=0 else 61}, {83 if chg>=0 else 0}, 0.1)"
                ))
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                    margin=dict(l=0, r=0, t=10, b=0), height=220, 
                    xaxis=dict(showgrid=False, zeroline=False, visible=False), 
                    yaxis=dict(showgrid=False, zeroline=False, visible=False),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            m_cap = info.get("marketCap", np.nan)
            pe = info.get("trailingPE", np.nan)
            high_52 = float(hist["High"].max())
            low_52 = float(hist["Low"].min())
            
            rsi_14 = compute_rsi(close_data)
            sma50 = float(close_data.rolling(50).mean().iloc[-1]) if len(close_data) >= 50 else curr_p
            atr_14 = compute_atr(hist["High"].dropna(), hist["Low"].dropna(), close_data)
            target_price = float(curr_p + (2 * atr_14)) if pd.notna(atr_14) else np.nan

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="bn-card"><div class="bn-card-label">Piyasa Değeri</div><div class="bn-card-value">{format_number(m_cap)}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="bn-card"><div class="bn-card-label">F/K Oranı</div><div class="bn-card-value">{float(pe) if pd.notna(pe) else "—"}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="bn-card"><div class="bn-card-label">6 Aylık Zirve/Dip</div><div style="font-size:1.3rem; font-weight:700; color:#fff;">{fmt_usd(high_52)} / {fmt_usd(low_52)}</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="bn-card"><div class="bn-card-label">Kısa Vade Hedef (ATR)</div><div class="bn-card-value" style="color:#00e676;">{fmt_usd(target_price)}</div></div>', unsafe_allow_html=True)

            st.markdown("### 🧠 Burak'tan Yorumlar")
            trend_txt = f"{selected_symbol} hissesi şu an **{fmt_usd(curr_p)}** seviyesinden işlem görüyor ve 50 günlük hareketli ortalamasının ({fmt_usd(sma50)}) **{'üzerinde pozitif' if curr_p > sma50 else 'altında negatif'}** bir eğilim gösteriyor."
            st.info(f"**📊 Trend Analizi:**\n\n{trend_txt}")

            if pd.notna(rsi_14):
                if rsi_14 > 70:
                    st.error(f"**⚠️ Risk Durumu:**\n\nAmerikan hisse senedi piyasasında bu hisse **{rsi_14:.1f} RSI** değeri ile aşırı alım bölgesine girmiş durumda. İndikatörler teknik yorgunluğa işaret ediyor.")
                    st.warning("**🎯 Strateji:**\n\nYeni alımlar için risk barındırıyor. Olası bir düzeltme beklenmeli, mevcut karlar için stop-loss seviyeleri güncellenmelidir.")
                elif rsi_14 < 35:
                    st.success(f"**✅ Risk Durumu:**\n\n**{rsi_14:.1f} RSI** seviyesinde aşırı satım bölgesinde. Satış baskısının yavaşladığı ve Wall Street standartlarına göre ucuz fiyatlandığı bir bölgedeyiz.")
                    st.info("**🎯 Strateji:**\n\nTeknik bir dip arayışı mevcut. Buradan gelebilecek yukarı yönlü tepki alımları için kademeli maliyetlenme (DCA) stratejisi izlenebilir.")
                else:
                    st.warning(f"**⚠️ Risk Durumu:**\n\nHisse senedi **{rsi_14:.1f} RSI** değeri ile dengeli (nötr) bir seyir izliyor. Aşırı bir fiyatlama veya köpük bulunmuyor.")
                    st.info("**🎯 Strateji:**\n\nHisse yatay konsolidasyon sürecinde olabilir. 50 günlük ortalamanın üzerinde kalındığı sürece tutma (HOLD) stratejisi benimsenebilir.")

            st.markdown('<div class="section-title">📰 Güncel Haber Akışı (Wall Street)</div>', unsafe_allow_html=True)
            if news:
                for n in news[:5]:
                    st.markdown(f"""
                    <div class="news-item">
                        <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                        <div class="news-meta"><span>🏢 {n['publisher']}</span><span>🕒 {n['date']}</span></div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info(f"**{selected_symbol}** için son 24 saate ait doğrulanmış global haber akışı bulunamadı. Yahoo Finance üzerinden detayları inceleyebilirsiniz.")

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: PORTFÖY SİMÜLATÖRÜ            ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    st.markdown('<div class="section-title">Hisse Satın Al ($ Bazlı)</div>', unsafe_allow_html=True)

    pa, pb, pc = st.columns([2, 1, 1])
    with pa:
        add_sym = st.selectbox("Hangi ABD hissesini almak istiyorsun?", sorted(us_symbols))
    anlik_fiyat = get_current_price(add_sym)
    
    with pb:
        st.markdown(f"""
        <div style="background:#1A1C24; border:1px solid var(--bn-border); border-radius:8px; padding:0.5rem 1rem; margin-top:1.8rem; text-align:center;">
            <div style="font-size:0.7rem; color:#848E9C;">O ANKİ FİYAT</div>
            <div style="font-size:1.6rem; font-weight:700; color:#0ECB81;">{fmt_usd(anlik_fiyat)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with pc:
        add_adet = st.number_input("Kaç adet alacaksın?", min_value=1, value=10, step=1)
        add_maliyet = anlik_fiyat
        
    if st.button("Portföye Ekle", type="primary", use_container_width=True):
        st.session_state.portfolio[add_sym] = {"adet": int(add_adet), "maliyet": float(add_maliyet)}
        st.success(f"{add_sym} portföyüne başarıyla eklendi!")
        st.rerun()

    if st.session_state.portfolio:
        st.markdown('<div class="section-title">Mevcut Portföyüm & Yapay Zeka Uyarıları</div>', unsafe_allow_html=True)
        df_market = fetch_market_data()
        
        bad_stocks = []
        for sym, data in st.session_state.portfolio.items():
            adet, maliyet = data["adet"], data["maliyet"]
            
            market_row = df_market[df_market["Sembol"] == sym] if not df_market.empty else pd.DataFrame()
            if not market_row.empty:
                guncel_f = float(market_row.iloc[0]["Fiyat ($)"])
                aksiyon = market_row.iloc[0]["Aksiyon"]
                rsi = float(market_row.iloc[0]["RSI"])
                if "SELL" in aksiyon or rsi > 70:
                    bad_stocks.append({"sym": sym, "aksiyon": aksiyon, "rsi": rsi, "deger": adet * guncel_f})
            else:
                guncel_f = get_current_price(sym)
                
            t_guncel, t_yatirim = float(adet * guncel_f), float(adet * maliyet)
            kar = t_guncel - t_yatirim
            kar_pct = (kar / t_yatirim * 100) if t_yatirim > 0 else 0
            k_c = "#0ECB81" if kar >= 0 else "#F6465D"
            
            st.markdown(f"""
            <div class="bn-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div><span style="font-size:1.4rem; font-weight:700; color:var(--bn-yellow);">{sym}</span><span style="color:#848E9C; margin-left:1rem;">{adet} Adet | Maliyet: {fmt_usd(maliyet)}</span></div>
                <div style="text-align:right;"><div style="font-size:1.2rem; font-weight:700; color:#EAECEF;">{fmt_usd(t_guncel)}</div><div style="color:{k_c}; font-weight:600;">{'+' if kar>=0 else ''}{fmt_usd(kar).replace('$','')} ({'+' if kar_pct>=0 else ''}{kar_pct:.1f}%)</div></div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Sat ({sym})", key=f"del_{sym}"):
                del st.session_state.portfolio[sym]
                st.rerun()
                
        if bad_stocks and not df_market.empty:
            st.markdown('<div class="section-title">🔄 Portföy Optimizasyonu (Swap Önerisi)</div>', unsafe_allow_html=True)
            iyi_hisseler = df_market[(~df_market["Sembol"].isin(st.session_state.portfolio.keys())) & (df_market["Aksiyon"].isin(["STRONG BUY", "BUY"])) & (df_market["RSI"] < 50)].sort_values("RSI").head(3)
            
            for bad in bad_stocks:
                st.markdown(f"""
                <div class="swap-card">
                    <div style="color:#F6465D; font-weight:700; font-size:1.1rem; margin-bottom:0.5rem;">⚠️ {bad['sym']} Hissesinde Bozulma Tespit Edildi!</div>
                    <div style="color:#EAECEF; font-size:0.9rem; margin-bottom:1rem;">
                        <b>{bad['sym']}</b> teknik olarak yorgunluk belirtileri gösteriyor (Sinyal: {bad['aksiyon']}, RSI: {bad['rsi']:.1f}). 
                        Bunu satarak <b>{fmt_usd(bad['deger'])}</b> nakite geçebilir ve yükseliş trendindeki şu hisselere geçiş yapabilirsin:
                    </div>
                """, unsafe_allow_html=True)
                for _, iyi in iyi_hisseler.iterrows():
                    st.markdown(f"""<div style="background:#161A1E; padding:0.8rem; border-radius:6px; border:1px solid #2B3139; margin-bottom:0.5rem; display:flex; justify-content:space-between;">
                        <div><span style="color:#0ECB81; font-weight:700;">{iyi['Sembol']}</span> (RSI: {iyi['RSI']:.1f})</div><div style="color:#848E9C;">Sinyal: <span style="color:#0ECB81;">{iyi['Aksiyon']}</span></div>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: AKILLI ÖNERİ MOTORU           ║
# ╚══════════════════════════════════════════╝
with tab_recommend:
    st.markdown('<div class="section-title">🤖 Yapay Zeka Destekli Tarama & Yıl Sonu Simülasyonu</div>', unsafe_allow_html=True)

    r1, r2 = st.columns([1, 1])
    with r1:
        butce = st.number_input("Yatırım Bütçen Ne Kadar? (USD Doları)", min_value=100, value=5000, step=500)
    with r2:
        risk = st.selectbox("Risk Profilin", ["Düşük Risk (Mega Şirketler)", "Yüksek Risk (Fırsat Hisseleri)"])
        
    if st.button("Benim İçin En İyi ABD Hisselerini Bul", type="primary", use_container_width=True):
        with st.spinner("Wall Street taranıyor, hedef fiyatlar ve yıl sonu ihtimalleri hesaplanıyor..."):
            df_scan = fetch_market_data().copy()
            if "Düşük" in risk:
                guvenli = ["AAPL","MSFT","GOOGL","AMZN","JPM","JNJ","V","WMT","PG","XOM","UNH"]
                df_scan = df_scan[df_scan["Sembol"].isin(guvenli)]
            else:
                kucuk = ["TSLA","AMD","NVDA","PLTR","SNOW","CRWD","UBER","SQ","SHOP","COIN","RBLX"]
                df_scan = df_scan[df_scan["Sembol"].isin(kucuk)]
                
            df_scan = df_scan[df_scan["RSI"] < 55].sort_values("RSI", ascending=True).head(3)
            
            if df_scan.empty:
                st.warning("Şu anki piyasa koşullarında bu profile uygun güvenli bir 'AL' fırsatı bulunamadı.")
            else:
                hisse_basi_butce = float(butce / len(df_scan))
                st.success(f"Yapay Zeka {len(df_scan)} adet fırsat hissesi buldu! Her birine {fmt_usd(hisse_basi_butce)} ayırabilirsin.")
                
                for _, row in df_scan.iterrows():
                    sym, fiyat = row["Sembol"], float(row["Fiyat ($)"])
                    close_hist = safe_history(sym, period="1y")["Close"].dropna()
                    fc = yil_sonu_tahmini(close_hist, row["RSI"], row["MACD_H"], fiyat, row["SMA50"])
                    
                    hedef_fiyat = fiyat * 1.15
                    stop_loss = fiyat * 0.92
                    bekleme = "3 - 6 Ay" if "Düşük" in risk else "1 - 3 Ay"
                    
                    st.markdown(f"""
                    <div style="background:#161A1E; border:1px solid #2B3139; border-left:4px solid #0ECB81; border-radius:8px; padding:1.5rem; margin-bottom:1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                            <span style="font-size:1.6rem; font-weight:800; color:#EAECEF;">{sym}</span>
                            <span style="font-size:1.2rem; font-weight:600; color:#0ECB81;">Alım Fiyatı: {fmt_usd(fiyat)}</span>
                        </div>
                        
                        <div style="display:flex; gap:2rem; margin-bottom:1.5rem; background:#1E2329; padding:1rem; border-radius:6px;">
                            <div><div style="color:#848E9C; font-size:0.75rem;">HEDEF SATIŞ FİYATI</div><div style="color:#0ECB81; font-weight:700; font-size:1.1rem;">{fmt_usd(hedef_fiyat)}</div></div>
                            <div><div style="color:#848E9C; font-size:0.75rem;">ZARAR KES (STOP-LOSS)</div><div style="color:#F6465D; font-weight:700; font-size:1.1rem;">{fmt_usd(stop_loss)}</div></div>
                            <div><div style="color:#848E9C; font-size:0.75rem;">TAHMİNİ BEKLEME SÜRESİ</div><div style="color:#F0B90B; font-weight:700; font-size:1.1rem;">{bekleme}</div></div>
                        </div>
                        
                        <div style="color:#848E9C; font-size:0.9rem; margin-bottom:1rem;">
                            <b>Neden Önerildi?</b> RSI seviyesi {row['RSI']:.1f} ile oldukça uygun. Teknik indikatörler <b>{row['Aksiyon']}</b> sinyali veriyor.
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if fc:
                        b_val, bl_val, br_val = float((hisse_basi_butce / fiyat) * fc["base"]), float((hisse_basi_butce / fiyat) * fc["bull"]), float((hisse_basi_butce / fiyat) * fc["bear"])
                        st.markdown(f"""
                        <div style="font-size:0.8rem; color:#848E9C; text-transform:uppercase; margin-bottom:0.5rem;">Yıl Sonuna Kadar Kazanç Olasılıkları ({fmt_usd(hisse_basi_butce)} Yatırım İçin)</div>
                        <div style="display:flex; gap:1rem;">
                            <div class="forecast-card" style="flex:1;"><div style="color:#0ECB81; font-size:0.8rem;">İyimser Senaryo</div><div style="font-size:1.3rem; font-weight:700; color:#EAECEF;">{fmt_usd(bl_val)}</div></div>
                            <div class="forecast-card base" style="flex:1;"><div style="color:#1E90FF; font-size:0.8rem;">Ortalama Beklenti</div><div style="font-size:1.3rem; font-weight:700; color:#EAECEF;">{fmt_usd(b_val)}</div></div>
                            <div class="forecast-card bear" style="flex:1;"><div style="color:#F6465D; font-size:0.8rem;">Kötü Senaryo</div><div style="font-size:1.3rem; font-weight:700; color:#EAECEF;">{fmt_usd(br_val)}</div></div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
