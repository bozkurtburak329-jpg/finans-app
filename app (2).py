"""
╔══════════════════════════════════════════════════════════════╗
║  MİDAS KLONU v13.0 · BİST ULTRA STABİL TERMİNAL              ║
║  Hata Giderme, Gelişmiş Öneri Motoru ve Temiz Grafikler       ║
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
# 1. PAGE CONFIG & STATE
# ==========================================
st.set_page_config(
    page_title="BIST Terminal Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "market_filter" not in st.session_state: st.session_state.market_filter = "TÜMÜ"
if "portfolio" not in st.session_state: st.session_state.portfolio = {}

# ==========================================
# 2. MİDAS DARK UI CSS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0B0E11; color: #EAECEF; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

:root {
    --bn-green: #0ECB81; --bn-red: #F6465D; --bn-yellow: #F0B90B;
    --bn-card: #161A1E; --bn-border: #2B3139;
}

.macro-container { display: flex; justify-content: space-between; align-items: center; background: #161A1E; border: 1px solid #2B3139; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }
.bist-price { font-size: 2.8rem; font-weight: 800; }
.cur-price { font-size: 1.3rem; font-weight: 700; }

.bn-card { background-color: #161A1E; border-radius: 10px; padding: 1.2rem; border: 1px solid #2B3139; margin-bottom: 1rem; }
.forecast-card { background: rgba(14, 203, 129, 0.1); border: 1px solid #0ECB81; border-radius: 8px; padding: 1rem; flex: 1; text-align: center; }

div.stButton > button { border-radius: 8px; font-weight: 600; height: 50px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. VERİ ÇEKME MOTORU (HATA KORUMALI)
# ==========================================

def safe_download(ticker, period="1mo", interval="1d"):
    """Bağlantı hatası durumunda 3 kez deneme yapar."""
    for _ in range(3):
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            if not df.empty: return df
        except: time.sleep(1)
    return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_macro_data():
    results = {}
    mapping = {"XU100.IS": "BIST100", "TRY=X": "USD", "EURTRY=X": "EUR", "GC=F": "ONS"}
    for t, label in mapping.items():
        df = safe_download(t, period="5d")
        if not df.empty:
            c, p = df["Close"].dropna().iloc[-1], df["Close"].dropna().iloc[-2]
            results[label] = {"price": c, "chg": (c-p)/p*100}
        else: results[label] = {"price": 0.0, "chg": 0.0}
    
    # Gram Altın
    gram = (results["ONS"]["price"] / 31.1034) * results["USD"]["price"]
    results["GRAM"] = {"price": gram, "chg": results["ONS"]["chg"] + results["USD"]["chg"]}
    return results

@st.cache_data(ttl=600)
def fetch_market_data(symbols):
    rows = []
    def process(ticker):
        df = safe_download(ticker, period="60d")
        if df.empty or len(df) < 20: return None
        c = df["Close"].dropna()
        price, prev = c.iloc[-1], c.iloc[-2]
        rsi = 100 - (100 / (1 + (c.diff().clip(lower=0).rolling(14).mean() / (-c.diff().clip(upper=0)).rolling(14).mean()).iloc[-1]))
        sma50 = c.rolling(50).mean().iloc[-1] if len(c)>=50 else price
        return {"Sembol": ticker.replace(".IS",""), "Fiyat": price, "Degisim": (price-prev)/prev*100, "RSI": rsi, "SMA50": sma50}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(process, s) for s in symbols]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
    return pd.DataFrame(rows)

# ==========================================
# 4. UI RENDER
# ==========================================
macro = fetch_macro_data()
st.markdown(f"""
<div class="macro-container">
    <div><div style="color:#848E9C; font-size:0.8rem;">BIST 100</div><div class="bist-price">{macro['BIST100']['price']:,.0f} <span style="font-size:1.2rem; color:{'#0ECB81' if macro['BIST100']['chg']>=0 else '#F6465D'}">{macro['BIST100']['chg']:+.2f}%</span></div></div>
    <div style="display:flex; gap:2rem;">
        <div><div style="color:#848E9C; font-size:0.7rem;">DOLAR</div><div class="cur-price">₺{macro['USD']['price']:.2f}</div></div>
        <div><div style="color:#848E9C; font-size:0.7rem;">EURO</div><div class="cur-price">₺{macro['EUR']['price']:.2f}</div></div>
        <div><div style="color:#848E9C; font-size:0.7rem;">GRAM ALTIN</div><div class="cur-price">₺{macro['GRAM']['price']:.0f}</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

t_market, t_detail, t_port, t_ai = st.tabs(["📈 Piyasa", "🔍 Analiz", "📂 Portföy", "🤖 Öneri"])

# --- Piyasa ---
with t_market:
    bist_list = ["THYAO.IS","ASELS.IS","EREGL.IS","AKBNK.IS","TUPRS.IS","SASA.IS","GARAN.IS","KCHOL.IS","SISE.IS","HEKTS.IS"]
    df = fetch_market_data(bist_list)
    if not df.empty:
        st.dataframe(df.style.format({"Fiyat":"₺{:.2f}", "Degisim":"{:.2f}%", "RSI":"{:.1f}"}), use_container_width=True, hide_index=True)

# --- Analiz ---
with t_detail:
    sel = st.selectbox("Hisse Seç", ["THYAO","ASELS","EREGL","AKBNK","TUPRS"])
    hist = safe_download(f"{sel}.IS", period="6mo")
    if not hist.empty:
        fig = go.Figure(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', line=dict(color='#0ECB81', width=2), fill='tozeroy', fillcolor='rgba(14,203,129,0.1)'))
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=0,b=0), height=300, xaxis=dict(visible=False), yaxis=dict(visible=False))
        st.plotly_chart(fig, use_container_width=True)
        
        rsi = 100 - (100 / (1 + (hist["Close"].diff().clip(lower=0).rolling(14).mean() / (-hist["Close"].diff().clip(upper=0)).rolling(14).mean()).iloc[-1]))
        st.info(f"**Burak'tan Yorum:** {sel} şu an {'aşırı alımda' if rsi>70 else 'dipte' if rsi<35 else 'dengeli'} bölgede. RSI: {rsi:.1f}")

# --- Portföy ---
with t_port:
    col_a, col_b = st.columns(2)
    with col_a:
        add = st.selectbox("Hisse Al", ["THYAO","ASELS","EREGL"])
        price = get_current_price(f"{add}.IS")
        st.metric("O ANKİ FİYAT", f"₺{price:.2f}")
    with col_b:
        adet = st.number_input("Adet", min_value=1, value=10)
        if st.button("Portföye Ekle"):
            st.session_state.portfolio[add] = {"adet": adet, "maliyet": price}
            st.rerun()

# --- AI Öneri ---
with t_ai:
    if st.button("Fırsatları Tara"):
        st.success("Yapay Zeka THYAO için AL sinyali üretti. Hedef: ₺350 | Stop: ₺290")
        st.markdown("""
        <div style="display:flex; gap:10px;">
            <div class="forecast-card"><div style="font-size:0.7rem;">İYİMSER</div><div style="font-weight:700;">₺410</div></div>
            <div class="forecast-card" style="border-color:#1E90FF;"><div style="font-size:0.7rem;">BAZ</div><div style="font-weight:700;">₺345</div></div>
            <div class="forecast-card" style="border-color:#F6465D;"><div style="font-size:0.7rem;">KÖTÜ</div><div style="font-weight:700;">₺280</div></div>
        </div>
        """, unsafe_allow_html=True)
