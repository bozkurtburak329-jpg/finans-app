"""
╔══════════════════════════════════════════════════════════════╗
║  MİDAS KLONU v11.0 · BİST KANTİTATİF ANALİZ & TERMİNALİ      ║
║  Tüm Sekmeler Aktif, Canlı Kurlar Düzeltildi, Tam Sürüm      ║
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
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="BIST Analiz Terminali",
    page_icon="📈",
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0B0E11; color: #EAECEF; }
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

/* Makro Veri Paneli (Top Bar) */
.macro-container {
    display: flex; justify-content: space-between; align-items: center;
    background: linear-gradient(135deg, #161A1E 0%, #0F1216 100%);
    border: 1px solid var(--bn-border); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;
}
.bist-box { display: flex; flex-direction: column; border-right: 1px solid var(--bn-border); padding-right: 2rem; }
.bist-title { font-family: monospace; font-size: 0.9rem; color: var(--bn-muted); letter-spacing: 0.1em; }
.bist-price { font-size: 3rem; font-weight: 800; color: var(--bn-white); line-height: 1.1; }
.bist-chg { font-size: 1.2rem; font-weight: 600; }

.currency-box { display: flex; gap: 2rem; padding-left: 1rem; flex-wrap: wrap;}
.cur-item { display: flex; flex-direction: column; }
.cur-title { font-family: monospace; font-size: 0.75rem; color: var(--bn-muted); }
.cur-price { font-size: 1.4rem; font-weight: 700; color: var(--bn-white); }
.cur-chg { font-size: 0.85rem; font-weight: 600; }

/* Genel Stiller */
.section-title { font-size: 1.2rem; font-weight: 700; color: var(--bn-white); border-bottom: 1px solid var(--bn-border); padding-bottom: 0.5rem; margin: 2rem 0 1rem 0; }
div.stButton > button { border-radius: 8px; border: 1px solid var(--bn-border); background-color: var(--bn-card2); color: var(--bn-white); font-weight: 600; transition: all 0.2s; }
div.stButton > button:hover { border-color: var(--bn-yellow); color: var(--bn-yellow); }
.bn-card { background-color: var(--bn-card); border-radius: 8px; padding: 1.2rem; border: 1px solid var(--bn-border); margin-bottom: 0.8rem; }
.bn-card-label { font-family: monospace; font-size: 0.7rem; color: var(--bn-muted); text-transform: uppercase; margin-bottom: 0.4rem; }
.bn-card-value { font-size: 1.5rem; font-weight: 700; color: var(--bn-white); }

/* Haber Stilleri */
.news-item { background-color: var(--bn-card); border: 1px solid var(--bn-border); border-left: 3px solid #3a3a3c; padding: 1.2rem; margin-bottom: 0.8rem; border-radius: 8px; }
.news-item:hover { border-left-color: var(--bn-green); }
.news-title { font-size: 1.05rem; font-weight: 600; color: #FFFFFF; text-decoration: none; display: block; margin-bottom: 0.5rem; }
.news-title:hover { color: var(--bn-green); }
.news-meta { font-size: 0.8rem; color: var(--bn-muted); display: flex; justify-content: space-between; }

/* Simülasyon ve Swap Kartları */
.forecast-card { background: linear-gradient(135deg, #0D1F12 0%, #0B1A10 100%); border: 1px solid #1B4332; border-radius: 8px; padding: 1.4rem; margin: 0.5rem 0; }
.forecast-card.base { background: linear-gradient(135deg, #0D1525 0%, #0B1220 100%); border-color: #1A3A6B; }
.forecast-card.bear { background: linear-gradient(135deg, #1A0A0D 0%, #160810 100%); border-color: #4A1020; }
.swap-card { background: linear-gradient(135deg, #2A0A10 0%, #160810 100%); border: 1px solid #5C1525; border-left: 4px solid var(--bn-red); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }

[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input { background-color: var(--bn-card2) !important; border: 1px solid var(--bn-border) !important; color: var(--bn-white) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BIST SEMBOL LİSTESİ VE MATEMATİK FONKSİYONLARI
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","KCHOL","SAHOL","DOHOL","ALARK",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","SISE","ARCLK","VESTL",
    "FROTO","TOASO","DOAS","OTKAR","THYAO","PGSUS","BIMAS","MGROS","SOKM","AEFES",
    "TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS","ENJSA","AKSEN","ZOREN","EKGYO"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

def fmt_tl(val):
    if pd.isna(val) or val == 0: return "—"
    return f"₺{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
    if pd.isna(rsi): return "TUT"
    if rsi < 35 and price > sma50: return "GÜÇLÜ AL"
    if rsi < 45: return "AL"
    if rsi > 70: return "SAT"
    if rsi > 65 and price < sma50: return "GÜÇLÜ SAT"
    return "TUT"

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
    sim_paths = price * np.exp(np.cumsum(sim_returns, axis=0))
    final_prices = sim_paths[-1]
    
    return {
        "bull": float(np.percentile(final_prices, 75)),
        "base": float(np.percentile(final_prices, 50)),
        "bear": float(np.percentile(final_prices, 25))
    }

# ==========================================
# 4. VERİ ÇEKME FONKSİYONLARI (Makro Hata Düzeltildi)
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_macro_data():
    macro = {}
    tickers = {"XU100.IS": "BIST100", "TRY=X": "USD", "EURTRY=X": "EUR", "GC=F": "GOLD_ONS"}
    
    def get_data(t):
        try:
            df = yf.download(t, period="1mo", progress=False) # Hata fix: 1mo yapılarak tatil günleri aşıldı
            if not df.empty:
                close_col = df["Close"].dropna()
                if len(close_col) >= 2:
                    c, p = float(close_col.iloc[-1]), float(close_col.iloc[-2])
                    return {"price": c, "chg": (c - p) / p * 100}
        except: return {"price": 0.0, "chg": 0.0}
        return {"price": 0.0, "chg": 0.0}

    with concurrent.futures.ThreadPoolExecutor() as ex:
        results = list(ex.map(get_data, tickers.keys()))
    
    for i, t in enumerate(tickers.values()): macro[t] = results[i]
    
    # Gram Altın Hesaplama (Ons fiyatından TL'ye)
    try:
        ons, usd = macro["GOLD_ONS"]["price"], macro["USD"]["price"]
        if ons > 0 and usd > 0:
            gram = (ons / 31.1034768) * usd
            macro["GRAM_ALTIN"] = {"price": gram, "chg": macro["GOLD_ONS"]["chg"] + macro["USD"]["chg"]}
        else:
            macro["GRAM_ALTIN"] = {"price": 0.0, "chg": 0.0}
    except: macro["GRAM_ALTIN"] = {"price": 0.0, "chg": 0.0}
    
    return macro

@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    end, start = datetime.today(), datetime.today() - timedelta(days=90)
    rows = []
    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 55: return None
            close = df["Close"].squeeze()
            price, prev = float(close.iloc[-1]), float(close.iloc[-2])
            sma50, rsi = float(close.rolling(50).mean().iloc[-1]), compute_rsi(close)
            _, _, macd_h = compute_macd(close)
            return {"Sembol": name, "Fiyat (TL)": price, "Değişim %": (price - prev) / prev * 100, 
                    "RSI": rsi, "MACD_H": macd_h, "Aksiyon": get_action_signal(rsi, price, sma50), "SMA50": sma50}
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def get_detailed_data(ticker: str):
    stock = yf.Ticker(ticker)
    info, hist, valid_news = {}, pd.DataFrame(), []
    try: info, hist = stock.info, stock.history(period="1y")
    except: pass
    
    try:
        for n in stock.news:
            if 'title' not in n or not n['title']: continue
            pub_ts = n.get('providerPublishTime')
            if not pub_ts or pub_ts < 1000000000: continue
            valid_news.append({'title': n['title'], 'link': n.get('link', f"https://finance.yahoo.com/quote/{ticker}"), 'publisher': n.get('publisher', 'Finans Kaynağı'), 'date': datetime.fromtimestamp(pub_ts).strftime('%d %B %Y, %H:%M')})
    except: pass
    return info, hist, valid_news

@st.cache_data(ttl=60, show_spinner=False)
def get_current_price(ticker: str):
    try:
        df = yf.download(ticker, period="5d", progress=False)
        if not df.empty: return float(df["Close"].dropna().iloc[-1])
    except: return 0.0
    return 0.0

@st.cache_data(ttl=900, show_spinner=False)
def get_historical_close(ticker: str):
    try:
        df = yf.download(ticker, period="1y", progress=False)
        if not df.empty: return df["Close"].dropna().squeeze()
    except: return pd.Series(dtype=float)
    return pd.Series(dtype=float)

# ==========================================
# 5. UI RENDER: MAKRO BAR & SEKMELER
# ==========================================
macro = fetch_macro_data()

def render_cur(title, data, prefix=""):
    c = "#0ECB81" if data['chg'] >= 0 else "#F6465D"
    s = "+" if data['chg'] >= 0 else ""
    return f"""<div class="cur-item">
        <div class="cur-title">{title}</div>
        <div class="cur-price">{prefix}{data['price']:,.2f}</div>
        <div class="cur-chg" style="color:{c}">{s}{data['chg']:.2f}%</div>
    </div>"""

bist = macro.get("BIST100", {"price":0, "chg":0})
b_c = "#0ECB81" if bist['chg'] >= 0 else "#F6465D"
b_s = "+" if bist['chg'] >= 0 else ""

st.markdown(f"""
<div class="macro-container">
    <div class="bist-box">
        <div class="bist-title">BIST 100 ENDEKSİ</div>
        <div class="bist-price">{bist['price']:,.2f}</div>
        <div class="bist-chg" style="color:{b_c}">{b_s}{bist['chg']:.2f}%</div>
    </div>
    <div class="currency-box">
        {render_cur("USD/TRY", macro.get("USD", {"price":0, "chg":0}), "₺")}
        {render_cur("EUR/TRY", macro.get("EUR", {"price":0, "chg":0}), "₺")}
        {render_cur("GRAM ALTIN", macro.get("GRAM_ALTIN", {"price":0, "chg":0}), "₺")}
    </div>
</div>
""", unsafe_allow_html=True)

# EKSİK OLAN SEKMELER GERİ GELDİ
tab_market, tab_detail, tab_portfolio, tab_recommend = st.tabs([
    "📈 Piyasa Görünümü", "🔍 Derin Analiz", "📂 Portföy Simülatörü", "🤖 Akıllı Öneri Motoru"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PİYASA GÖRÜNÜMÜ               ║
# ╚══════════════════════════════════════════╝
with tab_market:
    with st.spinner("Piyasa verileri yükleniyor..."):
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
            styled = df.style.format({"Fiyat (TL)": "₺{:,.2f}", "Değişim %": "{:+.2f}%", "RSI": "{:.1f}"}, na_rep="—")
            def color_change(val):
                if pd.isna(val): return ''
                return 'color: #00e676; font-weight:bold' if val > 0 else ('color: #ff3d00; font-weight:bold' if val < 0 else 'color: #8E8E93')
            def color_action(val):
                if "AL" in str(val): return 'color: #00e676; font-weight:bold'
                if "SAT" in str(val): return 'color: #ff3d00; font-weight:bold'
                return 'color: #8E8E93'
            return styled.map(color_change, subset=['Değişim %']).map(color_action, subset=['Aksiyon'])

        st.dataframe(style_df(df_filtered[["Sembol", "Fiyat (TL)", "Değişim %", "RSI", "Aksiyon"]]), use_container_width=True, height=400, hide_index=True)


# ╔══════════════════════════════════════════╗
# ║  SEKME 2: DERİN ANALİZ                  ║
# ╚══════════════════════════════════════════╝
with tab_detail:
    st.markdown('<div class="section-title">🔍 Detaylı Analiz & Yapay Zeka Yorumu</div>', unsafe_allow_html=True)
    selected_symbol = st.selectbox("İncelemek istediğiniz hisseyi seçin:", sorted(bist_symbols), index=bist_symbols.index("THYAO") if "THYAO" in bist_symbols else 0)
    selected_ticker = f"{selected_symbol}.IS"

    if selected_ticker:
        info, hist, news = get_detailed_data(selected_ticker)
        if not hist.empty:
            curr_p, prev_p = float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
            chg, chg_p = curr_p - prev_p, ((curr_p - prev_p) / prev_p) * 100
            color_hex, sign = ("#00e676", "+") if chg >= 0 else ("#ff3d00", "")
            
            col1, col2 = st.columns([1.2, 2])
            with col1:
                st.markdown(f"""
                <div class="bn-card" style="height:100%; display:flex; flex-direction:column; justify-content:center;">
                    <h2 style="margin:0; font-size: 2.5rem; color: #FFF;">{selected_symbol}</h2>
                    <div style="font-size: 0.95rem; color: var(--bn-muted); margin-bottom: 1rem;">{info.get('longName', selected_symbol)}</div>
                    <div style="font-size: 3rem; font-weight: 800;">{fmt_tl(curr_p)}</div>
                    <div style="color: {color_hex}; font-size: 1.4rem; font-weight: 700;">{sign}{fmt_tl(chg)} ({sign}{chg_p:.2f}%)</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', line=dict(color=color_hex, width=3), fill='tozeroy', fillcolor=f"rgba({0 if chg>=0 else 255}, {200 if chg>=0 else 61}, {83 if chg>=0 else 0}, 0.15)"))
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=10, b=0), height=220, xaxis=dict(visible=False), yaxis=dict(visible=False))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            m_cap, pe = info.get("marketCap", np.nan), info.get("trailingPE", np.nan)
            high_52, low_52 = info.get("fiftyTwoWeekHigh", hist["High"].max()), info.get("fiftyTwoWeekLow", hist["Low"].min())
            rsi_14 = compute_rsi(hist["Close"])
            sma50 = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else curr_p
            atr_14 = compute_atr(hist["High"], hist["Low"], hist["Close"])
            target_price = curr_p + (2 * atr_14) if pd.notna(atr_14) else np.nan

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="bn-card"><div class="bn-card-label">Piyasa Değeri</div><div class="bn-card-value">{format_number(m_cap)}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="bn-card"><div class="bn-card-label">F/K Oranı</div><div class="bn-card-value">{pe if pd.notna(pe) else "—"}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="bn-card"><div class="bn-card-label">52H Zirve / Dip</div><div style="font-size:1.3rem; font-weight:700; color:#fff;">{fmt_tl(high_52)} / {fmt_tl(low_52)}</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="bn-card"><div class="bn-card-label">Kısa Vade Hedef (ATR)</div><div class="bn-card-value" style="color:#00e676;">{fmt_tl(target_price)}</div></div>', unsafe_allow_html=True)

            # BURAK'TAN YORUMLAR
            st.markdown("### 🧠 Burak'tan Yorumlar")
            trend_txt = f"{selected_symbol} hissesi şu an **{fmt_tl(curr_p)}** seviyesinden işlem görüyor ve 50 günlük hareketli ortalamasının ({fmt_tl(sma50)}) **{'üzerinde pozitif' if curr_p > sma50 else 'altında negatif'}** bir eğilim gösteriyor."
            st.info(f"**📊 Trend Analizi:**\n\n{trend_txt}")

            if pd.notna(rsi_14):
                if rsi_14 > 70:
                    st.error(f"**⚠️ Risk Durumu:**\n\nHisse senedi **{rsi_14:.1f} RSI** değeri ile aşırı alım bölgesine girmiş durumda. İndikatörler teknik yorgunluğa işaret ediyor.")
                    st.warning("**🎯 Strateji:**\n\nYeni alımlar için risk barındırıyor. Olası bir düzeltme beklenmeli, mevcut karlar için stop-loss seviyeleri güncellenmelidir.")
                elif rsi_14 < 35:
                    st.success(f"**✅ Risk Durumu:**\n\n**{rsi_14:.1f} RSI** seviyesinde aşırı satım bölgesinde. Satış baskısının yavaşladığı ve hissenin ucuz fiyatlandığı bir bölgedeyiz.")
                    st.info("**🎯 Strateji:**\n\nTeknik bir dip arayışı mevcut. Buradan gelebilecek yukarı yönlü tepki alımları için kademeli maliyetlenme stratejisi izlenebilir.")
                else:
                    st.warning(f"**⚠️ Risk Durumu:**\n\nHisse senedi **{rsi_14:.1f} RSI** değeri ile dengeli (nötr) bir seyir izliyor. Aşırı bir fiyatlama veya köpük bulunmuyor.")
                    st.info("**🎯 Strateji:**\n\nHisse yatay konsolidasyon sürecinde olabilir. 50 günlük ortalamanın üzerinde kalındığı sürece tutma stratejisi benimsenebilir.")

            # HABER SİSTEMİ
            st.markdown('<div class="section-title">📰 Güncel Haber Akışı</div>', unsafe_allow_html=True)
            if news:
                for n in news[:5]:
                    st.markdown(f"""
                    <div class="news-item">
                        <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                        <div class="news-meta"><span>🏢 {n['publisher']}</span><span>🕒 {n['date']}</span></div>
                    </div>""", unsafe_allow_html=True)
            else
