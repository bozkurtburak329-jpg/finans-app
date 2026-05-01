"""
Burak Borsa Terminal PRO v11.0 (Cloud Native Edition)
- Sıfır Kütüphane Hatası (Scikit-Learn Kaldırıldı, Saf Algoritma Eklendi)
- Asenkron Kantitatif Veri Motoru
- Profesyonel Candlestick Grafikleri
- Modern Streamlit Arayüzü
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# 1. SAYFA AYARLARI VE CSS
# ==========================================
st.set_page_config(page_title="Burak Borsa Terminal PRO", page_icon="🦅", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background-color: #1E2329; border: 1px solid #2B3139;
        border-radius: 8px; padding: 15px; text-align: center;
    }
    .metric-title { font-size: 0.85rem; color: #848E9C; text-transform: uppercase; letter-spacing: 1px;}
    .metric-value { font-size: 1.5rem; font-weight: bold; color: #EAECEF; margin: 5px 0;}
    .metric-change.positive { color: #0ECB81; font-weight: bold; }
    .metric-change.negative { color: #F6465D; font-weight: bold; }
    .ai-box { background-color: #161A1E; padding: 20px; border-left: 5px solid #F0B90B; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

if "portfolio" not in st.session_state: st.session_state.portfolio = {}

# Hızlı tarama için optimize edilmiş BIST listesi
BIST_SYMBOLS = [
    "THYAO", "ISCTR", "KCHOL", "TUPRS", "GARAN", "AKBNK", "YKBNK", "EREGL", 
    "ASELS", "SAHOL", "BIMAS", "SISE", "FROTO", "TOASO", "TCELL", "ENKAI", 
    "PETKM", "PGSUS", "SASA", "HEKTS", "ASTOR", "ALARK"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in BIST_SYMBOLS}

# ==========================================
# 2. KANTİTATİF MOTOR (VERİ & İNDİKATÖR)
# ==========================================
@st.cache_data(ttl=300)
def fetch_macro_data():
    tickers = {"XU100.IS": "BIST 100", "USDTRY=X": "USD/TRY", "GC=F": "ALTIN (ONS)"}
    res = {}
    for t, name in tickers.items():
        try:
            df = yf.download(t, period="5d", progress=False)
            if not df.empty and len(df) >= 2:
                curr = float(df['Close'].iloc[-1].iloc[0]) if isinstance(df['Close'], pd.DataFrame) else float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2].iloc[0]) if isinstance(df['Close'], pd.DataFrame) else float(df['Close'].iloc[-2])
                res[name] = {"price": curr, "chg": ((curr - prev) / prev) * 100}
            else: res[name] = {"price": 0.0, "chg": 0.0}
        except: res[name] = {"price": 0.0, "chg": 0.0}
    
    try:
        ons = res.get("ALTIN (ONS)", {}).get("price", 0)
        usd = res.get("USD/TRY", {}).get("price", 0)
        res["GRAM ALTIN"] = {"price": (ons * usd) / 31.10, "chg": res.get("ALTIN (ONS)", {}).get("chg", 0)}
    except: pass
    return res

def calculate_technical_indicators(df):
    close = df['Close'].squeeze()
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMA
    df['EMA20'] = close.ewm(span=20, adjust=False).mean()
    df['EMA50'] = close.ewm(span=50, adjust=False).mean()
    return df.dropna()

@st.cache_data(ttl=600)
def fetch_market_snapshot():
    end = datetime.today()
    start = end - timedelta(days=60)
    rows = []

    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            if df.empty or len(df) < 20: return None
            close = df['Close'].squeeze()
            curr_p = float(close.iloc[-1])
            prev_p = float(close.iloc[-2])
            
            delta = close.diff().dropna()
            gain = delta.clip(lower=0).rolling(14).mean().iloc[-1]
            loss = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + (gain / loss))) if loss != 0 else 50
            
            return {
                "Sembol": name,
                "Fiyat": curr_p,
                "Değişim": ((curr_p - prev_p) / prev_p) * 100,
                "RSI": rsi,
                "Hacim": float(df['Volume'].squeeze().iloc[-1])
            }
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            if f.result(): rows.append(f.result())
            
    return pd.DataFrame(rows)

# ==========================================
# 3. KANTİTATİF ALGORİTMİK BEYİN (NO SKLEARN)
# ==========================================
def algorithmic_ai_decision(price, rsi, ema20, ema50):
    """
    Dış kütüphane gerektirmeyen, matematiksel ağırlıklandırma algoritması.
    Scikit-learn modelinin yaptığı risk/getiri skorlamasını taklit eder.
    """
    score = 0
    
    # Trend Analizi
    if price > ema50: score += 2  # Uzun vade pozitif
    else: score -= 2
    
    if ema20 > ema50: score += 1  # Kısa vade ivme pozitif
    else: score -= 1
    
    # RSI Momentum Analizi
    if rsi < 30: score += 3       # Aşırı satım, fırsat bölgesi
    elif 30 <= rsi < 45: score += 1 # Toparlanma emaresi
    elif 45 <= rsi <= 60: score += 0 # Nötr bölge
    elif 60 < rsi <= 70: score -= 1 # Isınma bölgesi
    elif rsi > 70: score -= 3     # Aşırı alım, düzeltme riski
    
    # Karar Mekanizması
    if score >= 3: return "GÜÇLÜ YÜKSELİŞ BEKLENTİSİ 🟢"
    elif 1 <= score < 3: return "YÜKSELİŞ EĞİLİMİ ↗️"
    elif score == 0: return "YATAY SEYİR (NÖTR) ⚪"
    elif -2 <= score < 0: return "DÜŞÜŞ EĞİLİMİ ↘️"
    else: return "GÜÇLÜ DÜŞÜŞ RİSKİ 🔴"

# ==========================================
# 4. ARAYÜZ (UI)
# ==========================================
st.title("Burak Borsa Terminali PRO 🦅")
st.caption("Saf Algoritmik Kantitatif Sinyal Motoru (Cloud-Native)")

# Makro Veriler
macro_data = fetch_macro_data()
m_cols = st.columns(4)
for col, (name, data) in zip(m_cols, macro_data.items()):
    val, chg = data['price'], data['chg']
    color = "positive" if chg >= 0 else "negative"
    sign = "+" if chg >= 0 else ""
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{name}</div>
            <div class="metric-value">{val:,.2f}</div>
            <div class="metric-change {color}">{sign}{chg:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.write("---")

tab_market, tab_ai, tab_portfolio = st.tabs(["📊 Piyasa Taraması", "🧠 Derin Algoritma Analizi", "💼 Portföy Yönetimi"])

# SEKME 1: PİYASA
with tab_market:
    st.subheader("BIST Profesyonel Tarama Ekranı")
    with st.spinner("Piyasa verileri çekiliyor... (Birkaç saniye sürebilir)"):
        df_market = fetch_market_snapshot()
        
        if not df_market.empty:
            st.dataframe(
                df_market.sort_values("Değişim", ascending=False),
                column_config={
                    "Sembol": st.column_config.TextColumn("Hisse", width="medium"),
                    "Fiyat": st.column_config.NumberColumn("Fiyat (TL)", format="%.2f ₺"),
                    "Değişim": st.column_config.NumberColumn("Günlük Değişim (%)", format="%.2f%%"),
                    "Hacim": st.column_config.NumberColumn("Hacim", format="%d"),
                    "RSI": st.column_config.ProgressColumn("RSI (14)", format="%.1f", min_value=0, max_value=100)
                },
                use_container_width=True, hide_index=True, height=500
            )

# SEKME 2: YAPAY ZEKA & GRAFİK
with tab_ai:
    st.subheader("Algoritmik Karar Destek Sistemi")
    c1, c2 = st.columns([1, 3])
    
    with c1:
        sel_sym = st.selectbox("Hisse Seçin:", BIST_SYMBOLS)
    
    with st.spinner(f"{sel_sym} için algoritmalar hesaplanıyor..."):
        df_hist = yf.download(f"{sel_sym}.IS", period="6mo", progress=False)
        
        if not df_hist.empty:
            df_hist = calculate_technical_indicators(df_hist)
            curr_p = float(df_hist['Close'].squeeze().iloc[-1])
            rsi_val = float(df_hist['RSI'].squeeze().iloc[-1])
            ema20_val = float(df_hist['EMA20'].squeeze().iloc[-1])
            ema50_val = float(df_hist['EMA50'].squeeze().iloc[-1])
            
            # SKLEARN YERİNE YENİ ALGORİTMA KULLANILIYOR
            ai_decision = algorithmic_ai_decision(curr_p, rsi_val, ema20_val, ema50_val)
            
            with c1:
                st.markdown(f"""
                <div class="ai-box">
                    <b>[ALGORİTMA RAPORU]</b><br><br>
                    <b>Varlık:</b> {sel_sym}<br>
                    <b>Fiyat:</b> {curr_p:.2f} TL<br>
                    <b>RSI (14):</b> {rsi_val:.1f}<br><br>
                    <b>Algoritma Kararı:</b><br>
                    <span style="font-size:1.1rem;font-weight:bold;">{ai_decision}</span>
                </div>
                """, unsafe_allow_html=True)
                
            with c2:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df_hist.index,
                    open=df_hist['Open'].squeeze(), high=df_hist['High'].squeeze(),
                    low=df_hist['Low'].squeeze(), close=df_hist['Close'].squeeze(),
                    name='Fiyat'
                ))
                fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['EMA20'].squeeze(), line=dict(color='orange', width=1.5), name='EMA 20'))
                fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['EMA50'].squeeze(), line=dict(color='blue', width=1.5), name='EMA 50'))

                fig.update_layout(
                    title=f"{sel_sym} Teknik Görünüm", yaxis_title='Fiyat (TL)',
                    template='plotly_dark', height=450, margin=dict(l=0, r=0, t=40, b=0),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)

# SEKME 3: PORTFÖY
with tab_portfolio:
    st.subheader("Portföy Yönetimi")
    p1, p2, p3, p4 = st.columns([2, 1, 1, 1])
    
    with p1: add_sym = st.selectbox("Portföye Ekle:", BIST_SYMBOLS)
    with p2: add_price = st.number_input("Maliyet (TL)", min_value=0.01, value=10.0)
    with p3: add_qty = st.number_input("Adet", min_value=1, value=100)
    with p4:
        st.write("")
        if st.button("➕ Ekle", use_container_width=True):
            st.session_state.portfolio[add_sym] = {"Adet": add_qty, "Maliyet": add_price}
            st.rerun()

    if st.session_state.portfolio:
        st.write("### Varlık Dağılımı")
        pf_df = pd.DataFrame.from_dict(st.session_state.portfolio, orient='index')
        pf_df['Toplam Maliyet'] = pf_df['Adet'] * pf_df['Maliyet']
        st.dataframe(pf_df, use_container_width=True)
        if st.button("🗑️ Tümünü Sil"):
            st.session_state.portfolio = {}
            st.rerun()
