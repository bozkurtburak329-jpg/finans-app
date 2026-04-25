"""
╔══════════════════════════════════════════════════════════════╗
║  KİŞİSEL FİNANS MERKEZİ  ·  v4.0 (Pro Trader Edition)        ║
║  Sekme 1 : Borç Erime & Özgürlük Simülatörü                  ║
║  Sekme 2 : Kantitatif Piyasa Tarayıcısı + Kripto + Simülatör ║
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

/* ── Kartlar & Diğerleri (Mevcut) ── */
.kpi-card { background: #0c1220; border: 1px solid #161d2e; border-radius: 12px; padding: 1.2rem; position: relative; }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; }
.kpi-card.green::before  { background: linear-gradient(90deg,#10b981,#34d399); }
.kpi-card.amber::before  { background: linear-gradient(90deg,#f59e0b,#fbbf24); }
.kpi-card.red::before    { background: linear-gradient(90deg,#ef4444,#dc2626); }
.kpi-card.blue::before   { background: linear-gradient(90deg,#3b82f6,#60a5fa); }
.kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; font-weight: 600; color: #8899b8; text-transform: uppercase; margin-bottom: 0.5rem; }
.kpi-value { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.8rem; margin-bottom: 0.3rem; }
.kpi-value.green { color: #34d399; } .kpi-value.amber { color: #fbbf24; } .kpi-value.red { color: #f87171; } .kpi-value.blue { color: #60a5fa; }
.hero-title { font-weight: 800; font-size: 2rem; background: linear-gradient(135deg,#eff6ff 0%,#93c5fd 45%,#60a5fa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.section-hdr { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; font-weight: 700; color: #8899b8; text-transform: uppercase; border-bottom: 1px solid #111827; padding-bottom: 0.4rem; margin: 2rem 0 1rem 0; }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR & LİSTELER
# ═════════════════════════════════════════════════════════════

def fmt_val(val: float, currency: str) -> str:
    if currency == "₺": return f"₺{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${val:,.2f}"

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

# Teknik Analiz Fonksiyonları (Mevcut)
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

# Geliştirilmiş Sinyal Motoru
def generate_signal(row: dict) -> tuple[str, str, str]:
    rsi = row.get("RSI")
    hist = row.get("MACD_Hist")
    above = row.get("Above_SMA50")
    
    # Detaylı Sinyal, CSS Sınıfı, Hızlı Aksiyon (AL/SAT/TUT)
    if pd.notna(rsi) and rsi < 30 and pd.notna(hist) and hist > 0:
        return "⬆ Güçlü Al", "signal-buy", "AL"
    if pd.notna(rsi) and rsi < 35:
        return "⬆ Dipte (Oversold)", "signal-buy", "AL"
    if pd.notna(rsi) and rsi > 70 and pd.notna(hist) and hist < 0:
        return "⬇ Güçlü Sat", "signal-sell", "SAT"
    if pd.notna(rsi) and rsi > 70:
        return "⚠ Aşırı Alım", "signal-sell", "SAT"
    if pd.notna(above) and above and pd.notna(hist) and hist > 0:
        return "↗ Trendle Git", "signal-hold", "TUT"
    if pd.notna(above) and not above:
        return "↘ Zayıf Trend", "signal-watch", "TUT"
    
    return "◼ Bekle", "signal-hold", "TUT"

@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_data(asset_type: str) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=365) # 52 haftalık veri için süreyi uzattık
    rows = []
    tickers_dict = TICKERS_CRYPTO if asset_type == "Kripto (Bitcoin vb.)" else TICKERS_BIST_US

    for ticker, name in tickers_dict.items():
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 60: continue

            close = df["Close"].squeeze()
            high = df["High"].squeeze()
            low = df["Low"].squeeze()
            volume = df["Volume"].squeeze()

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
            row_data["Aksiyon"] = action # Hızlı Aksiyon Kolonu
            rows.append(row_data)
        except Exception:
            continue
    return pd.DataFrame(rows)


# ═════════════════════════════════════════════════════════════
#  SİDEBAR — SCREENER FİLTRELERİ
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Varlık & Filtreler")
    
    # YENİ: Kripto / Borsa Ayrımı
    asset_class = st.radio(
        "Piyasa Seçimi", 
        ["Hisse Senedi (Borsa)", "Kripto (Bitcoin vb.)"],
        help="Tarama yapılacak piyasayı seçin."
    )
    
    st.markdown("---")
    
    sinyal_filtre = st.multiselect(
        "Aksiyon Durumu",
        ["AL", "SAT", "TUT"],
        default=["AL", "SAT", "TUT"],
    )

    rsi_range = st.slider("RSI Aralığı", 0, 100, (0, 100))
    st.markdown("---")
    st.markdown("""<div style='font-family:"IBM Plex Mono",monospace;font-size:0.7rem; color:#8899b8; line-height:1.7;'>
    <b>RSI < 30</b> → Dip / Aşırı Satılmış<br>
    <b>RSI > 70</b> → Zirve / Aşırı Alınmış<br>
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
    st.markdown(
        '<div class="hero">'
        '<div class="hero-title market">Kantitatif Trader Terminali</div>'
        '</div>',
        unsafe_allow_html=True)

    hdr_col, btn_col = st.columns([6, 1])
    with btn_col:
        # İkonlu, belirgin yenile butonu
        if st.button("🔄 Verileri Yenile", type="primary", use_container_width=True):
            st.cache_data.clear()

    with st.spinner(f"📡 {asset_class} verileri çekiliyor ve analiz ediliyor..."):
        df_raw = fetch_market_data(asset_class)

    if df_raw.empty:
        st.error("⚠️ Veri çekilemedi. İnternet bağlantınızı kontrol edin.")
        st.stop()

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

    # ── Sinyal Motoru Tablosu ───────────────────────────────
    st.markdown('<div class="section-hdr">⚡ CANLI PİYASA VE HIZLI AKSİYON TABLOSU</div>', unsafe_allow_html=True)

    if df_f.empty:
        st.info("ℹ️ Seçili filtrelerle eşleşen varlık bulunamadı.")
    else:
        display_cols = ["Ticker", "Şirket", "Piyasa", "Fiyat", "Döviz", "Değişim %", "RSI", "MACD_Hist", "Aksiyon", "Sinyal"]
        
        def style_signal_table(df):
            s = pd.DataFrame("", index=df.index, columns=df.columns)
            for i, row in df.iterrows():
                # Renklendirmeler
                if pd.notna(row.get("RSI")):
                    s.loc[i, "RSI"] = "color:#34d399;font-weight:700" if row["RSI"] < 35 else "color:#f87171;font-weight:700" if row["RSI"] > 65 else ""
                if pd.notna(row.get("Değişim %")):
                    s.loc[i, "Değişim %"] = "color:#34d399" if row["Değişim %"] >= 0 else "color:#f87171"
                
                # Aksiyon Kolonu (AL/SAT)
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


    # ── YENİ: GELECEK SENARYOSU VE İHTİMAL HESAPLAYICI ─────────────────
    st.markdown('<div class="section-hdr">🔮 GELECEK SENARYOSU & DETAYLI ANALİZ (Tıkla ve Simüle Et)</div>', unsafe_allow_html=True)
    
    col_sel, col_amt = st.columns([2, 1])
    with col_sel:
        # Tabloya tıklamak yerine buradan hisse/coin seçiliyor (en sağlam yöntem)
        selected_ticker = st.selectbox("Analiz Edilecek Varlığı Seçin", df_raw["Ticker"].tolist())
    with col_amt:
        curr_symbol = df_raw[df_raw["Ticker"] == selected_ticker]["Döviz"].iloc[0]
        invest_amount = st.number_input(f"Simülasyon Yatırım Tutarı ({curr_symbol})", min_value=10.0, value=1000.0, step=100.0)

    if selected_ticker:
        asset_data = df_raw[df_raw["Ticker"] == selected_ticker].iloc[0]
        current_price = asset_data["Fiyat"]
        ath = asset_data["52H_Zirve"]
        atl = asset_data["52H_Dip"]
        
        # Matematiksel hesaplamalar
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
# ║  SEKME 2 — BORÇ ERİME SİMÜLATÖRÜ (Değişmedi, Mevcut Kod)     ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_debt:
    st.info("Burası mevcut borç hesaplama kodun. Sınırı aşmamak için bu sekmenin içini mevcut app.py dosyasındaki kodunla aynı bırakabilirsin.")
    # Not: Mevcut "with tab_debt:" bloğunun içindeki tüm kodunu buraya yapıştıracaksın.

"""
