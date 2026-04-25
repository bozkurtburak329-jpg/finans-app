"""
╔══════════════════════════════════════════════════════════════╗
║  KİŞİSEL FİNANS MERKEZİ  ·  v5.0 (Pro Trader Edition)        ║
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
#  GLOBAL STİL (Yenilenmiş, Daha Güçlü Fontlar ve Hizalamalar)
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
/* DÜZELTME: KPI Değeri Ortada */
.kpi-value { 
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.8rem; line-height: 1; margin-bottom: 0.3rem; 
    text-align: center; display: flex; justify-content: center; 
}
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

# DÜZELTME: Taranan Varlık Sayısını Arttırdım (Alabildiğine)
TICKERS_BIST = {
    # BIST30 Tamamı
    "AKBNK.IS": "Akbank", "AKSEN.IS": "Aksa Enerji", "ALARK.IS": "Alarko Holding",
    "ARCLK.IS": "Arçelik", "ASELS.IS": "Aselsan", "BIMAS.IS": "BİM Mağazalar",
    "DOAS.IS": "Doğuş Otomotiv", "EKGYO.IS": "Emlak Konut REIC", "ENKAI.IS": "Enka İnşaat",
    "EREGL.IS": "Ereğli Demir Çelik", "FROTO.IS": "Ford Otosan", "GARAN.IS": "Garanti BBVA",
    "GUBRF.IS": "Gübre Fabrikaları", "HEKTS.IS": "Hektaş", "ISCTR.IS": "İş Bankası (C)",
    "KCHOL.IS": "Koç Holding", "KONTR.IS": "Kontrolmatik Teknoloji", "KOZAL.IS": "Koza Altın İşletmeleri",
    "KRDMD.IS": "Kardemir (D)", "ODAS.IS": "Odaş Elektrik", "PETKM.IS": "Petkim",
    "PGSUS.IS": "Pegasus Hava Yolları", "SAHOL.IS": "Sabancı Holding", "SASA.IS": "Sasa Polyester",
    "SISE.IS": "Şişecam", "TCELL.IS": "Turkcell", "THYAO.IS": "Türk Hava Yolları",
    "TOASO.IS": "Tofaş Otomotiv", "TUPRS.IS": "Tüpraş", "YKBNK.IS": "Yapı Kredi Bankası",
    # Popüler Diğer
    "AEEFES.IS": "Anadolu Efes", "AGHOL.IS": "AG Anadolu Grubu Holding", "BMEKS.IS": "Bimeks (Aşırı Volatil)",
    "DOHOL.IS": "Doğan Holding", "HALKB.IS": "Halk Bankası", "MGROS.IS": "Migros Ticaret",
    "OTKAR.IS": "Otokar", "SKBNK.IS": "Şekerbank", "SOKM.IS": "Şok Marketler Ticaret",
    "TATGD.IS": "Tat Gıda Ticaret", "TKFEN.IS": "Tekfen Holding", "TSPOR.IS": "Trabzonspor Sportif",
    "TTKOM.IS": "Türk Telekom", "VAKBN.IS": "Vakıfbank", "VESTL.IS": "Vestel",
    "YATAS.IS": "Yataş",
}

TICKERS_US = {
    # Teknoloji Devleri
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "GOOG": "Alphabet (A)",
    "GOOGL": "Alphabet (C)", "AMZN": "Amazon", "META": "Meta Platforms", "TSLA": "Tesla",
    "AMD": "AMD", "INTC": "Intel", "AVGO": "Broadcom", "QCOM": "Qualcomm",
    "CSCO": "Cisco Systems", "ADBE": "Adobe", "CRM": "Salesforce", "NFLX": "Netflix",
    "PYPL": "PayPal", "SQ": "Block", "UBER": "Uber Technologies", "SNOW": "Snowflake",
    # Finans & Sağlık & Perakende
    "JPM": "JPMorgan Chase", "BAC": "Bank of America", "WFC": "Wells Fargo", "GS": "Goldman Sachs",
    "MS": "Morgan Stanley", "V": "Visa", "MA": "Mastercard", "AXP": "American Express",
    "JNJ": "Johnson & Johnson", "PFE": "Pfizer", "ABBV": "AbbVie", "MRK": "Merck",
    "WMT": "Walmart", "HD": "Home Depot", "LOW": "Lowe's", "COST": "Costco",
    "DIS": "Walt Disney", "PEP": "PepsiCo", "KO": "Coca-Cola", "NKE": "Nike",
    "SBUX": "Starbucks", "MCD": "McDonald's", "BA": "Boeing", "XOM": "Exxon Mobil",
    "CVX": "Chevron", "ORCL": "Oracle", "IBM": "IBM", "TXN": "Texas Instruments",
    "MU": "Micron Technology", "ABT": "Abbott Laboratories", "ELV": "Elevance Health",
    "LLY": "Eli Lilly", "CVS": "CVS Health", "UNH": "UnitedHealth Group",
    "HD": "Home Depot", "LOW": "Lowe's", "HON": "Honeywell", "CAT": "Caterpillar",
    "DE": "Deere & Company", "LMT": "Lockheed Martin", "RTX": "RTX Corporation",
    "GE": "GE Aerospace", "MMM": "3M", "T": "AT&T", "VZ": "Verizon Communications",
}

TICKERS_CRYPTO = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin",
    "SOL-USD": "Solana", "XRP-USD": "Ripple", "AVAX-USD": "Avalanche",
    "DOGE-USD": "Dogecoin", "ADA-USD": "Cardano", "LINK-USD": "Chainlink",
    "MATIC-USD": "Polygon", "DOT-USD": "Polkadot", "XLM-USD": "Stellar",
    "LTC-USD": "Litecoin", "BCH-USD": "Bitcoin Cash", "SHIB-USD": "Shiba Inu",
    "UNI-USD": "Uniswap", "LINK-USD": "Chainlink", "TRX-USD": "TRON",
    "ATOM-USD": "Cosmos", "XMR-USD": "Monero", "ETC-USD": "Ethereum Classic",
    "FIL-USD": "Filecoin", "APT-USD": "Aptos", "NEAR-USD": "NEAR Protocol",
}

# Birleşik Liste
def get_extended_tickers(asset_type: str) -> dict:
    if asset_type == "Kripto (Bitcoin vb.)":
        return TICKERS_CRYPTO
    
    combined_tickers = {}
    if asset_type in ["Tümü", "🇹🇷 Hisse (Borsa İstanbul)"]:
        combined_tickers.update(TICKERS_BIST)
    if asset_type in ["Tümü", "🇺🇸 Hisse (Amerika Pazarı)"]:
        combined_tickers.update(TICKERS_US)
    
    if asset_type == "Tümü":
        return combined_tickers # Bu durum şu an filtrelemede yok ama fonksiyonel
    elif not combined_tickers: # asset_type spesifik hisse seçimi ise, o hisseyi barındıran listeyi bulmaya çalış
        # Bu kısım selected_ticker için `fetch_market_data`'da kullanılıyor
        #selected_ticker, selected_name = asset_type.split(" - ")
        if asset_type in TICKERS_BIST: return {asset_type: TICKERS_BIST[asset_type]}
        if asset_type in TICKERS_US: return {asset_type: TICKERS_US[asset_type]}
        if asset_type in TICKERS_CRYPTO: return {asset_type: TICKERS_CRYPTO[asset_type]}

    return combined_tickers


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

# DÜZELTME: Kelly Olasılık Hesabı (Abartılmış ve Felaket Odaklı)
def calculate_win_prob_felaket(rsi, hist, above, atr_pct, r_to_reward) -> float:
    """
    Abartılmış ve Felaket analiz için kazanma olasılığı hesabı. Kelly için p.
    RSI, MACD, Trend ve Volatiliteyi kullanarak olasılık belirler.
    Asimetrik risk-off odaklı felaket analiz (kazanma olasılığı düşükse Kelly girmeyi engeller).
    """
    base_p = 0.50 # Temel olasılık (%50 - Nötr)
    
    # RSI Etkisi (Aşırı satılmışsa p artar, aşırı alınmışsa p azalır)
    if rsi < 30: base_p += 0.15 # Al ihtimali artar (%65)
    elif rsi < 40: base_p += 0.08
    elif rsi > 70: base_p -= 0.15 # Sat ihtimali artar (Al olasılığı %35)
    elif rsi > 60: base_p -= 0.08

    # MACD Hist Etkisi (Artış varsa p artar)
    if hist > 0: base_p += 0.05
    elif hist < 0: base_p -= 0.05

    # Trend Etkisi (Above SMA50)
    if above: base_p += 0.10
    else: base_p -= 0.10

    # Volatilite Etkisi (Felaket Analiz: Volatilite yüksekse kazanç olasılığını azalt)
    if atr_pct > 5: base_p -= 0.05 # Yüksek volatilite = Yüksek risk, p azalır
    if atr_pct > 8: base_p -= 0.08 # Felaket volatilite = Felaket risk, p daha çok azalır

    # Risk/Ödül Oranı Etkisi (Felaket Analiz: Risk, Ödülden büyükse girmeyi engelle)
    if r_to_reward < 1: base_p -= 0.20 # Felaket Risk: Olasılığı %20 düşür

    # Olasılık Sınırları (0.01 - 0.99)
    return max(0.01, min(0.99, base_p))

@st.cache_data(ttl=900, show_spinner=False)
def fetch_market_data(asset_type: str, selected_ticker_full: str = None) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=365*2) # Simülasyon için 2 yıllık veri
    rows = []
    
    # asset_type filtre ise extended, selected_ticker ise tekli çekim
    tickers_dict = {}
    if selected_ticker_full:
        tickers_dict = {selected_ticker_full: ""} # Sadece seçilen hisseyi çek
    else:
        tickers_dict = get_extended_tickers(asset_type)

    if not tickers_dict: return pd.DataFrame(rows)

    for ticker, name in tickers_dict.items():
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 120: continue # Simülasyon için yeterli veri olmalı

            close = df["Close"].squeeze()
            high = df["High"].squeeze()
            low = df["Low"].squeeze()
            volume = df["Volume"].squeeze()

            # Son 1 yıllık (52 hafta) verileri kullan
            df_1y = df.iloc[-252:] if len(df) >= 252 else df
            close_1y = df_1y["Close"].squeeze()
            high_1y = df_1y["High"].squeeze()
            low_1y = df_1y["Low"].squeeze()

            price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            chg_pct = (price - prev_price) / prev_price * 100
            high_52w = float(high_1y.max())
            low_52w = float(low_1y.min())

            # Simülasyon için Volatilite Hesabı
            atr = compute_atr(high, low, close)
            atr_pct = round(atr / price * 100, 2) if price else np.nan

            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            macd_v, macd_sig, macd_hist = compute_macd(close)
            atr_sim = compute_atr(high, low, close) # Simülasyon için aynı ATR, her iki taraf için
            
            # Kuantitatif Hedefler ve Felaket Analiz (v5.0 Abartılmış Kısım)
            # Volatilite Bazlı Hedefler
            t1_reward_f = price + (2 * atr) # T1 (Hızlı Kar Al) Hedef
            t2_reward_f = price + (4 * atr) # T2 (Maksimum Beklenti) Hedef
            # Volatilite Bazlı Felaket Stop (Abartılmış)
            stop_f = price - (1.5 * atr) # Kuantitatif Stop
            
            # Risk/Ödül Hesabı (Stop ile Kar Al arası oran)
            reward_val = (t1_reward_f + t2_reward_f) / 2 # Ortalama Kar Al (Abartılmış)
            risk_reward_ratio_f = (reward_val - price) / (price - stop_f) if (price - stop_f) != 0 else np.nan

            # Kazanma Olasılığı (Abartılmış p)
            above_sma50 = price > sma50
            win_p_f = calculate_win_prob_felaket(rsi, macd_hist, above_sma50, atr_pct, risk_reward_ratio_f)

            # Kelly Kriteri Tabanlı Pozisyon (Abartılmış Pozisyonlama)
            # Kasa % hesabı (risk_reward_ratio_f = f* = p - q/b)
            kelly_f_percent = win_p_f - ( (1-win_p_f) / risk_reward_ratio_f ) if pd.notna(risk_reward_ratio_f) and risk_reward_ratio_f != 0 else np.nan
            kelly_f_percent = max(0, min(kelly_f_percent, 1.0)) if pd.notna(kelly_f_percent) else np.nan # Kelly oranı (0 - 1)

            market_label = ""
            currency = ""
            if "USD" in ticker:
                market_label = "₿ Kripto"
                currency = "$"
            else:
                market_label = "🇹🇷 BIST" if ticker.endswith(".IS") else "🇺🇸 ABD"
                currency = "₺" if ticker.endswith(".IS") else "$"

            # Şirket adı boşsa tickers'dan al, fetch_market_data(selected_ticker_full) için boş kalmasın
            if selected_ticker_full and not name:
                if selected_ticker_full in TICKERS_BIST: name = TICKERS_BIST[selected_ticker_full]
                elif selected_ticker_full in TICKERS_US: name = TICKERS_US[selected_ticker_full]
                elif selected_ticker_full in TICKERS_CRYPTO: name = TICKERS_CRYPTO[selected_ticker_full]
                if not name: name = selected_ticker_full # Hiç bulunamazsa ticker ismini koy

            row_data = {
                "Ticker": ticker, "Şirket": name, "Piyasa": market_label, "Fiyat": price, "Döviz": currency,
                "Değişim %": chg_pct, "RSI": rsi, "MACD_Hist": macd_hist, "SMA-50": sma50,
                "Above_SMA50": above_sma50, "F/SMA": price / sma50 if sma50 else 0, "ATR %": atr_pct,
                "52H_Zirve": high_52w, "52H_Dip": low_52w,
                # Kuantitatif Felaket Analiz Metrikleri
                "T1_Hedef": t1_reward_f, "T2_Hedef": t2_reward_f, "Stop_Seviyesi": stop_f,
                "Risk_Reward": risk_reward_ratio_f, "Kazanma_Olasiligi": win_p_f, "Kelly_Kasa_Percent": kelly_f_percent
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
    
    # DÜZELTME: Piyasa Bayrakları Sidebar'da
    asset_class = st.radio(
        "Piyasa Seçimi", 
        ["🇹🇷 Hisse (Borsa İstanbul)", "🇺🇸 Hisse (Amerika Pazarı)", "Kripto (Bitcoin vb.)"],
        help="Tarama yapılacak piyasayı seçin."
    )
    
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
    st.markdown('<div class="hero"><div class="hero-title market">Kantitatif Trader Terminali (Yüzlerce Varlık)</div></div>', unsafe_allow_html=True)

    hdr_col, btn_col = st.columns([6, 1])
    with btn_col:
        # DÜZELTME: Verileri Yenile İkonu
        if st.button("🔄 Verileri Yenile", type="primary", use_container_width=True):
            st.cache_data.clear()

    with st.spinner(f"📡 {asset_class} verileri çekiliyor ve analiz ediliyor... (Uzun Sürebilir)"):
        df_raw = fetch_market_data(asset_class)

    if df_raw.empty:
        st.error("⚠️ Veri çekilemedi. İnternet bağlantınızı kontrol edin veya varlık listesini kontrol edin.")
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
            # DÜZELTME: KPI Değeri Ortada (CSS ile sağlandı)
            st.markdown(f"""<div class="kpi-card {rc}">
            <div class="kpi-label">Piyasa Ort. RSI</div>
            <div class="kpi-value {rc}">{avg_rsi:.1f}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

        # Sinyal Motoru Tablosu
        st.markdown('<div class="section-hdr">⚡ CANLI PİYASA VE HIZLI AKSİYON TABLOSU (Felaket-v5.0 Analiz)</div>', unsafe_allow_html=True)

        if df_f.empty:
            st.info("ℹ️ Seçili filtrelerle eşleşen varlık bulunamadı.")
        else:
            display_cols = ["Ticker", "Şirket", "Piyasa", "Fiyat", "Döviz", "Değişim %", "RSI", "MACD_Hist", "Aksiyon", "Sinyal"]
            
            def style_signal_table(df):
                s = pd.DataFrame("", index=df.index, columns=df.columns)
                for i, row in df.iterrows():
                    # DÜZELTME: Piyasa Bayrakları Tablo'da (fetch_market_data'da market_label'da sağlandı)
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
        # DÜZELTME: Felaket Derecede Abartılmış Simülatif Analiz v5.0
        st.markdown('<div class="section-hdr">🔮 GELECEK SENARYOSU VE DETAYLI FELAKET ANALİZ (Abartılmış v5.0)</div>', unsafe_allow_html=True)
        col_sel, col_amt = st.columns([2, 1])
        with col_sel:
            # Analiz Edilecek Varlık Listesi Arttırıldı (Tarananların Tümü)
            ticker_options = [f"{ticker} - {df_raw[df_raw['Ticker'] == ticker]['Şirket'].iloc[0]}" for ticker in df_raw['Ticker']]
            selected_ticker_full_item = st.selectbox("Analiz Edilecek Varlığı Seçin (Abartılmış v5.0)", ticker_options)
            selected_ticker_full = selected_ticker_full_item.split(" - ")[0] if selected_ticker_full_item else None

        with col_amt:
            curr_symbol = df_raw[df_raw["Ticker"] == selected_ticker_full]["Döviz"].iloc[0] if selected_ticker_full else ""
            invest_amount = st.number_input(f"Simülasyon Yatırım Tutarı ({curr_symbol})", min_value=10.0, value=1000.0, step=100.0)

        if selected_ticker_full:
            asset_data = df_raw[df_raw["Ticker"] == selected_ticker_full].iloc[0]
            current_price = asset_data["Fiyat"]
            ath_52w = asset_data["52H_Zirve"]
            atl_52w = asset_data["52H_Dip"]
            
            # Kuantitatif Felaket Analiz Metrikleri (Abartılmış Kısım)
            t1_hedef = asset_data["T1_Hedef"]
            t2_hedef = asset_data["T2_Hedef"]
            stop_seviyesi = asset_data["Stop_Seviyesi"]
            risk_reward = asset_data["Risk_Reward"]
            win_p = asset_data["Kazanma_Olasiligi"]
            kelly_kasasi = asset_data["Kelly_Kasa_Percent"]
            atr_pct_val = asset_data["ATR %"]

            units_bought = invest_amount / current_price
            
            # Simüle Yatırım Karlılığı (ATH/ATL Bazlı)
            profit_ath = (units_bought * ath_52w) - invest_amount
            pct_ath = (ath_52w - current_price) / current_price * 100
            loss_atl = invest_amount - (units_bought * atl_52w)
            pct_atl = (current_price - atl_52w) / current_price * 100
            
            # Kelly Kriteri Tabanlı Maksimum Pozisyon (Risk Analizi)
            # Kelly Olasılığı Abartılmış (Felaket Analizine Göre Ayarlandı)
            max_pos_kasas_tl = invest_amount * kelly_kasasi if pd.notna(kelly_kasasi) else 0 # Kelly oranıyla kasa hesabına göre yatırılması gereken tutar

            # Volatilite Bazlı Felaket Analiz Metrikleri (TrailStopmantığı)
            # Stop ve Hedeflerin Volatiliteye (ATR) Göre Kuantitatif Tahmini
            
            st.markdown(f"""
            <div style='background:#0a0e18; border:2px solid #1e3a5f; border-radius:10px; padding:2rem; margin-top:1.5rem; border-left: 5px solid #1d4ed8; font-family:"Syne", sans-serif;'>
                <h3 style='color:#60a5fa; margin-top:0; border-bottom: 2px solid #1e3a5f; padding-bottom: 0.5rem;'>{asset_data['Şirket']} ({selected_ticker_full}) Felaket Kuantitatif Tahmin Motoru & Risk/Ödül Analizi v5.0 (Abartılmış)</h3>
                
                <p style='font-family:"IBM Plex Mono", monospace; font-size:1.1rem; color:#8899b8; margin-top:1rem;'>
                    Güncel Fiyat: <b style='color:#d4dbe8'>{fmt_val(current_price, curr_symbol)}</b> &nbsp;·&nbsp;
                    Yatırılacak Tutar: <b style='color:#34d399'>{fmt_val(invest_amount, curr_symbol)}</b><br>
                    Alınacak Adet: <b>{units_bought:.4f}</b>
                </p>
                <hr style='border-color:#161d2e; margin: 1.5rem 0;'>
                
                <div style='display:flex; justify-content:space-between; gap: 1rem;'>
                    <div style='width:48%; background:#052e16; padding:1.5rem; border-radius:8px; border:2px solid #065f46;'>
                        <div style='color:#34d399; font-weight:bold; margin-bottom:0.75rem; font-size:1.1rem;'>🚀 İyimser Senaryo (52H Zirvesi Tabanlı)</div>
                        Hedef Fiyat: {fmt_val(ath_52w, curr_symbol)} <br>
                        Yükseliş İhtimali Potansiyeli: <b>+%{pct_ath:.1f}</b> <br>
                        <div style='margin-top:1rem; font-size:1.3rem; border-top: 1px solid #065f46; padding-top: 0.5rem;'>Tahmini Kar: <b style='color:#10b981'>+{fmt_val(profit_ath, curr_symbol)}</b></div>
                    </div>
                    <div style='width:48%; background:#2d1515; padding:1.5rem; border-radius:8px; border:2px solid #7f1d1d;'>
                        <div style='color:#f87171; font-weight:bold; margin-bottom:0.75rem; font-size:1.1rem;'>📉 Kötümser Senaryo (52H Dibi Tabanlı)</div>
                        Destek Fiyatı: {fmt_val(atl_52w, curr_symbol)} <br>
                        Düşüş Riski: <b>-%{pct_atl:.1f}</b> <br>
                        <div style='margin-top:1rem; font-size:1.3rem; border-top: 1px solid #7f1d1d; padding-top: 0.5rem;'>Tahmini Zarar: <b style='color:#ef4444'>-{fmt_val(loss_atl, curr_symbol)}</b></div>
                    </div>
                </div>

                <hr style='border-color:#161d2e; margin: 1.5rem 0;'>
                
                <h4 style='color:#93c5fd; font-family:"Syne", sans-serif; margin-bottom:1rem;'>Felaket Risk Kontrolü & Kelly Tabanlı Maksimum Pozisyon (v5.0 Abartılmış Kısım)</h4>
                <div style='display:flex; justify-content:space-between; gap: 1rem;'>
                    <div style='width:48%; background:#0c1a2e; padding:1.5rem; border-radius:8px; border:2px solid #1e3a5f;'>
                        <div style='color:#60a5fa; font-weight:bold; margin-bottom:0.75rem; font-size:1.1rem;'>Risk Analizi & Kelly Kriteri Tabanlı Pozisyonlama</div>
                        Kasa Büyüklüğü % Hesabı (risk_reward_ratio_f = f* = p - q/b)<br>
                        Abartılmış Kazanma Olasılığı (p): <b>%{win_p*100:.1f}</b> <br>
                        Kasa % Olarak Önerilen Maksimum Giriş (f*): <b>%{kelly_kasasi*100:.1f}</b> <br>
                        <div style='margin-top:1rem; font-size:1.1rem;'>Önerilen Maksimum Tutar (TL Bazlı): <b>{fmt_val(max_pos_kasas_tl, curr_symbol)}</b></div>
                    </div>
                    <div style='width:48%; background:#2d1515; padding:1.5rem; border-radius:8px; border:2px solid #7f1d1d;'>
                        <div style='color:#fbbf24; font-weight:bold; margin-bottom:0.75rem; font-size:1.1rem;'>Kuantitatif Hedef Fiyatlar & Zarar Durdur (v5.0 Felaket Analiz)</div>
                        Volatilite Bazlı Hedefler (Current + n*ATR)<br>
                        T1_Hedef (Hızlı Kar Al - Kuantitatif Direnç): <b>{fmt_val(t1_hedef, curr_symbol)}</b> <br>
                        T2_Hedef (Maksimum Beklenti - Kuantitatif Direnç): <b>{fmt_val(t2_hedef, curr_symbol)}</b> <br>
                        <div style='margin-top:1rem; font-size:1.1rem;'>Kuantitatif Stop_Seviyesi (Kuantitatif Destek): <b style='color:#f87171'>{fmt_val(stop_seviyesi, curr_symbol)}</b></div>
                    </div>
                </div>

                <div style='background:#120606; border:1px solid #7f1d1d; border-radius:6px; padding:1.2rem; margin-top:1.5rem; color:#fca5a5; font-size: 0.95rem; font-family:"IBM Plex Mono",monospace;'>
                    <b style='color:#f87171'>Risk Notu (Abartılmış Felaket Analizi):</b><br>
                    Kelly Kasa %'si düşükse veya negatifse, kazanma olasılığı risk/ödül oranına göre yetersiz demektir. Bu durumda felaket analiz motoru bu varlığa girmeyi kesinlikle önermez (risk-off durumu).
                    Zarar Durdur (Kuantitatif Stop) ATR bazlı hesaplanmıştır; fiyatın volatilite alanının dışına çıktığı noktayı stop seviyesi olarak felaket bir analiz yöntemiyle belirler.
                    Risk/Ödül Oranı (Abartılmış Hedefler/Stop): <b>{risk_reward:.2f}x</b> <br>
                    %{kelly_kasasi*100:.1f} Kelly oranın negatifse, bu varlığa girmek kasanız için <b style='color:#ef4444'>FELAKET BIR RISK</b> taşımaktadır.
                    Kazanma Olasılığı Abartılmış (Felaket Analiz v5.0) durumuna göre %{win_p*100:.1f}'dır; olasılık düşükse felaket analizine göre girmeyin.
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
Kişisel Finans Merkezi v5.0 &nbsp;·&nbsp; Kuantitatif Felaket Analiz Motoru &nbsp;·&nbsp; Eğitim & Planlama Amaçlıdır &nbsp;·&nbsp; Finansal tavsiye değildir
</div>""", unsafe_allow_html=True)
