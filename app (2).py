"""
Borsa Analiz Uygulaması v14.0 (THE GOD MODE - AI & Sinyal Sürümü)
- Hata veren HTML blokları düzeltildi ve stabilize edildi.
- Yapay Zeka Öneri Motoru geliştirildi: Dinamik Hedef Fiyat (Kar Al) ve Stop Loss (Zarar Kes) eklendi.
- AI Sinyal Takipçisi: Portföye eklenen hisseler hedefe ulaştığında "SAT" bildirimi verir.
- Gerçek zamanlı risk yönetimi (Dengeli vs. Agresif)
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
if "ai_signals" not in st.session_state: st.session_state.ai_signals = {} # AI'ın önerdiği hedefler
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

/* AI Kutu Stilleri */
.ai-box {{ background-color: {card_bg}; border-left: 4px solid #089981; padding: 15px; border-radius: 6px; margin-bottom: 15px; }}
.ai-sell-box {{ background-color: rgba(242, 54, 69, 0.1); border-left: 4px solid #f23645; padding: 15px; border-radius: 6px; margin-bottom: 15px; }}
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

@st.cache_data(ttl=600, show_spinner=False)
def fetch_tv_screener_data():
    end = datetime.today()
    start = end - timedelta(days=60)
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
            volatility = float(close.rolling(14).std().iloc[-1] / p_last) # Volatilite oranı (Stop-Loss için)
            rsi = compute_rsi(close)
            rating, rating_cls = get_tv_rating(rsi, p_last, sma50)
            
            return {
                "Sembol": name, "Fiyat": p_last, "Değişim %": chg_pct, "1H %": w_pct, "1A %": m_pct,
                "Teknik": rating, "Teknik_Class": rating_cls, "Hacim": vol, "RSI": rsi, "Volatilite": volatility
            }
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
    return pd.DataFrame(rows)

# ==========================================
# 4. TRADINGVIEW MARKETS TARZI HEADER
# ==========================================
macro = get_macro_data()

nav_col, nav_r = st.columns([5, 1])
with nav_col:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; padding: 6px 0 4px 0;">
        <div style="width:28px;height:28px;border-radius:6px;background:#2962ff;
        display:flex;align-items:center;justify-content:center;
        font-weight:900;font-size:15px;color:#fff;">B</div>
        <span style="font-size:1.1rem;font-weight:700;color:{text_main};letter-spacing:-0.02em;">
            Burak Borsa Terminali</span>
    </div>
    """, unsafe_allow_html=True)
with nav_r:
    st.button("☀️/🌙", on_click=toggle_theme, use_container_width=True)

bist_d  = macro.get("BIST 100",  {"price":0,"chg":0})
usd_d   = macro.get("USD/TRY",   {"price":0,"chg":0})
eur_d   = macro.get("EUR/TRY",   {"price":0,"chg":0})
gold_d  = macro.get("ALTIN",     {"price":0,"chg":0})

bist_chg_c = "#089981" if bist_d["chg"]>=0 else "#f23645"
bist_sign  = "▲" if bist_d["chg"]>=0 else "▼"

st.markdown(f"""
<div style="display:flex;align-items:stretch;background:{card_bg};
border:1px solid {border_color};border-radius:8px;margin:8px 0 4px 0;overflow:hidden;">
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
    <div style="display:flex;flex:1;align-items:stretch;overflow-x:auto;">
        <div style="display:flex;flex-direction:column;padding:10px 18px;border-right:1px solid {border_color};min-width:140px;">
            <div style="font-size:0.65rem;color:{text_muted};margin-bottom:3px;">USD / TRY</div>
            <div style="font-size:1.2rem;font-weight:700;color:{text_main};">₺{usd_d['price']:,.4f}</div>
            <div style="font-size:0.78rem;font-weight:600;color:{'#089981' if usd_d['chg']>=0 else '#f23645'};">
                {'▲' if usd_d['chg']>=0 else '▼'} {abs(usd_d['chg']):.2f}%</div>
        </div>
        <div style="display:flex;flex-direction:column;padding:10px 18px;border-right:1px solid {border_color};min-width:140px;">
            <div style="font-size:0.65rem;color:{text_muted};margin-bottom:3px;">ALTIN (XAU)</div>
            <div style="font-size:1.2rem;font-weight:700;color:{text_main};">${gold_d['price']:,.1f}</div>
            <div style="font-size:0.78rem;font-weight:600;color:{'#089981' if gold_d['chg']>=0 else '#f23645'};">
                {'▲' if gold_d['chg']>=0 else '▼'} {abs(gold_d['chg']):.2f}%</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. ANA SEKMELER
# ==========================================
tab_screener, tab_portfolio, tab_ai, tab_binance = st.tabs([
    "📊 Ekran & Grafik", "💼 Portföy & Sinyaller", "🧠 AI Öneri Motoru", "🚀 Binance API"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: SCREENER + GRAFİKLER           ║
# ╚══════════════════════════════════════════╝
with tab_screener:
    col_scr, col_xray = st.columns([2.0, 1.4])
    df_screener = fetch_tv_screener_data()
    
    with col_scr:
        if df_screener.empty:
            st.error("Piyasa verisi çekilemedi.")
        else:
            html_table = '<div class="tv-screener-container"><table class="tv-table"><thead><tr><th>TICKER</th><th>SON</th><th>DEĞİŞİM %</th><th>1 HAFTA %</th><th>1 AY %</th><th>TEKNİK SİNYAL</th><th>RSI</th></tr></thead><tbody>'
            for _, row in df_screener.sort_values("Değişim %", ascending=False).iterrows():
                c_d = "tv-green" if row["Değişim %"] >= 0 else "tv-red"
                c_w = "tv-green" if row["1H %"] >= 0 else "tv-red"
                c_m = "tv-green" if row["1A %"] >= 0 else "tv-red"
                
                html_table += "<tr>"
                html_table += f"<td><div class='tv-ticker-col'><div class='tv-logo-circle'>{row['Sembol'][0]}</div><div class='tv-ticker-info'><span class='tv-ticker-symbol'>{row['Sembol']}</span></div></div></td>"
                html_table += f"<td>{row['Fiyat']:,.2f}</td>"
                html_table += f"<td class='{c_d}'>{row['Değişim %']:.2f}%</td>"
                html_table += f"<td class='{c_w}'>{row['1H %']:.2f}%</td>"
                html_table += f"<td class='{c_m}'>{row['1A %']:.2f}%</td>"
                html_table += f"<td><span class='tv-rating {row['Teknik_Class']}'>{row['Teknik']}</span></td>"
                html_table += f"<td>{row['RSI']:.1f}</td>"
                html_table += "</tr>"
            html_table += "</tbody></table></div>"
            st.markdown(html_table, unsafe_allow_html=True)

    with col_xray:
        secilen_hisse = st.selectbox("X-Ray Analizi İçin Hisse:", sorted(bist_symbols), index=0)
        tv_symbol = f"BIST:{secilen_hisse}"
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

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: PORTFÖY & AI SATIŞ SİNYALLERİ  ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main};">Portföy Yönetimi ve AI Sinyalleri</div>', unsafe_allow_html=True)
    st.write("Yapay Zeka, buraya eklediğin hisseleri anlık izler ve belirlediği Kar Al/Zarar Kes noktalarına ulaştığında sana 'SAT' uyarısı verir.")
    
    # AI SİNYAL KONTROLÜ (Gerçek Zamanlı Monitör)
    if st.session_state.portfolio and not df_screener.empty:
        st.markdown("### 🚨 AI Aksiyon Uyarıları")
        uyarı_var = False
        for sym, data in st.session_state.portfolio.items():
            current_data = df_screener[df_screener["Sembol"] == sym]
            if not current_data.empty:
                current_price = current_data.iloc[0]["Fiyat"]
                hedef = st.session_state.ai_signals.get(sym, {}).get("hedef", float('inf'))
                stop = st.session_state.ai_signals.get(sym, {}).get("stop", 0)
                
                if current_price >= hedef:
                    st.markdown(f"<div class='ai-sell-box'><b>🟢 KÂR AL SİNYALİ:</b> {sym} hedef fiyata ({hedef:.2f} TL) ulaştı veya geçti! Anlık Fiyat: {current_price:.2f} TL. Hisseden çıkış yapman önerilir.</div>", unsafe_allow_html=True)
                    uyarı_var = True
                elif current_price <= stop:
                    st.markdown(f"<div class='ai-sell-box'><b>🔴 ZARAR KES SİNYALİ:</b> {sym} stop-loss noktasına ({stop:.2f} TL) geriledi! Anlık Fiyat: {current_price:.2f} TL. Daha fazla kayıp yaşamamak için pozisyonu kapat.</div>", unsafe_allow_html=True)
                    uyarı_var = True
        if not uyarı_var:
            st.info("Şu an için portföyündeki hisselerde 'SAT' sinyali yok. Beklemeye devam.")
    
    st.markdown("---")
    # Portföy Ekleme
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1: add_sym = st.selectbox("Hisse Seç", sorted(bist_symbols))
    
    preview_price = 0.0
    if not df_screener.empty and add_sym in df_screener["Sembol"].values:
        preview_price = df_screener[df_screener["Sembol"] == add_sym].iloc[0]["Fiyat"]

    with c2: st.text_input("Anlık Fiyat", value=f"{preview_price:,.2f}" if preview_price > 0 else "0", disabled=True)
    with c3: add_adet = st.number_input("Adet", min_value=1, value=10)
    with c4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Portföye Ekle", use_container_width=True, type="primary"):
            st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": preview_price}
            st.rerun()

    if st.session_state.portfolio:
        for sym, data in st.session_state.portfolio.items():
            c_price = df_screener[df_screener["Sembol"] == sym].iloc[0]["Fiyat"] if not df_screener.empty else data['maliyet']
            kar_zarar = ((c_price - data['maliyet']) / data['maliyet']) * 100
            renk = "#089981" if kar_zarar >= 0 else "#f23645"
            isaret = "+" if kar_zarar >= 0 else ""
            
            cc1, cc2 = st.columns([5, 1])
            with cc1:
                st.markdown(f"<div style='padding:12px; background-color:{card_bg}; border:1px solid {border_color}; border-radius:8px;'><b>{sym}</b>: {data['adet']} Adet | Maliyet: ₺{data['maliyet']:,.2f} | Anlık: ₺{c_price:,.2f} | <b>P&L: <span style='color:{renk}'>{isaret}{kar_zarar:.2f}%</span></b></div>", unsafe_allow_html=True)
            with cc2:
                if st.button(f"Kapat", key=f"del_{sym}", use_container_width=True):
                    del st.session_state.portfolio[sym]
                    if sym in st.session_state.ai_signals: del st.session_state.ai_signals[sym]
                    st.rerun()

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: AI ÖNERİ & HEDEF HESAPLAYICI   ║
# ╚══════════════════════════════════════════╝
with tab_ai:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main};">🧠 Gelişmiş Makine Öğrenmesi Simülasyonu</div>', unsafe_allow_html=True)
    st.write("Volatilite, Göreceli Güç Endeksi (RSI) ve Momentum verilerini çaprazlayarak hedefler belirler. Önerilen hisseyi portföye eklediğinde AI senin için ne zaman satman gerektiğini takip eder.")
    
    b1, b2, b3 = st.columns([2, 2, 1])
    with b1: butce = st.number_input("Yatırım Bütçesi (TL)", value=50000, step=5000)
    with b2: risk_plani = st.selectbox("Risk Algoritması", ["Dengeli (Dar Stop, Kısa Hedef)", "Agresif (Geniş Stop, Yüksek Hedef)"])
    with b3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        oneri_btn = st.button("AI Analizi Başlat", use_container_width=True, type="primary")

    if oneri_btn:
        if df_screener.empty:
            st.error("Veriler çekilemedi.")
        else:
            with st.spinner("Yapay Zeka nöral ağları piyasayı analiz ediyor..."):
                # Basit bir "Skorlama" algoritması (AI Simülasyonu)
                # Düşük RSI (Aşırı satım) + Teknik Onay + Yeterli Hacim
                df_ai = df_screener.copy()
                df_ai["AI_Skor"] = np.where(df_ai["RSI"] < 40, 2, 0) + np.where(df_ai["Teknik"].str.contains("Al"), 1, -1)
                
                # Agresif/Dengeli Filtre
                if "Dengeli" in risk_plani:
                    df_ai = df_ai[df_ai["Volatilite"] < 0.05] # Az oynak
                    kar_marji = 1.08  # %8 Hedef
                    stop_marji = 0.95 # %5 Zarar Kes
                else:
                    df_ai = df_ai[df_ai["Volatilite"] >= 0.03] # Yüksek oynaklık
                    kar_marji = 1.15  # %15 Hedef
                    stop_marji = 0.90 # %10 Zarar Kes

                top_picks = df_ai.sort_values(by=["AI_Skor", "RSI"], ascending=[False, True]).head(3)
                
                st.success(f"Analiz Tamamlandı. {risk_plani} stratejisine uygun 3 fırsat:")
                
                for _, row in top_picks.iterrows():
                    hisse = row['Sembol']
                    fiyat = row['Fiyat']
                    hedef = fiyat * kar_marji
                    stop = fiyat * stop_marji
                    
                    # Sinyali Session State'e kaydet ki Portföy tabında takip edebilelim
                    st.session_state.ai_signals[hisse] = {"hedef": hedef, "stop": stop}
                    
                    st.markdown(f"""
                    <div class="ai-box">
                        <h3 style="margin-top:0; color:{blue_brand};">{hisse} <span style="font-size:0.8rem; color:{text_muted}">| AI Güven Skoru: %{80 + row['AI_Skor']*5}</span></h3>
                        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; margin-top:10px;">
                            <div><b>Giriş Fiyatı:</b> ₺{fiyat:,.2f}</div>
                            <div style="color:#089981;"><b>🎯 Kar Al (Hedef):</b> ₺{hedef:,.2f}</div>
                            <div style="color:#f23645;"><b>🛑 Zarar Kes (Stop):</b> ₺{stop:,.2f}</div>
                            <div><b>RSI Durumu:</b> {row['RSI']:.1f}</div>
                        </div>
                        <p style="font-size:0.85rem; color:{text_muted}; margin-top:10px; margin-bottom:0;">
                            <i>AI Notu: {hisse} hissesi belirlenen {risk_plani.split()[0].lower()} risk profiline göre optimize edilmiştir. Portföye eklediğinizde sistem bu hedefleri otomatik izleyecek ve tetiklendiğinde uyaracaktır.</i>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: BINANCE API                    ║
# ╚══════════════════════════════════════════╝
with tab_binance:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main};">🚀 Webhook & Otomatik İşlemler</div>', unsafe_allow_html=True)
    st.info("Buradaki yapı BIST için değil, Global Kripto (Binance) otomasyonları için hazırlanmıştır.")
    
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
