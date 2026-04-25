"""
╔══════════════════════════════════════════════════════════════╗
║  MİDAS KLONU v8.0 · BİST KANTİTATİF ANALİZ & HABER TERMİNALİ ║
║  Geliştirici: Burak Can Bozkurt                              ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures

# ==========================================
# 1. PAGE CONFIGURATION & MIDAS UI CSS
# ==========================================
st.set_page_config(
    page_title="BIST Analiz Terminali",
    page_icon="🇹🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Fontlar ve Temel Renkler */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0E1117; /* Midas Koyu Tema */
    color: #F5F5F5;
}

/* Değişkenler */
:root {
    --midas-green: #00c853;
    --midas-red: #ff3d00;
    --midas-bg: #0E1117;
    --midas-card: #1A1C24;
    --midas-border: #2B2D36;
    --midas-text-muted: #8E8E93;
}

/* Kart Stilleri */
.metric-container {
    display: flex; gap: 1rem; margin-bottom: 2rem;
}
.midas-metric-card {
    flex: 1; background-color: var(--midas-card); border: 1px solid var(--midas-border);
    border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column;
}
.metric-title { font-size: 0.85rem; color: var(--midas-text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 0.5rem; }
.metric-value { font-size: 2rem; font-weight: 800; color: #FFFFFF; }

.section-title { font-size: 1.25rem; font-weight: 700; margin: 2rem 0 1rem 0; color: #FFFFFF; border-bottom: 1px solid var(--midas-border); padding-bottom: 0.5rem; }

/* Burak'tan Yorumlar AI Kartı */
.ai-card {
    background: linear-gradient(145deg, #1A1C24 0%, #12141A 100%);
    border-left: 4px solid #3b82f6; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;
}
.ai-title { color: #60a5fa; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; display: flex; align-items: center; gap: 8px;}
.ai-section { margin-bottom: 1rem; }
.ai-section-title { font-size: 0.95rem; font-weight: 600; color: #E0E0E0; margin-bottom: 0.3rem;}
.ai-section-text { font-size: 0.9rem; color: #A1A1A6; line-height: 1.5; }

/* Haber Stilleri (1970 Bug Fix & Modern UI) */
.news-item {
    background-color: var(--midas-card); border: 1px solid var(--midas-border);
    border-left: 3px solid #3a3a3c; padding: 1.2rem; margin-bottom: 0.8rem; border-radius: 8px; transition: 0.2s;
}
.news-item:hover { background-color: #242631; border-left-color: var(--midas-green); }
.news-title { font-size: 1.05rem; font-weight: 600; color: #FFFFFF; text-decoration: none; display: block; margin-bottom: 0.5rem; line-height: 1.4; }
.news-title:hover { color: var(--midas-green); }
.news-meta { font-size: 0.8rem; color: var(--midas-text-muted); display: flex; justify-content: space-between; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BIST TICKER LIST (Genişletilmiş)
# ==========================================
bist_symbols = [
    "AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "HALKB", "ALBRK", "SKBNK", "TSKB", "KLNMA",
    "KCHOL", "SAHOL", "DOHOL", "ALARK", "ENKAI", "AGHOL", "TKFEN", "NTHOL", "GLYHO", "POLHO",
    "EREGL", "KRDMD", "TUPRS", "PETKM", "SASA", "HEKTS", "GUBRF", "SISE", "ARCLK", "VESTL",
    "BRISA", "GOODY", "CIMSA", "AKCNS", "OYAKC", "NUHCM", "BTCIM", "AFYON", "GOLTS", "BSOKE",
    "FROTO", "TOASO", "DOAS", "OTKAR", "KARSN", "ASUZU", "TMSN", "TTRAK",
    "THYAO", "PGSUS", "TAVHL", "CLEBI", "DOCO",
    "BIMAS", "MGROS", "SOKM", "AEFES", "CCOLA", "ULKER", "TATGD", "TUKAS", "PNSUT", "PETUN", "KERVT",
    "TCELL", "TTKOM", "ASELS", "ASTOR", "KONTR", "ALFAS", "ENJSA", "AKSEN", "ODAS", "SMARTG",
    "EUPWR", "MIATK", "GESAN", "CWENE", "YEOTK", "GWIND", "NATEN", "MAGEN", "AYDEM", "CANTE",
    "EKGYO", "ISGYO", "TRGYO", "HLGYO", "VKGYO", "DZGYO", "SNGYO", "ZRGYO", "PSGYO", "RYGYO",
    "KORDS", "VESBE", "AYGAZ", "AYEN", "ZOREN", "AKSA", "DEVA", "SELEC", "LKMNH", "RTALB",
    "MPARK", "ENSRI", "VAKKO", "YATAS", "AKFGY", "AKGRT", "ANSGR"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

# ==========================================
# 3. HELPER & TECHNICAL FUNCTIONS
# ==========================================
def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    val = (100 - (100 / (1 + rs))).iloc[-1]
    return round(float(val), 1) if pd.notna(val) else np.nan

def get_action_signal(rsi, price, sma50):
    if pd.isna(rsi): return "TUT"
    if rsi < 35 and price > sma50: return "GÜÇLÜ AL"
    if rsi < 45: return "AL"
    if rsi > 70: return "SAT"
    if rsi > 65 and price < sma50: return "GÜÇLÜ SAT"
    return "TUT"

# ==========================================
# 4. DATA FETCHING (Multithreaded & Cached)
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    end = datetime.today()
    start = end - timedelta(days=90)
    rows = []

    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 55: return None
            
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            chg_pct = (price - prev_price) / prev_price * 100
            
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            action = get_action_signal(rsi, price, sma50)
            
            return {
                "Sembol": name, 
                "Fiyat (₺)": price, 
                "Değişim %": chg_pct, 
                "RSI": rsi, 
                "Aksiyon": action,
                "SMA50_Durum": price > sma50
            }
        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None: rows.append(res)

    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def get_detailed_data(ticker: str):
    stock = yf.Ticker(ticker)
    info, hist = {}, pd.DataFrame()
    try:
        info = stock.info
        hist = stock.history(period="1y")
    except: pass
    
    # Haberler (1970 Bug Fix - Custom Parser)
    valid_news = []
    try:
        raw_news = stock.news
        for n in raw_news:
            if 'title' not in n or not n['title']: continue
            pub_ts = n.get('providerPublishTime')
            # 1970 bug önlemi: timestamp çok eskiyse yoksay
            if not pub_ts or pub_ts < 1000000000: continue 
            
            pub_date = datetime.fromtimestamp(pub_ts).strftime('%d %B %Y, %H:%M')
            valid_news.append({
                'title': n['title'],
                'link': n.get('link', f"https://finance.yahoo.com/quote/{ticker}"),
                'publisher': n.get('publisher', 'Finans Kaynağı'),
                'date': pub_date
            })
    except: pass

    return info, hist, valid_news

# ==========================================
# 5. UI & DASHBOARD RENDER
# ==========================================
st.markdown('<div class="app-header">🇹🇷 BIST Terminali</div>', unsafe_allow_html=True)

with st.spinner("Piyasa verileri yükleniyor..."):
    df_market = fetch_market_data()

if df_market.empty:
    st.error("Veri çekilemedi. İnternet bağlantınızı kontrol edin.")
    st.stop()

# --- METRİKLER ---
total_stocks = len(df_market)
up_stocks = len(df_market[df_market["Değişim %"] > 0])
down_stocks = len(df_market[df_market["Değişim %"] < 0])

st.markdown(f"""
<div class="metric-container">
    <div class="midas-metric-card">
        <div class="metric-title">Takip Edilen Varlık</div>
        <div class="metric-value">{total_stocks} Hisse</div>
    </div>
    <div class="midas-metric-card" style="border-left: 4px solid var(--midas-green);">
        <div class="metric-title">Yükselenler</div>
        <div class="metric-value" style="color: var(--midas-green);">{up_stocks}</div>
    </div>
    <div class="midas-metric-card" style="border-left: 4px solid var(--midas-red);">
        <div class="metric-title">Düşenler</div>
        <div class="metric-value" style="color: var(--midas-red);">{down_stocks}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SİDEBAR (Filtreleme & Arama) ---
with st.sidebar:
    st.markdown("### 🔍 Arama ve Filtreler")
    search_query = st.text_input("Hisse Ara (Örn: THYAO)").upper()
    action_filter = st.multiselect("Aksiyon Sinyali", ["GÜÇLÜ AL", "AL", "SAT", "GÜÇLÜ SAT", "TUT"], default=["GÜÇLÜ AL", "AL", "SAT", "GÜÇLÜ SAT", "TUT"])
    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Dataframe Filtreleme Uygulaması
df_filtered = df_market.copy()
if search_query:
    df_filtered = df_filtered[df_filtered["Sembol"].str.contains(search_query)]
if action_filter:
    df_filtered = df_filtered[df_filtered["Aksiyon"].isin(action_filter)]

# --- TABLO ---
st.markdown('<div class="section-title">📋 Genel Piyasa Görünümü</div>', unsafe_allow_html=True)

def style_df(df):
    styled = df.style.format({
        "Fiyat (₺)": "₺{:,.2f}",
        "Değişim %": "{:+.2f}%",
        "RSI": "{:.1f}"
    }, na_rep="—")
    
    def color_change(val):
        if pd.isna(val): return ''
        return 'color: #00c853; font-weight:bold' if val > 0 else ('color: #ff3d00; font-weight:bold' if val < 0 else 'color: #8E8E93')
    
    def color_action(val):
        if "AL" in str(val): return 'color: #00c853; font-weight:bold'
        if "SAT" in str(val): return 'color: #ff3d00; font-weight:bold'
        return 'color: #8E8E93'

    styled = styled.map(color_change, subset=['Değişim %'])
    styled = styled.map(color_action, subset=['Aksiyon'])
    return styled

st.dataframe(
    style_df(df_filtered[["Sembol", "Fiyat (₺)", "Değişim %", "RSI", "Aksiyon"]]), 
    use_container_width=True, 
    height=400, 
    hide_index=True
)

# --- DETAYLI ANALİZ & BURAK'TAN YORUMLAR ---
st.markdown('<div class="section-title">🔮 Detaylı Hisse Analizi & Yapay Zeka Yorumu</div>', unsafe_allow_html=True)

selected_symbol = st.selectbox("İncelemek istediğiniz hisseyi seçin:", sorted(bist_symbols), index=bist_symbols.index("THYAO") if "THYAO" in bist_symbols else 0)
selected_ticker = f"{selected_symbol}.IS"

if selected_ticker:
    info, hist, news = get_detailed_data(selected_ticker)
    
    if not hist.empty:
        curr_p = float(hist["Close"].iloc[-1])
        prev_p = float(hist["Close"].iloc[-2])
        chg = curr_p - prev_p
        chg_p = (chg / prev_p) * 100
        color_hex = "#00c853" if chg >= 0 else "#ff3d00"
        
        # Mini Grafik & Fiyat
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div style="background-color: var(--midas-card); border-radius: 12px; padding: 2rem; border: 1px solid var(--midas-border);">
                <h2 style="margin:0; font-size: 2.5rem; color: #FFF;">{selected_symbol}</h2>
                <div style="color: {color_hex}; font-size: 1.5rem; font-weight: 700; margin-top: 0.5rem;">
                    ₺{curr_p:,.2f} <span style="font-size: 1.1rem;">({chg:+.2f} / {chg_p:+.2f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', line=dict(color=color_hex, width=3), fill='tozeroy', fillcolor=f"rgba({0 if chg>=0 else 255}, {200 if chg>=0 else 61}, {83 if chg>=0 else 0}, 0.1)"))
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=10, b=0), height=180, xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # --- BURAK'TAN YORUMLAR (AI ANALYSIS) ---
        rsi_14 = compute_rsi(hist["Close"])
        sma50 = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else curr_p
        
        # Yapay Zeka Metin Üretimi
        trend_txt = f"Hisse 50 günlük ortalamasının (₺{sma50:.2f}) {'üzerinde pozitif' if curr_p > sma50 else 'altında zayıf'} bir eğilim gösteriyor. Kısa-orta vadeli momentum {'yükseliş' if curr_p > sma50 else 'düşüş'} yönlü."
        risk_txt = "Şu an nötr bölgede, aşırı risk barındırmıyor."
        opp_txt = "Kademeli alım / tutma stratejisi izlenebilir."

        if rsi_14 > 70:
            risk_txt = f"⚠️ YÜKSEK RİSK: RSI {rsi_14:.1f} seviyesinde. Hisse aşırı alım bölgesinde, sert kar satışları ve düzeltmeler gelebilir."
            opp_txt = "Yeni maliyetlenmeler için riskli. Mevcut pozisyonlar için kar al (take-profit) seviyeleri belirlenmeli."
        elif rsi_14 < 35:
            risk_txt = f"DÜŞÜK RİSK: RSI {rsi_14:.1f} seviyesi ile aşırı satım bölgesinde. Satış baskısı azalmış olabilir."
            opp_txt = "🎯 FIRSAT: Teknik bir dip oluşumu mevcut. Destek seviyelerinden kademeli alım ve yukarı yönlü tepki (rebound) ticareti için fırsat sunuyor."

        st.markdown(f"""
        <div class="ai-card">
            <div class="ai-title">🤖 Burak'tan Yorumlar</div>
            
            <div class="ai-section">
                <div class="ai-section-title">📈 Trend Analizi</div>
                <div class="ai-section-text">{trend_txt}</div>
            </div>
            
            <div class="ai-section">
                <div class="ai-section-title">⚠️ Risk Durumu</div>
                <div class="ai-section-text" style="color: {'#fca5a5' if rsi_14 > 70 else '#A1A1A6'}">{risk_txt}</div>
            </div>
            
            <div class="ai-section">
                <div class="ai-section-title">🎯 Fırsat & Beklenti</div>
                <div class="ai-section-text" style="color: {'#86efac' if rsi_14 < 35 else '#A1A1A6'}">{opp_txt}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- HABER SİSTEMİ (BUG FIX UYGULANDI) ---
        st.markdown('<div class="section-title">📰 Güncel Haber Akışı</div>', unsafe_allow_html=True)
        
        if news and len(news) > 0:
            for n in news[:5]:
                st.markdown(f"""
                <div class="news-item">
                    <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                    <div class="news-meta">
                        <span>🏢 {n['publisher']}</span>
                        <span>🕒 {n['date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Haber bulunamazsa şık bir Fallback Kartı
            st.markdown(f"""
            <div class="news-item" style="border-left-color: #3b82f6;">
                <div class="news-title">Güncel Haber Bulunamadı</div>
                <div style="color: #A1A1A6; font-size: 0.9rem; margin-top: 0.5rem; line-height: 1.5;">
                    Uluslararası veri ağlarında <b>{selected_symbol}</b> için son 24 saate ait haber akışı tespit edilemedi. Şirket gelişmelerini doğrudan incelemek için aşağıdaki bağlantıları kullanabilirsiniz.
                </div>
                <div style="margin-top: 1rem; display:flex; gap: 10px;">
                    <a href="https://tr.tradingview.com/symbols/BIST-{selected_symbol}/news/" target="_blank" style="color: #60a5fa; text-decoration: none; font-size:0.85rem; font-weight:600;">🔗 TradingView Haberleri</a>
                    <a href="https://www.kap.org.tr/tr/arama/bilesik?bildirimTipleri=OzelDurumAciklamasi&sirketler={selected_symbol}" target="_blank" style="color: #60a5fa; text-decoration: none; font-size:0.85rem; font-weight:600;">🔗 KAP Bildirimleri</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("Bu hisse senedi için detaylı veri çekilemedi.")
