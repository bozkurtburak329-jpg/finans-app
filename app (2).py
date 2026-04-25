"""
╔══════════════════════════════════════════════════════════════╗
║  KİŞİSEL FİNANS MERKEZİ  ·  v2.0                           ║
║  Sekme 1: Borç Erime & Özgürlük Simülatörü                  ║
║  Sekme 2: Kantitatif Piyasa Tarayıcısı (Market Screener)    ║
╚══════════════════════════════════════════════════════════════╝

Kurulum:
    pip install streamlit pandas numpy plotly yfinance

Çalıştırmak için:
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
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
#  GLOBAL STİL
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #080b12;
    color: #dde3ee;
}

/* Ana Sekme Navigasyonu */
[data-testid="stTabs"] > div:first-child {
    border-bottom: 1px solid #1a2236 !important;
    gap: 0 !important;
}
button[data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #4b5563 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    transition: all 0.2s !important;
}
button[data-baseweb="tab"]:hover { color: #9ca3af !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #34d399 !important;
    border-bottom-color: #34d399 !important;
}

/* KPI Kartı */
.kpi-card {
    background: #0f1623;
    border: 1px solid #1a2236;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-card.red::before    { background: linear-gradient(90deg,#ef4444,#dc2626); }
.kpi-card.green::before  { background: linear-gradient(90deg,#10b981,#34d399); }
.kpi-card.amber::before  { background: linear-gradient(90deg,#f59e0b,#fbbf24); }
.kpi-card.blue::before   { background: linear-gradient(90deg,#3b82f6,#60a5fa); }
.kpi-card.purple::before { background: linear-gradient(90deg,#8b5cf6,#a78bfa); }

.kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #374151;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.45rem;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.65rem;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.kpi-value.red    { color: #f87171; }
.kpi-value.green  { color: #34d399; }
.kpi-value.amber  { color: #fbbf24; }
.kpi-value.blue   { color: #60a5fa; }
.kpi-value.purple { color: #a78bfa; }
.kpi-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #4b5563;
}
.kpi-sub .pos { color: #34d399; }

/* Bölüm Başlığı */
.section-hdr {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #374151;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    border-bottom: 1px solid #1a2236;
    padding-bottom: 0.45rem;
    margin: 1.8rem 0 1rem 0;
}

/* Hero Başlık */
.hero { margin-bottom: 1.6rem; }
.hero-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2.2rem;
    letter-spacing: -0.025em;
    background: linear-gradient(135deg,#f0fdf4 0%,#86efac 45%,#34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.05;
}
.hero-title.market {
    background: linear-gradient(135deg,#eff6ff 0%,#93c5fd 45%,#60a5fa 100%);
    -webkit-background-clip: text;
    background-clip: text;
}
.hero-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #374151;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.3rem;
}

/* Info / Warning */
.info-box {
    background: #0a1628;
    border: 1px solid #1d4ed8;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #93c5fd;
    margin: 0.75rem 0;
}
.warn-box {
    background: #160a0a;
    border: 1px solid #7f1d1d;
    border-left: 3px solid #ef4444;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #fca5a5;
    margin: 0.75rem 0;
}

/* DataFrame */
[data-testid="stDataFrame"] table {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
}

/* Footer */
.footer {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: #1f2937;
    text-align: center;
    border-top: 1px solid #111827;
    padding-top: 1rem;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ═════════════════════════════════════════════════════════════

def fmt_tl(val: float) -> str:
    return f"₺{val:,.0f}".replace(",", ".")

def plotly_dark_layout(height=380, **kwargs):
    base = dict(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        font=dict(family="IBM Plex Mono", color="#6b7280", size=11),
        xaxis=dict(gridcolor="#1a2236", zerolinecolor="#1a2236"),
        yaxis=dict(gridcolor="#1a2236", zerolinecolor="#1a2236"),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0f1623", bordercolor="#1a2236",
                        font=dict(family="IBM Plex Mono", size=11)),
        legend=dict(bgcolor="#0f1623", bordercolor="#1a2236", borderwidth=1,
                    font=dict(size=10), orientation="h",
                    x=0.5, y=1.1, xanchor="center"),
        margin=dict(t=20, b=40, l=60, r=20),
        height=height,
    )
    base.update(kwargs)
    return base

# ─── BORÇ HESAPLAMA ───────────────────────────────────────────
def calculate_amortization(principal, monthly_rate, monthly_payment,
                            monthly_inflation=0.0, extra=0.0):
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
        balance -= principal_paid
        cum_inf *= (1 + monthly_inflation)
        rows.append({
            "Ay": ay,
            "Faiz (₺)": round(interest, 2),
            "Anapara (₺)": round(principal_paid, 2),
            "Nominal Kalan (₺)": round(max(balance, 0), 2),
            "Reel Kalan (₺)": round(max(balance / cum_inf, 0), 2),
        })
    return pd.DataFrame(rows)

# ─── RSI HESAPLAMA ────────────────────────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1) if not rsi.empty else np.nan

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
def fetch_market_data():
    end   = datetime.today()
    start = end - timedelta(days=200)
    results = []
    for ticker, name in TICKERS.items():
        try:
            df = yf.download(ticker, start=start, end=end,
                             progress=False, auto_adjust=True)
            if df.empty or len(df) < 55:
                continue
            close = df["Close"].squeeze()
            price      = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            change_pct = (price - prev_price) / prev_price * 100
            sma50      = float(close.rolling(50).mean().iloc[-1])
            rsi        = compute_rsi(close, 14)
            vol_recent = float(df["Volume"].squeeze().iloc[-5:].mean())
            vol_avg    = float(df["Volume"].squeeze().mean())
            market   = "🇹🇷 BIST" if ticker.endswith(".IS") else "🇺🇸 US"
            currency = "₺" if ticker.endswith(".IS") else "$"
            results.append({
                "Ticker":    ticker,
                "Şirket":    name,
                "Piyasa":    market,
                "Fiyat":     round(price, 2),
                "Döviz":     currency,
                "Değişim %": round(change_pct, 2),
                "RSI (14)":  rsi,
                "SMA-50":    round(sma50, 2),
                "F/SMA":     round(price / sma50, 4),
                "Vol Ratio": round(vol_recent / vol_avg, 2) if vol_avg else np.nan,
            })
        except Exception:
            continue
    return pd.DataFrame(results)


# ═════════════════════════════════════════════════════════════
#  ANA SEKMELER
# ═════════════════════════════════════════════════════════════
tab_debt, tab_market = st.tabs([
    "💸  Borç Erime Simülatörü",
    "📡  Kantitatif Piyasa Tarayıcısı",
])


# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 1 — BORÇ ERİME                                       ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_debt:
    st.markdown(
        '<div class="hero"><div class="hero-title">Borç Erime Simülatörü</div>'
        '<div class="hero-sub">// Debt-Freedom Planner · Senaryo Analizi</div></div>',
        unsafe_allow_html=True)

    # Girdiler
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        principal = st.number_input("💰 Güncel Borç (₺)", 100.0, 10_000_000.0,
                                    29_000.0, 500.0, format="%.0f")
    with c2:
        monthly_rate_pct = st.number_input("📈 Aylık Faiz (%)", 0.0, 30.0,
                                           3.5, 0.1, format="%.2f")
    with c3:
        monthly_payment = st.number_input("💳 Aylık Taksit (₺)", 100.0, 500_000.0,
                                          2_500.0, 100.0, format="%.0f")
    with c4:
        monthly_inflation_pct = st.number_input("🌡️ Aylık Enflasyon (%)", 0.0, 20.0,
                                                2.5, 0.1, format="%.2f")
    with c5:
        extra_payment = st.number_input("🚀 Ekstra Ödeme (₺)", 0.0, 100_000.0,
                                        500.0, 100.0, format="%.0f",
                                        help="Yemek/abonelik kısıptan borca eklenen tutar")

    monthly_rate      = monthly_rate_pct / 100
    monthly_inflation = monthly_inflation_pct / 100

    df_base  = calculate_amortization(principal, monthly_rate, monthly_payment,
                                      monthly_inflation, 0)
    df_extra = calculate_amortization(principal, monthly_rate, monthly_payment,
                                      monthly_inflation, extra_payment)

    if df_base is None:
        st.markdown(f"""<div class="warn-box">
        ⚠️  Taksit ({fmt_tl(monthly_payment)}) faiz maliyetini
        ({fmt_tl(principal * monthly_rate)}/ay) karşılamıyor.
        Taksiti artırın veya faizi düşürün.
        </div>""", unsafe_allow_html=True)
        st.stop()

    # KPI Hesapla
    total_months_base   = len(df_base)
    total_interest_base = df_base["Faiz (₺)"].sum()

    if df_extra is not None and extra_payment > 0:
        total_months_extra   = len(df_extra)
        total_interest_extra = df_extra["Faiz (₺)"].sum()
        saved_months         = total_months_base - total_months_extra
        saved_interest       = total_interest_base - total_interest_extra
    else:
        total_months_extra = total_months_base
        saved_months = saved_interest = 0

    # KPI Kartları
    k1, k2, k3, k4 = st.columns(4)
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
        delta_lbl = f'<span class="pos">−{saved_months} ay</span>' if saved_months > 0 else "—"
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Ekstra ile Erken Bitiş</div>
        <div class="kpi-value green">{total_months_extra if extra_payment else "—"} Ay</div>
        <div class="kpi-sub">{delta_lbl}</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Ekstra ile Faiz Tasarrufu</div>
        <div class="kpi-value green">{fmt_tl(saved_interest)}</div>
        <div class="kpi-sub">+{fmt_tl(extra_payment)}/ay ek ödemeyle</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Grafik 1: Borç Erime Eğrisi
    st.markdown('<div class="section-hdr">📉 Borç Erime Eğrisi — Nominal · Reel · Ekstra Senaryo</div>',
                unsafe_allow_html=True)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_base["Ay"], y=df_base["Nominal Kalan (₺)"],
        name="Nominal (Standart)", line=dict(color="#ef4444", width=2.5),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.05)",
        hovertemplate="<b>Ay %{x}</b><br>Nominal: ₺%{y:,.0f}<extra></extra>"))
    fig1.add_trace(go.Scatter(
        x=df_base["Ay"], y=df_base["Reel Kalan (₺)"],
        name="Reel (Enflasyon Etkili)", line=dict(color="#f59e0b", width=1.8, dash="dot"),
        hovertemplate="<b>Ay %{x}</b><br>Reel: ₺%{y:,.0f}<extra></extra>"))
    if df_extra is not None and extra_payment > 0:
        fig1.add_trace(go.Scatter(
            x=df_extra["Ay"], y=df_extra["Nominal Kalan (₺)"],
            name=f"Nominal (Ekstra +{fmt_tl(extra_payment)}/ay)",
            line=dict(color="#10b981", width=2.5),
            fill="tozeroy", fillcolor="rgba(16,185,129,0.05)",
            hovertemplate="<b>Ay %{x}</b><br>Ekstra: ₺%{y:,.0f}<extra></extra>"))
    fig1.add_hline(y=principal, line=dict(color="#1f2937", width=1, dash="longdash"),
                   annotation_text=f"Başlangıç {fmt_tl(principal)}",
                   annotation_font=dict(color="#374151", size=9))
    fig1.update_layout(**plotly_dark_layout(380),
                       yaxis=dict(gridcolor="#1a2236", zerolinecolor="#1a2236",
                                  tickprefix="₺", tickformat=",.0f"),
                       xaxis=dict(gridcolor="#1a2236", title="Ay"))
    st.plotly_chart(fig1, use_container_width=True)

    # Grafik 2: Faiz vs Anapara
    st.markdown('<div class="section-hdr">📊 Aylık Ödeme Dağılımı — Faiz vs Anapara</div>',
                unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df_base["Ay"], y=df_base["Faiz (₺)"],
                          name="Faiz", marker_color="#ef4444", opacity=0.85,
                          hovertemplate="Ay %{x}<br>Faiz: ₺%{y:,.0f}<extra></extra>"))
    fig2.add_trace(go.Bar(x=df_base["Ay"], y=df_base["Anapara (₺)"],
                          name="Anapara", marker_color="#10b981", opacity=0.85,
                          hovertemplate="Ay %{x}<br>Anapara: ₺%{y:,.0f}<extra></extra>"))
    fig2.update_layout(**plotly_dark_layout(280), barmode="stack",
                       yaxis=dict(gridcolor="#1a2236", zerolinecolor="#1a2236",
                                  tickprefix="₺", tickformat=",.0f"),
                       xaxis=dict(gridcolor="#1a2236", title="Ay"))
    st.plotly_chart(fig2, use_container_width=True)

    # Amortisman Tablosu
    st.markdown('<div class="section-hdr">📋 Amortisman Tablosu</div>', unsafe_allow_html=True)

    def fmt_df(df):
        d = df.copy()
        for col in ["Faiz (₺)", "Anapara (₺)", "Nominal Kalan (₺)", "Reel Kalan (₺)"]:
            d[col] = d[col].apply(lambda x: f"₺{x:,.2f}")
        return d

    sub1, sub2 = st.tabs(["📌 Standart Plan", f"🚀 Ekstra (+{fmt_tl(extra_payment)}/ay)"])
    with sub1:
        st.dataframe(fmt_df(df_base), use_container_width=True, height=380, hide_index=True)
        st.markdown(f"""<div class="info-box">
        📌 Toplam {total_months_base} ay &nbsp;·&nbsp;
        Toplam Faiz: {fmt_tl(total_interest_base)} &nbsp;·&nbsp;
        Anapara: {fmt_tl(principal)}
        </div>""", unsafe_allow_html=True)
    with sub2:
        if df_extra is not None and extra_payment > 0:
            st.dataframe(fmt_df(df_extra), use_container_width=True, height=380, hide_index=True)
            st.markdown(f"""<div class="info-box">
            🚀 Toplam {total_months_extra} ay &nbsp;·&nbsp;
            Faiz: {fmt_tl(total_interest_extra)} &nbsp;·&nbsp;
            <span style='color:#34d399'>Tasarruf: {fmt_tl(saved_interest)} + {saved_months} ay</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Ekstra ödeme tutarını yukarıdaki alandan girin.")


# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 2 — MARKET SCREENER                                   ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_market:
    st.markdown(
        '<div class="hero"><div class="hero-title market">Kantitatif Piyasa Tarayıcısı</div>'
        '<div class="hero-sub">// RSI · SMA-50 · BIST & US Markets · 15 dk cache</div></div>',
        unsafe_allow_html=True)

    col_btn, col_note = st.columns([1, 5])
    with col_btn:
        refresh = st.button("🔄 Veriyi Yenile", type="primary")
    with col_note:
        st.markdown("""<div style='font-family:"IBM Plex Mono",monospace;font-size:0.68rem;
        color:#374151;padding-top:0.6rem;'>
        Veri yfinance üzerinden çekilir · RSI &lt; 30 = Aşırı Satılmış · Fiyat &gt; SMA-50 = Güçlü Trend
        </div>""", unsafe_allow_html=True)

    if refresh:
        st.cache_data.clear()

    with st.spinner("📡  Piyasa verileri çekiliyor…"):
        df_mkt = fetch_market_data()

    if df_mkt.empty:
        st.markdown("""<div class="warn-box">
        ⚠️  Veri çekilemedi. İnternet bağlantınızı ve yfinance kurulumunu kontrol edin.
        </div>""", unsafe_allow_html=True)
        st.stop()

    # Özet KPI'lar
    oversold     = df_mkt[df_mkt["RSI (14)"] < 30]
    strong_trend = df_mkt[df_mkt["F/SMA"] > 1.0]
    avg_rsi      = df_mkt["RSI (14)"].mean()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class="kpi-card blue">
        <div class="kpi-label">Taranan Hisse</div>
        <div class="kpi-value blue">{len(df_mkt)}</div>
        <div class="kpi-sub">BIST + US</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="kpi-card green">
        <div class="kpi-label">Aşırı Satılmış (RSI&lt;30)</div>
        <div class="kpi-value green">{len(oversold)}</div>
        <div class="kpi-sub">Potansiyel alım fırsatı</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="kpi-card purple">
        <div class="kpi-label">Güçlü Trendli</div>
        <div class="kpi-value purple">{len(strong_trend)}</div>
        <div class="kpi-sub">Fiyat &gt; SMA-50</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        rc = "green" if avg_rsi < 50 else "amber" if avg_rsi < 70 else "red"
        st.markdown(f"""<div class="kpi-card {rc}">
        <div class="kpi-label">Ortalama RSI</div>
        <div class="kpi-value {rc}">{avg_rsi:.1f}</div>
        <div class="kpi-sub">Tüm hisseler ortalaması</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Tablo 1: Aşırı Satılmış
    st.markdown('<div class="section-hdr">🟢 Aşırı Satılmış — Potansiyel Ucuz Hisseler (RSI &lt; 30)</div>',
                unsafe_allow_html=True)

    if oversold.empty:
        st.markdown("""<div class="info-box">
        ℹ️  Şu an RSI &lt; 30 olan hisse bulunmuyor. Piyasa nötr/güçlü seyrediyor.
        </div>""", unsafe_allow_html=True)
    else:
        cols_os = ["Ticker","Şirket","Piyasa","Fiyat","Döviz","Değişim %","RSI (14)","SMA-50","Vol Ratio"]
        def style_os(df):
            s = pd.DataFrame("", index=df.index, columns=df.columns)
            s["RSI (14)"] = "color:#34d399;font-weight:600"
            s["Ticker"]   = "color:#34d399"
            return s
        st.dataframe(
            oversold[cols_os].style.apply(style_os, axis=None)
                .format({"Değişim %": "{:+.2f}%", "Vol Ratio": "{:.2f}x"}),
            use_container_width=True, hide_index=True)

    # Tablo 2: Güçlü Trend
    st.markdown('<div class="section-hdr">📈 Trendi Güçlü — Fiyat &gt; SMA-50</div>',
                unsafe_allow_html=True)

    if strong_trend.empty:
        st.markdown("""<div class="warn-box">⚠️  SMA-50 üzerinde hisse bulunamadı.</div>""",
                    unsafe_allow_html=True)
    else:
        cols_st = ["Ticker","Şirket","Piyasa","Fiyat","Döviz","Değişim %","RSI (14)","SMA-50","F/SMA","Vol Ratio"]
        def style_st(df):
            s = pd.DataFrame("", index=df.index, columns=df.columns)
            s["F/SMA"]   = "color:#60a5fa;font-weight:600"
            s["Ticker"]  = "color:#60a5fa"
            return s
        st.dataframe(
            strong_trend[cols_st].style.apply(style_st, axis=None)
                .format({"Değişim %": "{:+.2f}%", "F/SMA": "{:.3f}x", "Vol Ratio": "{:.2f}x"}),
            use_container_width=True, hide_index=True)

    # Tüm Hisseler Tablosu
    st.markdown('<div class="section-hdr">🗂️ Tüm Hisseler — Tam Özet</div>', unsafe_allow_html=True)

    def style_full(df):
        s = pd.DataFrame("", index=df.index, columns=df.columns)
        for i, row in df.iterrows():
            if pd.notna(row.get("RSI (14)")):
                if row["RSI (14)"] < 30:
                    s.loc[i, "RSI (14)"] = "color:#34d399;font-weight:600"
                elif row["RSI (14)"] > 70:
                    s.loc[i, "RSI (14)"] = "color:#f87171;font-weight:600"
                else:
                    s.loc[i, "RSI (14)"] = "color:#9ca3af"
            if pd.notna(row.get("Değişim %")):
                s.loc[i, "Değişim %"] = "color:#34d399" if row["Değişim %"] >= 0 else "color:#f87171"
            if pd.notna(row.get("F/SMA")):
                s.loc[i, "F/SMA"] = "color:#60a5fa" if row["F/SMA"] > 1 else "color:#f59e0b"
        return s

    cols_all = ["Ticker","Şirket","Piyasa","Fiyat","Döviz","Değişim %","RSI (14)","SMA-50","F/SMA","Vol Ratio"]
    st.dataframe(
        df_mkt[cols_all].style.apply(style_full, axis=None)
            .format({"Değişim %": "{:+.2f}%", "F/SMA": "{:.3f}x",
                     "Vol Ratio": "{:.2f}x", "RSI (14)": "{:.1f}"}),
        use_container_width=True, height=450, hide_index=True)

    # RSI Bar Grafiği
    st.markdown('<div class="section-hdr">📊 RSI Panoraması</div>', unsafe_allow_html=True)

    df_sorted  = df_mkt.sort_values("RSI (14)")
    rsi_colors = ["#34d399" if r < 30 else "#f87171" if r > 70 else "#60a5fa"
                  for r in df_sorted["RSI (14)"]]

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Bar(
        x=df_sorted["Ticker"],
        y=df_sorted["RSI (14)"],
        marker_color=rsi_colors, opacity=0.85,
        text=df_sorted["RSI (14)"].apply(lambda x: f"{x:.1f}"),
        textposition="outside",
        textfont=dict(size=10, family="IBM Plex Mono"),
        hovertemplate="<b>%{x}</b><br>RSI: %{y:.1f}<extra></extra>",
    ))
    fig_rsi.add_hline(y=70, line=dict(color="#f87171", width=1, dash="dash"),
                      annotation_text="Aşırı Alınmış (70)",
                      annotation_font=dict(color="#f87171", size=9))
    fig_rsi.add_hline(y=30, line=dict(color="#34d399", width=1, dash="dash"),
                      annotation_text="Aşırı Satılmış (30)",
                      annotation_font=dict(color="#34d399", size=9))
    fig_rsi.add_hline(y=50, line=dict(color="#1f2937", width=1))
    fig_rsi.update_layout(**plotly_dark_layout(320),
                          yaxis=dict(gridcolor="#1a2236", range=[0, 110], title="RSI"),
                          xaxis=dict(gridcolor="#1a2236", title="Ticker"),
                          showlegend=False)
    st.plotly_chart(fig_rsi, use_container_width=True)

    # Açıklama
    st.markdown("""<div class="info-box">
    <b>Göstergeler:</b> &nbsp;
    RSI (14) = 14 günlük momentum göstergesi. &nbsp;·&nbsp;
    SMA-50 = 50 günlük basit hareketli ortalama. &nbsp;·&nbsp;
    F/SMA = Fiyat / SMA-50; 1 üzeri = yukarı trend. &nbsp;·&nbsp;
    Vol Ratio = Son 5 gün hacmi / 6 ay ort. hacim. &nbsp;·&nbsp;
    <span style='color:#fbbf24'>Bu araç eğitim amaçlıdır; yatırım tavsiyesi değildir.</span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""<div class="footer">
Kişisel Finans Merkezi v2.0 &nbsp;·&nbsp; Eğitim & Planlama Amaçlıdır
&nbsp;·&nbsp; Finansal tavsiye değildir &nbsp;·&nbsp; Veriler yfinance üzerinden çekilir
</div>""", unsafe_allow_html=True)
