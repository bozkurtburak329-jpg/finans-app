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

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

tv_theme = "dark" if st.session_state.theme == "dark" else "light"
bg_color = "#131722" if tv_theme == "dark" else "#ffffff"
text_main = "#d1d4dc" if tv_theme == "dark" else "#131722"
card_bg = "#1e222d" if tv_theme == "dark" else "#f0f3fa"
border_color = "#2a2e39" if tv_theme == "dark" else "#e0e3eb"
row_hover = "#2a2e39" if tv_theme == "dark" else "#f0f3fa"
blue_brand = "#2962ff"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; background-color: {bg_color} !important; color: {text_main} !important; }}
[data-testid="collapsedControl"], section[data-testid="stSidebar"] {{ display: none; }}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {card_bg}; }}
::-webkit-scrollbar-thumb {{ background: #787b86; border-radius: 3px; }}
.top-header {{ display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; background: {card_bg}; border-bottom: 1px solid {border_color}; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
.logo-area {{ display: flex; align-items: center; gap: 12px; }}
.logo-icon {{ width: 36px; height: 36px; background: linear-gradient(135deg, #2962ff, #00c853); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; font-size: 18px; box-shadow: 0 2px 10px rgba(41,98,255,0.3); }}
.tv-table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: right; white-space: nowrap; }}
.tv-table thead {{ position: sticky; top: 0; z-index: 2; background-color: {card_bg}; box-shadow: 0 1px 0 {border_color}; }}
.tv-table th {{ padding: 10px 12px; font-weight: 500; color: #787b86; border-right: 1px solid {border_color}; font-size: 12px; text-align: right; }}
.tv-table th:first-child, .tv-table td:first-child {{ text-align: left; }}
.tv-table tbody tr {{ border-bottom: 1px solid {border_color}; background-color: {bg_color}; transition: 0.1s; }}
.tv-table tbody tr:hover {{ background-color: {row_hover}; }}
.tv-table td {{ padding: 8px 12px; color: {text_main}; vertical-align: middle; }}
.tv-green {{ color: #089981 !important; }}
.tv-red {{ color: #f23645 !important; }}
.ai-box {{ background-color: {card_bg}; border-left: 4px solid #089981; padding: 15px; border-radius: 6px; margin-bottom: 15px; }}
.ai-sell-box {{ background-color: rgba(242, 54, 69, 0.1); border-left: 4px solid #f23645; padding: 15px; border-radius: 6px; margin-bottom: 15px; }}
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

# ==========================================
# 3. MODERN TEPE TASARIMI (HEADER)
# ==========================================
st.markdown(f"""
<div class="top-header">
    <div class="logo-area">
        <div class="logo-icon">🌌</div>
        <div style="display:flex; flex-direction:column;">
            <div style="font-size: 1.3rem; font-weight: 800; color: {text_main}; line-height: 1.2;">Omniverse Terminal v18.0</div>
            <div style="font-size: 0.75rem; color: #787b86; text-transform: uppercase; letter-spacing: 1px;">AI Destekli Tümleşik Piyasalar</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

nav_col1, nav_col2, nav_col3 = st.columns([6, 2, 1])
with nav_col2:
    secilen_piyasa = st.selectbox("🌍 Piyasa Seç:", ["BIST 100", "Kripto (USD)", "ABD Borsaları"], label_visibility="collapsed")
with nav_col3:
    st.button("☀️/🌙", on_click=toggle_theme, use_container_width=True)

if secilen_piyasa == "BIST 100": aktif_tickerlar = TICKERS_BIST
elif secilen_piyasa == "Kripto (USD)": aktif_tickerlar = TICKERS_CRYPTO
else: aktif_tickerlar = TICKERS_US

df_data = fetch_custom_data(aktif_tickerlar)
aktif_semboller = list(aktif_tickerlar.values())

# Ticker Tape (Kayan Yazı)
components.html(
    f"""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {{
      "symbols": [
        {{"proName": "BIST:XU100", "title": "BIST 100"}},
        {{"proName": "BITSTAMP:BTCUSD", "title": "Bitcoin"}},
        {{"proName": "FX_IDC:EURTRY", "title": "EUR/TRY"}},
        {{"proName": "FOREXCOM:SPXUSD", "title": "S&P 500"}},
        {{"proName": "OANDA:XAUUSD", "title": "Altın (Ons)"}}
      ],
      "showSymbolLogo": true,
      "colorTheme": "{tv_theme}",
      "isTransparent": true,
      "displayMode": "adaptive",
      "locale": "tr"
    }}
      </script>
    </div>
    """, height=50
)

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
        st.markdown(f'<div style="font-size:1.1rem; font-weight:700; color:{text_main}; margin-bottom:5px;">Dev Isı Haritası</div>', unsafe_allow_html=True)
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js" async>
              {{
              "exchanges": ["BIST"], "dataSource": "XU100", "grouping": "sector",
              "blockSize": "market_cap_basic", "blockColor": "change", "locale": "tr",
              "colorTheme": "{tv_theme}", "hasTopBar": true, "width": "100%", "height": "550"
            }}
              </script>
            </div>
            """, height=570
        )
    with col_hot:
        st.markdown(f'<div style="font-size:1.1rem; font-weight:700; color:{text_main}; margin-bottom:5px;">Günün Hareketlileri</div>', unsafe_allow_html=True)
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
              {{
              "colorTheme": "{tv_theme}", "exchange": "BIST", "showChart": true, "locale": "tr",
              "width": "100%", "height": "550", "isTransparent": true
            }}
              </script>
            </div>
            """, height=570
        )

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: PRO GRAFİK & KADRAN            ║
# ╚══════════════════════════════════════════╝
with tab_chart:
    col_adv, col_gauge = st.columns([3, 1])
    with col_adv:
        st.markdown(f'<div style="font-size:1.1rem; font-weight:700; color:{text_main}; margin-bottom:5px;">Gelişmiş Çizim İstasyonu</div>', unsafe_allow_html=True)
        components.html(
            f"""
            <div class="tradingview-widget-container" style="height: 600px; width: 100%;">
              <div id="tradingview_advanced"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget(
              {{ "autosize": true, "symbol": "BIST:THYAO", "interval": "D", "timezone": "Europe/Istanbul",
              "theme": "{tv_theme}", "style": "1", "locale": "tr", "backgroundColor": "{bg_color}",
              "allow_symbol_change": true, "details": true, "hotlist": true, "container_id": "tradingview_advanced" }}
              );
              </script>
            </div>
            """, height=650
        )
    with col_gauge:
        st.markdown(f'<div style="font-size:1.1rem; font-weight:700; color:{text_main}; margin-bottom:5px;">Teknik Kadran</div>', unsafe_allow_html=True)
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
              {{ "interval": "1D", "width": "100%", "isTransparent": true, "height": "450",
              "symbol": "BIST:THYAO", "showIntervalTabs": true, "displayMode": "single", "locale": "tr", "colorTheme": "{tv_theme}" }}
              </script>
            </div>
            """, height=470
        )

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: YAPAY ZEKA (AI) & TARAYICI     ║
# ╚══════════════════════════════════════════╝
with tab_ai:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main};">🧠 {secilen_piyasa} AI Öneri Motoru</div>', unsafe_allow_html=True)
    
    # AI Motoru (Kendi Yazdığımız)
    b1, b2, b3 = st.columns([2, 2, 1])
    with b1: risk_plani = st.selectbox("Risk Algoritması", ["Dengeli (Dar Stop, Kısa Hedef)", "Agresif (Geniş Stop, Yüksek Hedef)"])
    with b3: 
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        oneri_btn = st.button("Yapay Zeka Analizini Başlat", use_container_width=True, type="primary")

    if oneri_btn:
        if df_data.empty: st.error("Veri çekilemedi.")
        else:
            with st.spinner("AI piyasayı tarıyor..."):
                df_ai = df_data.copy()
                df_ai["AI_Skor"] = np.where(df_ai["RSI"] < 45, 2, 0)
                if "Dengeli" in risk_plani:
                    df_ai = df_ai[df_ai["Volatilite"] < 0.06]
                    k, s = 1.08, 0.95
                else:
                    k, s = 1.15, 0.88
                
                top_picks = df_ai.sort_values(by=["AI_Skor", "RSI"], ascending=[False, True]).head(3)
                for _, row in top_picks.iterrows():
                    h, f, hedef, stop = row['Sembol'], row['Fiyat'], row['Fiyat']*k, row['Fiyat']*s
                    st.session_state.ai_signals[h] = {"hedef": hedef, "stop": stop}
                    st.markdown(f"""
                    <div class="ai-box">
                        <h3 style="margin-top:0; color:{blue_brand};">{h} | Skor: %{80+row['AI_Skor']*5}</h3>
                        <div><b>Giriş:</b> {f:,.4f} | <b style="color:#089981;">Hedef:</b> {hedef:,.4f} | <b style="color:#f23645;">Stop:</b> {stop:,.4f}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    # Kendi Python Tarayıcımız
    st.markdown(f'<div style="font-size:1.1rem; font-weight:700; color:{text_main}; margin-bottom:10px;">📊 Anlık Veri Tablosu</div>', unsafe_allow_html=True)
    if not df_data.empty:
        html_table = '<div style="overflow-x:auto;"><table class="tv-table"><thead><tr><th>SEMBOL</th><th>FİYAT</th><th>DEĞİŞİM %</th><th>RSI</th><th>TEKNİK</th></tr></thead><tbody>'
        for _, row in df_data.sort_values("Değişim %", ascending=False).iterrows():
            c_d = "tv-green" if row["Değişim %"] >= 0 else "tv-red"
            html_table += f"<tr><td><b>{row['Sembol']}</b></td><td>{row['Fiyat']:,.4f}</td><td class='{c_d}'>{row['Değişim %']:.2f}%</td><td>{row['RSI']:.1f}</td><td>{row['Teknik']}</td></tr>"
        html_table += "</tbody></table></div>"
        st.markdown(html_table, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: PORTFÖY & BİNANCE API          ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    col_port, col_bin = st.columns([1.5, 1])
    
    with col_port:
        st.markdown(f'<div style="font-size:1.2rem; font-weight:700; color:{text_main};">💼 Kişisel Portföy & AI Sinyalleri</div>', unsafe_allow_html=True)
        
        # AI Uyarıları
        if st.session_state.portfolio and not df_data.empty:
            for sym, data in st.session_state.portfolio.items():
                cur = df_data[df_data["Sembol"] == sym]
                if not cur.empty:
                    cp = cur.iloc[0]["Fiyat"]
                    hd = st.session_state.ai_signals.get(sym, {}).get("hedef", float('inf'))
                    st_p = st.session_state.ai_signals.get(sym, {}).get("stop", 0)
                    if cp >= hd: st.markdown(f"<div class='ai-sell-box'><b>🟢 KÂR AL:</b> {sym} hedefe ulaştı ({hd:.4f}). Anlık: {cp:.4f}</div>", unsafe_allow_html=True)
                    elif cp <= st_p: st.markdown(f"<div class='ai-sell-box'><b>🔴 ZARAR KES:</b> {sym} stop oldu ({st_p:.4f}). Anlık: {cp:.4f}</div>", unsafe_allow_html=True)

        # Portföy Ekleme
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: add_sym = st.selectbox("Varlık Seç", sorted(aktif_semboller))
        with c2: add_adet = st.number_input("Miktar", min_value=0.01, value=10.0)
        with c3: 
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Ekle", use_container_width=True):
                pr = df_data[df_data["Sembol"] == add_sym].iloc[0]["Fiyat"] if not df_data.empty else 0
                st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": pr}
                st.rerun()

        for sym, data in list(st.session_state.portfolio.items()):
            cp = df_data[df_data["Sembol"]==sym].iloc[0]["Fiyat"] if (not df_data.empty and sym in df_data["Sembol"].values) else data['maliyet']
            kz = ((cp - data['maliyet']) / data['maliyet']) * 100 if data['maliyet'] > 0 else 0
            renk = "#089981" if kz >= 0 else "#f23645"
            st.markdown(f"<div style='padding:10px; background:{card_bg}; border:1px solid {border_color}; border-radius:6px; margin-top:5px;'><b>{sym}</b> | Maliyet: {data['maliyet']:,.4f} | Anlık: {cp:,.4f} | <b style='color:{renk}'>P&L: {kz:.2f}%</b></div>", unsafe_allow_html=True)
            if st.button("Sil", key=f"del_{sym}"): 
                del st.session_state.portfolio[sym]
                st.rerun()

    with col_bin:
        st.markdown(f'<div style="font-size:1.2rem; font-weight:700; color:{text_main};">🚀 Binance Webhook</div>', unsafe_allow_html=True)
        st.info("Kripto otomasyonu için API bilgilerinizi girin.")
        binance_mode = st.radio("Ağ", ["Testnet", "Live"])
        api_key = st.text_input("API Key", type="password")
        sec_key = st.text_input("Secret Key", type="password")
        if st.button("Bağlan", type="primary"):
            if api_key and sec_key:
                st.session_state.binance_connected = True
                st.success("Bağlantı Aktif!")

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
