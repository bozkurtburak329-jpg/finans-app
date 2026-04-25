"""
BIST Analiz Terminali v4.0
- Binance Dark Tema
- Portfoy Simulatoru (Yil Sonu Tahmini)
- Beyin Takimi Analizi
- Haber Sistemi
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
    st.session_state.portfolio = {}   # {symbol: {adet, maliyet}}
if "portfolio_name" not in st.session_state:
    st.session_state.portfolio_name = "Portfoyum 2025"

# ==========================================
# 2. BİNANCE DARK TEMA CSS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* ── Temel ── */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0B0E11;
    color: #EAECEF;
}
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

/* ── Binance renk değişkenleri ── */
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

/* ── Header ── */
.app-header {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--bn-white);
    letter-spacing: -0.01em;
    padding: 1rem 0 0.2rem 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
.app-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--bn-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* ── Section title ── */
.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--bn-white);
    border-bottom: 1px solid var(--bn-border);
    padding-bottom: 0.5rem;
    margin: 2rem 0 1rem 0;
    letter-spacing: -0.01em;
}

/* ── Filtre butonları ── */
div.stButton > button {
    height: 70px;
    border-radius: 8px;
    border: 1px solid var(--bn-border);
    background-color: var(--bn-card2);
    color: var(--bn-white);
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.2s;
    letter-spacing: -0.01em;
}
div.stButton > button:hover {
    border-color: var(--bn-yellow);
    background-color: #252930;
    color: var(--bn-yellow);
}

/* ── Kart ── */
.bn-card {
    background-color: var(--bn-card);
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    border: 1px solid var(--bn-border);
    margin-bottom: 0.8rem;
}
.bn-card-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: var(--bn-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.4rem;
}
.bn-card-value {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--bn-white);
    letter-spacing: -0.02em;
}
.bn-card-value.green { color: var(--bn-green); }
.bn-card-value.red   { color: var(--bn-red); }
.bn-card-value.yellow{ color: var(--bn-yellow); }

/* ── Beyin Takimi AI Kart ── */
.brain-card {
    background: linear-gradient(135deg, #161A1E 0%, #0F1216 100%);
    border: 1px solid #2B3139;
    border-left: 3px solid var(--bn-yellow);
    border-radius: 8px;
    padding: 1.6rem;
    margin: 1rem 0;
}
.brain-header {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--bn-yellow);
    margin-bottom: 1.2rem;
    letter-spacing: -0.01em;
}
.brain-section {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #1E2329;
}
.brain-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.brain-section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--bn-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}
.brain-section-text {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.9rem;
    color: #C7CBD1;
    line-height: 1.65;
}

/* ── Fiyat Tahmin Kart ── */
.forecast-card {
    background: linear-gradient(135deg, #0D1F12 0%, #0B1A10 100%);
    border: 1px solid #1B4332;
    border-radius: 8px;
    padding: 1.4rem;
    margin: 0.5rem 0;
}
.forecast-card.bear {
    background: linear-gradient(135deg, #1A0A0D 0%, #160810 100%);
    border-color: #4A1020;
}
.forecast-card.base {
    background: linear-gradient(135deg, #0D1525 0%, #0B1220 100%);
    border-color: #1A3A6B;
}

/* ── Portfoy Kart ── */
.portfolio-card {
    background-color: var(--bn-card2);
    border: 1px solid var(--bn-border);
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 0.6rem;
}
.portfolio-ticker {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1rem;
    font-weight: 600;
    color: var(--bn-yellow);
}
.portfolio-detail {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--bn-muted);
    margin-top: 0.3rem;
}

/* ── Haber ── */
.news-item {
    background-color: var(--bn-card);
    border: 1px solid var(--bn-border);
    border-left: 3px solid var(--bn-border);
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    border-radius: 6px;
    transition: 0.2s;
}
.news-item:hover { border-left-color: var(--bn-green); background-color: var(--bn-card2); }
.news-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--bn-white);
    text-decoration: none;
    display: block;
    margin-bottom: 0.4rem;
    line-height: 1.4;
}
.news-title:hover { color: var(--bn-green); }
.news-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--bn-muted);
    display: flex;
    justify-content: space-between;
}

/* ── Sinyal rozeti ── */
.signal { display:inline-block; padding:0.15rem 0.6rem; border-radius:4px;
          font-family:'IBM Plex Mono',monospace; font-size:0.72rem; font-weight:600; }
.signal.guclu-al  { background:#0D2E1A; color:#0ECB81; border:1px solid #1B5E35; }
.signal.al        { background:#0A2218; color:#0ECB81; border:1px solid #144D2A; }
.signal.tut       { background:#1A1C22; color:#848E9C; border:1px solid #2B3139; }
.signal.sat       { background:#2A0A10; color:#F6465D; border:1px solid #5C1525; }
.signal.guclu-sat { background:#220810; color:#F6465D; border:1px solid #4A1020; }

/* ── Tab ── */
button[data-baseweb="tab"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: var(--bn-muted) !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    padding: 0.7rem 1.2rem !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--bn-yellow) !important;
    border-bottom-color: var(--bn-yellow) !important;
}
[data-testid="stTabs"] > div:first-child {
    border-bottom: 1px solid var(--bn-border) !important;
}

/* ── Input / Selectbox ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background-color: var(--bn-card2) !important;
    border: 1px solid var(--bn-border) !important;
    color: var(--bn-white) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    border-radius: 6px !important;
}
label { font-family:'IBM Plex Mono',monospace !important; font-size:0.72rem !important;
        color: var(--bn-muted) !important; text-transform:uppercase; letter-spacing:0.06em; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background: var(--bn-bg); }
::-webkit-scrollbar-thumb { background: var(--bn-border); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BIST SEMBOL LİSTESİ
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","ALBRK","SKBNK","TSKB","KLNMA",
    "KCHOL","SAHOL","DOHOL","ALARK","ENKAI","AGHOL","TKFEN","NTHOL","GLYHO","POLHO",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","SISE","ARCLK","VESTL",
    "BRISA","GOODY","CIMSA","AKCNS","OYAKC","NUHCM","BTCIM","AFYON","GOLTS","BSOKE",
    "FROTO","TOASO","DOAS","OTKAR","KARSN","ASUZU","TMSN","TTRAK",
    "THYAO","PGSUS","TAVHL","CLEBI","DOCO",
    "BIMAS","MGROS","SOKM","AEFES","CCOLA","ULKER","TATGD","TUKAS","PNSUT","PETUN","KERVT",
    "TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS","ENJSA","AKSEN","ODAS","SMARTG",
    "EUPWR","MIATK","GESAN","CWENE","YEOTK","GWIND","NATEN","MAGEN","AYDEM","CANTE",
    "EKGYO","ISGYO","TRGYO","HLGYO","VKGYO","DZGYO","SNGYO","ZRGYO","PSGYO","RYGYO",
    "KORDS","VESBE","AYGAZ","AYEN","ZOREN","AKSA","DEVA","SELEC","LKMNH","RTALB"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

# ==========================================
# 4. YARDIMCI FONKSİYONLAR
# ==========================================
def fmt_tl(val):
    try:
        if pd.isna(val) or val == 0: return "—"
        return f"TL {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "—"

def format_number(num):
    try:
        if pd.isna(num): return "—"
        if num >= 1_000_000_000: return f"TL {num/1_000_000_000:.2f} MLR"
        if num >= 1_000_000:     return f"TL {num/1_000_000:.2f} MLN"
        return f"TL {num:,.2f}"
    except:
        return "—"

def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain / loss.replace(0, np.nan)
        val   = (100 - (100 / (1 + rs))).iloc[-1]
        return round(float(val), 1) if pd.notna(val) else np.nan
    except:
        return np.nan

def compute_macd(series, fast=12, slow=26, signal=9):
    try:
        ema_f  = series.ewm(span=fast, adjust=False).mean()
        ema_s  = series.ewm(span=slow, adjust=False).mean()
        macd   = ema_f - ema_s
        sig    = macd.ewm(span=signal, adjust=False).mean()
        hist   = macd - sig
        return float(macd.iloc[-1]), float(sig.iloc[-1]), float(hist.iloc[-1])
    except:
        return np.nan, np.nan, np.nan

def compute_atr(high, low, close, period=14):
    try:
        pc = close.shift(1)
        tr = pd.concat([high-low,(high-pc).abs(),(low-pc).abs()],axis=1).max(axis=1)
        return float(tr.rolling(period).mean().iloc[-1])
    except:
        return np.nan

def get_action_signal(rsi, price, sma50):
    if pd.isna(rsi): return "TUT", "#848E9C", "tut"
    if rsi < 35 and price > sma50: return "GUCLU AL", "#0ECB81", "guclu-al"
    if rsi < 45:                   return "AL",       "#0ECB81", "al"
    if rsi > 70:                   return "SAT",      "#F6465D", "sat"
    if rsi > 65 and price < sma50: return "GUCLU SAT","#F6465D", "guclu-sat"
    return "TUT", "#848E9C", "tut"

def yil_sonu_tahmini(close_series, rsi, macd_hist, price, sma50, pe_ratio):
    """
    Monte Carlo + Teknik Skor bazli yil sonu fiyat tahmini.
    Bull / Base / Bear senaryosu.
    """
    if len(close_series) < 60:
        return None

    returns   = close_series.pct_change().dropna()
    mu        = float(returns.mean())
    sigma     = float(returns.std())
    n_days    = max(1, (datetime(datetime.today().year, 12, 31) - datetime.today()).days)
    n_sim     = 2000

    # Teknik skor: -1 (cok bearish) +1 (cok bullish)
    score = 0.0
    if pd.notna(rsi):
        if rsi < 35:   score += 0.4
        elif rsi < 50: score += 0.15
        elif rsi > 70: score -= 0.4
        elif rsi > 60: score -= 0.15
    if pd.notna(macd_hist):
        score += 0.3 if macd_hist > 0 else -0.3
    if pd.notna(price) and pd.notna(sma50) and sma50 > 0:
        score += 0.3 if price > sma50 else -0.3
    score = max(-1.0, min(1.0, score))

    # Drift'i skora gore ayarla
    mu_adj = mu + score * 0.0008

    np.random.seed(42)
    sim_returns = np.random.normal(mu_adj, sigma, (n_days, n_sim))
    sim_paths   = price * np.exp(np.cumsum(sim_returns, axis=0))
    final_prices = sim_paths[-1]

    bull = float(np.percentile(final_prices, 75))
    base = float(np.percentile(final_prices, 50))
    bear = float(np.percentile(final_prices, 25))

    # Olasilik: fiyatin simdiyi gecme olasiligi
    prob_up   = float((final_prices > price * 1.10).mean() * 100)
    prob_down = float((final_prices < price * 0.90).mean() * 100)

    return {
        "bull": bull, "base": base, "bear": bear,
        "prob_up": prob_up, "prob_down": prob_down,
        "score": score, "n_days": n_days,
        "paths": sim_paths[:, :50],  # grafik icin 50 path
    }

# ==========================================
# 5. VERİ ÇEKME
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    end   = datetime.today()
    start = end - timedelta(days=90)
    rows  = []

    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 55: return None
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            chg   = (price - prev) / prev * 100
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi   = compute_rsi(close)
            action, _, _ = get_action_signal(rsi, price, sma50)
            return {"Sembol": name, "Fiyat (TL)": price, "Degisim %": chg,
                    "RSI": rsi, "Aksiyon": action}
        except:
            return None

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
    try:
        info = stock.info
        hist = stock.history(period="1y")
    except:
        pass
    try:
        raw_news = stock.news or []
        for n in raw_news:
            content = n.get("content", {})
            title   = content.get("title") or n.get("title", "")
            link    = (content.get("canonicalUrl", {}) or {}).get("url") or \
                      n.get("link", f"https://finance.yahoo.com/quote/{ticker}")
            pub_ts  = n.get("providerPublishTime") or \
                      (content.get("pubDate") and
                       int(datetime.fromisoformat(content["pubDate"].replace("Z","")).timestamp()))
            publisher = (content.get("provider", {}) or {}).get("displayName") or \
                        n.get("publisher", "Finans Kaynagi")
            if not title or not pub_ts or pub_ts < 1_000_000_000:
                continue
            valid_news.append({
                "title": title, "link": link, "publisher": publisher,
                "date": datetime.fromtimestamp(pub_ts).strftime("%d.%m.%Y %H:%M")
            })
    except:
        pass
    return info, hist, valid_news

@st.cache_data(ttl=900, show_spinner=False)
def get_current_price(ticker: str) -> float:
    try:
        df = yf.download(ticker, period="2d", progress=False, auto_adjust=True)
        if not df.empty:
            return float(df["Close"].squeeze().iloc[-1])
    except:
        pass
    return 0.0

# ==========================================
# 6. ANA HEADER
# ==========================================
st.markdown(
    '<div class="app-header">BIST Analiz Terminali</div>'
    '<div class="app-sub">// Kantitatif Analiz · Portfoy Simulatoru · Beyin Takimi</div>',
    unsafe_allow_html=True)

# ==========================================
# 7. ANA SEKMELER
# ==========================================
tab_market, tab_detail, tab_portfolio = st.tabs([
    "  Piyasa Gorunumu  ",
    "  Derin Analiz  ",
    "  Portfoy Simulatoru  ",
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PİYASA GÖRÜNÜMÜ               ║
# ╚══════════════════════════════════════════╝
with tab_market:
    with st.spinner("Piyasa verileri yukleniyord..."):
        df_market = fetch_market_data()

    if df_market.empty:
        st.error("Veri cekilemedi.")
        st.stop()

    total_stocks = len(df_market)
    up_stocks    = len(df_market[df_market["Degisim %"] > 0])
    down_stocks  = len(df_market[df_market["Degisim %"] < 0])

    c1, c2, c3, c4 = st.columns([1, 1, 1, 0.6])
    with c1:
        if st.button(f"Tum Hisseler  |  {total_stocks}", use_container_width=True):
            st.session_state.market_filter = "TÜMÜ"
    with c2:
        if st.button(f"Yukselenler  |  {up_stocks}", use_container_width=True):
            st.session_state.market_filter = "YÜKSELENLER"
    with c3:
        if st.button(f"Dusenler  |  {down_stocks}", use_container_width=True):
            st.session_state.market_filter = "DÜŞENLER"
    with c4:
        if st.button("Yenile", use_container_width=True):
            st.cache_data.clear()
            st.session_state.market_filter = "TÜMÜ"
            st.rerun()

    df_filtered = df_market.copy()
    if st.session_state.market_filter == "YÜKSELENLER":
        df_filtered = df_filtered[df_filtered["Degisim %"] > 0]
    elif st.session_state.market_filter == "DÜŞENLER":
        df_filtered = df_filtered[df_filtered["Degisim %"] < 0]

    st.markdown(f'<div class="section-title">Piyasa Gorunumu — {st.session_state.market_filter}</div>',
                unsafe_allow_html=True)

    def style_df(df):
        s = df.style.format({"Fiyat (TL)": "TL {:,.2f}", "Degisim %": "{:+.2f}%",
                              "RSI": "{:.1f}"}, na_rep="—")
        def color_chg(v):
            if pd.isna(v): return ''
            return 'color:#0ECB81;font-weight:600' if v > 0 else \
                   ('color:#F6465D;font-weight:600' if v < 0 else 'color:#848E9C')
        def color_act(v):
            s = str(v)
            if "AL" in s: return 'color:#0ECB81;font-weight:700'
            if "SAT" in s: return 'color:#F6465D;font-weight:700'
            return 'color:#848E9C'
        return s.map(color_chg, subset=["Degisim %"]).map(color_act, subset=["Aksiyon"])

    st.dataframe(
        style_df(df_filtered[["Sembol","Fiyat (TL)","Degisim %","RSI","Aksiyon"]]),
        use_container_width=True, height=420, hide_index=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: DERİN ANALİZ                  ║
# ╚══════════════════════════════════════════╝
with tab_detail:
    st.markdown('<div class="section-title">Hisse Secin ve Derin Analiz Baslat</div>',
                unsafe_allow_html=True)

    selected_symbol = st.selectbox(
        "Hisse Senedi",
        sorted(bist_symbols),
        index=bist_symbols.index("THYAO") if "THYAO" in bist_symbols else 0,
    )
    selected_ticker = f"{selected_symbol}.IS"

    info, hist, news = get_detailed_data(selected_ticker)

    if hist.empty:
        st.warning("Bu hisse icin veri cekilemedi.")
    else:
        close  = hist["Close"].squeeze()
        curr_p = float(close.iloc[-1])
        prev_p = float(close.iloc[-2])
        chg    = curr_p - prev_p
        chg_p  = (chg / prev_p) * 100
        color_hex = "#0ECB81" if chg >= 0 else "#F6465D"
        sign   = "+" if chg >= 0 else ""

        # ── Fiyat + Mini Grafik ──────────────────────────────
        col1, col2 = st.columns([1.1, 2])
        with col1:
            long_name = info.get("longName", selected_symbol) if info else selected_symbol
            st.markdown(f"""
            <div class="bn-card" style="padding:1.8rem;">
                <div style="font-size:2rem;font-weight:800;color:#EAECEF;letter-spacing:-0.02em;">{selected_symbol}</div>
                <div style="font-size:0.8rem;color:#848E9C;margin-bottom:1rem;">{long_name}</div>
                <div style="font-size:2.4rem;font-weight:700;color:#EAECEF;letter-spacing:-0.02em;">
                    TL {curr_p:,.2f}
                </div>
                <div style="color:{color_hex};font-size:1.1rem;font-weight:600;margin-top:0.3rem;">
                    {sign}TL {abs(chg):,.2f} ({sign}{chg_p:.2f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            fig = go.Figure()
            r, g, b = (0, 203, 129) if chg >= 0 else (246, 70, 93)
            fig.add_trace(go.Scatter(
                x=hist.index, y=close,
                mode="lines",
                line=dict(color=color_hex, width=2),
                fill="tozeroy",
                fillcolor=f"rgba({r},{g},{b},0.1)",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=10,b=0), height=200,
                xaxis=dict(visible=False), yaxis=dict(visible=False),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        # ── Temel Veriler ───────────────────────────────────
        market_cap = info.get("marketCap", np.nan) if info else np.nan
        pe_ratio   = info.get("trailingPE", np.nan) if info else np.nan
        high_52    = info.get("fiftyTwoWeekHigh", float(hist["High"].max())) if info else float(hist["High"].max())
        low_52     = info.get("fiftyTwoWeekLow",  float(hist["Low"].min()))  if info else float(hist["Low"].min())

        rsi_14  = compute_rsi(close)
        macd_v, macd_s, macd_h = compute_macd(close)
        sma50   = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else curr_p
        atr_14  = compute_atr(hist["High"].squeeze(), hist["Low"].squeeze(), close)
        act_lbl, act_color, act_cls = get_action_signal(rsi_14, curr_p, sma50)
        target  = curr_p + (2 * atr_14) if pd.notna(atr_14) else np.nan

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        m1, m2, m3, m4, m5 = st.columns(5)
        def mcard(col, label, value, cls=""):
            col.markdown(
                f'<div class="bn-card"><div class="bn-card-label">{label}</div>'
                f'<div class="bn-card-value {cls}">{value}</div></div>',
                unsafe_allow_html=True)

        mcard(m1, "Piyasa Degeri", format_number(market_cap))
        mcard(m2, "F/K Orani", f"{pe_ratio:.1f}" if pd.notna(pe_ratio) else "—")
        mcard(m3, "RSI (14)", f"{rsi_14:.1f}" if pd.notna(rsi_14) else "—",
              "green" if pd.notna(rsi_14) and rsi_14 < 40 else
              "red"   if pd.notna(rsi_14) and rsi_14 > 65 else "")
        mcard(m4, "Kisa Vade Hedef", fmt_tl(target), "green")
        mcard(m5, "Aksiyon", act_lbl,
              "green" if "AL" in act_lbl else "red" if "SAT" in act_lbl else "")

        # ── YIL SONU TAHMİNİ ────────────────────────────────
        st.markdown('<div class="section-title">Yil Sonu Fiyat Tahmini (Monte Carlo)</div>',
                    unsafe_allow_html=True)

        forecast = yil_sonu_tahmini(close, rsi_14, macd_h, curr_p, sma50, pe_ratio)

        if forecast:
            days_left = forecast["n_days"]
            f1, f2, f3 = st.columns(3)

            bull_ret = (forecast["bull"] - curr_p) / curr_p * 100
            base_ret = (forecast["base"] - curr_p) / curr_p * 100
            bear_ret = (forecast["bear"] - curr_p) / curr_p * 100

            f1.markdown(f"""
            <div class="forecast-card">
                <div class="bn-card-label">Iyimser Senaryo (Bull)</div>
                <div style="font-size:1.8rem;font-weight:700;color:#0ECB81;margin:0.4rem 0;">
                    TL {forecast['bull']:,.2f}
                </div>
                <div style="font-size:0.85rem;color:#0ECB81;">+{bull_ret:.1f}%</div>
                <div style="font-size:0.72rem;color:#848E9C;margin-top:0.5rem;">
                    %10+ yukari olasiligi: %{forecast['prob_up']:.0f}
                </div>
            </div>""", unsafe_allow_html=True)

            f2.markdown(f"""
            <div class="forecast-card base">
                <div class="bn-card-label">Baz Senaryo (Median)</div>
                <div style="font-size:1.8rem;font-weight:700;color:#1E90FF;margin:0.4rem 0;">
                    TL {forecast['base']:,.2f}
                </div>
                <div style="font-size:0.85rem;color:#1E90FF;">{'+' if base_ret>=0 else ''}{base_ret:.1f}%</div>
                <div style="font-size:0.72rem;color:#848E9C;margin-top:0.5rem;">
                    {days_left} gun kaldi · 2.000 simulasyon
                </div>
            </div>""", unsafe_allow_html=True)

            f3.markdown(f"""
            <div class="forecast-card bear">
                <div class="bn-card-label">Karamsar Senaryo (Bear)</div>
                <div style="font-size:1.8rem;font-weight:700;color:#F6465D;margin:0.4rem 0;">
                    TL {forecast['bear']:,.2f}
                </div>
                <div style="font-size:0.85rem;color:#F6465D;">{bear_ret:.1f}%</div>
                <div style="font-size:0.72rem;color:#848E9C;margin-top:0.5rem;">
                    %10+ asagi olasiligi: %{forecast['prob_down']:.0f}
                </div>
            </div>""", unsafe_allow_html=True)

            # Monte Carlo Grafik (50 path)
            fig_mc = go.Figure()
            paths  = forecast["paths"]
            today  = datetime.today()
            dates  = [today + timedelta(days=i) for i in range(len(paths))]

            for i in range(paths.shape[1]):
                fig_mc.add_trace(go.Scatter(
                    x=dates, y=paths[:, i],
                    mode="lines",
                    line=dict(width=0.5,
                              color="rgba(240,185,11,0.12)" if forecast["score"] > 0
                              else "rgba(246,70,93,0.12)"),
                    showlegend=False, hoverinfo="skip",
                ))
            # Bull / Base / Bear cizgiler
            for val, col, name in [
                (forecast["bull"], "#0ECB81", "Bull (75p)"),
                (forecast["base"], "#1E90FF", "Base (50p)"),
                (forecast["bear"], "#F6465D", "Bear (25p)"),
            ]:
                fig_mc.add_hline(y=val, line=dict(color=col, width=1.5, dash="dash"),
                                 annotation_text=name,
                                 annotation_font=dict(color=col, size=10))
            fig_mc.add_hline(y=curr_p, line=dict(color="#848E9C", width=1),
                             annotation_text="Guncel Fiyat",
                             annotation_font=dict(color="#848E9C", size=10))
            fig_mc.update_layout(
                plot_bgcolor="#0B0E11", paper_bgcolor="#0B0E11",
                font=dict(family="IBM Plex Mono", color="#848E9C", size=10),
                xaxis=dict(gridcolor="#1E2329", tickfont=dict(size=9)),
                yaxis=dict(gridcolor="#1E2329", tickprefix="TL ", tickformat=",.0f"),
                margin=dict(t=20,b=40,l=70,r=20), height=300,
                title=dict(text=f"{selected_symbol} Monte Carlo Simulasyonu ({days_left} gun)",
                           font=dict(size=11, color="#848E9C", family="IBM Plex Mono"), x=0.5),
            )
            st.plotly_chart(fig_mc, use_container_width=True)

        # ── BEYİN TAKIMI ANALİZİ ────────────────────────────
        st.markdown('<div class="section-title">Beyin Takimi Analizi</div>', unsafe_allow_html=True)

        # Hesaplamalar
        trend_pos  = curr_p > sma50
        sma50_str  = "uzerinde" if trend_pos else "altinda"
        trend_str  = "yukselis trendinde" if trend_pos else "dusus trendinde"
        macd_str   = "pozitif (yukari momentum)" if pd.notna(macd_h) and macd_h > 0 else "negatif (asagi momentum)"
        rsi_str    = f"{rsi_14:.1f}" if pd.notna(rsi_14) else "—"
        curr_str   = f"TL {curr_p:,.2f}"
        sma50_fmt  = f"TL {sma50:,.2f}"
        high52_str = f"TL {high_52:,.2f}"
        low52_str  = f"TL {low_52:,.2f}"
        range52    = high_52 - low_52
        pos_in_range = ((curr_p - low_52) / range52 * 100) if range52 > 0 else 50
        atr_pct    = (atr_14 / curr_p * 100) if pd.notna(atr_14) and curr_p > 0 else 0

        # RSI bazli risk analizi
        if pd.notna(rsi_14):
            if rsi_14 > 70:
                risk_level = "YUKSEK"
                risk_color = "#F6465D"
                risk_txt = (
                    f"RSI {rsi_str} ile asiri alim bolgesinde. "
                    "Teknik indikorler kisa vadede yorgunluga ve kar satislarina isaret ediyor. "
                    "Yeni pozisyon acmak icin risk/odulun aleyhte oldugu bir bolge."
                )
                strateji_txt = (
                    "Mevcut pozisyonlar icin trailing stop-loss guncellenmeli. "
                    "Yeni alis icin SMA-50'ye ya da RSI 55 altina gerileme beklenmeli. "
                    "Pozisyon buyuklugu kucultulebilir."
                )
            elif rsi_14 < 35:
                risk_level = "DUSUK"
                risk_color = "#0ECB81"
                risk_txt = (
                    f"RSI {rsi_str} ile asiri satim bolgesinde. "
                    "Satis baskisi yavaslama sinyali veriyor, hisse tarihsel ortalamaya gore iskontolu. "
                    "Teknik temel bir dip olusum aramak icin uygun bolge."
                )
                strateji_txt = (
                    "Kademeli maliyetlenme (DCA) stratejisi uygulanabilir. "
                    "MACD pozitife donene kadar tam pozisyon alinmamali; "
                    "52 hafta dibinin yakininda stop-loss belirlenebilir."
                )
            else:
                risk_level = "ORTA"
                risk_color = "#F0B90B"
                risk_txt = (
                    f"RSI {rsi_str} ile dengeli (notr) bolgede. "
                    "Ne asiri alim ne asiri satim sinyali mevcut. "
                    "Hissenin yonu hacim ve makro gelismelere daha duyarli."
                )
                strateji_txt = (
                    "Trend yonunu dogrulamak icin islem hacmi ve makro veri takibi onerilir. "
                    "SMA-50 uzerinde kapanislar surdugunce tutma stratejisi uygulanabilir. "
                    "Kirilis durumunda pozisyon kucultulmeli."
                )
        else:
            risk_level = "BELIRSIZ"
            risk_color = "#848E9C"
            risk_txt   = "RSI hesaplanamadi; yeterli veri yok."
            strateji_txt = "Daha uzun gecmis verisi olan bir hisse tercih edilebilir."

        # Forecast bazli consensus
        if forecast:
            sc = forecast["score"]
            if sc > 0.4:
                consensus = "GUCLU POZITIF — Teknik indikorler gucluk teyit ediyor."
                cons_color = "#0ECB81"
            elif sc > 0:
                consensus = "TEMKINLI POZITIF — Orta vadede yukari egim var, dikkatli takip onerilir."
                cons_color = "#0ECB81"
            elif sc > -0.4:
                consensus = "TEMKINLI NEGATIF — Trend zayifliyor; yeni alimlar icin sabir onerilir."
                cons_color = "#F0B90B"
            else:
                consensus = "GUCLU NEGATIF — Teknik tablo baskici; risk yonetimi on planda olmali."
                cons_color = "#F6465D"
        else:
            consensus = "Veri yetersiz."
            cons_color = "#848E9C"

        brain_html = (
            '<div class="brain-card">'
            '<div class="brain-header">Beyin Takimi Analizi — ' + selected_symbol + '</div>'

            '<div class="brain-section">'
            '<div class="brain-section-title">Trend ve Momentum</div>'
            '<div class="brain-section-text">'
            f'Hisse su an SMA-50 ({sma50_fmt}) <b>{sma50_str}</b>, orta vadeli <b>{trend_str}</b>. '
            f'MACD histogram <b>{macd_str}</b>. '
            f'52 haftalik aralikta ({low52_str} - {high52_str}) pozisyonu: '
            f'aralik icerisinde <b>%{pos_in_range:.0f}</b> seviyesinde. '
            f'Gunluk ortalama volatilite (ATR%): <b>%{atr_pct:.2f}</b>.'
            '</div></div>'

            '<div class="brain-section">'
            f'<div class="brain-section-title">Risk Durumu — <span style="color:{risk_color}">{risk_level}</span></div>'
            f'<div class="brain-section-text">{risk_txt}</div>'
            '</div>'

            '<div class="brain-section">'
            '<div class="brain-section-title">Strateji Onerisi</div>'
            f'<div class="brain-section-text">{strateji_txt}</div>'
            '</div>'

            '<div class="brain-section">'
            '<div class="brain-section-title">Beyin Takimi Konsensus</div>'
            f'<div class="brain-section-text" style="color:{cons_color};font-weight:600;">{consensus}</div>'
            '</div>'

            '</div>'
        )
        st.markdown(brain_html, unsafe_allow_html=True)

        # ── HABERLER ─────────────────────────────────────────
        st.markdown('<div class="section-title">Guncel Haber Akisi</div>', unsafe_allow_html=True)

        if news:
            for n in news[:6]:
                st.markdown(f"""
                <div class="news-item">
                    <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                    <div class="news-meta">
                        <span>{n['publisher']}</span>
                        <span>{n['date']}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="news-item" style="border-left-color:#1E90FF;">
                <div class="news-title">Haber bulunamadi</div>
                <div style="color:#848E9C;font-size:0.85rem;margin-top:0.4rem;">
                    {selected_symbol} icin son 24 saate ait dogrulanmis haber yok.
                    KAP bildirimlerini inceleyebilirsiniz.
                </div>
                <div style="margin-top:0.8rem;">
                    <a href="https://www.kap.org.tr/tr/arama/bilesik?bildirimTipleri=OzelDurumAciklamasi&sirketler={selected_symbol}"
                       target="_blank" style="color:#1E90FF;font-size:0.8rem;font-weight:600;text-decoration:none;">
                       KAP Bildirimlerini Goruntule
                    </a>
                </div>
            </div>""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: PORTFÖY SIMÜLATÖRÜ            ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    st.markdown('<div class="section-title">Portfoy Simulatoru — Yil Sonu Tahmini</div>',
                unsafe_allow_html=True)

    # ── Portföy Adı ─────────────────────────────────────────
    pf_name = st.text_input("Portfoy Adi", value=st.session_state.portfolio_name)
    st.session_state.portfolio_name = pf_name

    # ── Hisse Ekle ──────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    pa, pb, pc, pd_col = st.columns([2, 1.5, 1.5, 1])
    with pa:
        add_sym = st.selectbox("Hisse Ekle", sorted(bist_symbols), key="add_sym")
    with pb:
        add_adet = st.number_input("Adet", min_value=1, value=100, step=10, key="add_adet")
    with pc:
        add_maliyet = st.number_input("Maliyet Fiyati (TL)", min_value=0.01, value=10.0,
                                      step=0.5, format="%.2f", key="add_maliyet")
    with pd_col:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Ekle", use_container_width=True, type="primary"):
            st.session_state.portfolio[add_sym] = {
                "adet": add_adet, "maliyet": add_maliyet
            }
            st.success(f"{add_sym} portfoya eklendi!")
            st.rerun()

    if not st.session_state.portfolio:
        st.markdown("""
        <div class="bn-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2rem;margin-bottom:1rem;">📂</div>
            <div style="color:#848E9C;font-size:0.9rem;">
                Portfoyunuz bos. Yukaridan hisse ekleyerek baslayin.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── Portföy Hesapla ──────────────────────────────────
        total_maliyet   = 0.0
        total_guncel    = 0.0
        total_bull      = 0.0
        total_base      = 0.0
        total_bear      = 0.0
        portfolio_rows  = []
        sil_listesi     = []

        progress_bar = st.progress(0, text="Portfoy hesaplaniyor...")
        symbols_list = list(st.session_state.portfolio.keys())

        for i, sym in enumerate(symbols_list):
            progress_bar.progress((i+1)/len(symbols_list),
                                  text=f"Analiz ediliyor: {sym}...")
            data   = st.session_state.portfolio[sym]
            ticker = f"{sym}.IS"

            try:
                _, hist_pf, _ = get_detailed_data(ticker)
                if hist_pf.empty:
                    sil_listesi.append(sym)
                    continue

                close_pf = hist_pf["Close"].squeeze()
                curr_p_pf = float(close_pf.iloc[-1])
                rsi_pf    = compute_rsi(close_pf)
                _, _, macd_h_pf = compute_macd(close_pf)
                sma50_pf  = float(close_pf.rolling(50).mean().iloc[-1]) if len(close_pf)>=50 else curr_p_pf
                pe_pf     = np.nan

                fc = yil_sonu_tahmini(close_pf, rsi_pf, macd_h_pf, curr_p_pf, sma50_pf, pe_pf)

                adet     = data["adet"]
                maliyet  = data["maliyet"]
                toplam_maliyet = adet * maliyet
                toplam_guncel  = adet * curr_p_pf
                karpf          = toplam_guncel - toplam_maliyet
                karpct         = (karpf / toplam_maliyet * 100) if toplam_maliyet > 0 else 0

                if fc:
                    bull_val = adet * fc["bull"]
                    base_val = adet * fc["base"]
                    bear_val = adet * fc["bear"]
                    bull_ret = (fc["bull"] - curr_p_pf) / curr_p_pf * 100
                    base_ret = (fc["base"] - curr_p_pf) / curr_p_pf * 100
                    bear_ret = (fc["bear"] - curr_p_pf) / curr_p_pf * 100
                    score    = fc["score"]
                else:
                    bull_val = base_val = bear_val = toplam_guncel
                    bull_ret = base_ret = bear_ret = 0.0
                    score    = 0.0

                total_maliyet  += toplam_maliyet
                total_guncel   += toplam_guncel
                total_bull     += bull_val
                total_base     += base_val
                total_bear     += bear_val

                portfolio_rows.append({
                    "sym": sym, "adet": adet, "maliyet": maliyet,
                    "curr_p": curr_p_pf,
                    "toplam_maliyet": toplam_maliyet,
                    "toplam_guncel": toplam_guncel,
                    "kar": karpf, "kar_pct": karpct,
                    "bull_val": bull_val, "base_val": base_val, "bear_val": bear_val,
                    "bull_ret": bull_ret, "base_ret": base_ret, "bear_ret": bear_ret,
                    "rsi": rsi_pf, "score": score,
                })
            except:
                continue

        progress_bar.empty()

        # ── Özet KPI'lar ──────────────────────────────────────
        pnl_total     = total_guncel - total_maliyet
        pnl_pct       = (pnl_total / total_maliyet * 100) if total_maliyet > 0 else 0
        bull_kazanc   = total_bull - total_maliyet
        base_kazanc   = total_base - total_maliyet
        bear_kazanc   = total_bear - total_maliyet

        st.markdown(f"<div style='margin:1rem 0 0.5rem 0;font-size:1.1rem;font-weight:700;color:#EAECEF;'>{pf_name}</div>",
                    unsafe_allow_html=True)

        k1, k2, k3, k4 = st.columns(4)
        def kcard(col, label, value, cls=""):
            col.markdown(
                f'<div class="bn-card"><div class="bn-card-label">{label}</div>'
                f'<div class="bn-card-value {cls}">{value}</div></div>',
                unsafe_allow_html=True)

        kcard(k1, "Toplam Maliyet",   fmt_tl(total_maliyet))
        kcard(k2, "Guncel Deger",     fmt_tl(total_guncel))
        pnl_cls = "green" if pnl_total >= 0 else "red"
        kcard(k3, "Kar / Zarar",
              f"{'+' if pnl_total>=0 else ''}{fmt_tl(pnl_total)} ({'+' if pnl_pct>=0 else ''}{pnl_pct:.1f}%)",
              pnl_cls)
        kcard(k4, "Hisse Sayisi",     str(len(portfolio_rows)))

        # ── Yıl Sonu Tahmin KPI'ları ─────────────────────────
        st.markdown('<div class="section-title">Yil Sonu Portfoy Tahmini</div>', unsafe_allow_html=True)

        y1, y2, y3 = st.columns(3)
        bull_cls = "green" if bull_kazanc >= 0 else "red"
        base_cls = "green" if base_kazanc >= 0 else "red"
        bear_cls = "green" if bear_kazanc >= 0 else "red"

        y1.markdown(f"""
        <div class="forecast-card">
            <div class="bn-card-label">Iyimser Senaryo (Bull)</div>
            <div class="bn-card-value green" style="font-size:1.6rem;">{fmt_tl(total_bull)}</div>
            <div style="color:#0ECB81;font-size:0.9rem;margin-top:0.3rem;">
                {'+' if bull_kazanc>=0 else ''}{fmt_tl(bull_kazanc)}
                ({'+' if (total_bull/total_maliyet-1)*100>=0 else ''}{(total_bull/total_maliyet-1)*100:.1f}%)
            </div>
        </div>""", unsafe_allow_html=True)

        y2.markdown(f"""
        <div class="forecast-card base">
            <div class="bn-card-label">Baz Senaryo (Median)</div>
            <div class="bn-card-value" style="font-size:1.6rem;color:#1E90FF;">{fmt_tl(total_base)}</div>
            <div style="color:#1E90FF;font-size:0.9rem;margin-top:0.3rem;">
                {'+' if base_kazanc>=0 else ''}{fmt_tl(base_kazanc)}
                ({'+' if (total_base/total_maliyet-1)*100>=0 else ''}{(total_base/total_maliyet-1)*100:.1f}%)
            </div>
        </div>""", unsafe_allow_html=True)

        y3.markdown(f"""
        <div class="forecast-card bear">
            <div class="bn-card-label">Karamsar Senaryo (Bear)</div>
            <div class="bn-card-value red" style="font-size:1.6rem;">{fmt_tl(total_bear)}</div>
            <div style="color:#F6465D;font-size:0.9rem;margin-top:0.3rem;">
                {'+' if bear_kazanc>=0 else ''}{fmt_tl(bear_kazanc)}
                ({'+' if (total_bear/total_maliyet-1)*100>=0 else ''}{(total_bear/total_maliyet-1)*100:.1f}%)
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Hisse Hisse Detay ─────────────────────────────────
        st.markdown('<div class="section-title">Hisse Detaylari</div>', unsafe_allow_html=True)

        for row in portfolio_rows:
            kar_cls = "#0ECB81" if row["kar"] >= 0 else "#F6465D"
            kar_sign = "+" if row["kar"] >= 0 else ""
            rsi_col = "#0ECB81" if pd.notna(row["rsi"]) and row["rsi"] < 40 else \
                      "#F6465D" if pd.notna(row["rsi"]) and row["rsi"] > 65 else "#848E9C"

            with st.container():
                dc1, dc2, dc3 = st.columns([2, 3, 1])
                with dc1:
                    st.markdown(f"""
                    <div class="portfolio-card">
                        <div class="portfolio-ticker">{row['sym']}</div>
                        <div class="portfolio-detail">
                            {row['adet']} adet  x  TL {row['maliyet']:,.2f} maliyet
                        </div>
                        <div style="margin-top:0.6rem;">
                            <span style="font-size:1.1rem;font-weight:700;color:#EAECEF;">
                                TL {row['curr_p']:,.2f}
                            </span>
                            <span style="color:{kar_cls};font-size:0.85rem;margin-left:0.5rem;">
                                {kar_sign}TL {abs(row['kar']):,.0f} ({kar_sign}{row['kar_pct']:.1f}%)
                            </span>
                        </div>
                        <div class="portfolio-detail" style="margin-top:0.4rem;">
                            RSI <span style="color:{rsi_col};">{row['rsi']:.1f}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

                with dc2:
                    st.markdown(f"""
                    <div class="portfolio-card">
                        <div class="bn-card-label">Yil Sonu Tahmin (Hisse Basina)</div>
                        <div style="display:flex;gap:1rem;margin-top:0.5rem;flex-wrap:wrap;">
                            <div>
                                <div style="font-size:0.62rem;color:#848E9C;text-transform:uppercase;">Bull</div>
                                <div style="font-size:1rem;font-weight:700;color:#0ECB81;">
                                    TL {row['bull_val']/row['adet']:,.2f}
                                    <span style="font-size:0.75rem;">(+{row['bull_ret']:.1f}%)</span>
                                </div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:#848E9C;text-transform:uppercase;">Baz</div>
                                <div style="font-size:1rem;font-weight:700;color:#1E90FF;">
                                    TL {row['base_val']/row['adet']:,.2f}
                                    <span style="font-size:0.75rem;">({'+' if row['base_ret']>=0 else ''}{row['base_ret']:.1f}%)</span>
                                </div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:#848E9C;text-transform:uppercase;">Bear</div>
                                <div style="font-size:1rem;font-weight:700;color:#F6465D;">
                                    TL {row['bear_val']/row['adet']:,.2f}
                                    <span style="font-size:0.75rem;">({row['bear_ret']:.1f}%)</span>
                                </div>
                            </div>
                        </div>
                        <div style="margin-top:0.6rem;">
                            <div style="font-size:0.62rem;color:#848E9C;margin-bottom:0.2rem;">Toplam Portfoy Degeri (Yil Sonu)</div>
                            <div style="display:flex;gap:0.6rem;">
                                <span style="color:#0ECB81;font-size:0.85rem;font-weight:600;">{fmt_tl(row['bull_val'])}</span>
                                <span style="color:#848E9C;">|</span>
                                <span style="color:#1E90FF;font-size:0.85rem;font-weight:600;">{fmt_tl(row['base_val'])}</span>
                                <span style="color:#848E9C;">|</span>
                                <span style="color:#F6465D;font-size:0.85rem;font-weight:600;">{fmt_tl(row['bear_val'])}</span>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                with dc3:
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                    if st.button(f"Sil  {row['sym']}", key=f"del_{row['sym']}", use_container_width=True):
                        del st.session_state.portfolio[row["sym"]]
                        st.rerun()

        # ── Portföy Pasta Grafiği ─────────────────────────────
        if len(portfolio_rows) > 1:
            st.markdown('<div class="section-title">Portfoy Dagilimi</div>', unsafe_allow_html=True)
            labels = [r["sym"] for r in portfolio_rows]
            values = [r["toplam_guncel"] for r in portfolio_rows]
            colors = ["#F0B90B","#0ECB81","#1E90FF","#F6465D","#C084FC",
                      "#FB923C","#34D399","#60A5FA","#F472B6","#A3E635"]

            fig_pie = go.Figure(go.Pie(
                labels=labels, values=values,
                hole=0.55,
                marker=dict(colors=colors[:len(labels)],
                            line=dict(color="#0B0E11", width=2)),
                textinfo="label+percent",
                textfont=dict(family="IBM Plex Mono", size=11, color="#EAECEF"),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} TL<br>%{percent}<extra></extra>",
            ))
            fig_pie.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(font=dict(family="IBM Plex Mono", color="#848E9C", size=10)),
                margin=dict(t=20,b=20,l=20,r=20), height=320,
                annotations=[dict(
                    text=f"TL {total_guncel:,.0f}",
                    font=dict(size=14, color="#EAECEF", family="IBM Plex Sans"),
                    showarrow=False,
                )],
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# FOOTER
# ==========================================
st.markdown("""
<div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#2B3139;
text-align:center;border-top:1px solid #161A1E;padding-top:1rem;margin-top:2rem;">
BIST Analiz Terminali v4.0  ·  Egitim Amaclıdır  ·  Yatirim Tavsiyesi Degildir
·  Monte Carlo simulasyonu gecmis veriye dayali olasiliksaldir, garanti icermez.
</div>
""", unsafe_allow_html=True)
