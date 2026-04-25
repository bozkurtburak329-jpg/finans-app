"""
╔══════════════════════════════════════════════════════════════╗
║  KİŞİSEL FİNANS MERKEZİ  ·  v3.0                           ║
║  Sekme 1 : Borç Erime & Özgürlük Simülatörü                 ║
║  Sekme 2 : Kantitatif Piyasa Tarayıcısı + Sinyal Motoru     ║
╚══════════════════════════════════════════════════════════════╝

Kurulum:
    pip install streamlit pandas numpy plotly yfinance

Çalıştır:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────
#  SAYFA YAPISI
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kişisel Finans Merkezi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  GLOBAL STİL
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #070a10;
    color: #d4dbe8;
}

/* ── Sekme Navigasyonu ── */
[data-testid="stTabs"] > div:first-child {
    border-bottom: 1px solid #161d2e !important;
}
button[data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.73rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #3d4f6b !important;
    padding: 0.8rem 1.6rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
}
button[data-baseweb="tab"]:hover { color: #8899b8 !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #34d399 !important;
    border-bottom-color: #34d399 !important;
}

/* ── KPI Kartı ── */
.kpi-card {
    background: #0c1220;
    border: 1px solid #161d2e;
    border-radius: 12px;
    padding: 1.2rem 1.4rem 1rem;
    position: relative;
    overflow: hidden;
    height: 100%;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 12px 12px 0 0;
}
.kpi-card.red::before    { background: linear-gradient(90deg,#ef4444,#dc2626); }
.kpi-card.green::before  { background: linear-gradient(90deg,#10b981,#34d399); }
.kpi-card.amber::before  { background: linear-gradient(90deg,#f59e0b,#fbbf24); }
.kpi-card.blue::before   { background: linear-gradient(90deg,#3b82f6,#60a5fa); }
.kpi-card.purple::before { background: linear-gradient(90deg,#8b5cf6,#a78bfa); }
.kpi-card.cyan::before   { background: linear-gradient(90deg,#06b6d4,#22d3ee); }

.kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem;
    color: #2e3d55;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.8rem;
    line-height: 1;
    margin-bottom: 0.3rem;
    letter-spacing: -0.02em;
}
.kpi-value.red    { color: #f87171; }
.kpi-value.green  { color: #34d399; }
.kpi-value.amber  { color: #fbbf24; }
.kpi-value.blue   { color: #60a5fa; }
.kpi-value.purple { color: #a78bfa; }
.kpi-value.cyan   { color: #22d3ee; }
.kpi-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    color: #3d4f6b;
    line-height: 1.4;
}
.kpi-sub .pos { color: #34d399; }
.kpi-sub .neg { color: #f87171; }

/* ── Hero Başlık ── */
.hero { margin-bottom: 1.4rem; }
.hero-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg,#f0fdf4 0%,#86efac 45%,#34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}
.hero-title.market {
    background: linear-gradient(135deg,#eff6ff 0%,#93c5fd 45%,#60a5fa 100%);
    -webkit-background-clip: text;
    background-clip: text;
}
.hero-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #2e3d55;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.25rem;
}

/* ── Bölüm Başlığı ── */
.section-hdr {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #2e3d55;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    border-bottom: 1px solid #111827;
    padding-bottom: 0.4rem;
    margin: 2rem 0 1rem 0;
}

/* ── Sinyal Rozeti ── */
.signal-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    letter-spacing: 0.04em;
}
.signal-buy    { background:#052e16; color:#34d399; border:1px solid #065f46; }
.signal-hold   { background:#0c1a2e; color:#60a5fa; border:1px solid #1e3a5f; }
.signal-overbought { background:#2d1515; color:#f87171; border:1px solid #7f1d1d; }
.signal-watch  { background:#1c1408; color:#fbbf24; border:1px solid #78350f; }

/* ── Info / Warning ── */
.info-box {
    background: #080f1e;
    border: 1px solid #1d4ed8;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #93c5fd;
    margin: 0.75rem 0;
    line-height: 1.6;
}
.warn-box {
    background: #120606;
    border: 1px solid #7f1d1d;
    border-left: 3px solid #ef4444;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #fca5a5;
    margin: 0.75rem 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0a0e18;
    border-right: 1px solid #111827;
}
[data-testid="stSidebar"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    color: #3d4f6b !important;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

/* ── DataFrame ── */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}

/* ── Footer ── */
.footer {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    color: #161d2e;
    text-align: center;
    border-top: 1px solid #0d1117;
    padding-top: 1.2rem;
    margin-top: 2.5rem;
}
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ═════════════════════════════════════════════════════════════

def fmt_tl(val: float) -> str:
    return f"₺{val:,.0f}".replace(",", ".")


def get_plotly_base(height: int = 380) -> dict:
    """
    Plotly update_layout() için temel dark-theme ayarları.
    ** ile açılmaya uygun düz dict döner.
    xaxis/yaxis override'ları dışarıdan ayrıca geçirilmeli.
    """
    return {
        "plot_bgcolor":  "#0b0f1a",
        "paper_bgcolor": "#0b0f1a",
        "font":          {"family": "IBM Plex Mono", "color": "#3d4f6b", "size": 11},
        "hovermode":     "x unified",
        "hoverlabel":    {"bgcolor": "#0c1220", "bordercolor": "#161d2e",
                          "font": {"family": "IBM Plex Mono", "size": 11}},
        "legend":        {"bgcolor": "#0c1220", "bordercolor": "#161d2e",
                          "borderwidth": 1, "font": {"size": 10},
                          "orientation": "h", "x": 0.5, "y": 1.1, "xanchor": "center"},
        "margin":        {"t": 20, "b": 45, "l": 65, "r": 20},
        "height":        height,
    }


def axis_style(title: str = "", prefix: str = "", fmt: str = "") -> dict:
    """Tek eksen stili — update_layout'a xaxis= / yaxis= olarak geçilir."""
    d: dict = {
        "gridcolor":     "#111827",
        "zerolinecolor": "#111827",
        "tickfont":      {"size": 10},
    }
    if title:  d["title"] = title
    if prefix: d["tickprefix"] = prefix
    if fmt:    d["tickformat"] = fmt
    return d


# ─── BORÇ AMORTİSMAN ─────────────────────────────────────────
def calculate_amortization(principal: float, monthly_rate: float,
                            monthly_payment: float, monthly_inflation: float = 0.0,
                            extra: float = 0.0):
    if monthly_rate > 0 and monthly_payment <= principal * monthly_rate:
        return None
    rows, balance, cum_inf, ay = [], principal, 1.0, 0
    total_pay = monthly_payment + extra
    while balance > 0.01 and ay < 600:
        ay += 1
        interest = balance * monthly_rate
        principal_paid = min(total_pay - interest, balance)
        if principal_paid <= 0:
            return None
        balance    -= principal_paid
        cum_inf    *= (1 + monthly_inflation)
        rows.append({
            "Ay":              ay,
            "Faiz (₺)":        round(interest, 2),
            "Anapara (₺)":     round(principal_paid, 2),
            "Nominal Kalan (₺)": round(max(balance, 0), 2),
            "Reel Kalan (₺)":  round(max(balance / cum_inf, 0), 2),
        })
    return pd.DataFrame(rows)


# ─── TEKNİK İNDİKATÖR FONKSİYONLARI ─────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    val   = rsi.iloc[-1]
    return round(float(val), 1) if pd.notna(val) else np.nan


def compute_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast   = series.ewm(span=fast, adjust=False).mean()
    ema_slow   = series.ewm(span=slow, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return (round(float(macd_line.iloc[-1]), 4),
            round(float(signal_line.iloc[-1]), 4),
            round(float(histogram.iloc[-1]), 4))


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> float:
    """Average True Range — volatilite ölçütü."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(float(atr), 4) if pd.notna(atr) else np.nan


# ─── SİNYAL MOTORU ───────────────────────────────────────────
def generate_signal(row: dict) -> tuple[str, str]:
    """
    RSI + MACD histogram + SMA-50 trend durumuna göre
    (etiket, css-sınıfı) döner.
    """
    rsi   = row.get("RSI")
    hist  = row.get("MACD_Hist")
    above = row.get("Above_SMA50")  # True/False

    # Öncelik sırası: aşırı satılmış → güçlü al → bekle → aşırı alım
    if pd.notna(rsi) and rsi < 30 and pd.notna(hist) and hist > 0:
        return "⬆ Güçlü Al",        "signal-buy"
    if pd.notna(rsi) and rsi < 30:
        return "⬆ Al (Oversold)",   "signal-buy"
    if pd.notna(rsi) and rsi > 70:
        return "⚠ Aşırı Alım",      "signal-overbought"
    if pd.notna(above) and above and pd.notna(hist) and hist > 0:
        return "↗ Trendle Git",     "signal-hold"
    if pd.notna(rsi) and 40 <= rsi <= 60:
        return "◼ Bekle",           "signal-hold"
    if pd.notna(above) and not above:
        return "↘ Zayıf Trend",     "signal-watch"
    return "◼ Bekle",               "signal-hold"


# ─── HİSSE LİSTESİ ───────────────────────────────────────────
TICKERS = {
    "THYAO.IS": "Türk Hava Yolları",
    "GARAN.IS": "Garanti BBVA",
    "ASELS.IS": "Aselsan",
    "EREGL.IS": "Ereğli Demir Çelik",
    "KCHOL.IS": "Koç Holding",
    "SISE.IS":  "Şişecam",
    "AAPL":     "Apple",
    "TSLA":     "Tesla",
    "NVDA":     "NVIDIA",
    "MSFT":     "Microsoft",
    "AMZN":     "Amazon",
    "META":     "Meta",
    "BABA":     "Alibaba",
    "PLTR":     "Palantir",
}


@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_data() -> pd.DataFrame:
    end   = datetime.today()
    start = end - timedelta(days=220)
    rows  = []

    for ticker, name in TICKERS.items():
        try:
            df = yf.download(ticker, start=start, end=end,
                             progress=False, auto_adjust=True)
            if df.empty or len(df) < 60:
                continue

            close  = df["Close"].squeeze()
            high   = df["High"].squeeze()
            low    = df["Low"].squeeze()
            volume = df["Volume"].squeeze()

            price      = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            chg_pct    = (price - prev_price) / prev_price * 100

            sma50  = float(close.rolling(50).mean().iloc[-1])
            ema20  = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
            rsi    = compute_rsi(close)
            macd_v, macd_sig, macd_hist = compute_macd(close)
            atr    = compute_atr(high, low, close)
            atr_pct = round(atr / price * 100, 2) if price else np.nan

            vol_5d  = float(volume.iloc[-5:].mean())
            vol_avg = float(volume.mean())
            vol_ratio = round(vol_5d / vol_avg, 2) if vol_avg else np.nan

            market   = "🇹🇷 BIST" if ticker.endswith(".IS") else "🇺🇸 US"
            currency = "₺" if ticker.endswith(".IS") else "$"

            row_data = {
                "Ticker":      ticker,
                "Şirket":      name,
                "Piyasa":      market,
                "Fiyat":       round(price, 2),
                "Döviz":       currency,
                "Değişim %":   round(chg_pct, 2),
                "RSI":         rsi,
                "MACD":        macd_v,
                "MACD_Sig":    macd_sig,
                "MACD_Hist":   macd_hist,
                "SMA-50":      round(sma50, 2),
                "EMA-20":      round(ema20, 2),
                "Above_SMA50": price > sma50,
                "F/SMA":       round(price / sma50, 3),
                "ATR %":       atr_pct,
                "Vol Ratio":   vol_ratio,
            }
            sig_label, sig_class = generate_signal(row_data)
            row_data["Sinyal"]       = sig_label
            row_data["Sinyal_Class"] = sig_class
            rows.append(row_data)

        except Exception:
            continue

    return pd.DataFrame(rows)


# ═════════════════════════════════════════════════════════════
#  SİDEBAR — SCREENER FİLTRELERİ
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔬 Screener Filtreleri")
    st.markdown("---")

    piyasa_filtre = st.selectbox(
        "Piyasa", ["Tümü", "🇹🇷 BIST", "🇺🇸 US"])

    sinyal_filtre = st.multiselect(
        "Sinyal Türü",
        ["⬆ Güçlü Al", "⬆ Al (Oversold)", "↗ Trendle Git",
         "◼ Bekle", "↘ Zayıf Trend", "⚠ Aşırı Alım"],
        default=["⬆ Güçlü Al", "⬆ Al (Oversold)", "↗ Trendle Git"],
    )

    rsi_range = st.slider("RSI Aralığı", 0, 100, (0, 100))

    vol_ratio_min = st.slider(
        "Min. Hacim Oranı (Vol Ratio)", 0.0, 5.0, 0.0, 0.1,
        help="Son 5 gün hacmi / 6 ay ortalaması. 1.5+ = hacim artışı")

    atr_max = st.slider(
        "Max. Volatilite (ATR %)", 0.0, 20.0, 20.0, 0.5,
        help="Günlük ortalama fiyat dalgalanması. Düşük = daha sakin hisse")

    st.markdown("---")
    st.markdown("""<div style='font-family:"IBM Plex Mono",monospace;font-size:0.62rem;
    color:#1f2937;line-height:1.7;'>
    RSI &lt; 30 → Aşırı Satılmış<br>
    RSI &gt; 70 → Aşırı Alınmış<br>
    MACD Hist &gt; 0 → Yukarı Momentum<br>
    F/SMA &gt; 1 → SMA Üzerinde<br>
    Vol Ratio &gt; 1.5 → Hacim Artışı
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  ANA SEKMELER
# ═════════════════════════════════════════════════════════════
tab_debt, tab_market = st.tabs([
    "💸  Borç Erime Simülatörü",
    "📡  Kantitatif Piyasa Tarayıcısı",
])


# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 1 — BORÇ ERİME SİMÜLATÖRÜ                           ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_debt:
    st.markdown(
        '<div class="hero">'
        '<div class="hero-title">Borç Erime Simülatörü</div>'
        '<div class="hero-sub">// Debt-Freedom Planner · Senaryo & Reel Değer Analizi</div>'
        '</div>',
        unsafe_allow_html=True)

    # ── Girdi Satırı ───────────────────────────────────────────
    g1, g2, g3, g4, g5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])
    with g1:
        principal = st.number_input(
            "💰 Güncel Borç (₺)", 100.0, 10_000_000.0,
            29_000.0, 500.0, format="%.0f")
    with g2:
        monthly_rate_pct = st.number_input(
            "📈 Aylık Faiz (%)", 0.0, 30.0, 3.5, 0.1, format="%.2f")
    with g3:
        monthly_payment = st.number_input(
            "💳 Aylık Taksit (₺)", 100.0, 500_000.0,
            2_500.0, 100.0, format="%.0f")
    with g4:
        monthly_inflation_pct = st.number_input(
            "🌡️ Aylık Enflasyon (%)", 0.0, 20.0, 2.5, 0.1, format="%.2f")
    with g5:
        extra_payment = st.number_input(
            "🚀 Ekstra Ödeme (₺)", 0.0, 100_000.0, 500.0, 100.0,
            format="%.0f", help="Yemek/abonelik kısıptan borca eklenen tutar")

    monthly_rate      = monthly_rate_pct / 100
    monthly_inflation = monthly_inflation_pct / 100

    df_base  = calculate_amortization(principal, monthly_rate, monthly_payment, monthly_inflation, 0)
    df_extra = calculate_amortization(principal, monthly_rate, monthly_payment, monthly_inflation, extra_payment)

    if df_base is None:
        st.markdown(f"""<div class="warn-box">
        ⚠️  Aylık taksit ({fmt_tl(monthly_payment)}) faiz maliyetini
        ({fmt_tl(principal * monthly_rate)}/ay) karşılamıyor.
        Taksiti artırın veya faiz oranını düşürün.
        </div>""", unsafe_allow_html=True)
        st.stop()

    # ── KPI Hesapla ────────────────────────────────────────────
    total_months_base    = len(df_base)
    total_interest_base  = df_base["Faiz (₺)"].sum()

    if df_extra is not None and extra_payment > 0:
        total_months_extra   = len(df_extra)
        total_interest_extra = df_extra["Faiz (₺)"].sum()
        saved_months         = total_months_base - total_months_extra
        saved_interest       = total_interest_base - total_interest_extra
    else:
        total_months_extra = total_months_base
        saved_months = saved_interest = 0

    final_real = float(df_base["Reel Kalan (₺)"].iloc[0])  # ilk ay reel

    # ── KPI Kartları ───────────────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(f"""<div class="kpi-card red">
        <div class="kpi-label">Standart Süre</div>
        <div class="kpi-value red">{total_months_base} Ay</div>
        <div class="kpi-sub">≈ {total_months_base/12:.1f} yıl</div>
        </div>""", unsafe_allow_html=True)

    with k2:
        st.markdown(f"""<div class="kpi-card amber">
        <div class="kpi-label">Toplam Faiz Maliyeti</div>
        <div class="kpi-value amber">{fmt_tl(total_interest_base)}</div>
        <div class="kpi-sub">Anaparaya oran: %{total_interest_base/principal*100:.1f}</div>
        </div>""", unsafe_allow_html=True)

    with k3:
        delta_lbl = f'<span class="pos">−{saved_months} ay erken</span>' if saved_months > 0 else "—"
        val_str   = f"{total_months_extra} Ay" if extra_payment > 0 else "—"
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Ekstra ile Bitiş</div>
        <div class="kpi-value green">{val_str}</div>
        <div class="kpi-sub">{delta_lbl}</div>
        </div>""", unsafe_allow_html=True)

    with k4:
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Faiz Tasarrufu</div>
        <div class="kpi-value green">{fmt_tl(saved_interest)}</div>
        <div class="kpi-sub">+{fmt_tl(extra_payment)}/ay ekstra ile</div>
        </div>""", unsafe_allow_html=True)

    with k5:
        enf_yillik = (1 + monthly_inflation) ** 12 - 1
        st.markdown(f"""<div class="kpi-card cyan">
        <div class="kpi-label">Yıllık Enflasyon</div>
        <div class="kpi-value cyan">%{enf_yillik*100:.1f}</div>
        <div class="kpi-sub">Aylık %{monthly_inflation_pct:.1f} bileşik</div>
        </div>""", unsafe_allow_html=True)

    # ── Grafik 1: Borç Erime Eğrisi ────────────────────────────
    st.markdown('<div class="section-hdr">📉 Borç Erime Eğrisi — Nominal · Reel · Ekstra Senaryo</div>',
                unsafe_allow_html=True)

    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=df_base["Ay"], y=df_base["Nominal Kalan (₺)"],
        name="Nominal (Standart)",
        line=dict(color="#ef4444", width=2.5),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.04)",
        hovertemplate="<b>Ay %{x}</b><br>Nominal: ₺%{y:,.0f}<extra></extra>"))

    fig1.add_trace(go.Scatter(
        x=df_base["Ay"], y=df_base["Reel Kalan (₺)"],
        name="Reel (Enflasyon İndirgeli)",
        line=dict(color="#f59e0b", width=2, dash="dot"),
        hovertemplate="<b>Ay %{x}</b><br>Reel: ₺%{y:,.0f}<extra></extra>"))

    if df_extra is not None and extra_payment > 0:
        fig1.add_trace(go.Scatter(
            x=df_extra["Ay"], y=df_extra["Nominal Kalan (₺)"],
            name=f"Nominal (Ekstra +{fmt_tl(extra_payment)}/ay)",
            line=dict(color="#34d399", width=2.5),
            fill="tozeroy", fillcolor="rgba(52,211,153,0.04)",
            hovertemplate="<b>Ay %{x}</b><br>Ekstra Senaryo: ₺%{y:,.0f}<extra></extra>"))

    fig1.add_hline(y=principal,
                   line=dict(color="#1f2937", width=1, dash="longdash"),
                   annotation_text=f"Başlangıç {fmt_tl(principal)}",
                   annotation_font=dict(color="#374151", size=9))

    layout1 = get_plotly_base(400)
    layout1["xaxis"] = axis_style("Ay")
    layout1["yaxis"] = axis_style("Kalan Borç", "₺", ",.0f")
    fig1.update_layout(**layout1)
    st.plotly_chart(fig1, use_container_width=True)

    # ── Grafik 2: Faiz vs Anapara Yığın ────────────────────────
    st.markdown('<div class="section-hdr">📊 Aylık Ödeme Dağılımı — Faiz vs Anapara</div>',
                unsafe_allow_html=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df_base["Ay"], y=df_base["Faiz (₺)"],
        name="Faiz", marker_color="#ef4444", opacity=0.82,
        hovertemplate="Ay %{x}<br>Faiz: ₺%{y:,.0f}<extra></extra>"))
    fig2.add_trace(go.Bar(
        x=df_base["Ay"], y=df_base["Anapara (₺)"],
        name="Anapara", marker_color="#10b981", opacity=0.82,
        hovertemplate="Ay %{x}<br>Anapara: ₺%{y:,.0f}<extra></extra>"))

    layout2 = get_plotly_base(280)
    layout2["barmode"] = "stack"
    layout2["xaxis"]   = axis_style("Ay")
    layout2["yaxis"]   = axis_style("Ödeme (₺)", "₺", ",.0f")
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True)

    # ── Amortisman Tablosu ──────────────────────────────────────
    st.markdown('<div class="section-hdr">📋 Amortisman Tablosu</div>', unsafe_allow_html=True)

    def fmt_df(df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        for col in ["Faiz (₺)", "Anapara (₺)", "Nominal Kalan (₺)", "Reel Kalan (₺)"]:
            d[col] = d[col].apply(lambda x: f"₺{x:,.2f}")
        return d

    sub1, sub2 = st.tabs(["📌 Standart Plan", f"🚀 Ekstra (+{fmt_tl(extra_payment)}/ay)"])
    with sub1:
        st.dataframe(fmt_df(df_base), use_container_width=True, height=360, hide_index=True)
        st.markdown(f"""<div class="info-box">
        📌 Toplam {total_months_base} ay &nbsp;·&nbsp;
        Toplam Faiz: {fmt_tl(total_interest_base)} &nbsp;·&nbsp;
        Anapara: {fmt_tl(principal)}
        </div>""", unsafe_allow_html=True)

    with sub2:
        if df_extra is not None and extra_payment > 0:
            st.dataframe(fmt_df(df_extra), use_container_width=True, height=360, hide_index=True)
            st.markdown(f"""<div class="info-box">
            🚀 Toplam {total_months_extra} ay &nbsp;·&nbsp;
            Faiz: {fmt_tl(total_interest_extra)} &nbsp;·&nbsp;
            <span style='color:#34d399'>Tasarruf: {fmt_tl(saved_interest)} + {saved_months} ay erken bitiş</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Sol üstteki 'Ekstra Ödeme' alanından tutar girin.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 2 — MARKET SCREENER + SİNYAL MOTORU                  ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_market:
    st.markdown(
        '<div class="hero">'
        '<div class="hero-title market">Kantitatif Piyasa Tarayıcısı</div>'
        '<div class="hero-sub">// RSI · MACD · SMA/EMA · Sinyal Motoru · 15 dk cache</div>'
        '</div>',
        unsafe_allow_html=True)

    hdr_col, btn_col = st.columns([5, 1])
    with btn_col:
        if st.button("🔄 Yenile", type="primary", use_container_width=True):
            st.cache_data.clear()

    with st.spinner("📡  Piyasa verileri ve sinyaller hesaplanıyor…"):
        df_raw = fetch_market_data()

    if df_raw.empty:
        st.markdown("""<div class="warn-box">
        ⚠️  Veri çekilemedi. İnternet bağlantınızı kontrol edin.
        </div>""", unsafe_allow_html=True)
        st.stop()

    # ── Filtreleri Uygula ───────────────────────────────────────
    df_f = df_raw.copy()

    if piyasa_filtre != "Tümü":
        df_f = df_f[df_f["Piyasa"] == piyasa_filtre]

    if sinyal_filtre:
        df_f = df_f[df_f["Sinyal"].isin(sinyal_filtre)]

    df_f = df_f[
        (df_f["RSI"] >= rsi_range[0]) &
        (df_f["RSI"] <= rsi_range[1])
    ]

    if vol_ratio_min > 0:
        df_f = df_f[df_f["Vol Ratio"] >= vol_ratio_min]

    df_f = df_f[df_f["ATR %"] <= atr_max]

    # ── KPI Özet ───────────────────────────────────────────────
    oversold     = df_raw[df_raw["RSI"] < 30]
    strong_trend = df_raw[df_raw["Above_SMA50"] == True]
    guclu_al     = df_raw[df_raw["Sinyal"].str.contains("Güçlü Al|Oversold", na=False)]
    avg_rsi      = df_raw["RSI"].mean()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class="kpi-card blue">
        <div class="kpi-label">Taranan Hisse</div>
        <div class="kpi-value blue">{len(df_raw)}</div>
        <div class="kpi-sub">Filtre sonucu: {len(df_f)} hisse</div>
        </div>""", unsafe_allow_html=True)

    with m2:
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Al Sinyali</div>
        <div class="kpi-value green">{len(guclu_al)}</div>
        <div class="kpi-sub">Güçlü Al + Oversold</div>
        </div>""", unsafe_allow_html=True)

    with m3:
        st.markdown(f"""<div class="kpi-card purple">
        <div class="kpi-label">SMA-50 Üzerinde</div>
        <div class="kpi-value purple">{len(strong_trend)}</div>
        <div class="kpi-sub">Güçlü fiyat trendi</div>
        </div>""", unsafe_allow_html=True)

    with m4:
        rc = "green" if avg_rsi < 40 else "amber" if avg_rsi < 65 else "red"
        st.markdown(f"""<div class="kpi-card {rc}">
        <div class="kpi-label">Ort. RSI</div>
        <div class="kpi-value {rc}">{avg_rsi:.1f}</div>
        <div class="kpi-sub">Piyasa nabzı</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Sinyal Motoru Ana Tablosu ───────────────────────────────
    st.markdown('<div class="section-hdr">⚡ Sinyal Motoru — Filtrelenmiş Sonuçlar</div>',
                unsafe_allow_html=True)

    if df_f.empty:
        st.markdown("""<div class="info-box">
        ℹ️  Seçili filtrelerle eşleşen hisse bulunamadı. Sol panelden filtreleri genişletin.
        </div>""", unsafe_allow_html=True)
    else:
        # Sinyal rozetlerini HTML olarak render et
        signal_html_rows = []
        for _, row in df_f.iterrows():
            signal_html_rows.append(
                f'<span class="signal-badge {row["Sinyal_Class"]}">{row["Sinyal"]}</span>'
            )

        display_cols = ["Ticker", "Şirket", "Piyasa", "Fiyat", "Döviz",
                        "Değişim %", "RSI", "MACD_Hist", "F/SMA", "ATR %", "Vol Ratio", "Sinyal"]

        def style_signal_table(df: pd.DataFrame) -> pd.DataFrame:
            s = pd.DataFrame("", index=df.index, columns=df.columns)
            for i, row in df.iterrows():
                # RSI rengi
                if pd.notna(row.get("RSI")):
                    if row["RSI"] < 30:
                        s.loc[i, "RSI"] = "color:#34d399;font-weight:700"
                    elif row["RSI"] > 70:
                        s.loc[i, "RSI"] = "color:#f87171;font-weight:700"
                    else:
                        s.loc[i, "RSI"] = "color:#9ca3af"
                # Değişim
                if pd.notna(row.get("Değişim %")):
                    s.loc[i, "Değişim %"] = (
                        "color:#34d399" if row["Değişim %"] >= 0 else "color:#f87171")
                # MACD Hist
                if pd.notna(row.get("MACD_Hist")):
                    s.loc[i, "MACD_Hist"] = (
                        "color:#34d399" if row["MACD_Hist"] > 0 else "color:#f87171")
                # F/SMA
                if pd.notna(row.get("F/SMA")):
                    s.loc[i, "F/SMA"] = (
                        "color:#60a5fa" if row["F/SMA"] > 1 else "color:#f59e0b")
                # Sinyal
                sig = row.get("Sinyal", "")
                if "Güçlü Al" in sig or "Oversold" in sig:
                    s.loc[i, "Sinyal"] = "color:#34d399;font-weight:700"
                elif "Aşırı Alım" in sig:
                    s.loc[i, "Sinyal"] = "color:#f87171;font-weight:700"
                elif "Zayıf" in sig:
                    s.loc[i, "Sinyal"] = "color:#fbbf24"
                else:
                    s.loc[i, "Sinyal"] = "color:#60a5fa"
            return s

        display_df = df_f[display_cols].copy()
        styled = (
            display_df.style
            .apply(style_signal_table, axis=None)
            .format({
                "Değişim %": "{:+.2f}%",
                "RSI":       "{:.1f}",
                "MACD_Hist": "{:+.4f}",
                "F/SMA":     "{:.3f}x",
                "ATR %":     "{:.2f}%",
                "Vol Ratio": "{:.2f}x",
            }, na_rep="—")
        )
        st.dataframe(styled, use_container_width=True, height=420, hide_index=True)

    # ── Al Sinyali Detay ────────────────────────────────────────
    st.markdown('<div class="section-hdr">🟢 Al Sinyali Detay — Oversold & Güçlü Al</div>',
                unsafe_allow_html=True)

    al_df = df_raw[df_raw["Sinyal"].str.contains("Güçlü Al|Oversold", na=False)]
    if al_df.empty:
        st.markdown("""<div class="info-box">
        ℹ️  Şu an Al sinyali veren hisse yok. Piyasa nötr/güçlü seyrediyor.
        </div>""", unsafe_allow_html=True)
    else:
        for _, row in al_df.iterrows():
            macd_dir = "↑ Yukarı" if row["MACD_Hist"] > 0 else "↓ Aşağı"
            st.markdown(f"""
            <div style='background:#070d18;border:1px solid #0d2a1a;border-left:3px solid #34d399;
            border-radius:8px;padding:0.7rem 1rem;margin:0.4rem 0;
            font-family:"IBM Plex Mono",monospace;font-size:0.72rem;'>
            <span style='color:#34d399;font-weight:700;font-size:0.85rem'>{row["Ticker"]}</span>
            &nbsp;&nbsp;<span style='color:#4b5563'>{row["Şirket"]}</span>
            &nbsp;&nbsp;<span class="signal-badge {row['Sinyal_Class']}">{row["Sinyal"]}</span>
            <br><br>
            <span style='color:#3d4f6b'>Fiyat:</span> <span style='color:#d4dbe8'>{row["Döviz"]}{row["Fiyat"]}</span>
            &nbsp;·&nbsp;
            <span style='color:#3d4f6b'>RSI:</span> <span style='color:#34d399;font-weight:600'>{row["RSI"]:.1f}</span>
            &nbsp;·&nbsp;
            <span style='color:#3d4f6b'>MACD:</span> <span style='color:#60a5fa'>{macd_dir} ({row["MACD_Hist"]:+.4f})</span>
            &nbsp;·&nbsp;
            <span style='color:#3d4f6b'>F/SMA:</span> <span style='color:#60a5fa'>{row["F/SMA"]:.3f}x</span>
            &nbsp;·&nbsp;
            <span style='color:#3d4f6b'>Vol Ratio:</span> <span style='color:#fbbf24'>{row["Vol Ratio"]:.2f}x</span>
            </div>
            """, unsafe_allow_html=True)

    # ── RSI Panoraması ─────────────────────────────────────────
    st.markdown('<div class="section-hdr">📊 RSI & MACD Panoraması</div>', unsafe_allow_html=True)

    df_sorted  = df_raw.sort_values("RSI")
    rsi_colors = [
        "#34d399" if r < 30 else "#f87171" if r > 70 else "#60a5fa"
        for r in df_sorted["RSI"]
    ]

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Bar(
        x=df_sorted["Ticker"],
        y=df_sorted["RSI"],
        marker_color=rsi_colors, opacity=0.85,
        text=df_sorted["RSI"].apply(lambda x: f"{x:.0f}"),
        textposition="outside",
        textfont=dict(size=10, family="IBM Plex Mono", color="#6b7280"),
        hovertemplate="<b>%{x}</b><br>RSI: %{y:.1f}<extra></extra>",
    ))
    fig_rsi.add_hline(y=70, line=dict(color="#f87171", width=1, dash="dash"),
                      annotation_text="Aşırı Alım (70)",
                      annotation_font=dict(color="#f87171", size=9))
    fig_rsi.add_hline(y=30, line=dict(color="#34d399", width=1, dash="dash"),
                      annotation_text="Aşırı Satılmış (30)",
                      annotation_font=dict(color="#34d399", size=9))
    fig_rsi.add_hline(y=50, line=dict(color="#1f2937", width=1))

    layout_rsi = get_plotly_base(300)
    layout_rsi["xaxis"]      = axis_style("Ticker")
    layout_rsi["yaxis"]      = {**axis_style("RSI"), "range": [0, 115]}
    layout_rsi["showlegend"] = False
    fig_rsi.update_layout(**layout_rsi)
    st.plotly_chart(fig_rsi, use_container_width=True)

    # MACD Histogram
    df_macd = df_raw.sort_values("MACD_Hist")
    macd_colors = ["#34d399" if v > 0 else "#f87171" for v in df_macd["MACD_Hist"]]

    fig_macd = go.Figure()
    fig_macd.add_trace(go.Bar(
        x=df_macd["Ticker"],
        y=df_macd["MACD_Hist"],
        marker_color=macd_colors, opacity=0.85,
        hovertemplate="<b>%{x}</b><br>MACD Hist: %{y:+.4f}<extra></extra>",
    ))
    fig_macd.add_hline(y=0, line=dict(color="#374151", width=1.5))

    layout_macd = get_plotly_base(260)
    layout_macd["xaxis"]      = axis_style("Ticker")
    layout_macd["yaxis"]      = axis_style("MACD Histogram")
    layout_macd["showlegend"] = False
    layout_macd["title"]      = {"text": "MACD Histogram (+ = Yukarı Momentum)",
                                  "font": {"size": 11, "color": "#3d4f6b",
                                           "family": "IBM Plex Mono"},
                                  "x": 0.5}
    fig_macd.update_layout(**layout_macd)
    st.plotly_chart(fig_macd, use_container_width=True)

    # ── Gösterge Açıklaması ─────────────────────────────────────
    st.markdown("""<div class="info-box">
    <b style='color:#60a5fa'>Sinyal Mantığı:</b> &nbsp;
    RSI &lt; 30 + MACD Hist &gt; 0 → <span style='color:#34d399'>Güçlü Al</span> &nbsp;·&nbsp;
    RSI &lt; 30 → <span style='color:#34d399'>Al (Oversold)</span> &nbsp;·&nbsp;
    RSI &gt; 70 → <span style='color:#f87171'>Aşırı Alım</span> &nbsp;·&nbsp;
    Fiyat &gt; SMA50 + MACD &gt; 0 → <span style='color:#60a5fa'>Trendle Git</span>
    <br>
    <b style='color:#60a5fa'>Göstergeler:</b> &nbsp;
    RSI(14) = Momentum · MACD(12,26,9) = Trend gücü · ATR% = Volatilite ·
    F/SMA = Fiyat/SMA-50 · Vol Ratio = Hacim ivmesi
    <br>
    <span style='color:#fbbf24'>⚠ Bu araç yalnızca eğitim amaçlıdır. Yatırım tavsiyesi değildir.</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""<div class="footer">
Kişisel Finans Merkezi v3.0 &nbsp;·&nbsp; Eğitim & Planlama Amaçlıdır
&nbsp;·&nbsp; Finansal tavsiye değildir &nbsp;·&nbsp;
Veriler yfinance üzerinden çekilir · 15 dk cache
</div>""", unsafe_allow_html=True)
