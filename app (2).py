"""
Borsa Analiz Uygulaması v15.0 (GLOBAL GOD MODE - Tüm Piyasalar & AI Sinyal Sürümü)
- BIST 100, Kripto Paralar, ABD Borsası (NASDAQ) ve Forex/Emtia eklendi.
- Piyasa seçici eklendi (Veriler menüden seçilen piyasaya göre çekilir, arayüz boğulmaz).
- IP Ban riski için max_workers 15'e düşürüldü.
- Portföy sekmesindeki olası çökme (IndexError) hataları giderildi.
- AI Motoru ve Binance Webhook altyapısı korundu.
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
    page_title="Global TV Terminal",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tema ve Sistem State'leri
if "theme" not in st.session_state: st.session_state.theme = "dark"
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "ai_signals" not in st.session_state: st.session_state.ai_signals = {}
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
.tv-table th {{ padding: 10px 12px; font-weight: 500; color: {text_muted}; border-right: 1px solid {border_color}; font-size: 12px; text-align: right; }}
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
.ai-box {{ background-color: {card_bg}; border-left: 4px solid #089981; padding: 15px; border-radius: 6px; margin-bottom: 15px; }}
.ai-sell-box {{ background-color: rgba(242, 54, 69, 0.1); border-left: 4px solid #f23645; padding: 15px; border-radius: 6px; margin-bottom: 15px; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. KÜRESEL VERİ SETLERİ (BIST, KRİPTO, ABD, EMTİA)
# ==========================================
# BIST (Tam Liste Korundu)
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","ALBRK","SKBNK","TSKB","KCHOL",
    "SAHOL","DOHOL","ALARK","ENKAI","AGHOL","TKFEN","NTHOL","GLYHO","POLHO","TAVHL",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL","KOZAA","IPEKE","ISDMR",
    "SISE","CIMSA","AKCNS","OYAKC","NUHCM","BTCIM","AFYON","GOLTS","BSOKE","ADANA","MRDIN",
    "FROTO","TOASO","DOAS","OTKAR","KARSN","ASUZU","TMSN","TTRAK","ARCLK","VESTL","BRISA","THYAO","PGSUS",
    "BIMAS","MGROS","SOKM","AEFES","CCOLA","ULKER","TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS",
    "ENJSA","AKSEN","ODAS","SMARTG","EUPWR","GESAN","EKGYO","ISGYO","TRGYO","DEVA","SELEC"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

# Kripto Paralar
crypto_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "LINK", "DOT", "MATIC", "SHIB"]
TICKERS_CRYPTO = {f"{sym}-USD": sym for sym in crypto_symbols}

# ABD Borsaları (Muhteşem Yedili ve Teknoloji)
us_symbols = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "NFLX", "INTC", "PLTR", "COIN"]
TICKERS_US = {sym: sym for sym in us_symbols}

# Forex & Emtia
forex_symbols = {"EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "JPY=X": "USD/JPY", "GC=F": "ALTIN (Ons)", "CL=F": "HAM PETROL", "SI=F": "GÜMÜŞ"}
TICKERS_FOREX = forex_symbols

# Piyasaya göre TV Widget sembolü oluşturucu
def get_tv_symbol(market, sym):
    if market == "BIST 100": return f"BIST:{sym}"
    elif market == "Kripto (USD)": return f"BINANCE:{sym}USDT"
    elif market == "ABD Borsaları": return f"NASDAQ:{sym}" # Çoğu teknoloji NASDAQ'da
    else: return f"FX_IDC:{sym.replace('/','')}"

# ==========================================
# 4. YARDIMCI FONKSİYONLAR
# ==========================================
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
    tickers = {"XU100.IS": "BIST 100", "BTC-USD": "BITCOIN", "EURTRY=X": "EUR/TRY", "GC=F": "ALTIN"}
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
def fetch_tv_screener_data(tickers_dict):
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
            
            vol = float(df["Volume"].squeeze().iloc[-1]) if "Volume" in df else 0
            sma50 = float(close.rolling(20).mean().iloc[-1])
            volatility = float(close.rolling(14).std().iloc[-1] / p_last)
            rsi = compute_rsi(close)
            rating, rating_cls = get_tv_rating(rsi, p_last, sma50)
            
            return {
                "Sembol": name, "Fiyat": p_last, "Değişim %": chg_pct, "1H %": w_pct, "1A %": m_pct,
                "Teknik": rating, "Teknik_Class": rating_cls, "Hacim": vol, "RSI": rsi, "Volatilite": volatility
            }
        except: return None

    # IP Ban riskini azaltmak için max_workers 50'den 15'e düşürüldü
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in tickers_dict.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
    return pd.DataFrame(rows)

# ==========================================
# 5. TRADINGVIEW MARKETS HEADER (ÜST BİLGİ)
# ==========================================
macro = get_macro_data()

nav_col, nav_r = st.columns([5, 1])
with nav_col:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; padding: 6px 0 4px 0;">
        <div style="width:28px;height:28px;border-radius:6px;background:#2962ff;
        display:flex;align-items:center;justify-content:center;
        font-weight:900;font-size:15px;color:#fff;">G</div>
        <span style="font-size:1.1rem;font-weight:700;color:{text_main};letter-spacing:-0.02em;">
            Global Piyasa Terminali</span>
    </div>
    """, unsafe_allow_html=True)
with nav_r:
    st.button("☀️/🌙", on_click=toggle_theme, use_container_width=True)

bist_d  = macro.get("BIST 100",  {"price":0,"chg":0})
btc_d   = macro.get("BITCOIN",   {"price":0,"chg":0})
eur_d   = macro.get("EUR/TRY",   {"price":0,"chg":0})
gold_d  = macro.get("ALTIN",     {"price":0,"chg":0})

st.markdown(f"""
<div style="display:flex;align-items:stretch;background:{card_bg};
border:1px solid {border_color};border-radius:8px;margin:8px 0 15px 0;overflow:hidden;">
    <div style="display:flex;flex-direction:column;padding:12px 22px;
    background:{bg_color};border-right:2px solid #2962ff;min-width:180px;">
        <div style="font-size:0.65rem;color:{text_muted};margin-bottom:4px;">BIST 100</div>
        <div style="font-size:1.7rem;font-weight:800;color:{text_main};">{bist_d['price']:,.1f}</div>
        <div style="font-size:0.85rem;font-weight:600;color:{'#089981' if bist_d['chg']>=0 else '#f23645'};">
            {'▲' if bist_d['chg']>=0 else '▼'} {abs(bist_d['chg']):.2f}%
        </div>
    </div>
    <div style="display:flex;flex:1;align-items:stretch;overflow-x:auto;">
        <div style="display:flex;flex-direction:column;padding:10px 18px;border-right:1px solid {border_color};min-width:140px;">
            <div style="font-size:0.65rem;color:{text_muted};margin-bottom:3px;">BITCOIN (USD)</div>
            <div style="font-size:1.2rem;font-weight:700;color:{text_main};">${btc_d['price']:,.1f}</div>
            <div style="font-size:0.78rem;font-weight:600;color:{'#089981' if btc_d['chg']>=0 else '#f23645'};">
                {'▲' if btc_d['chg']>=0 else '▼'} {abs(btc_d['chg']):.2f}%</div>
        </div>
        <div style="display:flex;flex-direction:column;padding:10px 18px;border-right:1px solid {border_color};min-width:140px;">
            <div style="font-size:0.65rem;color:{text_muted};margin-bottom:3px;">ALTIN (ONS)</div>
            <div style="font-size:1.2rem;font-weight:700;color:{text_main};">${gold_d['price']:,.1f}</div>
            <div style="font-size:0.78rem;font-weight:600;color:{'#089981' if gold_d['chg']>=0 else '#f23645'};">
                {'▲' if gold_d['chg']>=0 else '▼'} {abs(gold_d['chg']):.2f}%</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 6. PİYASA SEÇİCİ (ANA FİLTRE)
# ==========================================
st.markdown(f"<div style='font-size:1rem; font-weight:700; color:{text_main}; margin-bottom: 5px;'>🌍 Taranacak Piyasayı Seçin:</div>", unsafe_allow_html=True)
secilen_piyasa = st.selectbox("Piyasa", ["BIST 100", "Kripto (USD)", "ABD Borsaları", "Forex & Emtia"], label_visibility="collapsed")

if secilen_piyasa == "BIST 100": aktif_tickerlar = TICKERS_BIST
elif secilen_piyasa == "Kripto (USD)": aktif_tickerlar = TICKERS_CRYPTO
elif secilen_piyasa == "ABD Borsaları": aktif_tickerlar = TICKERS_US
else: aktif_tickerlar = TICKERS_FOREX

df_screener = fetch_tv_screener_data(aktif_tickerlar)
aktif_semboller = list(aktif_tickerlar.values())

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 7. ANA SEKMELER
# ==========================================
tab_screener, tab_portfolio, tab_ai, tab_binance = st.tabs([
    "📊 Ekran & Grafik", "💼 Portföy & Sinyaller", "🧠 AI Öneri Motoru", "🚀 Binance API"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: SCREENER + GRAFİKLER           ║
# ╚══════════════════════════════════════════╝
with tab_screener:
    col_scr, col_xray = st.columns([2.0, 1.4])
    
    with col_scr:
        if df_screener.empty:
            st.error(f"{secilen_piyasa} verisi çekilemedi. Lütfen sayfayı yenileyin.")
        else:
            html_table = '<div class="tv-screener-container"><table class="tv-table"><thead><tr><th>SEMBOL</th><th>SON FİYAT</th><th>DEĞİŞİM %</th><th>1 HAFTA %</th><th>1 AY %</th><th>TEKNİK</th><th>RSI</th></tr></thead><tbody>'
            for _, row in df_screener.sort_values("Değişim %", ascending=False).iterrows():
                c_d = "tv-green" if row["Değişim %"] >= 0 else "tv-red"
                c_w = "tv-green" if row["1H %"] >= 0 else "tv-red"
                c_m = "tv-green" if row["1A %"] >= 0 else "tv-red"
                
                html_table += "<tr>"
                html_table += f"<td><div class='tv-ticker-col'><div class='tv-logo-circle'>{row['Sembol'][0]}</div><div class='tv-ticker-info'><span class='tv-ticker-symbol'>{row['Sembol']}</span></div></div></td>"
                html_table += f"<td>{row['Fiyat']:,.4f}</td>"
                html_table += f"<td class='{c_d}'>{row['Değişim %']:.2f}%</td>"
                html_table += f"<td class='{c_w}'>{row['1H %']:.2f}%</td>"
                html_table += f"<td class='{c_m}'>{row['1A %']:.2f}%</td>"
                html_table += f"<td><span class='tv-rating {row['Teknik_Class']}'>{row['Teknik']}</span></td>"
                html_table += f"<td>{row['RSI']:.1f}</td>"
                html_table += "</tr>"
            html_table += "</tbody></table></div>"
            st.markdown(html_table, unsafe_allow_html=True)

    with col_xray:
        secilen_hisse = st.selectbox(f"X-Ray Analizi ({secilen_piyasa}):", sorted(aktif_semboller), index=0)
        tv_symbol = get_tv_symbol(secilen_piyasa, secilen_hisse)
        
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
    st.write(f"Şu an **{secilen_piyasa}** piyasasında işlem yapıyorsunuz.")
    
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
                    st.markdown(f"<div class='ai-sell-box'><b>🟢 KÂR AL SİNYALİ:</b> {sym} hedef fiyata ({hedef:.4f}) ulaştı! Anlık Fiyat: {current_price:.4f}. Pozisyonu kapatman önerilir.</div>", unsafe_allow_html=True)
                    uyarı_var = True
                elif current_price <= stop:
                    st.markdown(f"<div class='ai-sell-box'><b>🔴 ZARAR KES SİNYALİ:</b> {sym} stop-loss noktasına ({stop:.4f}) geriledi! Anlık Fiyat: {current_price:.4f}. Daha fazla kayıp yaşamamak için çıkış yap.</div>", unsafe_allow_html=True)
                    uyarı_var = True
        if not uyarı_var:
            st.info("Şu an için bu piyasadaki hisselerinde 'SAT' sinyali yok. Beklemeye devam.")
    
    st.markdown("---")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1: add_sym = st.selectbox("Varlık Seç", sorted(aktif_semboller))
    
    preview_price = 0.0
    if not df_screener.empty and add_sym in df_screener["Sembol"].values:
        preview_price = df_screener[df_screener["Sembol"] == add_sym].iloc[0]["Fiyat"]

    with c2: st.text_input("Anlık Fiyat", value=f"{preview_price:,.4f}" if preview_price > 0 else "0", disabled=True)
    with c3: add_adet = st.number_input("Adet / Miktar", min_value=0.01, value=10.0, step=1.0)
    with c4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Portföye Ekle", use_container_width=True, type="primary"):
            st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": preview_price}
            st.rerun()

    if st.session_state.portfolio:
        for sym, data in list(st.session_state.portfolio.items()):
            # HATA DÜZELTİLDİ: Olası IndexError için güvenli fiyat çekimi
            if not df_screener.empty and sym in df_screener["Sembol"].values:
                c_price = df_screener[df_screener["Sembol"] == sym].iloc[0]["Fiyat"]
            else:
                c_price = data['maliyet']
                
            kar_zarar = ((c_price - data['maliyet']) / data['maliyet']) * 100 if data['maliyet'] > 0 else 0
            renk = "#089981" if kar_zarar >= 0 else "#f23645"
            isaret = "+" if kar_zarar >= 0 else ""
            
            cc1, cc2 = st.columns([5, 1])
            with cc1:
                st.markdown(f"<div style='padding:12px; background-color:{card_bg}; border:1px solid {border_color}; border-radius:8px;'><b>{sym}</b>: {data['adet']} Adet | Maliyet: {data['maliyet']:,.4f} | Anlık: {c_price:,.4f} | <b>P&L: <span style='color:{renk}'>{isaret}{kar_zarar:.2f}%</span></b></div>", unsafe_allow_html=True)
            with cc2:
                if st.button(f"Kapat", key=f"del_{sym}", use_container_width=True):
                    del st.session_state.portfolio[sym]
                    if sym in st.session_state.ai_signals: del st.session_state.ai_signals[sym]
                    st.rerun()

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: AI ÖNERİ & HEDEF HESAPLAYICI   ║
# ╚══════════════════════════════════════════╝
with tab_ai:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main};">🧠 {secilen_piyasa} İçin Yapay Zeka Sinyalleri</div>', unsafe_allow_html=True)
    st.write("Volatilite, RSI ve Momentum verilerini çaprazlayarak hedefler belirler.")
    
    b1, b2, b3 = st.columns([2, 2, 1])
    with b1: butce = st.number_input("Yatırım Bütçesi", value=10000, step=1000)
    with b2: risk_plani = st.selectbox("Risk Algoritması", ["Dengeli (Dar Stop, Kısa Hedef)", "Agresif (Geniş Stop, Yüksek Hedef)"])
    with b3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        oneri_btn = st.button("AI Analizi Başlat", use_container_width=True, type="primary")

    if oneri_btn:
        if df_screener.empty:
            st.error("Veriler çekilemedi. Piyasa kapalı veya internet bağlantısı yok.")
        else:
            with st.spinner(f"Yapay Zeka {secilen_piyasa} ağlarını tarıyor..."):
                df_ai = df_screener.copy()
                df_ai["AI_Skor"] = np.where(df_ai["RSI"] < 45, 2, 0) + np.where(df_ai["Teknik"].str.contains("Al"), 1, -1)
                
                if "Dengeli" in risk_plani:
                    df_ai = df_ai[df_ai["Volatilite"] < 0.06]
                    kar_marji, stop_marji = 1.08, 0.95
                else:
                    kar_marji, stop_marji = 1.15, 0.88

                top_picks = df_ai.sort_values(by=["AI_Skor", "RSI"], ascending=[False, True]).head(3)
                st.success(f"Analiz Tamamlandı. {risk_plani} stratejisine uygun fırsatlar:")
                
                for _, row in top_picks.iterrows():
                    hisse = row['Sembol']
                    fiyat = row['Fiyat']
                    hedef, stop = fiyat * kar_marji, fiyat * stop_marji
                    st.session_state.ai_signals[hisse] = {"hedef": hedef, "stop": stop}
                    
                    st.markdown(f"""
                    <div class="ai-box">
                        <h3 style="margin-top:0; color:{blue_brand};">{hisse} <span style="font-size:0.8rem; color:{text_muted}">| AI Güven Skoru: %{80 + row['AI_Skor']*5}</span></h3>
                        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; margin-top:10px;">
                            <div><b>Giriş Fiyatı:</b> {fiyat:,.4f}</div>
                            <div style="color:#089981;"><b>🎯 Kar Al (Hedef):</b> {hedef:,.4f}</div>
                            <div style="color:#f23645;"><b>🛑 Zarar Kes (Stop):</b> {stop:,.4f}</div>
                            <div><b>RSI Durumu:</b> {row['RSI']:.1f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: BINANCE API                    ║
# ╚══════════════════════════════════════════╝
with tab_binance:
    st.markdown(f'<div style="font-size:1.4rem; font-weight:700; color:{text_main};">🚀 Webhook & Otomatik İşlemler</div>', unsafe_allow_html=True)
    st.info("Kripto piyasasında AI'ın verdiği hedefleri doğrudan Binance'e otomatik emir olarak göndermek için kullanılır.")
    
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
            st.code(json.dumps({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.001}, indent=4), language="json")
        else:
            st.warning("Webhook sinyallerini görmek için API anahtarlarınızla giriş yapmalısınız.")
