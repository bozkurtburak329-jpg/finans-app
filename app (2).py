"""
╔══════════════════════════════════════════════════════════════╗
║  KİŞİSEL FİNANS MERKEZİ  ·  v5.1 (Ultra Hızlı Pro Edition)   ║
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
import concurrent.futures  # Hızlı veri çekimi için eklendi

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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; background-color: #070a10; color: #d4dbe8; }

/* ── Sekme Navigasyonu ── */
[data-testid="stTabs"] > div:first-child { border-bottom: 1px solid #161d2e !important; }
button[data-baseweb="tab"] { font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important; font-weight: 700 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; color: #3d4f6b !important; padding: 0.8rem 1.6rem !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: #34d399 !important; border-bottom-color: #34d399 !important; }

/* ── Sinyal Rozeti ── */
.signal-badge { display: inline-block; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 800; padding: 0.3rem 0.7rem; border-radius: 4px; letter-spacing: 0.05em; }
.signal-buy    { background:#052e16; color:#34d399; border:1px solid #065f46; }
.signal-sell   { background:#2d1515; color:#f87171; border:1px solid #7f1d1d; }
.signal-hold   { background:#0c1a2e; color:#60a5fa; border:1px solid #1e3a5f; }
.signal-watch  { background:#1c1408; color:#fbbf24; border:1px solid #78350f; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #0a0e18; border-right: 1px solid #111827; }
[data-testid="stSidebar"] label { font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important; font-weight: 700 !important; color: #8899b8 !important; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── KPI Kartı ── */
.kpi-card { background: #0c1220; border: 1px solid #161d2e; border-radius: 12px; padding: 1.2rem 1.4rem 1rem; position: relative; overflow: hidden; height: 100%; }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 12px 12px 0 0; }
.kpi-card.red::before    { background: linear-gradient(90deg,#ef4444,#dc2626); }
.kpi-card.green::before  { background: linear-gradient(90deg,#10b981,#34d399); }
.kpi-card.amber::before  { background: linear-gradient(90deg,#f59e0b,#fbbf24); }
.kpi-card.blue::before   { background: linear-gradient(90deg,#3b82f6,#60a5fa); }
.kpi-card.cyan::before   { background: linear-gradient(90deg,#06b6d4,#22d3ee); }
.kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; font-weight: 600; color: #8899b8; text-transform: uppercase; margin-bottom: 0.5rem; }
.kpi-value { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.8rem; line-height: 1; margin-bottom: 0.3rem; text-align: center; display: flex; justify-content: center; }
.kpi-value.red    { color: #f87171; } .kpi-value.green  { color: #34d399; } .kpi-value.amber  { color: #fbbf24; } .kpi-value.blue   { color: #60a5fa; } .kpi-value.cyan   { color: #22d3ee; }
.kpi-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.66rem; color: #3d4f6b; line-height: 1.4; }
.kpi-sub .pos { color: #34d399; } .kpi-sub .neg { color: #f87171; }

/* ── Hero Başlık & Diğerleri ── */
.hero { margin-bottom: 1.4rem; }
.hero-title { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2rem; background: linear-gradient(135deg,#f0fdf4 0%,#86efac 45%,#34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1; }
.hero-title.market { background: linear-gradient(135deg,#eff6ff 0%,#93c5fd 45%,#60a5fa 100%); -webkit-background-clip: text; }
.hero-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #2e3d55; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.25rem; }
.section-hdr { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; font-weight: 700; color: #8899b8; text-transform: uppercase; border-bottom: 1px solid #111827; padding-bottom: 0.4rem; margin: 2rem 0 1rem 0; }
.info-box { background: #080f1e; border: 1px solid #1d4ed8; border-left: 3px solid #3b82f6; border-radius: 8px; padding: 0.7rem 1rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #93c5fd; margin: 0.75rem 0; }
.warn-box { background: #120606; border: 1px solid #7f1d1d; border-left: 3px solid #ef4444; border-radius: 8px; padding: 0.7rem 1rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #fca5a5; margin: 0.75rem 0; }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR & HİSSE LİSTELERİ
# ═════════════════════════════════════════════════════════════

def fmt_val(val: float, currency: str) -> str:
    if pd.isna(val): return "Veri Yok"
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

def calculate_amortization(principal, monthly_rate, monthly_payment, monthly_inflation=0.0, extra=0.0):
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
        rows.append({"Ay": ay, "Faiz (₺)": round(interest, 2), "Anapara (₺)": round(principal_paid, 2), "Nominal Kalan (₺)": round(max(balance, 0), 2), "Reel Kalan (₺)": round(max(balance / cum_inf, 0), 2)})
    return pd.DataFrame(rows)

# Hatalı/Eski hisseler temizlendi, BIST ve US havuzu genişletildi
TICKERS_BIST = {
    "AKBNK.IS": "Akbank", "AKSEN.IS": "Aksa Enerji", "ALARK.IS": "Alarko Holding", "ARCLK.IS": "Arçelik", 
    "ASELS.IS": "Aselsan", "ASTOR.IS": "Astor Enerji", "BIMAS.IS": "BİM Mağazalar", "DOAS.IS": "Doğuş Otomotiv", 
    "EKGYO.IS": "Emlak Konut", "ENKAI.IS": "Enka İnşaat", "EREGL.IS": "Ereğli Demir Çelik", "FROTO.IS": "Ford Otosan", 
    "GARAN.IS": "Garanti BBVA", "HEKTS.IS": "Hektaş", "ISCTR.IS": "İş Bankası (C)", "KCHOL.IS": "Koç Holding", 
    "KONTR.IS": "Kontrolmatik", "KOZAL.IS": "Koza Altın", "KRDMD.IS": "Kardemir (D)", "ODAS.IS": "Odaş Elektrik", 
    "PETKM.IS": "Petkim", "PGSUS.IS": "Pegasus", "SAHOL.IS": "Sabancı Holding", "SASA.IS": "Sasa Polyester", 
    "SISE.IS": "Şişecam", "TCELL.IS": "Turkcell", "THYAO.IS": "Türk Hava Yolları", "TOASO.IS": "Tofaş", 
    "TUPRS.IS": "Tüpraş", "YKBNK.IS": "Yapı Kredi", "AEFES.IS": "Anadolu Efes", "DOHOL.IS": "Doğan Holding", 
    "MGROS.IS": "Migros", "SOKM.IS": "Şok Marketler", "TTKOM.IS": "Türk Telekom", "VAKBN.IS": "Vakıfbank"
}

TICKERS_US = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "GOOGL": "Alphabet", "AMZN": "Amazon", 
    "META": "Meta", "TSLA": "Tesla", "AMD": "AMD", "INTC": "Intel", "AVGO": "Broadcom", "NFLX": "Netflix", 
    "PYPL": "PayPal", "UBER": "Uber", "JPM": "JPMorgan", "BAC": "Bank of America", "V": "Visa", 
    "JNJ": "Johnson & Johnson", "WMT": "Walmart", "DIS": "Walt Disney", "KO": "Coca-Cola", "BA": "Boeing"
}

TICKERS_CRYPTO = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin", "SOL-USD": "Solana", 
    "XRP-USD": "Ripple", "AVAX-USD": "Avalanche", "DOGE-USD": "Dogecoin", "ADA-USD": "Cardano", 
    "MATIC-USD": "Polygon", "DOT-USD": "Polkadot", "LINK-USD": "Chainlink", "TRX-USD": "TRON"
}

def get_extended_tickers(asset_type: str) -> dict:
    if asset_type == "Kripto (Bitcoin vb.)": return TICKERS_CRYPTO
    elif asset_type == "🇺🇸 Hisse (Amerika Pazarı)": return TICKERS_US
    else: return TICKERS_BIST

def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    val = (100 - (100 / (1 + rs))).iloc[-1]
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
    rsi, hist, above = row.get("RSI"), row.get("MACD_Hist"), row.get("Above_SMA50")
    if pd.notna(rsi) and rsi < 30 and pd.notna(hist) and hist > 0: return "⬆ Güçlü Al", "signal-buy", "AL"
    if pd.notna(rsi) and rsi < 35: return "⬆ Dipte (Oversold)", "signal-buy", "AL"
    if pd.notna(rsi) and rsi > 70 and pd.notna(hist) and hist < 0: return "⬇ Güçlü Sat", "signal-sell", "SAT"
    if pd.notna(rsi) and rsi > 70: return "⚠ Aşırı Alım", "signal-sell", "SAT"
    if pd.notna(above) and above and pd.notna(hist) and hist > 0: return "↗ Trendle Git", "signal-hold", "TUT"
    if pd.notna(above) and not above: return "↘ Zayıf Trend", "signal-watch", "TUT"
    return "◼ Bekle", "signal-hold", "TUT"

def calculate_win_prob_felaket(rsi, hist, above, atr_pct, r_to_reward) -> float:
    base_p = 0.50
    if pd.isna(rsi) or pd.isna(hist) or pd.isna(atr_pct): return np.nan
    if rsi < 30: base_p += 0.15
    elif rsi < 40: base_p += 0.08
    elif rsi > 70: base_p -= 0.15
    elif rsi > 60: base_p -= 0.08
    if hist > 0: base_p += 0.05
    elif hist < 0: base_p -= 0.05
    if above: base_p += 0.10
    else: base_p -= 0.10
    if atr_pct > 5: base_p -= 0.05
    if atr_pct > 8: base_p -= 0.08
    if pd.notna(r_to_reward) and r_to_reward < 1: base_p -= 0.20
    return max(0.01, min(0.99, base_p))

# ═════════════════════════════════════════════════════════════
#  MULTI-THREADING VERİ ÇEKİMİ (Çok Hızlı)
# ═════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_data(asset_type: str, selected_ticker_full: str = None) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=365*2)
    
    tickers_dict = {selected_ticker_full: ""} if selected_ticker_full else get_extended_tickers(asset_type)
    if not tickers_dict: return pd.DataFrame()

    rows = []

    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 60: return None
            
            df_1y = df.iloc[-252:] if len(df) >= 252 else df
            close, high, low = df["Close"].squeeze(), df["High"].squeeze(), df["Low"].squeeze()
            price, prev_price = float(close.iloc[-1]), float(close.iloc[-2])
            high_52w, low_52w = float(df_1y["High"].squeeze().max()), float(df_1y["Low"].squeeze().min())
            
            atr = compute_atr(high, low, close)
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi, (macd_v, macd_sig, macd_hist) = compute_rsi(close), compute_macd(close)
            
            atr_pct = round(atr / price * 100, 2) if price else np.nan
            t1_reward_f, t2_reward_f = price + (2 * atr), price + (4 * atr)
            stop_f = price - (1.5 * atr)
            
            reward_val = (t1_reward_f + t2_reward_f) / 2
            risk_reward_ratio_f = (reward_val - price) / (price - stop_f) if (price - stop_f) != 0 else np.nan
            
            above_sma50 = price > sma50
            win_p_f = calculate_win_prob_felaket(rsi, macd_hist, above_sma50, atr_pct, risk_reward_ratio_f)
            
            kelly_f_percent = np.nan
            if pd.notna(win_p_f) and pd.notna(risk_reward_ratio_f) and risk_reward_ratio_f != 0:
                kelly_raw = win_p_f - ((1 - win_p_f) / risk_reward_ratio_f)
                kelly_f_percent = max(0.0, min(kelly_raw, 1.0))
            
            market_label = "₿ Kripto" if "USD" in ticker else ("🇹🇷 BIST" if ticker.endswith(".IS") else "🇺🇸 ABD")
            currency = "$" if "USD" in ticker or not ticker.endswith(".IS") else "₺"
            
            if not name:
                name = TICKERS_BIST.get(ticker, TICKERS_US.get(ticker, TICKERS_CRYPTO.get(ticker, ticker)))
                
            row_data = {
                "Ticker": ticker, "Şirket": name, "Piyasa": market_label, "Fiyat": price, "Döviz": currency,
                "Değişim %": (price - prev_price) / prev_price * 100, "RSI": rsi, "MACD_Hist": macd_hist, 
                "SMA-50": sma50, "Above_SMA50": above_sma50, "F/SMA": price / sma50 if sma50 else 0, "ATR %": atr_pct,
                "52H_Zirve": high_52w, "52H_Dip": low_52w, "T1_Hedef": t1_reward_f, "T2_Hedef": t2_reward_f, 
                "Stop_Seviyesi": stop_f, "Risk_Reward": risk_reward_ratio_f, "Kazanma_Olasiligi": win_p_f, 
                "Kelly_Kasa_Percent": kelly_f_percent
            }
            sig_label, sig_class, action = generate_signal(row_data)
            row_data.update({"Sinyal": sig_label, "Sinyal_Class": sig_class, "Aksiyon": action})
            return row_data
        except Exception:
            return None

    # EKSİK 2: Asenkron Veri Çekimi (Hızlandırma)
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_ticker, t, n) for t, n in tickers_dict.items()]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None: rows.append(res)

    return pd.DataFrame(rows)

# ═════════════════════════════════════════════════════════════
#  SİDEBAR — SCREENER FİLTRELERİ
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Varlık & Filtreler")
    asset_class = st.radio("Piyasa Seçimi", ["🇹🇷 Hisse (Borsa İstanbul)", "🇺🇸 Hisse (Amerika Pazarı)", "Kripto (Bitcoin vb.)"])
    st.markdown("---")
    sinyal_filtre = st.multiselect("Aksiyon Durumu", ["AL", "SAT", "TUT"], default=["AL", "SAT", "TUT"])
    rsi_range = st.slider("RSI Aralığı", 0, 100, (0, 100))
    st.markdown("---")
    st.markdown("""<div style='font-family:"IBM Plex Mono",monospace;font-size:0.7rem; color:#8899b8; line-height:1.7;'>
    <b>RSI &lt; 30</b> → Dip / Aşırı Satılmış<br><b>RSI &gt; 70</b> → Zirve / Aşırı Alınmış</div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
#  ANA SEKMELER
# ═════════════════════════════════════════════════════════════
tab_market, tab_debt = st.tabs(["📡  Piyasa Tarayıcısı & Simülatör", "💸  Borç Erime Simülatörü"])

# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 1 — MARKET SCREENER + GELECEK SİMÜLATÖRÜ              ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_market:
    st.markdown('<div class="hero"><div class="hero-title market">Kantitatif Trader Terminali (Yüzlerce Varlık)</div></div>', unsafe_allow_html=True)

    hdr_col, btn_col = st.columns([6, 1])
    with btn_col:
        if st.button("🔄 Verileri Yenile", type="primary", use_container_width=True): st.cache_data.clear()

    with st.spinner(f"📡 {asset_class} verileri asenkron çekiliyor... (Hızlandırıldı)"):
        df_raw = fetch_market_data(asset_class)

    if df_raw.empty:
        st.error("⚠️ Veri çekilemedi. İnternet bağlantınızı veya hisse listesini kontrol edin.")
    else:
        df_f = df_raw.copy()
        if sinyal_filtre: df_f = df_f[df_f["Aksiyon"].isin(sinyal_filtre)]
        df_f = df_f[(df_f["RSI"] >= rsi_range[0]) & (df_f["RSI"] <= rsi_range[1])]

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"""<div class="kpi-card blue"><div class="kpi-label">Taranan Varlık</div><div class="kpi-value blue">{len(df_f)} / {len(df_raw)}</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="kpi-card green"><div class="kpi-label">Hızlı Aksiyon: AL</div><div class="kpi-value green">{len(df_raw[df_raw["Aksiyon"] == "AL"])}</div></div>""", unsafe_allow_html=True)
        with m3: st.markdown(f"""<div class="kpi-card red"><div class="kpi-label">Hızlı Aksiyon: SAT</div><div class="kpi-value red">{len(df_raw[df_raw["Aksiyon"] == "SAT"])}</div></div>""", unsafe_allow_html=True)
        with m4:
            avg_rsi = df_raw["RSI"].mean()
            rc = "green" if avg_rsi < 40 else "amber" if avg_rsi < 65 else "red"
            st.markdown(f"""<div class="kpi-card {rc}"><div class="kpi-label">Piyasa Ort. RSI</div><div class="kpi-value {rc}">{avg_rsi:.1f}</div></div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-hdr">⚡ CANLI PİYASA VE HIZLI AKSİYON TABLOSU</div>', unsafe_allow_html=True)

        if df_f.empty: st.info("ℹ️ Seçili filtrelerle eşleşen varlık bulunamadı.")
        else:
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

            display_df = df_f[["Ticker", "Şirket", "Piyasa", "Fiyat", "Döviz", "Değişim %", "RSI", "MACD_Hist", "Aksiyon", "Sinyal"]].copy()
            styled = display_df.style.apply(style_signal_table, axis=None).format({"Değişim %": "{:+.2f}%", "Fiyat": "{:,.2f}", "RSI": "{:.1f}", "MACD_Hist": "{:+.4f}"}, na_rep="—")
            st.dataframe(styled, use_container_width=True, height=350, hide_index=True)

        # GELECEK SENARYOSU SİMÜLATÖRÜ (NaN Güvenlik Korumalı)
        st.markdown('<div class="section-hdr">🔮 GELECEK SENARYOSU VE DETAYLI FELAKET ANALİZ (Abartılmış v5.1)</div>', unsafe_allow_html=True)
        col_sel, col_amt = st.columns([2, 1])
        with col_sel:
            ticker_options = [f"{t} - {df_raw[df_raw['Ticker']==t]['Şirket'].iloc[0]}" for t in df_raw['Ticker']]
            selected_ticker_full_item = st.selectbox("Analiz Edilecek Varlığı Seçin", ticker_options)
            selected_ticker_full = selected_ticker_full_item.split(" - ")[0] if selected_ticker_full_item else None

        with col_amt:
            curr_symbol = df_raw[df_raw["Ticker"] == selected_ticker_full]["Döviz"].iloc[0] if selected_ticker_full else ""
            invest_amount = st.number_input(f"Simülasyon Yatırım Tutarı ({curr_symbol})", min_value=10.0, value=1000.0, step=100.0)

        if selected_ticker_full:
            asset_data = df_raw[df_raw["Ticker"] == selected_ticker_full].iloc[0]
            cp = asset_data["Fiyat"]
            ath, atl = asset_data["52H_Zirve"], asset_data["52H_Dip"]
            
            units = invest_amount / cp if cp else 0
            prof_ath, pct_ath = (units * ath) - invest_amount, ((ath - cp) / cp * 100) if cp else 0
            loss_atl, pct_atl = invest_amount - (units * atl), ((cp - atl) / cp * 100) if cp else 0
            
            # EKSİK 3: Güvenli String Formatlama (NaN Çökmesini Engeller)
            wp = asset_data["Kazanma_Olasiligi"]
            kp = asset_data["Kelly_Kasa_Percent"]
            rr = asset_data["Risk_Reward"]
            
            wp_str = f"%{wp*100:.1f}" if pd.notna(wp) else "Yetersiz Veri"
            kp_str = f"%{kp*100:.1f}" if pd.notna(kp) else "Yetersiz Veri"
            rr_str = f"{rr:.2f}x" if pd.notna(rr) else "Hesaplanamadı"
            max_pos_tl = fmt_val(invest_amount * kp, curr_symbol) if pd.notna(kp) else "0.00"

            st.markdown(f"""
            <div style='background:#0a0e18; border:2px solid #1e3a5f; border-radius:10px; padding:2rem; margin-top:1.5rem; border-left: 5px solid #1d4ed8;'>
                <h3 style='color:#60a5fa; margin-top:0; border-bottom: 2px solid #1e3a5f; padding-bottom: 0.5rem;'>{asset_data['Şirket']} ({selected_ticker_full}) Felaket Kuantitatif Tahmin Motoru</h3>
                <p style='font-family:"IBM Plex Mono", monospace; font-size:1.1rem; color:#8899b8; margin-top:1rem;'>Güncel Fiyat: <b style='color:#d4dbe8'>{fmt_val(cp, curr_symbol)}</b> &nbsp;·&nbsp; Alınacak Adet: <b>{units:.4f}</b></p>
                <hr style='border-color:#161d2e; margin: 1.5rem 0;'>
                <div style='display:flex; justify-content:space-between; gap: 1rem;'>
                    <div style='width:48%; background:#052e16; padding:1.5rem; border-radius:8px; border:2px solid #065f46;'>
                        <div style='color:#34d399; font-weight:bold; font-size:1.1rem;'>🚀 İyimser Senaryo (52H Zirvesi)</div>
                        Hedef: {fmt_val(ath, curr_symbol)} | Potansiyel: <b>+%{pct_ath:.1f}</b><br>
                        <div style='margin-top:1rem; font-size:1.3rem; border-top: 1px solid #065f46; padding-top: 0.5rem;'>Tahmini Kar: <b style='color:#10b981'>+{fmt_val(prof_ath, curr_symbol)}</b></div>
                    </div>
                    <div style='width:48%; background:#2d1515; padding:1.5rem; border-radius:8px; border:2px solid #7f1d1d;'>
                        <div style='color:#f87171; font-weight:bold; font-size:1.1rem;'>📉 Kötümser Senaryo (52H Dibi)</div>
                        Destek: {fmt_val(atl, curr_symbol)} | Risk: <b>-%{pct_atl:.1f}</b><br>
                        <div style='margin-top:1rem; font-size:1.3rem; border-top: 1px solid #7f1d1d; padding-top: 0.5rem;'>Tahmini Zarar: <b style='color:#ef4444'>-{fmt_val(loss_atl, curr_symbol)}</b></div>
                    </div>
                </div>
                <hr style='border-color:#161d2e; margin: 1.5rem 0;'>
                <div style='display:flex; justify-content:space-between; gap: 1rem;'>
                    <div style='width:48%; background:#0c1a2e; padding:1.5rem; border-radius:8px; border:2px solid #1e3a5f;'>
                        <div style='color:#60a5fa; font-weight:bold; font-size:1.1rem;'>Risk Analizi & Kelly Kriteri (Abartılmış)</div>
                        Kazanma Olasılığı (p): <b>{wp_str}</b> <br>Kasa Önerilen Maks. Giriş (f*): <b>{kp_str}</b> <br>
                        <div style='margin-top:1rem; font-size:1.1rem;'>Maksimum Tutar: <b>{max_pos_tl}</b></div>
                    </div>
                    <div style='width:48%; background:#2d1515; padding:1.5rem; border-radius:8px; border:2px solid #7f1d1d;'>
                        <div style='color:#fbbf24; font-weight:bold; font-size:1.1rem;'>Kuantitatif Hedef & Zarar Durdur</div>
                        T1_Hedef (Direnç): <b>{fmt_val(asset_data['T1_Hedef'], curr_symbol)}</b> <br>T2_Hedef (Direnç): <b>{fmt_val(asset_data['T2_Hedef'], curr_symbol)}</b> <br>
                        <div style='margin-top:1rem; font-size:1.1rem;'>Stop_Seviyesi: <b style='color:#f87171'>{fmt_val(asset_data['Stop_Seviyesi'], curr_symbol)}</b></div>
                    </div>
                </div>
                <div style='background:#120606; border:1px solid #7f1d1d; border-radius:6px; padding:1.2rem; margin-top:1.5rem; color:#fca5a5; font-size: 0.95rem; font-family:"IBM Plex Mono",monospace;'>
                    <b style='color:#f87171'>Risk Notu:</b> Kelly % düşükse bu varlığa girmek kasanız için <b style='color:#ef4444'>FELAKET BIR RISK</b> taşımaktadır. Risk/Ödül Oranı: <b>{rr_str}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════╗
# ║  SEKME 2 — BORÇ ERİME SİMÜLATÖRÜ                             ║
# ╚══════════════════════════════════════════════════════════════╝
with tab_debt:
    st.markdown('<div class="hero"><div class="hero-title">Borç Erime Simülatörü</div></div>', unsafe_allow_html=True)
    g1, g2, g3, g4, g5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])
    with g1: principal = st.number_input("💰 Güncel Borç (₺)", 100.0, 10_000_000.0, 29_000.0, 500.0, format="%.0f")
    with g2: monthly_rate_pct = st.number_input("📈 Aylık Faiz (%)", 0.0, 30.0, 3.5, 0.1, format="%.2f")
    with g3: monthly_payment = st.number_input("💳 Aylık Taksit (₺)", 100.0, 500_000.0, 2_500.0, 100.0, format="%.0f")
    with g4: monthly_inflation_pct = st.number_input("🌡️ Aylık Enflasyon (%)", 0.0, 20.0, 2.5, 0.1, format="%.2f")
    with g5: extra_payment = st.number_input("🚀 Ekstra Ödeme (₺)", 0.0, 100_000.0, 500.0, 100.0, format="%.0f")

    monthly_rate, monthly_inflation = monthly_rate_pct / 100, monthly_inflation_pct / 100
    df_base = calculate_amortization(principal, monthly_rate, monthly_payment, monthly_inflation, 0)
    df_extra = calculate_amortization(principal, monthly_rate, monthly_payment, monthly_inflation, extra_payment)

    if df_base is None: st.markdown(f"""<div class="warn-box">⚠️ Aylık taksit ({fmt_tl(monthly_payment)}) faiz maliyetini karşılamıyor.</div>""", unsafe_allow_html=True)
    else:
        tmb, tib = len(df_base), df_base["Faiz (₺)"].sum()
        tme, tie, sm, si = (len(df_extra), df_extra["Faiz (₺)"].sum(), tmb - len(df_extra), tib - df_extra["Faiz (₺)"].sum()) if df_extra is not None and extra_payment > 0 else (tmb, tib, 0, 0)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: st.markdown(f"""<div class="kpi-card red"><div class="kpi-label">Standart Süre</div><div class="kpi-value red">{tmb} Ay</div></div>""", unsafe_allow_html=True)
        with k2: st.markdown(f"""<div class="kpi-card amber"><div class="kpi-label">Faiz Maliyeti</div><div class="kpi-value amber">{fmt_tl(tib)}</div></div>""", unsafe_allow_html=True)
        with k3: st.markdown(f"""<div class="kpi-card green"><div class="kpi-label">Ekstra Bitiş</div><div class="kpi-value green">{tme if extra_payment > 0 else '—'} Ay</div></div>""", unsafe_allow_html=True)
        with k4: st.markdown(f"""<div class="kpi-card green"><div class="kpi-label">Faiz Tasarrufu</div><div class="kpi-value green">{fmt_tl(si)}</div></div>""", unsafe_allow_html=True)
        with k5: st.markdown(f"""<div class="kpi-card cyan"><div class="kpi-label">Yıllık Enflasyon</div><div class="kpi-value cyan">%{( (1+monthly_inflation)**12 - 1 )*100:.1f}</div></div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">📉 Borç Erime Eğrisi</div>', unsafe_allow_html=True)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_base["Ay"], y=df_base["Nominal Kalan (₺)"], name="Nominal", line=dict(color="#ef4444", width=2.5)))
        fig1.add_trace(go.Scatter(x=df_base["Ay"], y=df_base["Reel Kalan (₺)"], name="Reel", line=dict(color="#f59e0b", width=2, dash="dot")))
        if df_extra is not None and extra_payment > 0: fig1.add_trace(go.Scatter(x=df_extra["Ay"], y=df_extra["Nominal Kalan (₺)"], name=f"Ekstra (+{fmt_tl(extra_payment)})", line=dict(color="#34d399", width=2.5)))
        fig1.update_layout(**get_plotly_base(400))
        st.plotly_chart(fig1, use_container_width=True)

st.markdown("""<div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#161d2e;text-align:center;border-top:1px solid #0d1117;padding-top:1.2rem;margin-top:2.5rem;">Kişisel Finans Merkezi v5.1 &nbsp;·&nbsp; Multi-Threaded Hızlı Veri &nbsp;·&nbsp; Eğitim Amaçlıdır</div>""", unsafe_allow_html=True)
