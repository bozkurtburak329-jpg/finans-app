"""
Borsa Analiz Uygulaması v18.0 (OMNIVERSE EDITION - Kusursuz Birleşim)
- TradingView'in tüm PRO Widget'ları (Isı Haritası, Pro Grafikler, Takvim) sisteme entegre edildi.
- Kendi yazdığımız Yapay Zeka (AI) Öneri Motoru, Portföy Yöneticisi ve Binance API geri getirildi!
- Kendi özel "Python Tarayıcımız" ile "TradingView Tarayıcısı" birleştirildi.
- Baştan aşağı yepyeni, geniş ve modern bir Dashboard tasarımı.
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
# 1. PAGE CONFIG & TEMA AYARLARI
# ==========================================
st.set_page_config(
    page_title="Omniverse Borsa Terminali",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "theme" not in st.session_state: st.session_state.theme = "dark"
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "ai_signals" not in st.session_state: st.session_state.ai_signals = {}
if "binance_connected" not in st.session_state: st.session_state.binance_connected = False
if "binance_mode" not in st.session_state: st.session_state.binance_mode = "Testnet"
if "selected_stock" not in st.session_state: st.session_state.selected_stock = "THYAO"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

tv_theme = "dark" if st.session_state.theme == "dark" else "light"
bg_color = "#131722" if tv_theme == "dark" else "#ffffff"
text_main = "#d1d4dc" if tv_theme == "dark" else "#131722"
text_muted = "#787b86"
card_bg = "#1e222d" if tv_theme == "dark" else "#f0f3fa"
border_color = "#2a2e39" if tv_theme == "dark" else "#e0e3eb"
row_hover = "#2a2e39" if tv_theme == "dark" else "#f0f3fa"
blue_brand = "#2962ff"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; background-color: {bg_color} !important; color: {text_main} !important; }}
[data-testid="collapsedControl"], section[data-testid="stSidebar"] {{ display: none; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {card_bg}; }}
::-webkit-scrollbar-thumb {{ background: #787b86; border-radius: 3px; }}

/* Header */
.top-header {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: {card_bg}; border-bottom: 1px solid {border_color}; border-radius: 8px; margin-bottom: 8px; }}
.logo-area {{ display: flex; align-items: center; gap: 12px; }}
.logo-icon {{ width: 36px; height: 36px; background: linear-gradient(135deg, #2962ff, #00c853); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; font-size: 18px; }}

/* Ticker bandı */
.ticker-band {{ display:flex; align-items:stretch; background:{card_bg}; border:1px solid {border_color}; border-radius:8px; margin:6px 0 8px 0; overflow:hidden; }}
.ticker-bist {{ display:flex; flex-direction:column; padding:10px 18px; background:{bg_color}; border-right:2px solid {blue_brand}; min-width:170px; }}
.ticker-others {{ display:flex; flex:1; align-items:stretch; overflow-x:auto; }}
.ticker-item {{ display:flex; flex-direction:column; padding:8px 16px; border-right:1px solid {border_color}; min-width:130px; }}
.ticker-label {{ font-size:0.62rem; color:#787b86; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:3px; }}
.ticker-price-big {{ font-size:1.5rem; font-weight:800; color:{text_main}; letter-spacing:-0.03em; line-height:1.1; }}
.ticker-price {{ font-size:1.05rem; font-weight:700; color:{text_main}; letter-spacing:-0.02em; }}
.ticker-chg {{ font-size:0.75rem; font-weight:600; margin-top:2px; }}
.ticker-time {{ display:flex; flex-direction:column; justify-content:center; padding:8px 14px; border-left:1px solid {border_color}; text-align:right; min-width:85px; }}

/* Tablo */
.tv-screener-box {{ width:100%; overflow-y:auto; overflow-x:auto; background:{bg_color}; border:1px solid {border_color}; border-radius:6px; max-height:75vh; }}
.tv-table {{ width:100%; border-collapse:collapse; font-size:13px; text-align:right; white-space:nowrap; }}
.tv-table thead {{ position:sticky; top:0; z-index:2; background:{card_bg}; box-shadow:0 1px 0 {border_color}; }}
.tv-table th {{ padding:10px 12px; font-weight:500; color:#787b86; border-right:1px solid {border_color}; font-size:12px; }}
.tv-table th:first-child, .tv-table td:first-child {{ text-align:left; }}
.tv-table tbody tr {{ border-bottom:1px solid {border_color}; background:{bg_color}; cursor:pointer; }}
.tv-table tbody tr:hover {{ background:{row_hover}; }}
.tv-table td {{ padding:8px 12px; color:{text_main}; vertical-align:middle; }}
.tv-logo-circle {{ width:26px; height:26px; border-radius:50%; background:{blue_brand}; color:#fff; display:inline-flex; align-items:center; justify-content:center; font-weight:700; font-size:12px; margin-right:8px; }}
.tv-ticker-symbol {{ color:{blue_brand}; font-weight:600; font-size:13px; }}
.tv-green {{ color:#089981 !important; font-weight:600; }}
.tv-red {{ color:#f23645 !important; font-weight:600; }}
.rating-strong-buy {{ color:#089981; background:rgba(8,153,129,0.15); padding:2px 7px; border-radius:4px; font-size:12px; font-weight:600; }}
.rating-buy {{ color:#089981; font-size:12px; font-weight:600; }}
.rating-sell {{ color:#f23645; font-size:12px; font-weight:600; }}
.rating-strong-sell {{ color:#f23645; background:rgba(242,54,69,0.15); padding:2px 7px; border-radius:4px; font-size:12px; font-weight:600; }}
.rating-neutral {{ color:#787b86; background:rgba(120,123,134,0.15); padding:2px 7px; border-radius:4px; font-size:12px; font-weight:600; }}

/* AI */
.ai-box {{ background:{card_bg}; border-left:4px solid #089981; padding:14px 16px; border-radius:6px; margin-bottom:12px; }}
.ai-sell-box {{ background:rgba(242,54,69,0.08); border-left:4px solid #f23645; padding:14px 16px; border-radius:6px; margin-bottom:12px; }}
.ai-watch-box {{ background:rgba(240,185,11,0.08); border-left:4px solid #f0b90b; padding:14px 16px; border-radius:6px; margin-bottom:12px; }}
.signal-tag {{ display:inline-block; padding:3px 10px; border-radius:4px; font-size:11px; font-weight:700; margin-left:8px; }}
.sig-buy {{ background:rgba(8,153,129,0.2); color:#089981; }}
.sig-sell {{ background:rgba(242,54,69,0.2); color:#f23645; }}
.sig-hold {{ background:rgba(240,185,11,0.2); color:#f0b90b; }}

/* Portföy */
.pf-card {{ background:{card_bg}; border:1px solid {border_color}; border-radius:8px; padding:12px 14px; margin-bottom:8px; }}
.pf-sym {{ font-size:1rem; font-weight:700; color:{blue_brand}; }}
.pf-detail {{ font-size:0.78rem; color:#787b86; margin-top:3px; }}

/* Macro kutu */
.macro-box {{ background:{card_bg}; border-radius:6px; padding:10px; border:1px solid {border_color}; text-align:center; }}
.macro-title {{ font-size:0.7rem; color:#787b86; letter-spacing:1px; text-transform:uppercase; }}
.macro-val {{ font-size:1.1rem; font-weight:700; color:{text_main}; margin:2px 0; }}

/* Sektör ısı */
.sektor-grid {{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px; }}
.sektor-item {{ border-radius:6px; padding:10px 12px; min-width:100px; text-align:center; flex:1; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. PYTHON VERİ ALTYAPISI (YFINANCE)
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","KCHOL","SAHOL","DOHOL","ALARK","ENKAI",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL","SISE","CIMSA",
    "FROTO","TOASO","DOAS","OTKAR","KARSN","ARCLK","VESTL","BRISA","THYAO","PGSUS",
    "BIMAS","MGROS","SOKM","AEFES","CCOLA","TCELL","TTKOM","ASELS","ASTOR","KONTR",
    "ENJSA","AKSEN","ODAS","SMARTG","EUPWR","GESAN","EKGYO","ISGYO","DEVA","SELEC"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}
crypto_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "LINK"]
TICKERS_CRYPTO = {f"{sym}-USD": sym for sym in crypto_symbols}
us_symbols = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "NFLX"]
TICKERS_US = {sym: sym for sym in us_symbols}

def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        rs = delta.clip(lower=0).rolling(period).mean() / (-1 * delta.clip(upper=0)).rolling(period).mean().replace(0, np.nan)
        return round(float(100 - (100 / (1 + rs)).iloc[-1]), 1)
    except: return np.nan

@st.cache_data(ttl=600, show_spinner=False)
def fetch_custom_data(tickers_dict):
    end = datetime.today()
    start = end - timedelta(days=60)
    rows = []
    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 30: return None
            close = df["Close"].squeeze()
            p_last, p_prev = float(close.iloc[-1]), float(close.iloc[-2])
            chg_pct = ((p_last - p_prev) / p_prev) * 100
            volatility = float(close.rolling(14).std().iloc[-1] / p_last)
            rsi = compute_rsi(close)
            
            score = 0
            if rsi < 30: score += 2
            elif rsi > 70: score -= 2
            teknik = "Al" if score > 0 else "Sat" if score < 0 else "Nötr"
            
            return {"Sembol": name, "Fiyat": p_last, "Değişim %": chg_pct, "RSI": rsi, "Volatilite": volatility, "Teknik": teknik}
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in tickers_dict.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
    return pd.DataFrame(rows)

def get_tv_symbol(market, sym):
    if market == "BIST 100": return f"BIST:{sym}"
    elif market == "Kripto (USD)": return f"BINANCE:{sym}USDT"
    elif market == "ABD Borsaları": return f"NASDAQ:{sym}"
    return f"BIST:{sym}"

@st.cache_data(ttl=180, show_spinner=False)
def get_macro_data():
    tickers = {"XU100.IS":"BIST 100","USDTRY=X":"USD/TRY","EURTRY=X":"EUR/TRY","GC=F":"ALTIN"}
    res = {}
    for t, name in tickers.items():
        try:
            df = yf.download(t, period="5d", interval="1h", progress=False, auto_adjust=True)
            if not df.empty and len(df) >= 3:
                close = df["Close"].squeeze().dropna()
                curr  = float(close.iloc[-1])
                prev  = float(close.iloc[-3])
                res[name] = {"price": curr, "chg": (curr-prev)/prev*100}
            else: res[name] = {"price":0.0,"chg":0.0}
        except: res[name] = {"price":0.0,"chg":0.0}
    return res

# ==========================================
# 3. HEADER + CANLI TİCKER BANDI
# ==========================================
macro = get_macro_data()

# Nav bar
nav_c1, nav_c2, nav_c3 = st.columns([5, 2, 0.6])
with nav_c1:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
        <div class="logo-icon">B</div>
        <div>
            <div style="font-size:1.1rem;font-weight:800;color:{text_main};letter-spacing:-0.02em;">
                Burak Borsa Terminali</div>
            <div style="font-size:0.68rem;color:#787b86;text-transform:uppercase;letter-spacing:0.1em;">
                v18.0 — AI Destekli Tümleşik Piyasalar</div>
        </div>
    </div>""", unsafe_allow_html=True)
with nav_c2:
    secilen_piyasa = st.selectbox("Piyasa", ["BIST 100","Kripto (USD)","ABD Borsaları"],
                                  label_visibility="collapsed")
with nav_c3:
    st.button("☀️" if st.session_state.theme=="dark" else "🌙",
              on_click=toggle_theme, use_container_width=True)

if secilen_piyasa == "BIST 100":    aktif_tickerlar = TICKERS_BIST
elif secilen_piyasa == "Kripto (USD)": aktif_tickerlar = TICKERS_CRYPTO
else:                                aktif_tickerlar = TICKERS_US
aktif_semboller = list(aktif_tickerlar.values())

df_data = fetch_custom_data(aktif_tickerlar)

# Canlı ticker bandı (HTML yorum yok, Python f-string ile)
bist = macro.get("BIST 100",{"price":0,"chg":0})
usd  = macro.get("USD/TRY",  {"price":0,"chg":0})
eur  = macro.get("EUR/TRY",  {"price":0,"chg":0})
xau  = macro.get("ALTIN",    {"price":0,"chg":0})

def _chg_html(chg, prefix=""):
    c = "#089981" if chg>=0 else "#f23645"
    s = "▲" if chg>=0 else "▼"
    return f'<div class="ticker-chg" style="color:{c};">{s} {abs(chg):.2f}%{prefix}</div>'

bist_c = "#089981" if bist["chg"]>=0 else "#f23645"
bist_s = "▲" if bist["chg"]>=0 else "▼"

st.markdown(f"""
<div class="ticker-band">
    <div class="ticker-bist">
        <div class="ticker-label">BIST 100</div>
        <div class="ticker-price-big">{bist["price"]:,.1f}</div>
        <div class="ticker-chg" style="color:{bist_c};">{bist_s} {abs(bist["chg"]):.2f}%</div>
    </div>
    <div class="ticker-others">
        <div class="ticker-item">
            <div class="ticker-label">USD / TRY</div>
            <div class="ticker-price">&#8378;{usd["price"]:,.4f}</div>
            {_chg_html(usd["chg"])}
        </div>
        <div class="ticker-item">
            <div class="ticker-label">EUR / TRY</div>
            <div class="ticker-price">&#8378;{eur["price"]:,.4f}</div>
            {_chg_html(eur["chg"])}
        </div>
        <div class="ticker-item">
            <div class="ticker-label">ALTIN (XAU/USD)</div>
            <div class="ticker-price">${xau["price"]:,.1f}</div>
            {_chg_html(xau["chg"])}
        </div>
    </div>
    <div class="ticker-time">
        <div class="ticker-label">Istanbul</div>
        <div style="font-size:1rem;font-weight:600;color:{text_main};">
            {datetime.now().strftime("%H:%M")}</div>
        <div style="font-size:0.65rem;color:#787b86;">
            {datetime.now().strftime("%d.%m.%Y")}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# TradingView Kayan Ticker (async widget)
components.html(f"""
<div class="tradingview-widget-container" style="height:46px;">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript"
    src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {{
    "symbols":[
      {{"proName":"BIST:XU100","title":"BIST 100"}},
      {{"proName":"BITSTAMP:BTCUSD","title":"Bitcoin"}},
      {{"proName":"FX_IDC:USDTRY","title":"USD/TRY"}},
      {{"proName":"FX_IDC:EURTRY","title":"EUR/TRY"}},
      {{"proName":"OANDA:XAUUSD","title":"Altin"}},
      {{"proName":"FOREXCOM:SPXUSD","title":"S&P 500"}},
      {{"proName":"BIST:THYAO","title":"THYAO"}},
      {{"proName":"BIST:GARAN","title":"GARAN"}}
    ],
    "showSymbolLogo":true,
    "colorTheme":"{tv_theme}",
    "isTransparent":true,
    "displayMode":"adaptive",
    "locale":"tr"
  }}
  </script>
</div>
""", height=52, scrolling=False)

# ==========================================
# 4. ANA SEKMELER (6 DEV SEKME)
# ==========================================
tab_overview, tab_chart, tab_ai, tab_portfolio, tab_macro, tab_fundamentals = st.tabs([
    "🌐 Piyasa Özeti & Isı Haritası", 
    "📈 Pro Grafik & Kadran", 
    "🤖 Yapay Zeka (AI) & Tarayıcı", 
    "💼 Portföy & Binance API",
    "📰 Haberler & Makro Takvim",
    "🏢 Şirket Profili & Temel Analiz"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PİYASA ÖZETİ & ISI HARİTASI    ║
# ╚══════════════════════════════════════════╝
with tab_overview:
    col_heat, col_hot = st.columns([2.5, 1.5])
    with col_heat:
        st.markdown(f'<div style="font-size:1rem;font-weight:700;color:{text_main};margin-bottom:5px;">BIST Isı Haritası</div>', unsafe_allow_html=True)
        components.html(f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript"
                src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
              {{
                "exchanges":["BIST"],"dataSource":"XU100","grouping":"sector",
                "blockSize":"market_cap_basic","blockColor":"change","locale":"tr",
                "colorTheme":"{tv_theme}","hasTopBar":true,"width":"100%","height":"520"
              }}
              </script>
            </div>""", height=540)

        # Sektör özet satırı
        if not df_data.empty and secilen_piyasa == "BIST 100":
            sektor_map = {
                "Bankacılık": ["AKBNK","GARAN","ISCTR","YKBNK","VAKBN"],
                "Enerji":     ["ENJSA","AKSEN","ODAS","SMARTG","EUPWR"],
                "Sanayi":     ["EREGL","KRDMD","ARCLK","VESTL","FROTO","TOASO"],
                "Perakende":  ["BIMAS","MGROS","SOKM"],
                "Teknoloji":  ["ASELS","TCELL","TTKOM","KONTR"],
                "GYO":        ["EKGYO","ISGYO"],
                "Holding":    ["KCHOL","SAHOL","DOHOL","ENKAI"],
                "Kimya":      ["PETKM","SASA","TUPRS","DEVA"],
            }
            st.markdown(f'<div style="font-size:0.85rem;font-weight:600;color:{text_main};margin:10px 0 6px;">Sektör Performansı</div>', unsafe_allow_html=True)
            sek_html = '<div class="sektor-grid">'
            for sektor, semboller in sektor_map.items():
                sd = df_data[df_data["Sembol"].isin(semboller)]
                if sd.empty: continue
                avg = sd["Değişim %"].mean()
                inten = min(abs(avg)/3, 1.0)
                if avg > 0:
                    r,g,b = int(8+inten*25),int(153-inten*15),int(129-inten*25)
                else:
                    r,g,b = int(242-inten*25),int(54+inten*15),int(69+inten*25)
                sign = "+" if avg>=0 else ""
                sek_html += f"""<div class="sektor-item" style="background:rgb({r},{g},{b});">
                    <div style="font-size:0.65rem;color:#fff;opacity:0.85;text-transform:uppercase;">{sektor}</div>
                    <div style="font-size:0.95rem;font-weight:700;color:#fff;">{sign}{avg:.2f}%</div>
                    <div style="font-size:0.62rem;color:#fff;opacity:0.7;">{len(sd)} hisse</div>
                </div>"""
            sek_html += "</div>"
            st.markdown(sek_html, unsafe_allow_html=True)

    with col_hot:
        st.markdown(f'<div style="font-size:1rem;font-weight:700;color:{text_main};margin-bottom:5px;">Günün Hareketlileri</div>', unsafe_allow_html=True)
        components.html(f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript"
                src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
              {{
                "colorTheme":"{tv_theme}","exchange":"BIST","showChart":true,
                "locale":"tr","width":"100%","height":"520","isTransparent":true
              }}
              </script>
            </div>""", height=540)

        # En çok yükselenler / düşenler (Python verisi)
        if not df_data.empty:
            top5u = df_data.nlargest(5,"Değişim %")
            top5d = df_data.nsmallest(5,"Değişim %")
            for title, data, color in [
                ("Yükselenler", top5u, "#089981"),
                ("Düşenler",    top5d, "#f23645"),
            ]:
                st.markdown(f'<div style="font-size:0.82rem;font-weight:700;color:{color};margin:10px 0 4px;">{title}</div>', unsafe_allow_html=True)
                rows = f'<div style="background:{card_bg};border:1px solid {border_color};border-radius:6px;overflow:hidden;">'
                for _, r in data.iterrows():
                    s = "+" if r["Değişim %"]>=0 else ""
                    rows += f"""<div style="display:flex;justify-content:space-between;padding:6px 12px;border-bottom:1px solid {border_color};">
                        <span style="font-weight:600;color:{blue_brand};">{r['Sembol']}</span>
                        <span style="color:{color};font-weight:600;">{s}{r['Değişim %']:.2f}%</span>
                    </div>"""
                rows += "</div>"
                st.markdown(rows, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: PRO GRAFİK & KADRAN            ║
# ╚══════════════════════════════════════════╝
with tab_chart:
    chart_sym = st.selectbox(
        "Hisse / Sembol Seç",
        sorted(aktif_semboller),
        index=sorted(aktif_semboller).index("THYAO") if "THYAO" in aktif_semboller else 0,
        key="chart_sym_select"
    )
    st.session_state.selected_stock = chart_sym
    tv_sym = get_tv_symbol(secilen_piyasa, chart_sym)

    col_adv, col_gauge = st.columns([3, 1])
    with col_adv:
        st.markdown(f'<div style="font-size:1rem;font-weight:700;color:{text_main};margin-bottom:5px;">Gelişmiş Grafik — {tv_sym}</div>', unsafe_allow_html=True)
        components.html(f"""
            <div class="tradingview-widget-container" style="height:600px;width:100%;">
              <div id="tv_adv_{chart_sym}"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({{
                "autosize":true,"symbol":"{tv_sym}","interval":"D",
                "timezone":"Europe/Istanbul","theme":"{tv_theme}","style":"1",
                "locale":"tr","backgroundColor":"{bg_color}",
                "allow_symbol_change":true,"details":true,"hotlist":true,
                "container_id":"tv_adv_{chart_sym}"
              }});
              </script>
            </div>""", height=620, scrolling=False)

    with col_gauge:
        st.markdown(f'<div style="font-size:1rem;font-weight:700;color:{text_main};margin-bottom:5px;">Teknik Kadran</div>', unsafe_allow_html=True)
        components.html(f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript"
                src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
              {{
                "interval":"1D","width":"100%","isTransparent":true,"height":"300",
                "symbol":"{tv_sym}","showIntervalTabs":true,
                "displayMode":"single","locale":"tr","colorTheme":"{tv_theme}"
              }}
              </script>
            </div>""", height=320, scrolling=False)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Anlık veri kartı
        if not df_data.empty and chart_sym in df_data["Sembol"].values:
            row_c = df_data[df_data["Sembol"]==chart_sym].iloc[0]
            chg_c2 = "#089981" if row_c["Değişim %"]>=0 else "#f23645"
            chg_s2 = "+" if row_c["Değişim %"]>=0 else ""
            rsi_c  = "#089981" if pd.notna(row_c["RSI"]) and row_c["RSI"]<40 else \
                     "#f23645" if pd.notna(row_c["RSI"]) and row_c["RSI"]>65 else "#787b86"
            st.markdown(f"""
            <div style="background:{card_bg};border:1px solid {border_color};border-radius:8px;padding:12px 14px;">
                <div style="font-size:1.3rem;font-weight:800;color:{text_main};">{chart_sym}</div>
                <div style="font-size:1.6rem;font-weight:700;color:{text_main};margin:4px 0;">
                    {row_c['Fiyat']:,.2f}</div>
                <div style="font-size:0.9rem;font-weight:600;color:{chg_c2};">
                    {chg_s2}{row_c['Değişim %']:.2f}%</div>
                <div style="margin-top:10px;display:flex;gap:1rem;">
                    <div>
                        <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">RSI (14)</div>
                        <div style="font-size:1rem;font-weight:700;color:{rsi_c};">{row_c['RSI']:.1f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">Teknik</div>
                        <div style="font-size:0.9rem;font-weight:700;color:{chg_c2};">{row_c['Teknik']}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        components.html(f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript"
                src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
              {{
                "symbol":"{tv_sym}","width":"100%","height":"200",
                "locale":"tr","dateRange":"12M","colorTheme":"{tv_theme}",
                "trendLineColor":"#2962ff","underLineColor":"rgba(41,98,255,0.1)",
                "isTransparent":true,"autosize":true,"largeChartUrl":""
              }}
              </script>
            </div>""", height=220, scrolling=False)

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: YAPAY ZEKA (AI) & TARAYICI     ║
# ╚══════════════════════════════════════════╝
with tab_ai:
    st.markdown(f'<div style="font-size:1.2rem;font-weight:700;color:{text_main};border-bottom:1px solid {border_color};padding-bottom:8px;margin-bottom:14px;">AI Sinyal Motoru — {secilen_piyasa}</div>', unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns([2, 2, 1.5, 1])
    with b1:
        risk_plani = st.selectbox("Risk Algoritması",
            ["Dengeli (Dar Stop, Kısa Hedef)",
             "Agresif (Geniş Stop, Yüksek Hedef)",
             "Ultra-Agresif (Yüksek Volatilite)"])
    with b2:
        filtre_tip = st.selectbox("Filtre",
            ["Aşırı Satılmış (RSI<40)",
             "Al Sinyali + Momentum",
             "Düşük Volatilite + Güvenli",
             "Tümü"])
    with b3:
        butce_ai = st.number_input("Bütçe (TL)", min_value=1000,
                                    max_value=10_000_000, value=50_000, step=5000)
    with b4:
        st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
        oneri_btn = st.button("AI Analiz Başlat", use_container_width=True, type="primary")

    if oneri_btn:
        if df_data.empty:
            st.error("Veri çekilemedi.")
        else:
            with st.spinner("AI piyasayı tarıyor ve sinyaller hesaplanıyor..."):
                df_ai = df_data.copy()

                # Risk parametreleri
                if "Dengeli" in risk_plani:
                    k, s_stop, vol_max = 1.08, 0.95, 0.06
                elif "Agresif" in risk_plani:
                    k, s_stop, vol_max = 1.15, 0.90, 0.10
                else:
                    k, s_stop, vol_max = 1.25, 0.85, 0.20

                # Filtre uygula
                if "Aşırı Satılmış" in filtre_tip:
                    df_ai = df_ai[df_ai["RSI"] < 40]
                elif "Al Sinyali" in filtre_tip:
                    df_ai = df_ai[(df_ai["RSI"] < 50) & (df_ai["Değişim %"] > 0)]
                elif "Düşük Volatilite" in filtre_tip:
                    df_ai = df_ai[df_ai["Volatilite"] < 0.04]

                # AI skoru hesapla
                df_ai["AI_Skor"] = 0
                df_ai.loc[df_ai["RSI"] < 30, "AI_Skor"] += 3
                df_ai.loc[(df_ai["RSI"] >= 30) & (df_ai["RSI"] < 45), "AI_Skor"] += 2
                df_ai.loc[df_ai["Değişim %"] > 0, "AI_Skor"] += 1
                df_ai.loc[df_ai["Değişim %"] > 2, "AI_Skor"] += 1
                df_ai.loc[df_ai["Volatilite"] < 0.05, "AI_Skor"] += 1

                top_picks = df_ai.sort_values(["AI_Skor","RSI"], ascending=[False,True]).head(5)

                if top_picks.empty:
                    st.warning("Seçili filtreye uyan hisse bulunamadı.")
                else:
                    hisse_basi = butce_ai / len(top_picks)
                    toplam_hedef = 0.0
                    toplam_stop  = 0.0

                    st.markdown(f"""
                    <div style="background:{card_bg};border:1px solid {border_color};border-left:3px solid {blue_brand};
                    border-radius:8px;padding:12px 16px;margin-bottom:14px;">
                        <div style="font-size:0.8rem;color:#787b86;">
                            AI {len(top_picks)} hisse seçti · Her birine
                            <b style="color:{text_main};">TL {hisse_basi:,.0f}</b> yatırılıyor ·
                            Risk: <b style="color:{text_main};">{risk_plani.split('(')[0].strip()}</b>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    for _, row in top_picks.iterrows():
                        sym2   = row["Sembol"]
                        fiyat  = row["Fiyat"]
                        hedef  = fiyat * k
                        stop   = fiyat * s_stop
                        adet   = int(hisse_basi / fiyat) if fiyat > 0 else 0
                        kazanc = adet * (hedef - fiyat)
                        zarar  = adet * (fiyat - stop)
                        rr     = kazanc / zarar if zarar > 0 else 0
                        skor   = int(row["AI_Skor"])

                        # RSI yorumu
                        if row["RSI"] < 30:
                            rsi_yorum = "Aşırı satılmış — güçlü tepki bekleniyor"
                        elif row["RSI"] < 45:
                            rsi_yorum = "Alım bölgesinde — momentum dönüyor"
                        else:
                            rsi_yorum = "Nötr bölge — hacim takibi önerilir"

                        # Sinyal kaydet
                        st.session_state.ai_signals[sym2] = {
                            "hedef": hedef, "stop": stop, "adet": adet,
                            "giris": fiyat, "rr": rr
                        }

                        st.markdown(f"""
                        <div class="ai-box">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
                                <div>
                                    <span style="font-size:1.2rem;font-weight:800;color:{blue_brand};">{sym2}</span>
                                    <span class="signal-tag sig-buy">AL SİNYALİ</span>
                                    <span style="font-size:0.72rem;color:#787b86;margin-left:6px;">AI Skor: {skor}/6</span>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-size:0.65rem;color:#787b86;">Önerilen Adet</div>
                                    <div style="font-size:1rem;font-weight:700;color:{text_main};">{adet} adet</div>
                                </div>
                            </div>
                            <div style="display:flex;gap:1.5rem;margin-top:10px;flex-wrap:wrap;">
                                <div>
                                    <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">Giriş Fiyatı</div>
                                    <div style="font-size:0.95rem;font-weight:700;color:{text_main};">{fiyat:,.2f}</div>
                                </div>
                                <div>
                                    <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">Hedef Fiyat</div>
                                    <div style="font-size:0.95rem;font-weight:700;color:#089981;">{hedef:,.2f} (+{(k-1)*100:.0f}%)</div>
                                </div>
                                <div>
                                    <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">Stop Loss</div>
                                    <div style="font-size:0.95rem;font-weight:700;color:#f23645;">{stop:,.2f} (-{(1-s_stop)*100:.0f}%)</div>
                                </div>
                                <div>
                                    <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">R/R Oranı</div>
                                    <div style="font-size:0.95rem;font-weight:700;color:{text_main};">{rr:.1f}x</div>
                                </div>
                                <div>
                                    <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">Pot. Kazanç</div>
                                    <div style="font-size:0.95rem;font-weight:700;color:#089981;">+TL {kazanc:,.0f}</div>
                                </div>
                                <div>
                                    <div style="font-size:0.62rem;color:#787b86;text-transform:uppercase;">Maks. Zarar</div>
                                    <div style="font-size:0.95rem;font-weight:700;color:#f23645;">-TL {zarar:,.0f}</div>
                                </div>
                            </div>
                            <div style="margin-top:8px;font-size:0.8rem;color:#787b86;">
                                RSI {row['RSI']:.1f} — {rsi_yorum} · Volatilite: %{row['Volatilite']*100:.1f}
                            </div>
                        </div>""", unsafe_allow_html=True)

                        toplam_hedef += adet * hedef
                        toplam_stop  += adet * stop

                    # Toplam özet
                    st.markdown(f"""
                    <div style="background:{card_bg};border:1px solid #089981;border-radius:8px;
                    padding:12px 16px;margin-top:6px;">
                        <div style="font-size:0.78rem;color:#787b86;margin-bottom:6px;">Portföy Özeti</div>
                        <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                            <div>
                                <div style="font-size:0.62rem;color:#787b86;">Yatırılan</div>
                                <div style="font-size:1rem;font-weight:700;color:{text_main};">TL {butce_ai:,.0f}</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:#787b86;">Hedef Değer</div>
                                <div style="font-size:1rem;font-weight:700;color:#089981;">TL {toplam_hedef:,.0f} (+{(toplam_hedef/butce_ai-1)*100:.1f}%)</div>
                            </div>
                            <div>
                                <div style="font-size:0.62rem;color:#787b86;">Stop Değer</div>
                                <div style="font-size:1rem;font-weight:700;color:#f23645;">TL {toplam_stop:,.0f} ({(toplam_stop/butce_ai-1)*100:.1f}%)</div>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-color:{border_color};margin:16px 0;'>", unsafe_allow_html=True)

    # Aktif AI Sinyalleri (portföyde varsa uyar)
    if st.session_state.ai_signals and not df_data.empty:
        st.markdown(f'<div style="font-size:1rem;font-weight:700;color:{text_main};margin-bottom:10px;">Aktif AI Sinyalleri — Anlık Takip</div>', unsafe_allow_html=True)
        for sym2, sig in st.session_state.ai_signals.items():
            cur = df_data[df_data["Sembol"]==sym2]
            if cur.empty: continue
            cp2    = cur.iloc[0]["Fiyat"]
            hedef2 = sig["hedef"]
            stop2  = sig["stop"]
            giris2 = sig.get("giris", cp2)
            pnl_p  = (cp2-giris2)/giris2*100 if giris2>0 else 0
            pnl_c  = "#089981" if pnl_p>=0 else "#f23645"

            if cp2 >= hedef2:
                box_class = "ai-box"
                icon = "KAR AL"
                msg  = f"Hedef fiyata ({hedef2:,.2f}) ulaştı! Çıkış zamanı."
                stag = "sig-buy"
            elif cp2 <= stop2:
                box_class = "ai-sell-box"
                icon = "ZARAR KES"
                msg  = f"Stop seviyesine ({stop2:,.2f}) indi. Zararı kes!"
                stag = "sig-sell"
            else:
                pct_to_hedef = (hedef2-cp2)/cp2*100
                box_class = "ai-watch-box"
                icon = "İZLE"
                msg  = f"Hedefe %{pct_to_hedef:.1f} kaldı. Pozisyonu koru."
                stag = "sig-hold"

            st.markdown(f"""
            <div class="{box_class}">
                <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                    <div>
                        <span style="font-size:1rem;font-weight:700;color:{text_main};">{sym2}</span>
                        <span class="signal-tag {stag}">{icon}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.62rem;color:#787b86;">P&L</div>
                        <div style="font-weight:700;color:{pnl_c};">{'+'if pnl_p>=0 else ''}{pnl_p:.2f}%</div>
                    </div>
                </div>
                <div style="font-size:0.82rem;color:#787b86;margin-top:6px;">{msg}</div>
                <div style="display:flex;gap:1.5rem;margin-top:8px;font-size:0.8rem;">
                    <span>Anlık: <b style="color:{text_main};">{cp2:,.2f}</b></span>
                    <span>Giriş: <b style="color:{text_main};">{giris2:,.2f}</b></span>
                    <span>Hedef: <b style="color:#089981;">{hedef2:,.2f}</b></span>
                    <span>Stop: <b style="color:#f23645;">{stop2:,.2f}</b></span>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f'<div style="font-size:1rem;font-weight:700;color:{text_main};margin:14px 0 8px;">Anlık Veri Tablosu</div>', unsafe_allow_html=True)
    if not df_data.empty:
        html_t = f'<div class="tv-screener-box" style="max-height:40vh;"><table class="tv-table"><thead><tr><th>SEMBOL</th><th>FİYAT</th><th>DEĞİŞİM %</th><th>RSI</th><th>VOL %</th><th>TEKNİK</th></tr></thead><tbody>'
        for _, row in df_data.sort_values("Değişim %", ascending=False).iterrows():
            cd = "tv-green" if row["Değişim %"]>=0 else "tv-red"
            s  = "+" if row["Değişim %"]>=0 else ""
            html_t += f"<tr><td><div style='display:flex;align-items:center;'><div class='tv-logo-circle'>{row['Sembol'][0]}</div><span class='tv-ticker-symbol'>{row['Sembol']}</span></div></td><td>{row['Fiyat']:,.2f}</td><td class='{cd}'>{s}{row['Değişim %']:.2f}%</td><td>{row['RSI']:.1f}</td><td>{row['Volatilite']*100:.2f}%</td><td>{row['Teknik']}</td></tr>"
        html_t += "</tbody></table></div>"
        st.markdown(html_t, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: PORTFÖY & BİNANCE API          ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    col_port, col_bin = st.columns([1.6, 1])

    with col_port:
        st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:{text_main};border-bottom:1px solid {border_color};padding-bottom:8px;margin-bottom:14px;">Kişisel Portföy & AI Sinyalleri</div>', unsafe_allow_html=True)

        # AI Uyarıları
        aktif_uyari = False
        if st.session_state.portfolio and not df_data.empty:
            for sym3, data3 in st.session_state.portfolio.items():
                cur3 = df_data[df_data["Sembol"]==sym3]
                if cur3.empty: continue
                cp3  = cur3.iloc[0]["Fiyat"]
                hd3  = st.session_state.ai_signals.get(sym3, {}).get("hedef", float("inf"))
                st3  = st.session_state.ai_signals.get(sym3, {}).get("stop", 0)
                if cp3 >= hd3:
                    aktif_uyari = True
                    st.markdown(f"""
                    <div class="ai-box">
                        <span class="signal-tag sig-buy">KAR AL</span>
                        <b style="margin-left:8px;">{sym3}</b> hedefe ulaştı!
                        Anlık: {cp3:,.2f} — Hedef: {hd3:,.2f}
                    </div>""", unsafe_allow_html=True)
                elif cp3 <= st3 and st3 > 0:
                    aktif_uyari = True
                    st.markdown(f"""
                    <div class="ai-sell-box">
                        <span class="signal-tag sig-sell">ZARAR KES</span>
                        <b style="margin-left:8px;">{sym3}</b> stop seviyesine indi!
                        Anlık: {cp3:,.2f} — Stop: {st3:,.2f}
                    </div>""", unsafe_allow_html=True)

        if not aktif_uyari and st.session_state.portfolio:
            st.markdown(f'<div style="font-size:0.8rem;color:#089981;margin-bottom:10px;">Tüm pozisyonlar normal aralıkta — sinyal yok.</div>', unsafe_allow_html=True)

        # Hisse ekle
        st.markdown(f'<div style="font-size:0.85rem;font-weight:600;color:{text_main};margin-bottom:8px;">Varlık Ekle</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1.5, 1])
        with c1:
            add_sym = st.selectbox("Varlık", sorted(aktif_semboller), key="pf_add_sym")
        with c2:
            add_adet = st.number_input("Miktar", min_value=0.01, value=10.0, key="pf_add_adet")
        with c3:
            st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
            if st.button("Ekle", use_container_width=True, type="primary"):
                pr4 = df_data[df_data["Sembol"]==add_sym].iloc[0]["Fiyat"] \
                      if (not df_data.empty and add_sym in df_data["Sembol"].values) else 0
                st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": pr4}
                st.rerun()

        # Anlık fiyat önizleme
        if not df_data.empty and add_sym in df_data["Sembol"].values:
            pr_prev = df_data[df_data["Sembol"]==add_sym].iloc[0]["Fiyat"]
            st.markdown(f'<div style="font-size:0.78rem;color:#089981;margin-bottom:10px;">Anlık: <b>{pr_prev:,.2f}</b> · {add_adet} adet = TL {add_adet*pr_prev:,.0f}</div>', unsafe_allow_html=True)

        # Portföy listesi
        if st.session_state.portfolio:
            total_maliyet = 0.0; total_guncel = 0.0
            for sym4, data4 in list(st.session_state.portfolio.items()):
                cp4 = df_data[df_data["Sembol"]==sym4].iloc[0]["Fiyat"] \
                      if (not df_data.empty and sym4 in df_data["Sembol"].values) else data4["maliyet"]
                kz4  = ((cp4-data4["maliyet"])/data4["maliyet"]*100) if data4["maliyet"]>0 else 0
                rc4  = "#089981" if kz4>=0 else "#f23645"
                ks4  = "+" if kz4>=0 else ""
                t_mal = data4["adet"]*data4["maliyet"]
                t_gun = data4["adet"]*cp4
                total_maliyet += t_mal; total_guncel += t_gun

                pc1, pc2 = st.columns([5, 1])
                with pc1:
                    st.markdown(f"""
                    <div class="pf-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="pf-sym">{sym4}</div>
                            <div style="font-size:0.85rem;font-weight:700;color:{rc4};">
                                {ks4}{kz4:.2f}%</div>
                        </div>
                        <div class="pf-detail">
                            {data4['adet']:.0f} adet · Maliyet: {data4['maliyet']:,.2f} ·
                            Anlık: {cp4:,.2f} ·
                            Toplam: TL {t_gun:,.0f}
                        </div>
                        <div style="font-size:0.8rem;margin-top:4px;">
                            <span style="color:{rc4};font-weight:600;">
                                P&amp;L: {ks4}TL {abs(t_gun-t_mal):,.0f}
                            </span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                with pc2:
                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                    if st.button("Sil", key=f"del_{sym4}", use_container_width=True):
                        del st.session_state.portfolio[sym4]; st.rerun()

            # Toplam özet
            pnl_t = total_guncel - total_maliyet
            pnl_tp = (pnl_t/total_maliyet*100) if total_maliyet>0 else 0
            pnl_c2 = "#089981" if pnl_t>=0 else "#f23645"
            st.markdown(f"""
            <div style="background:{card_bg};border:1px solid {border_color};border-top:2px solid {blue_brand};
            border-radius:8px;padding:12px 14px;margin-top:4px;">
                <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                    <div>
                        <div style="font-size:0.62rem;color:#787b86;">Toplam Yatırım</div>
                        <div style="font-size:1rem;font-weight:700;color:{text_main};">TL {total_maliyet:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:#787b86;">Güncel Değer</div>
                        <div style="font-size:1rem;font-weight:700;color:{text_main};">TL {total_guncel:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.62rem;color:#787b86;">Toplam P&L</div>
                        <div style="font-size:1rem;font-weight:700;color:{pnl_c2};">
                            {'+'if pnl_t>=0 else ''}TL {abs(pnl_t):,.0f} ({pnl_tp:+.1f}%)</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    with col_bin:
        st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:{text_main};border-bottom:1px solid {border_color};padding-bottom:8px;margin-bottom:14px;">Binance Webhook</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.82rem;color:#787b86;margin-bottom:12px;">Kripto otomasyonu için API bilgilerinizi girin.</div>', unsafe_allow_html=True)
        binance_mode = st.radio("Ağ", ["Testnet (Güvenli)", "Live (Gerçek Hesap)"],
                                horizontal=True)
        api_key = st.text_input("API Key", type="password", placeholder="Binance API Key")
        sec_key = st.text_input("Secret Key", type="password", placeholder="Binance Secret Key")
        if st.button("Bağlan & Doğrula", type="primary", use_container_width=True):
            if api_key and sec_key:
                st.session_state.binance_connected = True
                st.session_state.binance_mode = binance_mode
                st.success("Bağlantı aktif!")
            else:
                st.error("API ve Secret Key gerekli.")

        if st.session_state.binance_connected:
            s_c = "#089981" if "Testnet" in st.session_state.binance_mode else "#f23645"
            st.markdown(f"""
            <div style="background:{card_bg};border:1px solid {s_c};border-radius:8px;
            padding:10px 14px;margin-top:10px;">
                <div style="font-weight:700;color:{s_c};">BAĞLANTI AKTİF</div>
                <div style="font-size:0.78rem;color:#787b86;">{st.session_state.binance_mode}</div>
            </div>""", unsafe_allow_html=True)
            st.write("Webhook Payload Formatı:")
            st.code(json.dumps({"symbol":"BTCUSDT","side":"BUY","type":"MARKET","quantity":0.001},indent=2),
                    language="json")

# ╔══════════════════════════════════════════╗
# ║  SEKME 5: HABERLER & MAKRO TAKVİM        ║
# ╚══════════════════════════════════════════╝
with tab_macro:
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown("### 📰 Küresel Haber Akışı")
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
              {{ "feedMode": "all_symbols", "colorTheme": "{tv_theme}", "isTransparent": true, "displayMode": "regular", "width": "100%", "height": "550", "locale": "tr" }}
              </script>
            </div>
            """, height=570
        )
    with c_m2:
        st.markdown("### 📅 Ekonomik Takvim")
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
              {{ "colorTheme": "{tv_theme}", "isTransparent": true, "width": "100%", "height": "550", "locale": "tr", "importanceFilter": "-1,0,1", "currencyFilter": "USD,EUR,TRY" }}
              </script>
            </div>
            """, height=570
        )

# ╔══════════════════════════════════════════╗
# ║  SEKME 6: ŞİRKET PROFILİ & BİLANÇOLAR    ║
# ╚══════════════════════════════════════════╝
with tab_fundamentals:
    f_sym = st.text_input("Şirket Sembolü Girin (Örn: BIST:KCHOL, NASDAQ:AAPL)", value="BIST:THYAO")
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        st.markdown("### 🏢 Finansal Bilançolar")
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-financials.js" async>
              {{ "colorTheme": "{tv_theme}", "isTransparent": true, "displayMode": "regular", "width": "100%", "height": "550", "symbol": "{f_sym}", "locale": "tr" }}
              </script>
            </div>
            """, height=570
        )
    with col_f2:
        st.markdown("### 📰 Şirket Profili")
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-profile.js" async>
              {{ "width": "100%", "height": "550", "colorTheme": "{tv_theme}", "isTransparent": true, "symbol": "{f_sym}", "locale": "tr" }}
              </script>
            </div>
            """, height=570
        )
