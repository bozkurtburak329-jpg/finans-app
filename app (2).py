"""
╔══════════════════════════════════════════════════════════════╗
║  KİŞİSEL FİNANS MERKEZİ  ·  v4.0 (Pro Trader Edition)        ║
║  Sekme 1 : Kantitatif Piyasa Tarayıcısı + Kripto + Simülatör ║
║  Sekme 2 : Borç Erime & Özgürlük Simülatörü                  ║
╚══════════════════════════════════════════════════════════════╝
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
#  GLOBAL STİL (Yenilenmiş, Daha Güçlü Fontlar)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #070a10;
    color: #d4dbe8;
}

/* ── Sekme Navigasyonu ── */
[data-testid="stTabs"] > div:first-child { border-bottom: 1px solid #161d2e !important; }
button[data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #3d4f6b !important;
    padding: 0.8rem 1.6rem !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #34d399 !important;
    border-bottom-color: #34d399 !important;
}

/* ── Sinyal Rozeti (Daha Belirgin) ── */
.signal-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    font-weight: 800;
    padding: 0.3rem 0.7rem;
    border-radius: 4px;
    letter-spacing: 0.05em;
}
.signal-buy    { background:#052e16; color:#34d399; border:1px solid #065f46; }
.signal-sell   { background:#2d1515; color:#f87171; border:1px solid #7f1d1d; }
.signal-hold   { background:#0c1a2e; color:#60a5fa; border:1px solid #1e3a5f; }
.signal-watch  { background:#1c1408; color:#fbbf24; border:1px solid #78350f; }

/* ── Sidebar (Daha Kalın Yazılar) ── */
[data-testid="stSidebar"] { background: #0a0e18; border-right: 1px solid #111827; }
[data-testid="stSidebar"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    color: #8899b8 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── KPI Kartı ── */
.kpi-card {
    background: #0c1220; border: 1px solid #161d2e; border-radius: 12px;
    padding: 1.2rem 1.4rem 1rem; position: relative; overflow: hidden; height: 100%;
}
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 12px 12px 0 0; }
.kpi-card.red::before    { background: linear-gradient(90deg,#ef4444,#dc2626); }
.kpi-card.green::before  { background: linear-gradient(90deg,#10b981,#34d399); }
.kpi-card.amber::before  { background: linear-gradient(90deg,#f59e0b,#fbbf24); }
.kpi-card.blue::before   { background: linear-gradient(90deg,#3b82f6,#60a5fa); }
.kpi-card.cyan::before   { background: linear-gradient(90deg,#06b6d4,#22d3ee); }

.kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; font-weight: 600; color: #8899b8; text-transform: uppercase; margin-bottom: 0.5rem; }
.kpi-value { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.8rem; line-height: 1; margin-bottom: 0.3rem; }
.kpi-value.red    { color: #f87171; }
.kpi-value.green  { color: #34d399; }
.kpi-value.amber  { color: #fbbf24; }
.kpi-value.blue   { color: #60a5fa; }
.kpi-value.cyan   { color: #22d3ee; }
.kpi-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.66rem; color: #3d4f6b; line-height: 1.4; }
.kpi-sub .pos { color: #34d399; }
.kpi-sub .neg { color: #f87171; }

/* ── Hero Başlık ── */
.hero { margin-bottom: 1.4rem; }
.hero-title {
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2rem;
    background: linear-gradient(135deg,#f0fdf4 0%,#86efac 45%,#34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1;
}
.hero-title.market { background: linear-gradient(135deg,#eff6ff 0%,#93c5fd 45%,#60a5fa 100%); -webkit-background-clip: text; }
.hero-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #2e3d55; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.25rem; }

/* ── Bölüm Başlığı ── */
.section-hdr { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; font-weight: 700; color: #8899b8; text-transform: uppercase; border-bottom: 1px solid #111827; padding-bottom: 0.4rem; margin: 2rem 0 1rem 0; }

/* ── Info / Warning ── */
.info-box { background: #080f1e; border: 1px solid #1d4ed8; border-left: 3px solid #3b82f6; border-radius: 8px; padding: 0.7rem 1rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #93c5fd; margin: 0.75rem 0; }
.warn-box { background: #120606; border: 1px solid #7f1d1d; border-left: 3px solid #ef4444; border-radius: 8px; padding: 0.7rem 1rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #fca5a5; margin: 0.75rem 0; }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR & LİSTELER
# ═════════════════════════════════════════════════════════════

def fmt_val(val: float, currency: str) -> str:
    if currency == "₺": return f"₺{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${val:,.2f}"

def fmt_tl(val: float) -> str:
    return f"₺{val:,.0f}".replace(",", ".")

def get_plotly_base(height: int = 380) -> dict:
    return {
        "plot_bgcolor":  "#0b0f1a", "paper_bgcolor": "#0b0f1a",
        "font":          {"family": "IBM Plex Mono", "color": "#3d4f6b", "size": 11},
        "hovermode":     "x unified",
        "hoverlabel":    {"bgcolor": "#0c1220", "bordercolor": "#161d2e", "font": {"family": "IBM Plex Mono", "size": 11}},
        "legend":        {"bgcolor": "#0c1220", "bordercolor": "#161d2e", "borderwidth": 1, "font": {"size": 10}, "orientation": "h", "x": 0.5, "y": 1.1, "xanchor": "center"},
        "margin":        {"t": 20, "b": 45, "l": 65, "r": 20},
        "height":        height,
    }

def axis_style(title: str = "", prefix: str = "", fmt: str = "") -> dict:
    d: dict = {"gridcolor": "#111827", "zerolinecolor": "#111827", "tickfont": {"size": 10}}
    if title:  d["title"] = title
    if prefix: d["tickprefix"] = prefix
    if fmt:    d["tickformat"] = fmt
    return d

def calculate_amortization(principal: float, monthly_rate: float, monthly_payment: float, monthly_inflation: float = 0.0, extra: float = 0.0):
    if monthly_rate > 0 and monthly_payment <= principal * monthly_rate: return None
    rows, balance, cum_inf, ay = [], principal, 1.0, 0
    total_pay = monthly_payment + extra
    while balance > 0.01 and ay < 600:
        ay += 1
        interest = balance * monthly_rate
        principal_paid = min(total_pay - interest, balance)
        if principal_paid <= 0: return None
        balance -= principal_paid
        cum_inf *= (1 + monthly_inflation)
        rows.append({
            "Ay": ay, "Faiz (₺)": round(interest, 2), "Anapara (₺)": round(principal_paid, 2),
            "Nominal Kalan (₺)": round(max(balance, 0), 2), "Reel Kalan (₺)": round(max(balance / cum_inf, 0), 2),
        })
    return pd.DataFrame(rows)

TICKERS_BIST_US = {
    "THYAO.IS": "Türk Hava Yolları", "GARAN.IS": "Garanti BBVA", "ASELS.IS": "Aselsan",
    "EREGL.IS": "Ereğli Demir Çelik", "KCHOL.IS": "Koç Holding", "SISE.IS": "Şişecam",
    "AAPL": "Apple", "TSLA": "Tesla", "NVDA": "NVIDIA", "MSFT": "Microsoft"
}

TICKERS_CRYPTO = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin",
    "SOL-USD": "Solana", "XRP-USD": "Ripple", "AVAX-USD": "Avalanche",
    "DOGE-USD": "Dogecoin", "ADA-USD": "Cardano"
}

def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return round(float(val), 1) if pd.notna(val) else np.nan

def compute_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return round(float(macd_line.iloc[-1]), 4), round(float(signal_line.iloc[-1]), 4), round(float(histogram.iloc[-1]), 4)

def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> float:
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(float(atr), 4) if pd.notna(atr) else np.nan

def generate_signal(row: dict) -> tuple[str, str, str]:
    rsi = row.get("RSI")
    hist = row.get("MACD_Hist")
    above = row.get("Above_SMA50")
    
    if pd.notna(rsi) and rsi < 30 and pd.notna(hist) and hist > 0: return "⬆ Güçlü Al", "signal-buy", "AL"
    if pd.notna(rsi) and rsi < 35: return "⬆ Dipte (Oversold)", "signal-buy", "AL"
    if pd.notna(rsi) and rsi > 70 and pd.notna(hist) and hist < 0: return "⬇ Güçlü Sat", "signal-sell", "SAT"
    if pd.notna(rsi) and rsi > 70: return "⚠ Aşırı Alım", "signal-sell", "SAT"
    if pd.notna(above) and above and pd.notna(hist) and hist > 0: return "↗ Trendle Git", "signal-hold", "TUT"
    if pd.notna(above) and not above: return "↘ Zayıf Trend", "signal-watch", "TUT"
    return "◼ Bekle", "signal-hold", "TUT"

@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_data(asset_type: str) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=365)
    rows = []
    tickers_dict = TICKERS_CRYPTO if asset_type == "Kripto (Bitcoin vb.)" else TICKERS_BIST_US

    for ticker, name in tickers_dict.items():
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 60: continue

            close = df["Close"].squeeze()
            high = df["High"].squeeze()
            low = df["Low"].squeeze()

            price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            chg_pct = (price - prev_price) / prev_price * 100
            high_52w = float(high.max())
            low_52w = float(low.min())

            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            macd_v, macd_sig, macd_hist = compute_macd(close)
            atr = compute_atr(high, low, close)
            atr_pct = round(atr / price * 100, 2) if price else np.nan

            if "USD" in ticker:
                market, currency = "₿ Kripto", "$"
            else:
                market = "🇹🇷 BIST" if ticker.endswith(".IS") else "🇺🇸 ABD"
                currency = "₺" if ticker.endswith(".IS") else "$"

            row_data = {
                "Ticker": ticker, "Şirket": name, "Piyasa": market, "Fiyat": price, "Döviz": currency,
                "Değişim %": chg_pct, "RSI": rsi, "MACD_Hist": macd_hist, "SMA-50": sma50,
                "Above_SMA50": price > sma50, "F/SMA": price / sma50 if sma50 else 0, "ATR %": atr_pct,
                "52H_Zirve": high_52w, "52H_Dip": low_52w
            }
            sig_label, sig_class, action = generate_signal(row_data)
            row_data["Sinyal"] = sig_label
            row_data["Sinyal_Class"] = sig_class
            row_data["Aksiyon"] = action
            rows.append(row_data)
        except Exception:
            continue
    return pd.DataFrame(rows)


# ═════════════════════════════════════════════════════════════
#  SİDEBAR — SCREENER FİLTRELERİ
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Varlık & Filtreler")
    
    asset_class = st.radio("Piyasa Seçimi", ["Hisse Senedi (Borsa)", "Kripto (Bitcoin vb.)"], help="Tarama yapılacak piyasayı seçin.")
    st.markdown("---")
    
    sinyal_filtre = st.multiselect("Aksiyon Durumu", ["AL", "SAT", "TUT"], default=["AL", "SAT", "TUT"])
    rsi_range = st.slider("RSI Aralığı", 0, 100, (0, 100))
    st.markdown("---")
    st.markdown("""<div style='font-family:"IBM Plex Mono",monospace;font-size:0.7rem; color:#8899b8; line-height:1.7;'>
    <b>RSI &lt; 30</b> → Dip / Aşırı Satılmış<br>
    <b>RSI &gt; 70</b> → Zirve / Aşırı Alınmış<br>
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  ANA SEKMELER
# ═════════════════════════════════════════════════════════════
tab_market, tab_debt = st.tabs([
    "📡  Piyasa Tarayıcısı & Simülatör",
    "💸  Borç Erime Simülatörü"
])

# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 1 — MARKET SCREENER + GELECEK SİMÜLATÖRÜ              ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_market:
    st.markdown('<div class="hero"><div class="hero-title market">Kantitatif Trader Terminali</div></div>', unsafe_allow_html=True)

    hdr_col, btn_col = st.columns([6, 1])
    with btn_col:
        if st.button("🔄 Verileri Yenile", type="primary", use_container_width=True):
            st.cache_data.clear()

    with st.spinner(f"📡 {asset_class} verileri çekiliyor ve analiz ediliyor..."):
        df_raw = fetch_market_data(asset_class)

    if df_raw.empty:
        st.error("⚠️ Veri çekilemedi. İnternet bağlantınızı kontrol edin.")
    else:
        # Filtreleri Uygula
        df_f = df_raw.copy()
        if sinyal_filtre: df_f = df_f[df_f["Aksiyon"].isin(sinyal_filtre)]
        df_f = df_f[(df_f["RSI"] >= rsi_range[0]) & (df_f["RSI"] <= rsi_range[1])]

        # KPI Özet
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div class="kpi-card blue">
            <div class="kpi-label">Taranan Varlık</div>
            <div class="kpi-value blue">{len(df_f)} / {len(df_raw)}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            al_count = len(df_raw[df_raw["Aksiyon"] == "AL"])
            st.markdown(f"""<div class="kpi-card green">
            <div class="kpi-label">Hızlı Aksiyon: AL</div>
            <div class="kpi-value green">{al_count}</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            sat_count = len(df_raw[df_raw["Aksiyon"] == "SAT"])
            st.markdown(f"""<div class="kpi-card red">
            <div class="kpi-label">Hızlı Aksiyon: SAT</div>
            <div class="kpi-value red">{sat_count}</div>
            </div>""", unsafe_allow_html=True)
        with m4:
            avg_rsi = df_raw["RSI"].mean()
            rc = "green" if avg_rsi < 40 else "amber" if avg_rsi < 65 else "red"
            st.markdown(f"""<div class="kpi-card {rc}">
            <div class="kpi-label">Piyasa Ort. RSI</div>
            <div class="kpi-value {rc}">{avg_rsi:.1f}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

        # Sinyal Motoru Tablosu
        st.markdown('<div class="section-hdr">⚡ CANLI PİYASA VE HIZLI AKSİYON TABLOSU</div>', unsafe_allow_html=True)

        if df_f.empty:
            st.info("ℹ️ Seçili filtrelerle eşleşen varlık bulunamadı.")
        else:
            display_cols = ["Ticker", "Şirket", "Piyasa", "Fiyat", "Döviz", "Değişim %", "RSI", "MACD_Hist", "Aksiyon", "Sinyal"]
            
            def style_signal_table(df):
                s = pd.DataFrame("", index=df.index, columns=df.columns)
                for i, row in df.iterrows():
                    if pd.notna(row.get("RSI")): s.loc[i, "RSI"] = "color:#34d399;font-weight:700" if row["RSI"] < 35 else "color:#f87171;font-weight:700" if row["RSI"] > 65 else ""
                    if pd.notna(row.get("Değişim %")): s.loc[i, "Değişim %"] = "color:#34d399" if row["Değişim %"] >= 0 else "color:#f87171"
                    
                    act = row.get("Aksiyon", "")
                    if act == "AL": s.loc[i, "Aksiyon"] = "background-color:#065f46; color:#34d399; font-weight:bold"
                    elif act == "SAT": s.loc[i, "Aksiyon"] = "background-color:#7f1d1d; color:#f87171; font-weight:bold"
                    else: s.loc[i, "Aksiyon"] = "color:#8899b8"
                return s

            display_df = df_f[display_cols].copy()
            styled = display_df.style.apply(style_signal_table, axis=None).format({
                "Değişim %": "{:+.2f}%", "Fiyat": "{:,.2f}", "RSI": "{:.1f}", "MACD_Hist": "{:+.4f}"
            }, na_rep="—")
            st.dataframe(styled, use_container_width=True, height=350, hide_index=True)

        # GELECEK SENARYOSU SİMÜLATÖRÜ
        st.markdown('<div class="section-hdr">🔮 GELECEK SENARYOSU & DETAYLI ANALİZ (Tıkla ve Simüle Et)</div>', unsafe_allow_html=True)
        col_sel, col_amt = st.columns([2, 1])
        with col_sel:
            selected_ticker = st.selectbox("Analiz Edilecek Varlığı Seçin", df_raw["Ticker"].tolist())
        with col_amt:
            curr_symbol = df_raw[df_raw["Ticker"] == selected_ticker]["Döviz"].iloc[0]
            invest_amount = st.number_input(f"Simülasyon Yatırım Tutarı ({curr_symbol})", min_value=10.0, value=1000.0, step=100.0)

        if selected_ticker:
            asset_data = df_raw[df_raw["Ticker"] == selected_ticker].iloc[0]
            current_price = asset_data["Fiyat"]
            ath = asset_data["52H_Zirve"]
            atl = asset_data["52H_Dip"]
            
            units_bought = invest_amount / current_price
            profit_ath = (units_bought * ath) - invest_amount
            pct_ath = (ath - current_price) / current_price * 100
            loss_atl = invest_amount - (units_bought * atl)
            pct_atl = (current_price - atl) / current_price * 100
            
            st.markdown(f"""
            <div style='background:#0a0e18; border:1px solid #1e3a5f; border-radius:8px; padding:1.5rem; margin-top:1rem;'>
                <h4 style='color:#60a5fa; margin-top:0; font-family:"Syne", sans-serif;'>{asset_data['Şirket']} ({selected_ticker}) Simülasyonu</h4>
                <p style='font-family:"IBM Plex Mono", monospace; font-size:0.9rem; color:#8899b8;'>
                    Güncel Fiyat: <b style='color:#d4dbe8'>{fmt_val(current_price, curr_symbol)}</b><br>
                    Şu an <b style='color:#34d399'>{fmt_val(invest_amount, curr_symbol)}</b> yatırırsan tahmini olarak <b>{units_bought:.4f} adet</b> alırsın.
                </p>
                <hr style='border-color:#161d2e'>
                <div style='display:flex; justify-content:space-between;'>
                    <div style='width:48%; background:#052e16; padding:1rem; border-radius:6px; border:1px solid #065f46;'>
                        <div style='color:#34d399; font-weight:bold; margin-bottom:0.5rem;'>🚀 İyimser Senaryo (52 Hafta Zirvesi)</div>
                        Hedef Fiyat: {fmt_val(ath, curr_symbol)} <br>
                        Yükseliş İhtimali Potansiyeli: <b>+%{pct_ath:.1f}</b> <br>
                        <div style='margin-top:0.5rem; font-size:1.1rem;'>Tahmini Kar: <b style='color:#10b981'>+{fmt_val(profit_ath, curr_symbol)}</b></div>
                    </div>
                    <div style='width:48%; background:#2d1515; padding:1rem; border-radius:6px; border:1px solid #7f1d1d;'>
                        <div style='color:#f87171; font-weight:bold; margin-bottom:0.5rem;'>📉 Kötümser Senaryo (52 Hafta Dibi)</div>
                        Destek Fiyatı: {fmt_val(atl, curr_symbol)} <br>
                        Düşüş Riski: <b>-%{pct_atl:.1f}</b> <br>
                        <div style='margin-top:0.5rem; font-size:1.1rem;'>Tahmini Zarar: <b style='color:#ef4444'>-{fmt_val(loss_atl, curr_symbol)}</b></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 2 — BORÇ ERİME SİMÜLATÖRÜ (Tam Entegre Edildi)        ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_debt:
    st.markdown('<div class="hero"><div class="hero-title">Borç Erime Simülatörü</div><div class="hero-sub">// Debt-Freedom Planner · Senaryo & Reel Değer Analizi</div></div>', unsafe_allow_html=True)

    g1, g2, g3, g4, g5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])
    with g1: principal = st.number_input("💰 Güncel Borç (₺)", 100.0, 10_000_000.0, 29_000.0, 500.0, format="%.0f")
    with g2: monthly_rate_pct = st.number_input("📈 Aylık Faiz (%)", 0.0, 30.0, 3.5, 0.1, format="%.2f")
    with g3: monthly_payment = st.number_input("💳 Aylık Taksit (₺)", 100.0, 500_000.0, 2_500.0, 100.0, format="%.0f")
    with g4: monthly_inflation_pct = st.number_input("🌡️ Aylık Enflasyon (%)", 0.0, 20.0, 2.5, 0.1, format="%.2f")
    with g5: extra_payment = st.number_input("🚀 Ekstra Ödeme (₺)", 0.0, 100_000.0, 500.0, 100.0, format="%.0f", help="Yemek/abonelik kısıptan borca eklenen tutar")

    monthly_rate = monthly_rate_pct / 100
    monthly_inflation = monthly_inflation_pct / 100

    df_base = calculate_amortization(principal, monthly_rate, monthly_payment, monthly_inflation, 0)
    df_extra = calculate_amortization(principal, monthly_rate, monthly_payment, monthly_inflation, extra_payment)

    if df_base is None:
        st.markdown(f"""<div class="warn-box">⚠️ Aylık taksit ({fmt_tl(monthly_payment)}) faiz maliyetini ({fmt_tl(principal * monthly_rate)}/ay) karşılamıyor. Taksiti artırın veya faiz oranını düşürün.</div>""", unsafe_allow_html=True)
    else:
        total_months_base = len(df_base)
        total_interest_base = df_base["Faiz (₺)"].sum()

        if df_extra is not None and extra_payment > 0:
            total_months_extra = len(df_extra)
            total_interest_extra = df_extra["Faiz (₺)"].sum()
            saved_months = total_months_base - total_months_extra
            saved_interest = total_interest_base - total_interest_extra
        else:
            total_months_extra = total_months_base
            saved_months = saved_interest = 0

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(f"""<div class="kpi-card red"><div class="kpi-label">Standart Süre</div><div class="kpi-value red">{total_months_base} Ay</div><div class="kpi-sub">≈ {total_months_base/12:.1f} yıl</div></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="kpi-card amber"><div class="kpi-label">Toplam Faiz Maliyeti</div><div class="kpi-value amber">{fmt_tl(total_interest_base)}</div><div class="kpi-sub">Anaparaya oran: %{total_interest_base/principal*100:.1f}</div></div>""", unsafe_allow_html=True)
        with k3:
            delta_lbl = f'<span class="pos">−{saved_months} ay erken</span>' if saved_months > 0 else "—"
            val_str = f"{total_months_extra} Ay" if extra_payment > 0 else "—"
            st.markdown(f"""<div class="kpi-card green"><div class="kpi-label">Ekstra ile Bitiş</div><div class="kpi-value green">{val_str}</div><div class="kpi-sub">{delta_lbl}</div></div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""<div class="kpi-card green"><div class="kpi-label">Faiz Tasarrufu</div><div class="kpi-value green">{fmt_tl(saved_interest)}</div><div class="kpi-sub">+{fmt_tl(extra_payment)}/ay ekstra ile</div></div>""", unsafe_allow_html=True)
        with k5:
            enf_yillik = (1 + monthly_inflation) ** 12 - 1
            st.markdown(f"""<div class="kpi-card cyan"><div class="kpi-label">Yıllık Enflasyon</div><div class="kpi-value cyan">%{enf_yillik*100:.1f}</div><div class="kpi-sub">Aylık %{monthly_inflation_pct:.1f} bileşik</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">📉 Borç Erime Eğrisi — Nominal · Reel · Ekstra Senaryo</div>', unsafe_allow_html=True)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_base["Ay"], y=df_base["Nominal Kalan (₺)"], name="Nominal (Standart)", line=dict(color="#ef4444", width=2.5), fill="tozeroy", fillcolor="rgba(239,68,68,0.04)", hovertemplate="<b>Ay %{x}</b><br>Nominal: ₺%{y:,.0f}<extra></extra>"))
        fig1.add_trace(go.Scatter(x=df_base["Ay"], y=df_base["Reel Kalan (₺)"], name="Reel (Enflasyon İndirgeli)", line=dict(color="#f59e0b", width=2, dash="dot"), hovertemplate="<b>Ay %{x}</b><br>Reel: ₺%{y:,.0f}<extra></extra>"))
        if df_extra is not None and extra_payment > 0:
            fig1.add_trace(go.Scatter(x=df_extra["Ay"], y=df_extra["Nominal Kalan (₺)"], name=f"Nominal (Ekstra +{fmt_tl(extra_payment)}/ay)", line=dict(color="#34d399", width=2.5), fill="tozeroy", fillcolor="rgba(52,211,153,0.04)", hovertemplate="<b>Ay %{x}</b><br>Ekstra Senaryo: ₺%{y:,.0f}<extra></extra>"))
        fig1.add_hline(y=principal, line=dict(color="#1f2937", width=1, dash="longdash"), annotation_text=f"Başlangıç {fmt_tl(principal)}", annotation_font=dict(color="#374151", size=9))

        layout1 = get_plotly_base(400)
        layout1["xaxis"] = axis_style("Ay")
        layout1["yaxis"] = axis_style("Kalan Borç", "₺", ",.0f")
        fig1.update_layout(**layout1)
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown('<div class="section-hdr">📊 Aylık Ödeme Dağılımı — Faiz vs Anapara</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df_base["Ay"], y=df_base["Faiz (₺)"], name="Faiz", marker_color="#ef4444", opacity=0.82, hovertemplate="Ay %{x}<br>Faiz: ₺%{y:,.0f}<extra></extra>"))
        fig2.add_trace(go.Bar(x=df_base["Ay"], y=df_base["Anapara (₺)"], name="Anapara", marker_color="#10b981", opacity=0.82, hovertemplate="Ay %{x}<br>Anapara: ₺%{y:,.0f}<extra></extra>"))
        layout2 = get_plotly_base(280)
        layout2["barmode"] = "stack"
        layout2["xaxis"] = axis_style("Ay")
        layout2["yaxis"] = axis_style("Ödeme (₺)", "₺", ",.0f")
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="section-hdr">📋 Amortisman Tablosu</div>', unsafe_allow_html=True)
        def fmt_df(df: pd.DataFrame) -> pd.DataFrame:
            d = df.copy()
            for col in ["Faiz (₺)", "Anapara (₺)", "Nominal Kalan (₺)", "Reel Kalan (₺)"]: d[col] = d[col].apply(lambda x: f"₺{x:,.2f}")
            return d

        sub1, sub2 = st.tabs(["📌 Standart Plan", f"🚀 Ekstra (+{fmt_tl(extra_payment)}/ay)"])
        with sub1:
            st.dataframe(fmt_df(df_base), use_container_width=True, height=360, hide_index=True)
            st.markdown(f"""<div class="info-box">📌 Toplam {total_months_base} ay &nbsp;·&nbsp; Toplam Faiz: {fmt_tl(total_interest_base)} &nbsp;·&nbsp; Anapara: {fmt_tl(principal)}</div>""", unsafe_allow_html=True)
        with sub2:
            if df_extra is not None and extra_payment > 0:
                st.dataframe(fmt_df(df_extra), use_container_width=True, height=360, hide_index=True)
                st.markdown(f"""<div class="info-box">🚀 Toplam {total_months_extra} ay &nbsp;·&nbsp; Faiz: {fmt_tl(total_interest_extra)} &nbsp;·&nbsp; <span style='color:#34d399'>Tasarruf: {fmt_tl(saved_interest)} + {saved_months} ay erken bitiş</span></div>""", unsafe_allow_html=True)
            else:
                st.info("Sol üstteki 'Ekstra Ödeme' alanından tutar girin.")

# ─────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""<div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#161d2e;text-align:center;border-top:1px solid #0d1117;padding-top:1.2rem;margin-top:2.5rem;">
Kişisel Finans Merkezi v4.0 &nbsp;·&nbsp; Eğitim & Planlama Amaçlıdır &nbsp;·&nbsp; Finansal tavsiye değildir
</div>""", unsafe_allow_html=True)
