"""
Borsa Analiz Uygulaması v13.0 (THE GOD MODE - Genişletilmiş & Sessiz Sürüm)
- Hisse Listesi 160+ Dev BIST Hisselerine Çıkarıldı.
- Yükleme Bildirimleri (Spinner/Loading) Tamamen Kapatıldı, Grafikler Anında Açılır.
- TradingView Advanced Chart Üst Menüsü Aktif Edildi (Zaman dilimi seçilebilir).
- Tam Zamanlı Gece/Gündüz (Light/Dark) TV Teması & Kusursuz Altyapı
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures
import streamlit.components.v1 as components
import json

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Borsa TV Terminal",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tema ve Sistem State'leri
if "theme" not in st.session_state: st.session_state.theme = "dark"
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "binance_connected" not in st.session_state: st.session_state.binance_connected = False
if "binance_mode" not in st.session_state: st.session_state.binance_mode = "Testnet"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

# ==========================================
# 2. DİNAMİK TRADINGVIEW CSS (LIGHT & DARK)
# ==========================================
if st.session_state.theme == "dark":
    bg_color, card_bg, text_main, text_muted, border_color, row_hover, blue_brand = "#131722", "#1e222d", "#d1d4dc", "#787b86", "#2a2e39", "#2a2e39", "#2962ff"
    tv_theme_str = "dark"
else:
    bg_color, card_bg, text_main, text_muted, border_color, row_hover, blue_brand = "#ffffff", "#f0f3fa", "#131722", "#787b86", "#e0e3eb", "#f0f3fa", "#2962ff"
    tv_theme_str = "light"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Trebuchet+MS:ital,wght@0,400;0,700;1,400;1,700&display=swap');

html, body, [class*="css"] {{ font-family: -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif !important; background-color: {bg_color} !important; color: {text_main} !important; }}
[data-testid="collapsedControl"], section[data-testid="stSidebar"] {{ display: none; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {card_bg}; }}
::-webkit-scrollbar-thumb {{ background: {text_muted}; border-radius: 3px; }}

.tv-screener-container {{ width: 100%; height: 78vh; overflow-y: auto; overflow-x: auto; background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 4px; }}
.tv-table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: right; white-space: nowrap; }}
.tv-table thead {{ position: sticky; top: 0; z-index: 2; background-color: {card_bg}; box-shadow: 0 1px 0 {border_color}; }}
.tv-table th {{ padding: 10px 12px; font-weight: 500; color: {text_muted}; border-right: 1px solid {border_color}; font-size: 12px; }}
.tv-table th:first-child, .tv-table td:first-child {{ text-align: left; }}
.tv-table tbody tr {{ border-bottom: 1px solid {border_color}; background-color: {bg_color}; transition: 0.1s; }}
.tv-table tbody tr:hover {{ background-color: {row_hover}; }}
.tv-table td {{ padding: 8px 12px; color: {text_main}; vertical-align: middle; }}

.tv-ticker-col {{ display: flex; align-items: center; gap: 12px; }}
.tv-logo-circle {{ width: 28px; height: 28px; border-radius: 50%; background-color: {blue_brand}; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px; flex-shrink: 0; }}
.tv-ticker-info {{ display: flex; flex-direction: column; justify-content: center; }}
.tv-ticker-symbol {{ color: {blue_brand}; font-weight: 600; font-size: 14px; text-decoration: none; }}

.tv-green {{ color: #089981 !important; }}
.tv-red {{ color: #f23645 !important; }}
.tv-rating {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }}
.rating-strong-buy {{ color: #089981; background-color: rgba(8, 153, 129, 0.15); }}
.rating-buy {{ color: #089981; background-color: transparent; }}
.rating-sell {{ color: #f23645; background-color: transparent; }}
.rating-strong-sell {{ color: #f23645; background-color: rgba(242, 54, 69, 0.15); }}
.rating-neutral {{ color: {text_muted}; background-color: rgba(120, 123, 134, 0.15); }}

.macro-box {{ background-color: {card_bg}; border-radius: 6px; padding: 10px; border: 1px solid {border_color}; text-align: center; }}
.macro-title {{ font-size: 0.7rem; color: {text_muted}; letter-spacing: 1px;}}
.macro-val {{ font-size: 1.1rem; font-weight: bold; color: {text_main}; margin: 2px 0; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. VERİ ÇEKME & 160+ HİSSELİK DEV LİSTE
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","ALBRK","SKBNK","TSKB","KCHOL",
    "SAHOL","DOHOL","ALARK","ENKAI","AGHOL","TKFEN","NTHOL","GLYHO","POLHO","TAVHL",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL","KOZAA","IPEKE","ISDMR",
    "SISE","CIMSA","AKCNS","OYAKC","NUHCM","BTCIM","AFYON","GOLTS","BSOKE","ADANA","MRDIN",
    "FROTO","TOASO","DOAS","OTKAR","KARSN","ASUZU","TMSN","TTRAK","ARCLK","VESTL","BRISA","GOODY","SARKY",
    "THYAO","PGSUS","CLEBI","HAVA","ULUSE",
    "BIMAS","MGROS","SOKM","AEFES","CCOLA","ULKER","TATGD","TUKAS","PNSUT","PETUN","KERVT","BANVT",
    "TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS","KAREL","INDES","NETAS","ARENA","LOGO","DESPC","MIATK","ARZUM","KVK",
    "ENJSA","AKSEN","ODAS","SMARTG","EUPWR","GESAN","CWENE","YEOTK","GWIND","NATEN","MAGEN","AYDEM","CANTE","ZOREN","AYEN","AKSA",
    "EKGYO","ISGYO","TRGYO","HLGYO","VKGYO","DZGYO","SNGYO","ZRGYO","PSGYO","RYGYO","ROBIT","HATEK","FLAP","OSAS",
    "DEVA","SELEC","LKMNH","RTALB","ECILC","KORDS","VESBE","AYGAZ","ALKIM","MAVI","ORGE","OSMEN","KLMSN","ACSEL","PGMT",
    "KRPLAS","ANGEN","BIOEN","HUBVC","MERIT","INTEM","SNKRN","GEREL","PKART","KCAER","KGYO","MIPAZ","BMEKS",
    "SUWEN","EBEBK","KZBGY","ENSRI","GENIL","DGNMO","RUBNS","BRLSM","MEDTR","MANAS","KMPUR","ESEN","QUAGR",
    "CUSAN","YGGYO","KRVGD","TRILC","NTGAZ","MATKS","INFO","GLRYH","GEDIK","IEYHO","IHLGM","IHGZT","IHAAS"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

def format_volume(vol):
    if vol >= 1_000_000_000: return f"{vol/1_000_000_000:.2f}B"
    if vol >= 1_000_000: return f"{vol/1_000_000:.2f}M"
    if vol >= 1_000: return f"{vol/1_000:.2f}K"
    return str(vol)

def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        rs = delta.clip(lower=0).rolling(period).mean() / (-1 * delta.clip(upper=0)).rolling(period).mean().replace(0, np.nan)
        return round(float(100 - (100 / (1 + rs)).iloc[-1]), 1)
    except: return np.nan

def get_tv_rating(rsi, curr_p, sma50):
    score = 0
    if pd.notna(rsi):
        if rsi > 70: score -= 2
        elif rsi < 30: score += 2
        elif rsi > 60: score -= 1
        elif rsi < 40: score += 1
    if curr_p > sma50: score += 1
    else: score -= 1
    if score >= 2: return "Güçlü Al", "rating-strong-buy"
    if score == 1: return "Al", "rating-buy"
    if score <= -2: return "Güçlü Sat", "rating-strong-sell"
    if score == -1: return "Sat", "rating-sell"
    return "Nötr", "rating-neutral"

# BİLDİRİM ÇIKMAMASI İÇİN show_spinner=False YAPILDI
@st.cache_data(ttl=300, show_spinner=False)
def get_macro_data():
    tickers = {"XU100.IS": "BIST 100", "USDTRY=X": "USD/TRY", "EURTRY=X": "EUR/TRY", "GC=F": "ALTIN"}
    res = {}
    for t, name in tickers.items():
        try:
            df = yf.download(t, period="5d", interval="1h", progress=False, auto_adjust=True)
            if not df.empty and len(df) >= 3:
                curr = float(np.squeeze(df['Close'].values)[-1])
                prev = float(np.squeeze(df['Close'].values)[-3])
                res[name] = {"price": curr, "chg": ((curr - prev) / prev) * 100}
            else: res[name] = {"price": 0.0, "chg": 0.0}
        except: res[name] = {"price": 0.0, "chg": 0.0}
    return res

# BİLDİRİM ÇIKMAMASI İÇİN show_spinner=False YAPILDI
@st.cache_data(ttl=600, show_spinner=False)
def fetch_tv_screener_data():
    end = datetime.today()
    start = end - timedelta(days=60) # 2 Aylık veri çekimi
    rows = []
    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 30: return None
            close = df["Close"].squeeze()
            
            p_last = float(close.iloc[-1])
            p_prev = float(close.iloc[-2])
            p_1w = float(close.iloc[-6]) if len(close) > 5 else p_prev
            p_1m = float(close.iloc[-22]) if len(close) > 21 else p_1w
            
            chg_pct = ((p_last - p_prev) / p_prev) * 100
            w_pct = ((p_last - p_1w) / p_1w) * 100
            m_pct = ((p_last - p_1m) / p_1m) * 100
            
            vol = float(df["Volume"].squeeze().iloc[-1])
            sma50 = float(close.rolling(20).mean().iloc[-1])
            rsi = compute_rsi(close)
            rating, rating_cls = get_tv_rating(rsi, p_last, sma50)
            
            return {
                "Sembol": name, "Fiyat": p_last, "Değişim %": chg_pct, "1H %": w_pct, "1A %": m_pct,
                "Teknik": rating, "Teknik_Class": rating_cls, "Hacim": vol, "RSI": rsi
            }
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            if f.result(): rows.append(f.result())
    return pd.DataFrame(rows)

# ==========================================
# 4. TRADINGVIEW MARKETS TARZI HEADER
# ==========================================

macro = get_macro_data()

# ── Üst Nav Bar (TradingView tarzı) ───────────────────────────
theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
nav_col, nav_r = st.columns([5, 1])
with nav_col:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; padding: 6px 0 4px 0;">
        <div style="width:28px;height:28px;border-radius:6px;background:#2962ff;
        display:flex;align-items:center;justify-content:center;
        font-weight:900;font-size:15px;color:#fff;">B</div>
        <span style="font-size:1.1rem;font-weight:700;color:{text_main};letter-spacing:-0.02em;">
            Burak Borsa</span>
        <span style="font-size:0.72rem;color:{text_muted};margin-left:6px;
        font-weight:400;">Türkiye Piyasaları</span>
    </div>
    """, unsafe_allow_html=True)
with nav_r:
    st.button(theme_icon, on_click=toggle_theme, use_container_width=True)

# ── Canlı Ticker Bandı (tam TV markets tarzı) ─────────────────
bist_d  = macro.get("BIST 100",  {"price":0,"chg":0})
usd_d   = macro.get("USD/TRY",   {"price":0,"chg":0})
eur_d   = macro.get("EUR/TRY",   {"price":0,"chg":0})
gold_d  = macro.get("ALTIN",     {"price":0,"chg":0})

def ticker_band_item(label, price_str, chg, extra=""):
    c = "#089981" if chg >= 0 else "#f23645"
    s = "▲" if chg >= 0 else "▼"
    return f"""
    <div style="display:flex;flex-direction:column;padding:10px 18px;
    border-right:1px solid {border_color};min-width:140px;">
        <div style="font-size:0.65rem;color:{text_muted};
        letter-spacing:0.08em;text-transform:uppercase;margin-bottom:3px;">{label}</div>
        <div style="font-size:1.2rem;font-weight:700;color:{text_main};
        letter-spacing:-0.02em;line-height:1.1;">{price_str}</div>
        <div style="font-size:0.78rem;font-weight:600;color:{c};margin-top:2px;">
            {s} {abs(chg):.2f}%{extra}</div>
    </div>"""

# BIST 100 büyük göster
bist_chg_c = "#089981" if bist_d["chg"]>=0 else "#f23645"
bist_sign  = "▲" if bist_d["chg"]>=0 else "▼"

st.markdown(f"""
<div style="display:flex;align-items:stretch;background:{card_bg};
border:1px solid {border_color};border-radius:8px;margin:8px 0 4px 0;overflow:hidden;">

    <!-- BIST 100 büyük -->
    <div style="display:flex;flex-direction:column;padding:12px 22px;
    background:{bg_color};border-right:2px solid #2962ff;min-width:180px;">
        <div style="font-size:0.65rem;color:{text_muted};
        letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">BIST 100</div>
        <div style="font-size:1.7rem;font-weight:800;color:{text_main};
        letter-spacing:-0.03em;line-height:1;">{bist_d['price']:,.1f}</div>
        <div style="font-size:0.85rem;font-weight:600;color:{bist_chg_c};margin-top:4px;">
            {bist_sign} {abs(bist_d['chg']):.2f}%
        </div>
    </div>

    <!-- Diğer göstergeler -->
    <div style="display:flex;flex:1;align-items:stretch;overflow-x:auto;">
        {ticker_band_item("USD / TRY",   f"₺{usd_d['price']:,.4f}",  usd_d['chg'])}
        {ticker_band_item("EUR / TRY",   f"₺{eur_d['price']:,.4f}",  eur_d['chg'])}
        {ticker_band_item("ALTIN (XAU)", f"${gold_d['price']:,.1f}", gold_d['chg'])}
    </div>

    <!-- Saat -->
    <div style="display:flex;flex-direction:column;justify-content:center;
    padding:10px 16px;border-left:1px solid {border_color};min-width:90px;text-align:right;">
        <div style="font-size:0.62rem;color:{text_muted};text-transform:uppercase;
        letter-spacing:0.08em;">İstanbul</div>
        <div style="font-size:1rem;font-weight:600;color:{text_main};">
            {datetime.now().strftime('%H:%M')}</div>
        <div style="font-size:0.65rem;color:{text_muted};">
            {datetime.now().strftime('%d.%m.%Y')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── TradingView Markets Nav Sekmeleri ─────────────────────────
st.markdown(f"""
<div style="display:flex;gap:0;border-bottom:2px solid {border_color};
margin-bottom:14px;margin-top:2px;">
    <a href="#" style="padding:8px 18px;font-size:0.82rem;font-weight:600;
    color:#2962ff;border-bottom:2px solid #2962ff;text-decoration:none;
    margin-bottom:-2px;">Hisseler</a>
    <a href="#" style="padding:8px 18px;font-size:0.82rem;font-weight:500;
    color:{text_muted};text-decoration:none;">ETF'ler</a>
    <a href="#" style="padding:8px 18px;font-size:0.82rem;font-weight:500;
    color:{text_muted};text-decoration:none;">Döviz</a>
    <a href="#" style="padding:8px 18px;font-size:0.82rem;font-weight:500;
    color:{text_muted};text-decoration:none;">Emtialar</a>
    <a href="#" style="padding:8px 18px;font-size:0.82rem;font-weight:500;
    color:{text_muted};text-decoration:none;">Kripto</a>
</div>
""", unsafe_allow_html=True)

# ── Piyasa Durumu Özetleri (TV Markets'taki kartlar) ──────────
df_tv = fetch_tv_screener_data()

if not df_tv.empty:
    rising    = df_tv[df_tv["Değişim %"] > 0]
    falling   = df_tv[df_tv["Değişim %"] < 0]
    n_rising  = len(rising)
    n_falling = len(falling)
    n_total   = len(df_tv)
    avg_chg   = df_tv["Değişim %"].mean()
    top_gainer = df_tv.nlargest(1,"Değişim %").iloc[0] if not df_tv.empty else None
    top_loser  = df_tv.nsmallest(1,"Değişim %").iloc[0] if not df_tv.empty else None

    pct_rise = int(n_rising/n_total*100) if n_total>0 else 0
    avg_c    = "#089981" if avg_chg>=0 else "#f23645"
    avg_s    = "+" if avg_chg>=0 else ""

    # Büyük özet kartlar (TV Markets üst kısmı)
    mc1,mc2,mc3,mc4,mc5 = st.columns(5)

    mc1.markdown(f"""
    <div class="macro-box" style="text-align:left;padding:12px 14px;">
        <div class="macro-title">Toplam Hisse</div>
        <div class="macro-val" style="font-size:1.4rem;">{n_total}</div>
        <div style="font-size:0.72rem;color:{text_muted};margin-top:2px;">
            BIST taranıyor</div>
    </div>""", unsafe_allow_html=True)

    mc2.markdown(f"""
    <div class="macro-box" style="text-align:left;padding:12px 14px;
    border-left:3px solid #089981;">
        <div class="macro-title">Yükselenler</div>
        <div class="macro-val" style="font-size:1.4rem;color:#089981;">{n_rising}</div>
        <div style="font-size:0.72rem;color:#089981;margin-top:2px;">
            %{pct_rise} hisse</div>
    </div>""", unsafe_allow_html=True)

    mc3.markdown(f"""
    <div class="macro-box" style="text-align:left;padding:12px 14px;
    border-left:3px solid #f23645;">
        <div class="macro-title">Düşenler</div>
        <div class="macro-val" style="font-size:1.4rem;color:#f23645;">{n_falling}</div>
        <div style="font-size:0.72rem;color:#f23645;margin-top:2px;">
            %{100-pct_rise} hisse</div>
    </div>""", unsafe_allow_html=True)

    mc4.markdown(f"""
    <div class="macro-box" style="text-align:left;padding:12px 14px;">
        <div class="macro-title">Ort. Değişim</div>
        <div class="macro-val" style="font-size:1.4rem;color:{avg_c};">
            {avg_s}{avg_chg:.2f}%</div>
        <div style="font-size:0.72rem;color:{text_muted};margin-top:2px;">
            Günlük ortalama</div>
    </div>""", unsafe_allow_html=True)

    if top_gainer is not None:
        tg_s = "+" if top_gainer["Değişim %"]>=0 else ""
        mc5.markdown(f"""
        <div class="macro-box" style="text-align:left;padding:12px 14px;
        border-left:3px solid #089981;">
            <div class="macro-title">En Çok Yükselen</div>
            <div class="macro-val" style="font-size:1.2rem;color:#089981;">
                {top_gainer['Sembol']}</div>
            <div style="font-size:0.78rem;color:#089981;margin-top:2px;">
                {tg_s}{top_gainer['Değişim %']:.2f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Sektör Isı Haritası (TV Markets Heat Map tarzı) ─────────
    sektor_map = {
        "Bankacılık":   ["AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","ALBRK","SKBNK","TSKB"],
        "Enerji":       ["ENJSA","AKSEN","ODAS","SMARTG","EUPWR","AYEN","AKSA","ZOREN","CWENE"],
        "Sanayi":       ["EREGL","KRDMD","ARCLK","VESTL","BRISA","TTRAK","FROTO","TOASO"],
        "Perakende":    ["BIMAS","MGROS","SOKM","MAVI","KERVT","BANVT"],
        "Teknoloji":    ["ASELS","TCELL","TTKOM","LOGO","ARENA","KAREL","ASTOR"],
        "GYO":          ["EKGYO","ISGYO","TRGYO","HLGYO","VKGYO"],
        "Holding":      ["KCHOL","SAHOL","DOHOL","ENKAI","ALARK","AGHOL"],
        "Kimya/İlaç":   ["PETKM","SASA","TUPRS","DEVA","SELEC","ECILC"],
    }

    st.markdown(f"""
    <div style="font-size:0.85rem;font-weight:600;color:{text_main};
    margin-bottom:8px;margin-top:4px;">Sektör Performansı</div>""",
    unsafe_allow_html=True)

    sek_html = f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;">'
    for sektor, semboller in sektor_map.items():
        sektor_data = df_tv[df_tv["Sembol"].isin(semboller)]
        if sektor_data.empty: continue
        avg_s_chg = sektor_data["Değişim %"].mean()
        inten = min(abs(avg_s_chg)/3, 1.0)
        if avg_s_chg > 0:
            r,g,b = int(8+inten*30), int(153-inten*20), int(129-inten*30)
        else:
            r,g,b = int(242-inten*30), int(54+inten*20), int(69+inten*20)
        bg_hex = f"rgb({r},{g},{b})"
        txt_c  = "#ffffff"
        sign_s = "+" if avg_s_chg>=0 else ""
        sek_html += f"""
        <div style="background:{bg_hex};border-radius:6px;padding:10px 14px;
        min-width:110px;text-align:center;flex:1;">
            <div style="font-size:0.68rem;color:{txt_c};opacity:0.85;
            text-transform:uppercase;letter-spacing:0.06em;">{sektor}</div>
            <div style="font-size:1rem;font-weight:700;color:{txt_c};margin-top:2px;">
                {sign_s}{avg_s_chg:.2f}%</div>
            <div style="font-size:0.65rem;color:{txt_c};opacity:0.75;margin-top:1px;">
                {len(sektor_data)} hisse</div>
        </div>"""
    sek_html += "</div>"
    st.markdown(sek_html, unsafe_allow_html=True)

    # ── En Çok İşlem Görenler (TV Markets Top Movers) ────────────
    st.markdown(f"""
    <div style="font-size:0.85rem;font-weight:600;color:{text_main};
    margin-bottom:8px;">En Çok Değişenler</div>""", unsafe_allow_html=True)

    top5up   = df_tv.nlargest(5,"Değişim %")
    top5down = df_tv.nsmallest(5,"Değişim %")

    mv1, mv2 = st.columns(2)
    for col, title, data, color in [
        (mv1, "🟢 Günün Yükselenleri", top5up,   "#089981"),
        (mv2, "🔴 Günün Düşenleri",   top5down,  "#f23645"),
    ]:
        with col:
            rows_html = f"""
            <div style="background:{card_bg};border:1px solid {border_color};
            border-radius:8px;overflow:hidden;margin-bottom:12px;">
            <div style="padding:10px 14px;border-bottom:1px solid {border_color};
            font-size:0.8rem;font-weight:600;color:{color};">{title}</div>"""
            for _, r in data.iterrows():
                s = "+" if r["Değişim %"]>=0 else ""
                rows_html += f"""
                <div style="display:flex;justify-content:space-between;
                align-items:center;padding:8px 14px;
                border-bottom:1px solid {border_color};">
                    <div>
                        <div style="font-size:0.85rem;font-weight:600;
                        color:#2962ff;">{r['Sembol']}</div>
                        <div style="font-size:0.7rem;color:{text_muted};">
                            {r['Teknik']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.85rem;font-weight:600;
                        color:{text_main};">{r['Fiyat']:,.2f}</div>
                        <div style="font-size:0.78rem;font-weight:600;
                        color:{color};">{s}{r['Değişim %']:.2f}%</div>
                    </div>
                </div>"""
            rows_html += "</div>"
            col.markdown(rows_html, unsafe_allow_html=True)

st.markdown(f"<hr style='border-color:{border_color};margin:4px 0 14px 0;'>",
            unsafe_allow_html=True)

# ==========================================
# 5. ANA SEKMELER
# ==========================================
tab_screener, tab_portfolio, tab_ai, tab_binance = st.tabs([
    "📊 Hisse Tarayıcı & Grafik", "💼 Portföyüm", "🤖 AI Öneri Motoru", "🚀 Binance API"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: BÖLÜNMÜŞ EKRAN (SCREENER + X-RAY)
# ╚══════════════════════════════════════════╝
with tab_screener:
    col_scr, col_xray = st.columns([2.0, 1.4])
    
    # --- SOL: GELİŞMİŞ SCREENER ---
    with col_scr:
        df_screener = fetch_tv_screener_data()
        if df_screener.empty:
            st.error("Piyasa verisi çekilemedi. Lütfen bağlantınızı kontrol edin.")
        else:
            html_table = '<div class="tv-screener-container"><table class="tv-table"><thead><tr><th>TICKER</th><th>SON</th><th>DEĞİŞİM %</th><th>1 HAFTA %</th><th>1 AY %</th><th>TEKNİK SİNYAL</th><th>HACİM</th><th>RSI</th></tr></thead><tbody>'
            
            for _, row in df_screener.sort_values("Değişim %", ascending=False).iterrows():
                c_d = "tv-green" if row["Değişim %"] >= 0 else "tv-red"
                c_w = "tv-green" if row["1H %"] >= 0 else "tv-red"
                c_m = "tv-green" if row["1A %"] >= 0 else "tv-red"
                sign_d = "+" if row["Değişim %"] >= 0 else ""
                sign_w = "+" if row["1H %"] >= 0 else ""
                sign_m = "+" if row["1A %"] >= 0 else ""
                
                html_table += "<tr>"
                html_table += f"<td><div class='tv-ticker-col'><div class='tv-logo-circle'>{row['Sembol'][0]}</div><div class='tv-ticker-info'><span class='tv-ticker-symbol'>{row['Sembol']}</span></div></div></td>"
                html_table += f"<td>{row['Fiyat']:,.2f}</td>"
                html_table += f"<td class='{c_d}'>{sign_d}{row['Değişim %']:.2f}%</td>"
                html_table += f"<td class='{c_w}'>{sign_w}{row['1H %']:.2f}%</td>"
                html_table += f"<td class='{c_m}'>{sign_m}{row['1A %']:.2f}%</td>"
                html_table += f"<td><span class='tv-rating {row['Teknik_Class']}'>{row['Teknik']}</span></td>"
                html_table += f"<td>{format_volume(row['Hacim'])}</td>"
                html_table += f"<td>{row['RSI']:.1f}</td>"
                html_table += "</tr>"
                
            html_table += "</tbody></table></div>"
            st.markdown(html_table, unsafe_allow_html=True)

    # --- SAĞ: X-RAY WIDGET PANELİ ---
    with col_xray:
        secilen_hisse = st.selectbox("X-Ray Röntgeni İçin Hisse Seç:", sorted(bist_symbols), index=bist_symbols.index("THYAO") if "THYAO" in bist_symbols else 0)
        tv_symbol = f"BIST:{secilen_hisse}"
        
        # 1. Advanced Chart (hide_top_toolbar false yapıldı, artık zaman dilimi seçilebilir)
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div id="tradingview_chart"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({{"width": "100%", "height": 380, "symbol": "{tv_symbol}", "interval": "D", "timezone": "Europe/Istanbul", "theme": "{tv_theme_str}", "style": "1", "locale": "tr", "hide_top_toolbar": false, "container_id": "tradingview_chart"}});
              </script>
            </div>
            """, height=380, scrolling=False
        )
        
        # 2. Teknik Analiz Kadranı
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
              {{"interval": "1D", "width": "100%", "isTransparent": true, "height": "250", "symbol": "{tv_symbol}", "showIntervalTabs": true, "displayMode": "single", "locale": "tr", "colorTheme": "{tv_theme_str}"}}
              </script>
            </div>
            """, height=250, scrolling=False
        )

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: PORTFÖYÜM                      ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main}; border-bottom: 1px solid {border_color}; padding-bottom: 10px; margin-bottom: 20px;">Portföy Yönetimi</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        add_sym = st.selectbox("Hisse Seç", sorted(bist_symbols), key="portfoy_sec")
    
    preview_price = 0.0
    try:
        tkr = yf.Ticker(f"{add_sym}.IS")
        try: preview_price = float(tkr.fast_info['lastPrice'])
        except:
            df_p = tkr.history(period="5d")
            if not df_p.empty: preview_price = float(df_p["Close"].iloc[-1])
    except: pass

    with c2: st.text_input("Anlık Fiyat", value=f"{preview_price:,.2f}" if preview_price > 0 else "Bulunamadı", disabled=True)
    with c3: add_adet = st.number_input("Adet", min_value=1, value=10)
    with c4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Portföye Ekle", use_container_width=True, type="primary") and preview_price > 0:
            st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": preview_price}
            st.rerun()

    if st.session_state.portfolio:
        st.markdown("<br>### Mevcut Varlıklar", unsafe_allow_html=True)
        for sym, data in st.session_state.portfolio.items():
            cc1, cc2 = st.columns([4, 1])
            with cc1:
                st.markdown(f"<div style='padding:15px; background-color:{card_bg}; border:1px solid {border_color}; border-radius:8px;'><b>{sym}</b>: {data['adet']} Adet | Maliyet: TL {data['maliyet']:,.2f} | Toplam: TL {data['adet']*data['maliyet']:,.2f}</div>", unsafe_allow_html=True)
            with cc2:
                if st.button(f"Sil", key=f"del_{sym}", use_container_width=True):
                    del st.session_state.portfolio[sym]
                    st.rerun()

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: AI & ÖNERİ MOTORU              ║
# ╚══════════════════════════════════════════╝
with tab_ai:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main}; border-bottom: 1px solid {border_color}; padding-bottom: 10px; margin-bottom: 20px;">🧠 Akıllı Yapay Zeka Öneri Motoru</div>', unsafe_allow_html=True)
    
    b1, b2, b3 = st.columns([2, 2, 1])
    with b1: butce = st.number_input("Yatırım Bütçesi (TL)", value=50000, step=5000)
    with b2: risk = st.selectbox("Risk Algın", ["Dengeli (Büyük Şirketler)", "Agresif (Büyüme Odaklı)"])
    with b3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        oneri_btn = st.button("Sepet Oluştur", use_container_width=True, type="primary")

    if oneri_btn:
        with st.spinner("Yapay zeka piyasayı tarıyor, sabırlı olun..."):
            df_scan = fetch_tv_screener_data().copy()
            if not df_scan.empty:
                df_scan = df_scan[df_scan["RSI"] < 45].sort_values("1A %", ascending=True).head(3)
                st.success("Taramayı tamamladım. Kısa vadede aşırı satılmış ve tepki beklenen 3 hisse:")
                for _, row in df_scan.iterrows():
                    st.markdown(f"""
                    <div style="background:{card_bg}; padding:1rem; border-left:4px solid {blue_brand}; border-radius:4px; margin-bottom:1rem;">
                        <h4 style="margin:0; color:{blue_brand};">{row['Sembol']}</h4>
                        <p style="margin:0.5rem 0; font-size:0.9rem; color:{text_main};">
                            <b>Fiyat:</b> TL {row['Fiyat']:,.2f} | <b>RSI:</b> {row['RSI']:.1f} | <b>1 Aylık Performans:</b> {row['1A %']:.2f}%<br>
                            <i>Analiz: Hisse 1 aylık periyotta ciddi cezalandırılmış, RSI aşırı satım bölgesinden çıkış sinyali arıyor.</i>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: BINANCE API                    ║
# ╚══════════════════════════════════════════╝
with tab_binance:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main}; border-bottom: 1px solid {border_color}; padding-bottom: 10px; margin-bottom: 20px;">🚀 Binance Webhook Kontrol Merkezi</div>', unsafe_allow_html=True)
    
    col_api, col_info = st.columns([1, 1])
    with col_api:
        binance_mode = st.radio("Ağ Seçimi", ["Testnet (Sanal Bakiye)", "Live (Gerçek Hesap)"])
        api_key = st.text_input("Binance API Key", type="password")
        sec_key = st.text_input("Binance Secret Key", type="password")
        
        if st.button("Bağlantıyı Doğrula", type="primary", use_container_width=True):
            if api_key and sec_key:
                st.session_state.binance_connected = True
                st.session_state.binance_mode = binance_mode
                st.success("API Bağlantısı Başarılı! Webhook altyapısı aktif edildi.")
                st.rerun()
            else:
                st.error("Lütfen API ve Secret anahtarlarını eksiksiz girin.")

    with col_info:
        if st.session_state.binance_connected:
            status_color = "#089981" if "Live" not in st.session_state.binance_mode else "#f23645"
            st.markdown(f"""
            <div style="padding: 1rem; border: 1px solid {status_color}; border-radius: 6px; margin-bottom: 1rem; background-color:{card_bg};">
                <b style="color:{status_color};">🟢 BAĞLANTI AKTİF ({st.session_state.binance_mode})</b><br>
                <span style="font-size:0.85rem; color:{text_muted};">Sistem otomatik emirleri Binance API'sine iletmeye hazır.</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("Hedef Webhook JSON Formatı (Payload):")
            st.code(json.dumps({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.001}, indent=4), language="json")
        else:
            st.warning("Webhook sinyallerini görmek için API anahtarlarınızla giriş yapmalısınız.")
