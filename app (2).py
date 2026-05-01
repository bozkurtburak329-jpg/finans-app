"""
Burak Borsa Analiz v5.0
Kurulum: pip install streamlit pandas numpy plotly yfinance requests
Calistir: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures
import hashlib

# ═══════════════════════════════════════════════════════════
# 1. SAYFA YAPISI
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Burak Borsa Analiz",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

for key, default in [
    ("market_filter", "TÜMÜ"),
    ("portfolio", {}),
    ("selected_news", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ═══════════════════════════════════════════════════════════
# 2. CSS — MİDAS / BİNANCE KARANLIK TEMA
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0B0E11;
    color: #EAECEF;
}
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#0B0E11; }
::-webkit-scrollbar-thumb { background:#2B3139; border-radius:2px; }

/* ── Sekmeler ── */
[data-testid="stTabs"] > div:first-child { border-bottom:1px solid #1E2329 !important; }
button[data-baseweb="tab"] {
    font-family:'Inter',sans-serif !important;
    font-size:0.82rem !important; font-weight:600 !important;
    color:#5E6673 !important; background:transparent !important;
    padding:0.75rem 1.4rem !important; border-bottom:2px solid transparent !important;
    border-radius:0 !important; transition:all .2s !important;
}
button[data-baseweb="tab"]:hover { color:#EAECEF !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color:#F0B90B !important; border-bottom-color:#F0B90B !important;
}

/* ── Butonlar ── */
div.stButton > button {
    background:#1E2329; border:1px solid #2B3139; color:#EAECEF;
    font-family:'Inter',sans-serif; font-size:0.82rem; font-weight:600;
    border-radius:6px; transition:all .2s; height:48px;
}
div.stButton > button:hover {
    background:#252B33; border-color:#F0B90B; color:#F0B90B;
}
div.stButton > button[kind="primary"] {
    background:#F0B90B; color:#0B0E11; border:none;
}
div.stButton > button[kind="primary"]:hover {
    background:#d4a50a; color:#0B0E11;
}

/* ── Input ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background:#1E2329 !important; border:1px solid #2B3139 !important;
    color:#EAECEF !important; font-family:'JetBrains Mono',monospace !important;
    border-radius:6px !important; font-size:0.85rem !important;
}
[data-testid="stSelectbox"] > div > div {
    background:#1E2329 !important; border:1px solid #2B3139 !important;
    color:#EAECEF !important; border-radius:6px !important;
}
label {
    font-family:'JetBrains Mono',monospace !important;
    font-size:0.68rem !important; color:#5E6673 !important;
    text-transform:uppercase; letter-spacing:0.07em;
}

/* ── Kart bileşenleri ── */
.card {
    background:#161A1E; border:1px solid #1E2329;
    border-radius:10px; padding:1.2rem 1.4rem;
    position:relative; overflow:hidden;
}
.card-accent-green::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#0ECB81,#05a865); }
.card-accent-red::before   { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#F6465D,#c43348); }
.card-accent-yellow::before{ content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#F0B90B,#c49309); }
.card-accent-blue::before  { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#1E90FF,#0066cc); }

.card-label {
    font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#5E6673;
    text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.4rem;
}
.card-value {
    font-family:'Inter',sans-serif; font-weight:700; font-size:1.5rem;
    line-height:1.1; letter-spacing:-0.02em;
}
.card-value.green  { color:#0ECB81; }
.card-value.red    { color:#F6465D; }
.card-value.yellow { color:#F0B90B; }
.card-value.white  { color:#EAECEF; }
.card-sub { font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#5E6673; margin-top:0.3rem; }

/* ── Section başlığı ── */
.sec-title {
    font-family:'Inter',sans-serif; font-size:0.95rem; font-weight:700;
    color:#EAECEF; border-bottom:1px solid #1E2329;
    padding-bottom:0.5rem; margin:1.8rem 0 1rem 0;
}

/* ── Banner (giriş) ── */
.hero-name {
    font-family:'Inter',sans-serif; font-size:1.9rem; font-weight:800;
    color:#EAECEF; letter-spacing:-0.03em; line-height:1;
}
.hero-name span { color:#F0B90B; }
.hero-sub {
    font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#5E6673;
    text-transform:uppercase; letter-spacing:0.1em; margin-top:0.2rem;
}

/* ── Ticker bant kartı ── */
.ticker-band {
    display:flex; gap:1rem; flex-wrap:wrap; margin:1rem 0 1.4rem 0;
}
.ticker-item {
    flex:1; min-width:160px; background:#161A1E; border:1px solid #1E2329;
    border-radius:10px; padding:1rem 1.2rem; cursor:default;
}
.ticker-item.bist { border-top:2px solid #F0B90B; }
.ticker-item.dolar{ border-top:2px solid #0ECB81; }
.ticker-item.euro { border-top:2px solid #1E90FF; }
.ticker-label { font-family:'JetBrains Mono',monospace; font-size:0.6rem; color:#5E6673; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.3rem; }
.ticker-price { font-family:'Inter',sans-serif; font-size:1.55rem; font-weight:800; letter-spacing:-0.025em; line-height:1.1; }
.ticker-price.bist  { color:#F0B90B; }
.ticker-price.dolar { color:#0ECB81; }
.ticker-price.euro  { color:#1E90FF; }
.ticker-change { font-size:0.78rem; font-weight:600; margin-top:0.2rem; }
.ticker-change-sub { font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#5E6673; margin-top:0.15rem; }

/* ── Haber ── */
.news-card {
    background:#161A1E; border:1px solid #1E2329; border-radius:8px;
    padding:1rem 1.2rem; margin-bottom:0.5rem;
    border-left:3px solid #1E2329; cursor:pointer; transition:all .2s;
}
.news-card:hover { border-left-color:#F0B90B; background:#1A1E24; }
.news-card.active { border-left-color:#0ECB81; background:#0D1810; }
.news-title-text {
    font-family:'Inter',sans-serif; font-size:0.9rem; font-weight:600;
    color:#EAECEF; line-height:1.45; margin-bottom:0.4rem;
}
.news-meta { font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#5E6673; }

/* ── Haber detay paneli ── */
.news-detail {
    background:#0F1318; border:1px solid #1E2329; border-radius:10px;
    padding:1.4rem 1.6rem; margin-top:0.5rem;
}
.news-detail-title {
    font-family:'Inter',sans-serif; font-size:1.05rem; font-weight:700;
    color:#EAECEF; line-height:1.4; margin-bottom:0.8rem;
}
.news-detail-body {
    font-family:'Inter',sans-serif; font-size:0.88rem; color:#9BA3AF;
    line-height:1.75;
}

/* ── Beyin Takımı ── */
.brain-wrap {
    background:linear-gradient(135deg,#0F1318 0%,#0A0D10 100%);
    border:1px solid #1E2329; border-left:3px solid #F0B90B;
    border-radius:10px; padding:1.6rem; margin:1rem 0;
}
.brain-header {
    font-family:'Inter',sans-serif; font-size:1rem; font-weight:700;
    color:#F0B90B; margin-bottom:1.2rem; display:flex; align-items:center; gap:0.6rem;
}
.brain-row {
    display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1rem;
}
.brain-block {
    background:#161A1E; border:1px solid #1E2329; border-radius:8px; padding:1rem 1.2rem;
}
.brain-block-title {
    font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#5E6673;
    text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;
}
.brain-block-text { font-family:'Inter',sans-serif; font-size:0.85rem; color:#C0C8D4; line-height:1.65; }
.brain-full { grid-column:1/-1; }
.brain-signal {
    display:inline-block; padding:0.25rem 0.8rem; border-radius:5px;
    font-family:'JetBrains Mono',monospace; font-size:0.78rem; font-weight:700;
    margin-bottom:0.5rem;
}
.brain-signal.buy  { background:#052e16; color:#0ECB81; border:1px solid #065f46; }
.brain-signal.sell { background:#1a0509; color:#F6465D; border:1px solid #6b1525; }
.brain-signal.hold { background:#111827; color:#848E9C; border:1px solid #1f2937; }

/* ── Gauge bar ── */
.gauge-bar { height:6px; border-radius:3px; background:#1E2329; margin:0.4rem 0; overflow:hidden; }
.gauge-fill { height:100%; border-radius:3px; }

/* ── Portföy kartı ── */
.pf-card {
    background:#161A1E; border:1px solid #1E2329; border-radius:8px; padding:1rem 1.2rem;
    margin-bottom:0.5rem;
}
.pf-sym { font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:700; color:#F0B90B; }

/* ── Tahmin band ── */
.fc-band { display:flex; gap:0; width:100%; border-radius:8px; overflow:hidden; margin-top:0.8rem; }
.fc-cell { flex:1; padding:0.7rem 0.5rem; text-align:center; }
.fc-cell-label { font-family:'JetBrains Mono',monospace; font-size:0.58rem; color:#5E6673; margin-bottom:0.3rem; text-transform:uppercase; }
.fc-cell-val { font-family:'Inter',sans-serif; font-size:0.95rem; font-weight:700; }
.fc-cell-pct { font-family:'JetBrains Mono',monospace; font-size:0.68rem; margin-top:0.1rem; }

/* ── Oneri kartı ── */
.oneri-card {
    background:#161A1E; border:1px solid #2B3139; border-left:3px solid #F0B90B;
    border-radius:8px; padding:1.2rem 1.4rem; margin-bottom:0.8rem;
}

/* ── DataFrame ── */
[data-testid="stDataFrame"] { font-family:'JetBrains Mono',monospace !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 3. HİSSE LİSTESİ
# ═══════════════════════════════════════════════════════════
bist_symbols = list(dict.fromkeys([
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","ALBRK","SKBNK","TSKB","KLNMA","QNBFB",
    "KCHOL","SAHOL","DOHOL","ALARK","ENKAI","AGHOL","TKFEN","NTHOL","GLYHO","POLHO","TAVHL",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL","KOZAA","ISDMR",
    "SISE","CIMSA","AKCNS","OYAKC","NUHCM","BTCIM","AFYON","GOLTS","BSOKE","ADANA","MRDIN","ANACM","TRKCM",
    "ARCLK","VESTL","BRISA","GOODY","SARKY","SODA","BAGFS",
    "FROTO","TOASO","DOAS","OTKAR","KARSN","ASUZU","TMSN","TTRAK",
    "THYAO","PGSUS","CLEBI","USAS","ULUSE",
    "BIMAS","MGROS","SOKM","AEFES","CCOLA","ULKER","TATGD","TUKAS","PNSUT","PETUN","KERVT","BANVT",
    "TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS","KAREL","INDES","NETAS","LOGO","MIATK",
    "ENJSA","AKSEN","ODAS","SMARTG","EUPWR","GESAN","CWENE","YEOTK","GWIND","NATEN","MAGEN","AYDEM","CANTE","ZOREN","AYEN","AKSA",
    "EKGYO","ISGYO","TRGYO","HLGYO","VKGYO","DZGYO","SNGYO","ZRGYO","PSGYO","RYGYO",
    "ROBIT","HATEK","FLAP","OSAS",
    "DEVA","SELEC","LKMNH","RTALB","ECILC","KORDS","VESBE","AYGAZ","ALKIM",
    "MAVI","ORGE","OSMEN","KLMSN","ACSEL","PGMT","KRPLAS","ANGEN","BIOEN","HUBVC","MERIT","SNKRN","GEREL","PKART",
]))
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

# ═══════════════════════════════════════════════════════════
# 4. YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════
def fmt_tl(v):
    try:
        if pd.isna(v): return "—"
        return f"TL {v:,.2f}"
    except: return "—"

def fmt_big(v):
    try:
        if pd.isna(v): return "—"
        if v >= 1e9: return f"TL {v/1e9:.2f} mlr"
        if v >= 1e6: return f"TL {v/1e6:.1f} mln"
        return f"TL {v:,.0f}"
    except: return "—"

def compute_rsi(s, p=14):
    try:
        d = s.diff().dropna()
        g = d.clip(lower=0).rolling(p).mean()
        l = (-d.clip(upper=0)).rolling(p).mean()
        r = g / l.replace(0, np.nan)
        v = (100 - 100/(1+r)).iloc[-1]
        return round(float(v),1) if pd.notna(v) else np.nan
    except: return np.nan

def compute_macd(s, f=12, sl=26, sig=9):
    try:
        ef = s.ewm(span=f,adjust=False).mean()
        es = s.ewm(span=sl,adjust=False).mean()
        m  = ef - es
        sg = m.ewm(span=sig,adjust=False).mean()
        return float(m.iloc[-1]), float(sg.iloc[-1]), float((m-sg).iloc[-1])
    except: return np.nan,np.nan,np.nan

def compute_atr(h,l,c,p=14):
    try:
        pc = c.shift(1)
        tr = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
        return float(tr.rolling(p).mean().iloc[-1])
    except: return np.nan

def get_signal(rsi, price, sma50):
    if pd.isna(rsi): return "TUT","#848E9C","hold"
    if rsi < 35 and price > sma50: return "GUCLU AL","#0ECB81","buy"
    if rsi < 45: return "AL","#0ECB81","buy"
    if rsi > 70: return "SAT","#F6465D","sell"
    if rsi > 65 and price < sma50: return "GUCLU SAT","#F6465D","sell"
    return "TUT","#848E9C","hold"

def monte_carlo(close, rsi, macd_h, price, sma50):
    if len(close) < 60: return None
    ret   = close.pct_change().dropna()
    mu    = float(ret.mean())
    sigma = float(ret.std())
    n_days= max(1,(datetime(datetime.today().year,12,31)-datetime.today()).days)
    n_sim = 3000
    score = 0.0
    if pd.notna(rsi):
        if rsi<35:   score+=0.4
        elif rsi<50: score+=0.15
        elif rsi>70: score-=0.4
        elif rsi>60: score-=0.15
    if pd.notna(macd_h): score += 0.3 if macd_h>0 else -0.3
    if pd.notna(price) and pd.notna(sma50) and sma50>0:
        score += 0.3 if price>sma50 else -0.3
    score = max(-1.0, min(1.0, score))
    mu_adj = mu + score*0.0008
    np.random.seed(42)
    sim = np.random.normal(mu_adj, sigma, (n_days, n_sim))
    paths = price * np.exp(np.cumsum(sim, axis=0))
    fp = paths[-1]
    return {
        "bull":float(np.percentile(fp,75)),
        "base":float(np.percentile(fp,50)),
        "bear":float(np.percentile(fp,25)),
        "p90": float(np.percentile(fp,90)),
        "p10": float(np.percentile(fp,10)),
        "prob_up":  float((fp>price*1.1).mean()*100),
        "prob_down":float((fp<price*0.9).mean()*100),
        "score":score, "n_days":n_days,
        "paths":paths[:,:60],
        "sigma_annual": sigma * np.sqrt(252) * 100,
    }

# ═══════════════════════════════════════════════════════════
# 5. VERİ ÇEKME FONKSİYONLARI
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=120, show_spinner=False)
def get_market_overview():
    syms = {"XU100.IS":"BIST 100","USDTRY=X":"Dolar/TL","EURTRY=X":"Euro/TL","GC=F":"Altin (USD)"}
    results = {}
    for ticker, label in syms.items():
        try:
            # Son 5 günlük veri — saatlik değişim için
            df = yf.download(ticker, period="5d", interval="1h", progress=False, auto_adjust=True)
            if df.empty or len(df) < 3: continue
            close = df["Close"].squeeze()
            curr  = float(close.iloc[-1])
            # 2 saatlik değişim
            prev2h = float(close.iloc[-3]) if len(close)>=3 else float(close.iloc[-2])
            chg2h  = (curr - prev2h) / prev2h * 100
            # Günlük değişim
            df_d = yf.download(ticker, period="2d", progress=False, auto_adjust=True)
            close_d = df_d["Close"].squeeze() if not df_d.empty else close
            prev_d  = float(close_d.iloc[-2]) if len(close_d)>=2 else curr
            chg_d   = (curr - prev_d) / prev_d * 100
            results[label] = {"price":curr,"chg2h":chg2h,"chg_d":chg_d,"ticker":ticker}
        except: continue
    return results

@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    end=datetime.today(); start=end-timedelta(days=90)
    rows=[]
    def proc(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df)<55: return None
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            chg   = (price-prev)/prev*100
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi   = compute_rsi(close)
            act,_,_ = get_signal(rsi, price, sma50)
            return {"Sembol":name,"Fiyat":price,"Degisim %":chg,"RSI":rsi,"Aksiyon":act}
        except: return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        futs = [ex.submit(proc, t, n) for t,n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futs):
            r = f.result()
            if r: rows.append(r)
    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def get_detail(ticker: str):
    stock = yf.Ticker(ticker)
    info, hist, news_out = {}, pd.DataFrame(), []
    try:
        info = stock.info or {}
        hist = stock.history(period="1y")
    except: pass
    try:
        raw = stock.news or []
        for n in raw:
            content = n.get("content",{})
            title   = content.get("title") or n.get("title","")
            link    = (content.get("canonicalUrl",{}) or {}).get("url") or n.get("link","")
            pub     = n.get("providerPublishTime") or 0
            if not pub:
                pd_str = content.get("pubDate","")
                try:
                    pub = int(datetime.fromisoformat(pd_str.replace("Z","")).timestamp())
                except: pub = 0
            publisher = (content.get("provider",{}) or {}).get("displayName") or n.get("publisher","Kaynak")
            summary  = content.get("summary","") or ""
            if title and pub > 1_000_000_000:
                news_out.append({
                    "title":title,"link":link,"publisher":publisher,
                    "date":datetime.fromtimestamp(pub).strftime("%d.%m.%Y %H:%M"),
                    "summary":summary,
                })
    except: pass
    return info, hist, news_out

@st.cache_data(ttl=300, show_spinner=False)
def get_price(ticker: str) -> float:
    try:
        df = yf.download(ticker, period="2d", progress=False, auto_adjust=True)
        if not df.empty: return float(df["Close"].squeeze().iloc[-1])
    except: pass
    return 0.0

# ═══════════════════════════════════════════════════════════
# 6. BAŞLIK + CANLI BANT
# ═══════════════════════════════════════════════════════════
st.markdown(
    '<div class="hero-name">Burak <span>Borsa</span> Analiz</div>'
    '<div class="hero-sub">// BIST · Derin Analiz · Portfoy Simulatoru · Beyin Takimi</div>',
    unsafe_allow_html=True)

# Canlı bant
with st.spinner(""):
    ov = get_market_overview()

if ov:
    order = ["BIST 100","Dolar/TL","Euro/TL","Altin (USD)"]
    cls_map= {"BIST 100":"bist","Dolar/TL":"dolar","Euro/TL":"euro","Altin (USD)":"dolar"}
    cols_ov = st.columns(len([k for k in order if k in ov]))
    ci = 0
    for lbl in order:
        if lbl not in ov: continue
        d = ov[lbl]
        p = d["price"]; c2 = d["chg2h"]; cd = d["chg_d"]
        cc = "#0ECB81" if c2>=0 else "#F6465D"
        cs = "+" if c2>=0 else ""
        cds= "+" if cd>=0 else ""
        cl = cls_map.get(lbl,"dolar")
        if lbl=="BIST 100":
            fp = f"{p:,.1f}"
        elif lbl=="Altin (USD)":
            fp = f"${p:,.1f}"
        else:
            fp = f"{p:,.4f}"
        cols_ov[ci].markdown(f"""
        <div class="ticker-item {cl}">
            <div class="ticker-label">{lbl}</div>
            <div class="ticker-price {cl}">{fp}</div>
            <div class="ticker-change" style="color:{cc};">{cs}{c2:.2f}% <span style="color:#5E6673;font-weight:400;font-size:0.7rem;">(2 saat)</span></div>
            <div class="ticker-change-sub">Gunluk: {cds}{cd:.2f}%</div>
        </div>""", unsafe_allow_html=True)
        ci += 1

st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 7. ANA SEKMELER
# ═══════════════════════════════════════════════════════════
tab_market, tab_detail, tab_portfolio = st.tabs([
    "  Piyasa  ",
    "  Derin Analiz  ",
    "  Portfoy & Oneri  ",
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1 — PİYASA GÖRÜNÜMÜ              ║
# ╚══════════════════════════════════════════╝
with tab_market:
    with st.spinner("Hisseler yukleniyor..."):
        df_mkt = fetch_market_data()

    if df_mkt.empty:
        st.error("Veri cekilemedi. Lutfen sayfayi yenileyin.")
        st.stop()

    total = len(df_mkt)
    ups   = int((df_mkt["Degisim %"]>0).sum())
    downs = int((df_mkt["Degisim %"]<0).sum())

    b1,b2,b3,b4 = st.columns([1,1,1,0.6])
    with b1:
        if st.button(f"Tum Hisseler  |  {total}", use_container_width=True):
            st.session_state.market_filter="TÜMÜ"
    with b2:
        if st.button(f"Yukselenler  |  {ups}", use_container_width=True):
            st.session_state.market_filter="YÜKSELENLER"
    with b3:
        if st.button(f"Dusenler  |  {downs}", use_container_width=True):
            st.session_state.market_filter="DÜŞENLER"
    with b4:
        if st.button("Yenile", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    df_fil = df_mkt.copy()
    if st.session_state.market_filter=="YÜKSELENLER":
        df_fil = df_fil[df_fil["Degisim %"]>0]
    elif st.session_state.market_filter=="DÜŞENLER":
        df_fil = df_fil[df_fil["Degisim %"]<0]

    st.markdown(f'<div class="sec-title">Piyasa — {st.session_state.market_filter}</div>',
                unsafe_allow_html=True)

    def style_mkt(df):
        s = df.style.format({"Fiyat":"TL {:,.2f}","Degisim %":"{:+.2f}%","RSI":"{:.1f}"}, na_rep="—")
        def cc(v):
            if pd.isna(v): return ''
            return 'color:#0ECB81;font-weight:600' if v>0 else ('color:#F6465D;font-weight:600' if v<0 else '')
        def ca(v):
            v=str(v)
            if "AL" in v: return 'color:#0ECB81;font-weight:700'
            if "SAT" in v: return 'color:#F6465D;font-weight:700'
            return 'color:#848E9C'
        return s.map(cc,subset=["Degisim %"]).map(ca,subset=["Aksiyon"])

    st.dataframe(style_mkt(df_fil[["Sembol","Fiyat","Degisim %","RSI","Aksiyon"]]),
                 use_container_width=True, height=480, hide_index=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 2 — DERİN ANALİZ                 ║
# ╚══════════════════════════════════════════╝
with tab_detail:
    # Hisse seçimi — anlık fiyatlı
    sa, sb = st.columns([3, 2])
    with sa:
        sel_sym = st.selectbox(
            "Hangi hisseyi analiz etmek istiyorsun?",
            sorted(bist_symbols),
            index=sorted(bist_symbols).index("THYAO") if "THYAO" in bist_symbols else 0,
            key="detail_sym")
    with sb:
        preview_p = get_price(f"{sel_sym}.IS")
        if preview_p > 0:
            st.markdown(f"""
            <div style="background:#0D1810;border:1px solid #1B4332;border-radius:8px;
            padding:0.8rem 1.1rem;margin-top:1.6rem;">
                <div class="ticker-label">{sel_sym} Anlık Fiyat</div>
                <div style="font-size:1.6rem;font-weight:800;color:#0ECB81;letter-spacing:-0.02em;">
                    TL {preview_p:,.2f}
                </div>
            </div>""", unsafe_allow_html=True)

    sel_ticker = f"{sel_sym}.IS"
    with st.spinner(f"{sel_sym} analiz ediliyor..."):
        info, hist, news = get_detail(sel_ticker)

    if hist.empty:
        st.warning("Bu hisse icin veri cekilemedi.")
    else:
        close  = hist["Close"].squeeze()
        curr_p = float(close.iloc[-1])
        prev_p = float(close.iloc[-2])
        chg    = curr_p - prev_p
        chg_p  = chg / prev_p * 100
        ch_col = "#0ECB81" if chg>=0 else "#F6465D"
        ch_s   = "+" if chg>=0 else ""

        # ── Fiyat kartı + Midas tarzı grafik ───────────────
        col_price, col_chart = st.columns([1, 2.2])

        with col_price:
            long_name = (info.get("longName","") or sel_sym) if info else sel_sym
            mkt_cap   = fmt_big(info.get("marketCap",np.nan) if info else np.nan)
            pe        = info.get("trailingPE",np.nan) if info else np.nan
            high52    = info.get("fiftyTwoWeekHigh", float(hist["High"].max())) if info else float(hist["High"].max())
            low52     = info.get("fiftyTwoWeekLow",  float(hist["Low"].min()))  if info else float(hist["Low"].min())

            st.markdown(f"""
            <div class="card" style="padding:1.6rem;">
                <div style="font-size:1.8rem;font-weight:800;color:#EAECEF;letter-spacing:-0.03em;">{sel_sym}</div>
                <div style="font-size:0.78rem;color:#5E6673;margin-bottom:1rem;">{long_name}</div>
                <div style="font-size:2.6rem;font-weight:800;color:#EAECEF;letter-spacing:-0.03em;line-height:1;">
                    TL {curr_p:,.2f}
                </div>
                <div style="color:{ch_col};font-size:1rem;font-weight:700;margin-top:0.3rem;">
                    {ch_s}TL {abs(chg):,.2f} &nbsp; {ch_s}{chg_p:.2f}%
                </div>
                <div style="margin-top:1.2rem;display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;">
                    <div style="background:#1E2329;border-radius:6px;padding:0.6rem 0.8rem;">
                        <div class="card-label">Piyasa Degeri</div>
                        <div style="font-size:0.88rem;font-weight:600;color:#EAECEF;">{mkt_cap}</div>
                    </div>
                    <div style="background:#1E2329;border-radius:6px;padding:0.6rem 0.8rem;">
                        <div class="card-label">F/K Orani</div>
                        <div style="font-size:0.88rem;font-weight:600;color:#EAECEF;">{f"{pe:.1f}" if pd.notna(pe) else "—"}</div>
                    </div>
                    <div style="background:#1E2329;border-radius:6px;padding:0.6rem 0.8rem;">
                        <div class="card-label">52H Yuksek</div>
                        <div style="font-size:0.88rem;font-weight:600;color:#0ECB81;">TL {high52:,.2f}</div>
                    </div>
                    <div style="background:#1E2329;border-radius:6px;padding:0.6rem 0.8rem;">
                        <div class="card-label">52H Dusuk</div>
                        <div style="font-size:0.88rem;font-weight:600;color:#F6465D;">TL {low52:,.2f}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        with col_chart:
            # Midas tarzı: sabit boyut, displayModeBar kapalı, hover iyi
            r,g,b = (14,203,129) if chg>=0 else (246,70,93)
            fig_main = go.Figure()
            fig_main.add_trace(go.Scatter(
                x=hist.index, y=close,
                mode="lines",
                line=dict(color=ch_col, width=1.8),
                fill="tozeroy",
                fillcolor=f"rgba({r},{g},{b},0.08)",
                hovertemplate="<b>%{x|%d %b %Y}</b><br>TL %{y:,.2f}<extra></extra>",
                name=sel_sym,
            ))
            # SMA50 çiz
            sma50_ser = close.rolling(50).mean()
            fig_main.add_trace(go.Scatter(
                x=hist.index, y=sma50_ser,
                mode="lines",
                line=dict(color="#F0B90B", width=1, dash="dot"),
                name="SMA-50",
                hovertemplate="SMA50: TL %{y:,.2f}<extra></extra>",
            ))
            fig_main.update_layout(
                plot_bgcolor="#0B0E11", paper_bgcolor="#0B0E11",
                margin=dict(l=50,r=10,t=15,b=35),
                height=260,   # Sabit yükseklik — büyümez
                xaxis=dict(
                    gridcolor="#1E2329", tickfont=dict(size=9,family="JetBrains Mono"),
                    showline=False, zeroline=False,
                ),
                yaxis=dict(
                    gridcolor="#1E2329", tickprefix="TL ",
                    tickfont=dict(size=9,family="JetBrains Mono"),
                    tickformat=",.0f", showline=False, zeroline=False, side="right",
                ),
                legend=dict(
                    bgcolor="rgba(0,0,0,0)", font=dict(size=9,color="#5E6673"),
                    x=0.01, y=0.99,
                ),
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#1E2329",bordercolor="#2B3139",
                                font=dict(family="JetBrains Mono",size=11)),
            )
            st.plotly_chart(fig_main, use_container_width=True,
                            config={"displayModeBar":False, "scrollZoom":False})

        # ── İndikatörler ──────────────────────────────────
        rsi_14 = compute_rsi(close)
        macd_v, macd_s, macd_h = compute_macd(close)
        sma50  = float(close.rolling(50).mean().iloc[-1]) if len(close)>=50 else curr_p
        atr_14 = compute_atr(hist["High"].squeeze(), hist["Low"].squeeze(), close)
        act_lbl, act_col, act_cls = get_signal(rsi_14, curr_p, sma50)
        target = curr_p + 2*atr_14 if pd.notna(atr_14) else np.nan
        atr_pct = (atr_14/curr_p*100) if pd.notna(atr_14) and curr_p>0 else 0

        i1,i2,i3,i4,i5 = st.columns(5)
        def icard(col, label, val, cls="white", sub=""):
            col.markdown(
                f'<div class="card"><div class="card-label">{label}</div>'
                f'<div class="card-value {cls}" style="font-size:1.25rem;">{val}</div>'
                + (f'<div class="card-sub">{sub}</div>' if sub else '') +
                '</div>', unsafe_allow_html=True)

        icard(i1,"RSI (14)",
              f"{rsi_14:.1f}" if pd.notna(rsi_14) else "—",
              "green" if pd.notna(rsi_14) and rsi_14<40 else "red" if pd.notna(rsi_14) and rsi_14>65 else "white",
              "Asiri satim" if pd.notna(rsi_14) and rsi_14<30 else "Asiri alim" if pd.notna(rsi_14) and rsi_14>70 else "Notr")
        icard(i2,"MACD Hist",
              f"{macd_h:+.3f}" if pd.notna(macd_h) else "—",
              "green" if pd.notna(macd_h) and macd_h>0 else "red",
              "Yukari momentum" if pd.notna(macd_h) and macd_h>0 else "Asagi momentum")
        icard(i3,"SMA-50",
              fmt_tl(sma50),
              "green" if curr_p>sma50 else "red",
              "Fiyat uzerinde" if curr_p>sma50 else "Fiyat altinda")
        icard(i4,"ATR Volatilite",f"%{atr_pct:.2f}","white","Gunluk ort. salınim")
        icard(i5,"Sinyal",act_lbl,
              "green" if "AL" in act_lbl else "red" if "SAT" in act_lbl else "white")

        # ── Yıl Sonu Monte Carlo ──────────────────────────
        st.markdown('<div class="sec-title">Yil Sonu Fiyat Tahmini — Monte Carlo (3.000 sim)</div>',
                    unsafe_allow_html=True)

        fc = monte_carlo(close, rsi_14, macd_h, curr_p, sma50)
        if fc:
            days_left = fc["n_days"]
            bull_r = (fc["bull"]-curr_p)/curr_p*100
            base_r = (fc["base"]-curr_p)/curr_p*100
            bear_r = (fc["bear"]-curr_p)/curr_p*100
            p90_r  = (fc["p90"]-curr_p)/curr_p*100
            p10_r  = (fc["p10"]-curr_p)/curr_p*100

            mc1,mc2,mc3,mc4,mc5 = st.columns(5)
            for col,(lbl,val,ret,clr) in zip(
                [mc1,mc2,mc3,mc4,mc5],
                [("P90 (En Iy)",fc["p90"],p90_r,"green"),
                 ("Bull %75",   fc["bull"],bull_r,"green"),
                 ("Baz %50",    fc["base"],base_r,"blue" if base_r>=0 else "red"),
                 ("Bear %25",   fc["bear"],bear_r,"red"),
                 ("P10 (En Ko)",fc["p10"], p10_r,"red")]):
                col.markdown(
                    f'<div class="card"><div class="card-label">{lbl}</div>'
                    f'<div class="card-value {clr}" style="font-size:1.1rem;">TL {val:,.2f}</div>'
                    f'<div class="card-sub" style="color:{"#0ECB81" if ret>=0 else "#F6465D"};">{ret:+.1f}%</div>'
                    '</div>', unsafe_allow_html=True)

            # Olasılık ve Volatilite
            pb1,pb2,pb3 = st.columns(3)
            pb1.markdown(f"""
            <div class="card" style="margin-top:0.5rem;">
                <div class="card-label">%10+ Yukari Olasiligi</div>
                <div class="card-value green">{fc['prob_up']:.0f}%</div>
                <div class="gauge-bar"><div class="gauge-fill" style="width:{fc['prob_up']}%;background:#0ECB81;"></div></div>
            </div>""", unsafe_allow_html=True)
            pb2.markdown(f"""
            <div class="card" style="margin-top:0.5rem;">
                <div class="card-label">%10+ Asagi Olasiligi</div>
                <div class="card-value red">{fc['prob_down']:.0f}%</div>
                <div class="gauge-bar"><div class="gauge-fill" style="width:{fc['prob_down']}%;background:#F6465D;"></div></div>
            </div>""", unsafe_allow_html=True)
            pb3.markdown(f"""
            <div class="card" style="margin-top:0.5rem;">
                <div class="card-label">Yillik Volatilite</div>
                <div class="card-value yellow">{fc['sigma_annual']:.1f}%</div>
                <div class="card-sub">{days_left} gun kaldi · Yil sonuna</div>
            </div>""", unsafe_allow_html=True)

            # Monte Carlo Fan Grafiği — sabit boyut
            fig_mc = go.Figure()
            today_dt = datetime.today()
            dates_mc = [today_dt + timedelta(days=i) for i in range(len(fc["paths"]))]
            paths = fc["paths"]
            for i in range(paths.shape[1]):
                alpha = 0.08 if fc["score"]>0 else 0.06
                col_mc = f"rgba(14,203,129,{alpha})" if fc["score"]>0 else f"rgba(246,70,93,{alpha})"
                fig_mc.add_trace(go.Scatter(
                    x=dates_mc, y=paths[:,i], mode="lines",
                    line=dict(width=0.4, color=col_mc),
                    showlegend=False, hoverinfo="skip"))
            for val,c,nm in [
                (fc["bull"],"#0ECB81","Bull %75"),
                (fc["base"],"#1E90FF","Baz %50"),
                (fc["bear"],"#F6465D","Bear %25"),
            ]:
                fig_mc.add_hline(y=val,line=dict(color=c,width=1.5,dash="dash"),
                                 annotation_text=nm,annotation_font=dict(color=c,size=9))
            fig_mc.add_hline(y=curr_p,line=dict(color="#848E9C",width=1),
                             annotation_text="Simdi",annotation_font=dict(color="#848E9C",size=9))
            fig_mc.update_layout(
                plot_bgcolor="#0B0E11", paper_bgcolor="#0B0E11",
                margin=dict(l=65,r=15,t=15,b=35), height=240,
                xaxis=dict(gridcolor="#1E2329",tickfont=dict(size=8,family="JetBrains Mono")),
                yaxis=dict(gridcolor="#1E2329",tickprefix="TL ",tickformat=",.0f",
                           tickfont=dict(size=8,family="JetBrains Mono"),side="right"),
                hovermode=False,
            )
            st.plotly_chart(fig_mc, use_container_width=True,
                            config={"displayModeBar":False,"scrollZoom":False})

        # ── BEYİN TAKIMI ANALİZİ ──────────────────────────
        st.markdown('<div class="sec-title">Beyin Takimi Analizi</div>', unsafe_allow_html=True)

        # Kapsamlı hesaplamalar
        trend_pos   = curr_p > sma50
        range52     = high52 - low52
        pos52       = (curr_p - low52)/range52*100 if range52>0 else 50
        vol_score   = "Dusuk" if pd.notna(atr_pct) and atr_pct<2 else ("Yuksek" if pd.notna(atr_pct) and atr_pct>5 else "Orta")

        # Teknik puanlama (0-100)
        tech_score = 50
        if pd.notna(rsi_14):
            if rsi_14 < 35:   tech_score += 25
            elif rsi_14 < 50: tech_score += 10
            elif rsi_14 > 70: tech_score -= 25
            elif rsi_14 > 60: tech_score -= 10
        if pd.notna(macd_h):
            tech_score += 15 if macd_h > 0 else -15
        if trend_pos: tech_score += 10
        else:         tech_score -= 10
        tech_score = max(0, min(100, tech_score))

        # Risk seviyesi
        if pd.notna(rsi_14) and rsi_14>70:
            risk_lv, risk_col = "YUKSEK","#F6465D"
            risk_txt = (f"RSI {rsi_14:.0f} ile hisse asiri alim bolgesinde. "
                "Teknik yorgunluk belirtileri var. Kisa vadede kar satislari gelebilir. "
                "Bu bolgede yeni pozisyon acmak risk/odul dengesi acisindan elverisli degil.")
            strateji = ("Mevcut pozisyonlarda stop-loss seviyelerini guncelleyin. "
                f"Yeni alis icin RSI'in 55 altina ya da SMA-50'ye (TL {sma50:,.2f}) gerileme bekleyin. "
                "Pozisyon buyuklugunuzu azaltmayi degerlendirebilirsiniz.")
        elif pd.notna(rsi_14) and rsi_14<35:
            risk_lv, risk_col = "DUSUK (FIRSAT)","#0ECB81"
            risk_txt = (f"RSI {rsi_14:.0f} ile hisse asiri satim bolgesinde. "
                "Satis baskisi yavaslama emaresi veriyor. "
                f"52 haftalik aralikta alt %{pos52:.0f} civarinda seyrediyor — tarihsel olarak iskontolu.")
            strateji = ("Kademeli birikim (DCA) stratejisi uygulanabilir. "
                "MACD histogram pozitife donene kadar tam pozisyon almayiniz. "
                f"Stop-loss icin 52 hafta dibi TL {low52:,.2f} referans alinabilir.")
        else:
            risk_lv, risk_col = "ORTA","#F0B90B"
            risk_txt = (f"RSI {rsi_14:.0f if pd.notna(rsi_14) else '—'} ile notr bolgede. "
                "Belirgin bir asiri fiyatlama ya da iskonto sinyali yok. "
                "Hissenin yonu hacim verisi ve makro gelismelere daha duyarli.")
            strateji = ("Trend dogrulama icin islem hacmini takip edin. "
                f"SMA-50 ({fmt_tl(sma50)}) uzerindeki kapanislar surdugunce tutma uygun. "
                "Kirilis durumunda pozisyon azaltilmali.")

        # Consensus
        if fc:
            sc = fc["score"]
            if sc>0.4:   cons,cons_c="GUCLU POZITIF","#0ECB81"
            elif sc>0:   cons,cons_c="TEMKINLI POZITIF","#34d399"
            elif sc>-0.4:cons,cons_c="TEMKINLI NEGATIF","#F0B90B"
            else:        cons,cons_c="GUCLU NEGATIF","#F6465D"
        else: cons,cons_c="Yeterli veri yok","#848E9C"

        score_bar_w = tech_score
        score_col   = "#0ECB81" if tech_score>60 else "#F6465D" if tech_score<40 else "#F0B90B"

        brain_html = f"""
        <div class="brain-wrap">
            <div class="brain-header">
                Beyin Takimi — {sel_sym}
                <span class="brain-signal {'buy' if 'AL' in act_lbl else 'sell' if 'SAT' in act_lbl else 'hold'}">{act_lbl}</span>
            </div>

            <div class="brain-row">
                <div class="brain-block">
                    <div class="brain-block-title">Teknik Puan</div>
                    <div style="font-size:1.6rem;font-weight:800;color:{score_col};letter-spacing:-0.02em;">{tech_score}<span style="font-size:0.8rem;color:#5E6673;">/100</span></div>
                    <div class="gauge-bar" style="margin-top:0.5rem;"><div class="gauge-fill" style="width:{score_bar_w}%;background:{score_col};"></div></div>
                    <div class="card-sub" style="margin-top:0.3rem;">RSI + MACD + Trend birlesimi</div>
                </div>
                <div class="brain-block">
                    <div class="brain-block-title">Trend Durumu</div>
                    <div class="brain-block-text">
                        <b style="color:{'#0ECB81' if trend_pos else '#F6465D'};">
                            {'Yukselis Trendinde' if trend_pos else 'Dusus Trendinde'}
                        </b><br>
                        SMA-50: TL {sma50:,.2f}<br>
                        MACD: <span style="color:{'#0ECB81' if pd.notna(macd_h) and macd_h>0 else '#F6465D'};">
                            {'Pozitif (yukari momentum)' if pd.notna(macd_h) and macd_h>0 else 'Negatif (asagi momentum)'}
                        </span><br>
                        52H Araliginda: <b>%{pos52:.0f}</b> konumunda<br>
                        Volatilite: <b>{vol_score}</b> (ATR %{atr_pct:.2f})
                    </div>
                </div>
            </div>

            <div class="brain-row">
                <div class="brain-block">
                    <div class="brain-block-title">Risk Analizi — <span style="color:{risk_col};">{risk_lv}</span></div>
                    <div class="brain-block-text">{risk_txt}</div>
                </div>
                <div class="brain-block">
                    <div class="brain-block-title">Strateji Onerisi</div>
                    <div class="brain-block-text">{strateji}</div>
                </div>
            </div>

            <div class="brain-row">
                <div class="brain-block brain-full">
                    <div class="brain-block-title">Beyin Takimi Konsensus</div>
                    <div style="font-size:1rem;font-weight:700;color:{cons_c};margin-bottom:0.5rem;">{cons}</div>
                    <div class="brain-block-text">
                        {'Monte Carlo ' + str(fc["n_days"]) + " gunluk simülasyon: Baz senaryo TL " + f"{fc['base']:,.2f}" + f" ({base_r:+.1f}%). " if fc else ""}
                        {"Yukari olasilik %" + f"{fc['prob_up']:.0f}" + " — asagi olasilik %" + f"{fc['prob_down']:.0f}." if fc else ""}
                        {"Yillik volatilite: %" + f"{fc['sigma_annual']:.1f}." if fc else ""}
                    </div>
                </div>
            </div>
        </div>"""
        st.markdown(brain_html, unsafe_allow_html=True)

        # ── HABERLER — tıklanınca detay ──────────────────
        st.markdown('<div class="sec-title">Haber Akisi — Son Haberler</div>',
                    unsafe_allow_html=True)

        if not news:
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title-text">Hisse haberi bulunamadi</div>
                <div class="news-meta">
                    <a href="https://www.kap.org.tr/tr/arama/bilesik?bildirimTipleri=OzelDurumAciklamasi&sirketler={sel_sym}"
                       target="_blank" style="color:#1E90FF;text-decoration:none;">
                       KAP Bildirimlerini Goruntule
                    </a>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            news_key = f"news_{sel_sym}"
            if news_key not in st.session_state:
                st.session_state[news_key] = None

            for ni, n in enumerate(news[:10]):
                # Başlığı daha ilgi çekici formatla
                title = n["title"]
                date  = n["date"]
                pub   = n["publisher"]
                link  = n["link"]
                summary = n.get("summary","")

                is_active = st.session_state.get(news_key) == ni
                card_cls  = "news-card active" if is_active else "news-card"

                st.markdown(f"""
                <div class="{card_cls}" onclick="void(0)">
                    <div class="news-title-text">{title}</div>
                    <div class="news-meta">{pub} &nbsp;·&nbsp; {date}
                        &nbsp;·&nbsp;
                        <a href="{link}" target="_blank" style="color:#F0B90B;text-decoration:none;">
                            Kaynaga Git
                        </a>
                    </div>
                </div>""", unsafe_allow_html=True)

                btn_lbl = "Haberi Kapat" if is_active else "Detayli Incele"
                if st.button(btn_lbl, key=f"news_btn_{sel_sym}_{ni}", use_container_width=False):
                    st.session_state[news_key] = None if is_active else ni
                    st.rerun()

                if is_active:
                    # Özet yoksa kısa analiz üret
                    if summary:
                        detail_body = summary
                    else:
                        detail_body = (
                            f"Bu haber {pub} tarafindan {date} tarihinde yayinlandi. "
                            f"{sel_sym} ({long_name}) hissenin guncel durumu ve piyasa kosullari cercevesinde "
                            f"degerlendirildiginde, bu gelisme yatirimcilar tarafindan yakindan takip edilmektedir. "
                            f"Tam haberi okumak icin asagidaki kaynaga gidiniz."
                        )

                    st.markdown(f"""
                    <div class="news-detail">
                        <div class="news-detail-title">{title}</div>
                        <div class="news-detail-body">{detail_body}</div>
                        <div style="margin-top:1rem;">
                            <a href="{link}" target="_blank"
                               style="color:#F0B90B;font-weight:600;font-size:0.85rem;text-decoration:none;">
                               Tam Haberi Oku &rarr;
                            </a>
                        </div>
                    </div>""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 3 — PORTFÖY & AKILLI ÖNERİ      ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    pf_tab1, pf_tab2 = st.tabs(["  Portfoyum  ","  Akilli Oneri Motoru  "])

    # ════════════════════════════════════════
    #  ALT SEKME 1: PORTFÖYÜM
    # ════════════════════════════════════════
    with pf_tab1:
        st.markdown('<div class="sec-title">Portfoyume Hisse Ekle</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#1A1C24;border:1px solid #1E2329;border-left:3px solid #F0B90B;
        border-radius:8px;padding:0.9rem 1.1rem;margin-bottom:1rem;font-size:0.83rem;color:#5E6673;">
        <b style="color:#F0B90B;">Nasil kullanilir?</b> &nbsp;
        Hisse sec → kac adet aldigini gir → hangi fiyattan aldigini gir → Ekle.
        Sistem yil sonu tahminini otomatik hesaplar.
        </div>""", unsafe_allow_html=True)

        pa, pb = st.columns([3, 2])
        with pa:
            add_sym = st.selectbox("Hisse", sorted(bist_symbols), key="pf_add_sym")
        with pb:
            pp = get_price(f"{add_sym}.IS")
            if pp > 0:
                st.markdown(f"""
                <div style="background:#0D1810;border:1px solid #1B4332;border-radius:8px;
                padding:0.75rem 1rem;margin-top:1.6rem;">
                    <div class="ticker-label">{add_sym} Anlık Fiyat</div>
                    <div style="font-size:1.5rem;font-weight:800;color:#0ECB81;letter-spacing:-0.02em;">
                        TL {pp:,.2f}
                    </div>
                </div>""", unsafe_allow_html=True)

        pc1, pc2, pc3 = st.columns([2, 2, 1])
        with pc1:
            add_adet = st.number_input("Kac adet?", min_value=1, value=10, step=5, key="pf_adet")
        with pc2:
            add_mal  = st.number_input("Hangi fiyattan aldin? (TL)",
                                       min_value=0.01,
                                       value=round(pp,2) if pp>0 else 10.0,
                                       step=0.5, format="%.2f", key="pf_mal")
        with pc3:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            if st.button("Ekle", type="primary", use_container_width=True):
                st.session_state.portfolio[add_sym] = {"adet":add_adet,"maliyet":add_mal}
                st.success(f"{add_sym} eklendi!"); st.rerun()

        # Anlık hesap önizleme
        if pp > 0:
            t_mal = add_adet * add_mal
            t_gun = add_adet * pp
            fark  = t_gun - t_mal
            fc    = "#0ECB81" if fark>=0 else "#F6465D"
            fs    = "+" if fark>=0 else ""
            st.markdown(f"""
            <div style="background:#1E2329;border:1px solid #2B3139;border-radius:8px;
            padding:0.8rem 1.1rem;display:flex;gap:2rem;flex-wrap:wrap;margin:0.5rem 0;">
                <div><div class="card-label">Toplam Yatirim</div>
                     <div style="font-size:1rem;font-weight:700;color:#EAECEF;">TL {t_mal:,.0f}</div></div>
                <div><div class="card-label">Simdi Degeri</div>
                     <div style="font-size:1rem;font-weight:700;color:{fc};">TL {t_gun:,.0f}</div></div>
                <div><div class="card-label">Kar / Zarar</div>
                     <div style="font-size:1rem;font-weight:700;color:{fc};">{fs}TL {abs(fark):,.0f}</div></div>
            </div>""", unsafe_allow_html=True)

        # ── Portföy listesi ─────────────────────────────
        if not st.session_state.portfolio:
            st.markdown("""
            <div class="card" style="text-align:center;padding:3rem;margin-top:1rem;">
                <div style="font-size:2rem;margin-bottom:0.6rem;">📂</div>
                <div style="color:#5E6673;font-size:0.9rem;">Portfoy bos. Yukaridaki formdan hisse ekleyin.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="sec-title">Portfoy Ozeti</div>', unsafe_allow_html=True)

            t_yat=t_gun2=t_bull=t_base=t_bear=0.0
            rows=[]
            pb_bar = st.progress(0,"Analiz yapiliyor...")
            syms_pf = list(st.session_state.portfolio.keys())

            for i,sym in enumerate(syms_pf):
                pb_bar.progress((i+1)/len(syms_pf), f"Analiz: {sym}...")
                d = st.session_state.portfolio[sym]
                try:
                    _, h_pf, _ = get_detail(f"{sym}.IS")
                    if h_pf.empty: continue
                    cl = h_pf["Close"].squeeze()
                    cp = float(cl.iloc[-1])
                    ri = compute_rsi(cl)
                    _,_,mh = compute_macd(cl)
                    sm = float(cl.rolling(50).mean().iloc[-1]) if len(cl)>=50 else cp
                    fc_pf = monte_carlo(cl,ri,mh,cp,sm)
                    adet2=d["adet"]; mal2=d["maliyet"]
                    ty=adet2*mal2; tg=adet2*cp
                    kar=tg-ty; kp=(kar/ty*100) if ty>0 else 0
                    bv=adet2*fc_pf["bull"] if fc_pf else tg
                    bav=adet2*fc_pf["base"] if fc_pf else tg
                    bev=adet2*fc_pf["bear"] if fc_pf else tg
                    br=(fc_pf["bull"]-cp)/cp*100 if fc_pf else 0
                    bar2=(fc_pf["base"]-cp)/cp*100 if fc_pf else 0
                    ber=(fc_pf["bear"]-cp)/cp*100 if fc_pf else 0
                    t_yat+=ty; t_gun2+=tg; t_bull+=bv; t_base+=bav; t_bear+=bev
                    rows.append({"sym":sym,"adet":adet2,"mal":mal2,"cp":cp,
                                 "ty":ty,"tg":tg,"kar":kar,"kp":kp,
                                 "bv":bv,"bav":bav,"bev":bev,"br":br,"bar":bar2,"ber":ber,"rsi":ri})
                except: continue
            pb_bar.empty()

            pnl=t_gun2-t_yat; pnl_p=(pnl/t_yat*100) if t_yat>0 else 0
            bk=t_bull-t_yat; bak=t_base-t_yat; bek=t_bear-t_yat
            pc="green" if pnl>=0 else "red"; ps="+" if pnl>=0 else ""

            k1,k2,k3,k4 = st.columns(4)
            k1.markdown(f'<div class="card"><div class="card-label">Toplam Yatirim</div><div class="card-value white" style="font-size:1.2rem;">TL {t_yat:,.0f}</div></div>',unsafe_allow_html=True)
            k2.markdown(f'<div class="card"><div class="card-label">Simdi Degeri</div><div class="card-value white" style="font-size:1.2rem;">TL {t_gun2:,.0f}</div></div>',unsafe_allow_html=True)
            k3.markdown(f'<div class="card"><div class="card-label">Kar / Zarar</div><div class="card-value {pc}" style="font-size:1.2rem;">{ps}TL {abs(pnl):,.0f} ({ps}{pnl_p:.1f}%)</div></div>',unsafe_allow_html=True)
            k4.markdown(f'<div class="card"><div class="card-label">Hisse Sayisi</div><div class="card-value white" style="font-size:1.2rem;">{len(rows)}</div></div>',unsafe_allow_html=True)

            st.markdown('<div class="sec-title">Yil Sonu Tahmini</div>', unsafe_allow_html=True)
            y1,y2,y3 = st.columns(3)
            y1.markdown(f"""<div class="forecast-card" style="background:#0D2E1A;border:1px solid #1B4332;border-radius:8px;padding:1.1rem;">
                <div class="card-label">En Iyi Senaryo</div>
                <div style="font-size:1.6rem;font-weight:800;color:#0ECB81;">TL {t_bull:,.0f}</div>
                <div style="color:#0ECB81;font-size:0.85rem;">+TL {bk:,.0f} &nbsp; ({bk/t_yat*100:+.1f}%)</div>
            </div>""", unsafe_allow_html=True)
            y2.markdown(f"""<div style="background:#0D1525;border:1px solid #1A3A6B;border-radius:8px;padding:1.1rem;">
                <div class="card-label">Ortalama Senaryo</div>
                <div style="font-size:1.6rem;font-weight:800;color:#1E90FF;">TL {t_base:,.0f}</div>
                <div style="color:#1E90FF;font-size:0.85rem;">{bak/t_yat*100:+.1f}%</div>
            </div>""", unsafe_allow_html=True)
            y3.markdown(f"""<div style="background:#1A0A0D;border:1px solid #4A1020;border-radius:8px;padding:1.1rem;">
                <div class="card-label">Kotu Senaryo</div>
                <div style="font-size:1.6rem;font-weight:800;color:#F6465D;">TL {t_bear:,.0f}</div>
                <div style="color:#F6465D;font-size:0.85rem;">{bek/t_yat*100:+.1f}%</div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div class="sec-title">Hisselerim</div>', unsafe_allow_html=True)
            for row in rows:
                kc="#0ECB81" if row["kar"]>=0 else "#F6465D"
                ks="+" if row["kar"]>=0 else ""
                fd=row["cp"]-row["mal"]; fdc="#0ECB81" if fd>=0 else "#F6465D"; fds="+" if fd>=0 else ""
                rc="#0ECB81" if pd.notna(row["rsi"]) and row["rsi"]<40 else "#F6465D" if pd.notna(row["rsi"]) and row["rsi"]>65 else "#848E9C"

                hc1,hc2,hc3 = st.columns([3,4,0.8])
                with hc1:
                    st.markdown(f"""
                    <div class="pf-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="pf-sym">{row['sym']}</div>
                            <div style="font-size:0.68rem;color:#5E6673;">{row['adet']} adet</div>
                        </div>
                        <div style="display:flex;gap:1.5rem;margin-top:0.6rem;flex-wrap:wrap;">
                            <div><div class="card-label">Alisin</div>
                                 <div style="font-size:0.88rem;font-weight:600;color:#EAECEF;">TL {row['mal']:,.2f}</div></div>
                            <div><div class="card-label">Simdi</div>
                                 <div style="font-size:0.88rem;font-weight:600;color:#EAECEF;">TL {row['cp']:,.2f}</div>
                                 <div style="font-size:0.72rem;color:{fdc};">{fds}TL {abs(fd):,.2f}</div></div>
                            <div><div class="card-label">Yatirim</div>
                                 <div style="font-size:0.88rem;font-weight:600;color:#EAECEF;">TL {row['ty']:,.0f}</div></div>
                        </div>
                        <div style="margin-top:0.6rem;padding-top:0.5rem;border-top:1px solid #1E2329;
                        display:flex;justify-content:space-between;">
                            <span style="color:{kc};font-weight:700;">{ks}TL {abs(row['kar']):,.0f} ({ks}{row['kp']:.1f}%)</span>
                            <span style="color:{rc};font-size:0.72rem;">RSI {row['rsi']:.0f if pd.notna(row['rsi']) else '—'}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

                with hc2:
                    st.markdown(f"""
                    <div class="pf-card">
                        <div class="card-label" style="margin-bottom:0.6rem;">Yil Sonu Tahmin ({row['adet']} adet)</div>
                        <div class="fc-band">
                            <div class="fc-cell" style="background:#0D2E1A;border-radius:6px 0 0 6px;border:1px solid #1B4332;">
                                <div class="fc-cell-label">En Iyi</div>
                                <div class="fc-cell-val" style="color:#0ECB81;">TL {row['bv']:,.0f}</div>
                                <div class="fc-cell-pct" style="color:#0ECB81;">+{row['br']:.0f}%</div>
                            </div>
                            <div class="fc-cell" style="background:#0D1525;border:1px solid #1A3A6B;border-left:none;border-right:none;">
                                <div class="fc-cell-label">Ortalama</div>
                                <div class="fc-cell-val" style="color:#1E90FF;">TL {row['bav']:,.0f}</div>
                                <div class="fc-cell-pct" style="color:#1E90FF;">{row['bar']:+.0f}%</div>
                            </div>
                            <div class="fc-cell" style="background:#1A0A0D;border-radius:0 6px 6px 0;border:1px solid #4A1020;">
                                <div class="fc-cell-label">Kotu</div>
                                <div class="fc-cell-val" style="color:#F6465D;">TL {row['bev']:,.0f}</div>
                                <div class="fc-cell-pct" style="color:#F6465D;">{row['ber']:+.0f}%</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                with hc3:
                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                    if st.button("Sil", key=f"del_{row['sym']}", use_container_width=True):
                        del st.session_state.portfolio[row["sym"]]; st.rerun()

    # ════════════════════════════════════════
    #  ALT SEKME 2: AKILLI ÖNERİ MOTORU
    # ════════════════════════════════════════
    with pf_tab2:
        st.markdown('<div class="sec-title">Akilli Oneri Motoru — Borsaci Analiz Beyni</div>',
                    unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#0F1318;border:1px solid #1E2329;border-left:3px solid #0ECB81;
        border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;font-size:0.83rem;color:#5E6673;">
        <b style="color:#0ECB81;">Borsaci Analiz Beyni</b> aktif.<br>
        Butceni gir, risk profilini sec. Sistem 150+ BIST hissesini RSI, MACD, Momentum,
        Volatilite ve Teknik Skor kriterleriyle tarar. Her hisse icin Monte Carlo yil sonu
        tahmini hesaplar. Portfoyunde hisse varsa SAT / TUT / EKLE sinyali verir.
        </div>""", unsafe_allow_html=True)

        oa,ob,oc = st.columns([2,2,1])
        with oa:
            butce = st.number_input("Butcen? (TL)", min_value=500, max_value=10_000_000,
                                    value=10_000, step=500, format="%d")
        with ob:
            risk_p = st.selectbox("Risk Profili",
                                  ["Dusuk — Buyuk, Guvenli Sirketler",
                                   "Orta — Karma Portfoy",
                                   "Yuksek — Buyuyebilecek Kucuk Hisseler"])
        with oc:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            go_btn = st.button("Analiz Et", type="primary", use_container_width=True)

        if go_btn:
            with st.spinner("Borsaci Beyni calisiyor — 150+ hisse taranıyor..."):
                df_sc = fetch_market_data().copy()

            if df_sc.empty:
                st.error("Veri cekilemedi.")
            else:
                if "Dusuk" in risk_p:
                    wl = ["AKBNK","GARAN","ISCTR","YKBNK","KCHOL","SAHOL","EREGL",
                          "FROTO","TOASO","THYAO","TCELL","BIMAS","ARCLK","SISE",
                          "TUPRS","ENKAI","AKSEN","TTKOM","ALARK","CCOLA"]
                    df_sc = df_sc[df_sc["Sembol"].isin(wl)]
                elif "Yuksek" in risk_p:
                    wl = ["ASTOR","SMARTG","EUPWR","GESAN","CWENE","YEOTK","GWIND",
                          "MAGEN","ROBIT","HATEK","MAVI","ORGE","OSMEN","KLMSN",
                          "ACSEL","PGMT","ANGEN","BIOEN","HUBVC","MERIT","SNKRN"]
                    df_sc = df_sc[df_sc["Sembol"].isin(wl)]

                df_sc = df_sc[df_sc["RSI"] < 65].copy()

                def calc_score(row):
                    s=0; rsi=row.get("RSI",50); act=str(row.get("Aksiyon",""))
                    if pd.notna(rsi):
                        if rsi<35: s+=45
                        elif rsi<45: s+=28
                        elif rsi<55: s+=12
                    if "GUCLU AL" in act: s+=35
                    elif "AL" in act: s+=22
                    chg=row.get("Degisim %",0)
                    if pd.notna(chg) and chg>0: s+=10
                    return s

                df_sc["Skor"] = df_sc.apply(calc_score, axis=1)
                df_sc = df_sc.sort_values("Skor", ascending=False).head(5)

                # Monte Carlo her hisse için
                mc_res = {}
                with st.spinner("Monte Carlo hesaplaniyor..."):
                    for _, row in df_sc.iterrows():
                        sym = row["Sembol"]
                        try:
                            _, h_mc, _ = get_detail(f"{sym}.IS")
                            if not h_mc.empty:
                                cl = h_mc["Close"].squeeze()
                                ri = compute_rsi(cl)
                                _,_,mh = compute_macd(cl)
                                sm = float(cl.rolling(50).mean().iloc[-1]) if len(cl)>=50 else float(cl.iloc[-1])
                                mc_res[sym] = monte_carlo(cl,ri,mh,float(cl.iloc[-1]),sm)
                        except: mc_res[sym]=None

                n_h = len(df_sc); hb = butce/n_h
                t_bull_o=t_base_o=t_bear_o=0.0
                for _, row in df_sc.iterrows():
                    sym=row["Sembol"]; f=row["Fiyat"]; a=int(hb/f) if f>0 else 0
                    fc2=mc_res.get(sym)
                    if fc2 and a>0:
                        t_bull_o+=a*fc2["bull"]; t_base_o+=a*fc2["base"]; t_bear_o+=a*fc2["bear"]
                    elif a>0:
                        t_bull_o+=a*f; t_base_o+=a*f; t_bear_o+=a*f

                # Özet banner
                st.markdown(f"""
                <div style="background:#0D1F12;border:1px solid #1B4332;border-radius:10px;
                padding:1.2rem 1.4rem;margin:1rem 0;">
                    <div style="font-size:0.7rem;color:#5E6673;margin-bottom:0.6rem;text-transform:uppercase;letter-spacing:0.08em;">
                        Borsaci Oneri Ozeti — {n_h} hisse · TL {butce:,.0f} butce · Monte Carlo 3.000 sim
                    </div>
                    <div style="display:flex;gap:2.5rem;flex-wrap:wrap;">
                        <div><div class="card-label">Yatirilan</div>
                             <div style="font-size:1.2rem;font-weight:800;color:#EAECEF;">TL {butce:,.0f}</div></div>
                        <div><div class="card-label">En Iyi Senaryo</div>
                             <div style="font-size:1.2rem;font-weight:800;color:#0ECB81;">TL {t_bull_o:,.0f}
                             <span style="font-size:0.8rem;">({(t_bull_o/butce-1)*100:+.1f}%)</span></div></div>
                        <div><div class="card-label">Ortalama Senaryo</div>
                             <div style="font-size:1.2rem;font-weight:800;color:#1E90FF;">TL {t_base_o:,.0f}
                             <span style="font-size:0.8rem;">({(t_base_o/butce-1)*100:+.1f}%)</span></div></div>
                        <div><div class="card-label">Kotu Senaryo</div>
                             <div style="font-size:1.2rem;font-weight:800;color:#F6465D;">TL {t_bear_o:,.0f}
                             <span style="font-size:0.8rem;">({(t_bear_o/butce-1)*100:+.1f}%)</span></div></div>
                    </div>
                </div>""", unsafe_allow_html=True)

                st.markdown('<div class="sec-title">Onerilen Hisseler — Detayli Borsaci Analizi</div>',
                            unsafe_allow_html=True)

                for idx,(_, row) in enumerate(df_sc.iterrows(),1):
                    sym=row["Sembol"]; fiyat=row["Fiyat"]; rsi=row["RSI"]
                    aksiyon=row["Aksiyon"]; degisim=row["Degisim %"]
                    adet_on=int(hb/fiyat) if fiyat>0 else 0
                    t_mal_on=adet_on*fiyat; skor=row["Skor"]
                    fc3=mc_res.get(sym)

                    # Monte Carlo sonuçları
                    if fc3 and adet_on>0:
                        bv3=adet_on*fc3["bull"]; bav3=adet_on*fc3["base"]; bev3=adet_on*fc3["bear"]
                        br3=(fc3["bull"]-fiyat)/fiyat*100
                        bar3=(fc3["base"]-fiyat)/fiyat*100
                        ber3=(fc3["bear"]-fiyat)/fiyat*100
                        pu3=fc3["prob_up"]; pd3=fc3["prob_down"]
                        vol3=fc3["sigma_annual"]
                        sc3=fc3["score"]
                        mc_ok3=True
                    else:
                        mc_ok3=False
                        bv3=bav3=bev3=t_mal_on
                        br3=bar3=ber3=pu3=pd3=vol3=0.0; sc3=0.0

                    # Neden önerildi
                    nedenler=[]
                    if pd.notna(rsi) and rsi<35: nedenler.append("RSI asiri satim — iskontolu gorece")
                    elif pd.notna(rsi) and rsi<45: nedenler.append("RSI alim bolgesi")
                    if "GUCLU AL" in str(aksiyon): nedenler.append("Guclu teknik AL sinyali")
                    elif "AL" in str(aksiyon): nedenler.append("Teknik AL sinyali")
                    if pd.notna(degisim) and degisim>0: nedenler.append(f"Bugun +{degisim:.1f}% yukseliyor")
                    if mc_ok3 and sc3>0.3: nedenler.append("Monte Carlo: pozitif momentum egilimi")
                    if not nedenler: nedenler.append("Dengeli teknik gorunum")
                    neden_str=" &nbsp;·&nbsp; ".join(nedenler)

                    # Borsacı yorum
                    if mc_ok3:
                        if sc3>0.4: borsaci_yorum=f"{sym} icin teknik tablo guclu pozitif. RSI {rsi:.0f}, MACD yukari donuyor. Baz senaryoda %{bar3:.0f} getiri bekleniyor. Risk/odul dengesi alim yonunde."
                        elif sc3>0: borsaci_yorum=f"{sym} temkinli pozitif gorunumde. RSI {rsi:.0f} notr bolgede, dikkatli giris onerilir. Baz senaryoda %{bar3:.0f} getiri potansiyeli var."
                        else: borsaci_yorum=f"{sym} dusuk teknik skor almis. Kisa vade icin riskli gorulebilir. Ancak {risk_p.split('—')[0].strip()} profili ile degerlendirilebilir."
                    else: borsaci_yorum=f"{sym} icin Monte Carlo verisi hesaplanamadi. Teknik gorunum: {aksiyon}."

                    rsi_c="#0ECB81" if pd.notna(rsi) and rsi<40 else "#F6465D" if pd.notna(rsi) and rsi>65 else "#848E9C"
                    chg_c="#0ECB81" if pd.notna(degisim) and degisim>=0 else "#F6465D"
                    chg_s="+" if pd.notna(degisim) and degisim>=0 else ""
                    act_bg="#052e16" if "AL" in str(aksiyon) else "#1a0509" if "SAT" in str(aksiyon) else "#111827"
                    act_fc="#0ECB81" if "AL" in str(aksiyon) else "#F6465D" if "SAT" in str(aksiyon) else "#848E9C"

                    mc_html3=""
                    if mc_ok3:
                        mc_html3 = f"""
                        <div style="margin-top:1rem;padding-top:0.8rem;border-top:1px solid #1E2329;">
                            <div class="card-label" style="margin-bottom:0.5rem;">
                                Yil Sonu Tahmin ({adet_on} adet) · Volatilite %{vol3:.1f} · 3.000 sim
                            </div>
                            <div class="fc-band">
                                <div class="fc-cell" style="background:#0D2E1A;border-radius:6px 0 0 6px;border:1px solid #1B4332;">
                                    <div class="fc-cell-label">En Iyi</div>
                                    <div class="fc-cell-val" style="color:#0ECB81;">TL {bv3:,.0f}</div>
                                    <div class="fc-cell-pct" style="color:#0ECB81;">+{br3:.0f}%</div>
                                </div>
                                <div class="fc-cell" style="background:#0D1525;border:1px solid #1A3A6B;border-left:none;border-right:none;">
                                    <div class="fc-cell-label">Ortalama</div>
                                    <div class="fc-cell-val" style="color:#1E90FF;">TL {bav3:,.0f}</div>
                                    <div class="fc-cell-pct" style="color:#1E90FF;">{bar3:+.0f}%</div>
                                </div>
                                <div class="fc-cell" style="background:#1A0A0D;border-radius:0 6px 6px 0;border:1px solid #4A1020;">
                                    <div class="fc-cell-label">Kotu</div>
                                    <div class="fc-cell-val" style="color:#F6465D;">TL {bev3:,.0f}</div>
                                    <div class="fc-cell-pct" style="color:#F6465D;">{ber3:+.0f}%</div>
                                </div>
                            </div>
                            <div style="display:flex;gap:2rem;margin-top:0.5rem;flex-wrap:wrap;">
                                <div style="font-size:0.72rem;color:#5E6673;">
                                    %10+ yukari: <span style="color:#0ECB81;font-weight:600;">%{pu3:.0f}</span>
                                </div>
                                <div style="font-size:0.72rem;color:#5E6673;">
                                    %10+ asagi: <span style="color:#F6465D;font-weight:600;">%{pd3:.0f}</span>
                                </div>
                                <div style="font-size:0.72rem;color:#5E6673;">
                                    Borsaci Yorumu: <span style="color:#EAECEF;">{borsaci_yorum}</span>
                                </div>
                            </div>
                        </div>"""

                    st.markdown(f"""
                    <div class="oneri-card">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
                            <div>
                                <div style="display:flex;align-items:center;gap:0.8rem;flex-wrap:wrap;">
                                    <span style="font-size:1.5rem;font-weight:800;color:#F0B90B;">#{idx} {sym}</span>
                                    <span style="background:{act_bg};color:{act_fc};padding:0.2rem 0.6rem;
                                    border-radius:4px;font-size:0.72rem;font-weight:700;
                                    border:1px solid {act_fc}44;">{aksiyon}</span>
                                    <span style="background:#1A1C24;color:#848E9C;padding:0.2rem 0.6rem;
                                    border-radius:4px;font-size:0.68rem;border:1px solid #2B3139;">
                                        Skor {skor}/100
                                    </span>
                                </div>
                                <div style="font-size:0.78rem;color:#5E6673;margin-top:0.3rem;">{neden_str}</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="card-label">Guncel Fiyat</div>
                                <div style="font-size:1.2rem;font-weight:800;color:#EAECEF;">TL {fiyat:,.2f}</div>
                                <div style="font-size:0.8rem;color:{chg_c};">{chg_s}{degisim:.1f}% bugun</div>
                            </div>
                        </div>
                        <div style="display:flex;gap:2rem;margin-top:0.8rem;flex-wrap:wrap;">
                            <div><div class="card-label">Onerilecek Adet</div>
                                 <div style="font-size:1rem;font-weight:700;color:#EAECEF;">{adet_on} adet</div></div>
                            <div><div class="card-label">Bu Hisseye Yatirim</div>
                                 <div style="font-size:1rem;font-weight:700;color:#F0B90B;">TL {t_mal_on:,.0f}</div></div>
                            <div><div class="card-label">RSI</div>
                                 <div style="font-size:1rem;font-weight:700;color:{rsi_c};">{rsi:.0f}</div></div>
                        </div>
                        {mc_html3}
                    </div>""", unsafe_allow_html=True)

                # Portföydeki hisseler için sinyal
                if st.session_state.portfolio:
                    st.markdown('<div class="sec-title">Portfoyundeki Hisseler — SAT / TUT / EKLE Sinyali</div>',
                                unsafe_allow_html=True)
                    for pf_sym, pf_d in st.session_state.portfolio.items():
                        try:
                            _, ph, _ = get_detail(f"{pf_sym}.IS")
                            if ph.empty: continue
                            pcl = ph["Close"].squeeze()
                            pcp = float(pcl.iloc[-1])
                            pri = compute_rsi(pcl)
                            psm = float(pcl.rolling(50).mean().iloc[-1]) if len(pcl)>=50 else pcp
                            pa_lbl,_,_ = get_signal(pri, pcp, psm)
                            pkar= (pcp - pf_d["maliyet"])/pf_d["maliyet"]*100
                            pkc = "#0ECB81" if pkar>=0 else "#F6465D"
                            pks = "+" if pkar>=0 else ""

                            if "SAT" in pa_lbl:
                                sc_c="#F6465D"; sc_bg="#1a0509"; sc_lbl="SAT SINYALI"
                                alt = list(df_sc["Sembol"])[0] if not df_sc.empty else "—"
                                yorum = f"RSI {pri:.0f} ile asiri alim bolgesinde. Kar realize edilebilir. Yerine {alt} degerlendirilebilir."
                            elif "AL" in pa_lbl:
                                sc_c="#0ECB81"; sc_bg="#052e16"; sc_lbl="TUT / EKLE"
                                yorum = f"Teknik gorunum olumlu. RSI {pri:.0f}, SMA-50 {'uzerinde' if pcp>psm else 'altinda'}. Tutmaya devam edin."
                            else:
                                sc_c="#F0B90B"; sc_bg="#1A1500"; sc_lbl="IZLE"
                                yorum = f"Notr bolgede. RSI {pri:.0f}. Makro ve hacim verilerini takip edin."

                            st.markdown(f"""
                            <div style="background:#161A1E;border:1px solid #1E2329;border-left:3px solid {sc_c};
                            border-radius:8px;padding:1rem 1.2rem;margin-bottom:0.5rem;
                            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
                                <div>
                                    <div style="display:flex;align-items:center;gap:0.8rem;">
                                        <span style="font-size:1.1rem;font-weight:700;color:#EAECEF;">{pf_sym}</span>
                                        <span style="background:{sc_bg};color:{sc_c};padding:0.2rem 0.6rem;
                                        border-radius:4px;font-size:0.72rem;font-weight:700;border:1px solid {sc_c}44;">{sc_lbl}</span>
                                    </div>
                                    <div style="font-size:0.8rem;color:#5E6673;margin-top:0.3rem;">{yorum}</div>
                                </div>
                                <div style="text-align:right;">
                                    <div class="card-label">Simdi / Alisin</div>
                                    <div style="font-size:1rem;font-weight:700;color:#EAECEF;">TL {pcp:,.2f}</div>
                                    <div style="font-size:0.82rem;color:{pkc};">{pks}{pkar:.1f}% &nbsp; {pf_d['adet']} adet</div>
                                </div>
                            </div>""", unsafe_allow_html=True)
                        except: continue

                # Portföye ekle butonu
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                if st.button("Bu Onerileri Portfoyume Ekle", type="primary"):
                    for _, row in df_sc.iterrows():
                        sym=row["Sembol"]; f2=row["Fiyat"]
                        a2=int(hb/f2) if f2>0 else 0
                        if a2>0:
                            st.session_state.portfolio[sym]={"adet":a2,"maliyet":round(f2,2)}
                    st.success("Eklendi! 'Portfoyum' sekmesine gecin."); st.rerun()

                st.markdown("""
                <div style="font-size:0.68rem;color:#2B3139;margin-top:1rem;padding:0.5rem;
                border-radius:4px;background:#0F1318;">
                Monte Carlo gecmis volatilite bazlidir. Yatirim tavsiyesi degildir.
                Lütfen kendi arastirmanizi yapiniz.
                </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:#1E2329;
text-align:center;border-top:1px solid #161A1E;padding-top:1rem;margin-top:2rem;">
Burak Borsa Analiz v5.0  ·  Egitim Amaclıdır  ·  Yatirim Tavsiyesi Degildir
·  Monte Carlo gecmis veriye dayali olasiliksaldir, garanti icermez.
</div>
""", unsafe_allow_html=True)
