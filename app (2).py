"""
Burak Borsa Analiz Uygulaması v11.0 (THE ULTIMATE TRADINGVIEW CLONE)
- Kusursuz Gece/Gündüz (Light/Dark) TV Teması Entegrasyonu
- 'Burada henüz veri yok' Hatası (TV Widget Uyumu) Giderildi
- Tam İnteraktif Profesyonel Çizim Grafiği (Advanced Chart) Gömdük
- 52 Hafta Zirve/Dip, YTD Performans gibi Ekstra Screener Sütunları
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Burak Borsa Terminali",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tema ve diğer state'ler
if "theme" not in st.session_state:
    st.session_state.theme = "dark" # Varsayılan karanlık mod
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "binance_connected" not in st.session_state:
    st.session_state.binance_connected = False
if "binance_mode" not in st.session_state:
    st.session_state.binance_mode = "Testnet"

def toggle_theme():
    if st.session_state.theme == "dark":
        st.session_state.theme = "light"
    else:
        st.session_state.theme = "dark"

# ==========================================
# 2. DİNAMİK TRADINGVIEW CSS (LIGHT & DARK)
# ==========================================
# Tema değişkenlerini TV'nin orijinal Hex kodlarıyla ayarlıyoruz
if st.session_state.theme == "dark":
    bg_color = "#131722"
    card_bg = "#1e222d"
    text_main = "#d1d4dc"
    text_muted = "#787b86"
    border_color = "#2a2e39"
    row_hover = "#2a2e39"
    blue_brand = "#2962ff"
    tv_theme_str = "dark"
else:
    bg_color = "#ffffff"
    card_bg = "#f0f3fa"
    text_main = "#131722"
    text_muted = "#787b86"
    border_color = "#e0e3eb"
    row_hover = "#f0f3fa"
    blue_brand = "#2962ff"
    tv_theme_str = "light"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Trebuchet+MS:ital,wght@0,400;0,700;1,400;1,700&display=swap');

html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif !important;
    background-color: {bg_color} !important; 
    color: {text_main} !important;
}}
[data-testid="collapsedControl"] {{ display: none; }}
section[data-testid="stSidebar"] {{ display: none; }}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {card_bg}; }}
::-webkit-scrollbar-thumb {{ background: {text_muted}; border-radius: 3px; }}

/* SCREENER TABLOSU */
.tv-screener-container {{
    width: 100%; height: 75vh; overflow-y: auto; overflow-x: auto;
    background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 4px;
}}
.tv-table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: right; white-space: nowrap; }}
.tv-table thead {{ position: sticky; top: 0; z-index: 2; background-color: {card_bg}; box-shadow: 0 1px 0 {border_color}; }}
.tv-table th {{ padding: 10px 12px; font-weight: 500; color: {text_muted}; border-right: 1px solid {border_color}; font-size: 12px; }}
.tv-table th:first-child {{ text-align: left; }}
.tv-table tbody tr {{ border-bottom: 1px solid {border_color}; background-color: {bg_color}; transition: 0.1s; }}
.tv-table tbody tr:hover {{ background-color: {row_hover}; }}
.tv-table td {{ padding: 8px 12px; color: {text_main}; vertical-align: middle; }}
.tv-table td:first-child {{ text-align: left; }}

.tv-ticker-col {{ display: flex; align-items: center; gap: 12px; }}
.tv-logo-circle {{
    width: 28px; height: 28px; border-radius: 50%; background-color: {blue_brand};
    color: #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px; flex-shrink: 0;
}}
.tv-ticker-info {{ display: flex; flex-direction: column; justify-content: center; }}
.tv-ticker-symbol {{ color: {blue_brand}; font-weight: 600; font-size: 14px; text-decoration: none; }}
.tv-ticker-desc {{ color: {text_muted}; font-size: 11px; margin-top: 2px; }}

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
# 3. YARDIMCI FONKSİYONLAR & TV UYUMLU LİSTE
# ==========================================
# "Henüz veri yok" hatasını önlemek için TradingView'un kesin desteklediği BIST100 ana tahtaları
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","KCHOL","SAHOL","DOHOL","ALARK","ENKAI",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL","SISE","CIMSA",
    "FROTO","TOASO","DOAS","OTKAR","ARCLK","VESTL","THYAO","PGSUS","BIMAS","MGROS",
    "SOKM","AEFES","CCOLA","TCELL","TTKOM","ASELS","ASTOR","KONTR","ENJSA","AKSEN"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

def format_volume(vol):
    if vol >= 1_000_000_000: return f"{vol/1_000_000_000:.3f}B"
    if vol >= 1_000_000: return f"{vol/1_000_000:.3f}M"
    if vol >= 1_000: return f"{vol/1_000:.3f}K"
    return str(vol)

def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain / loss.replace(0, np.nan)
        val   = (100 - (100 / (1 + rs))).iloc[-1]
        return round(float(val), 1) if pd.notna(val) else np.nan
    except: return np.nan

def compute_macd(series):
    try:
        ema_12 = series.ewm(span=12, adjust=False).mean()
        ema_26 = series.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        sig = macd.ewm(span=9, adjust=False).mean()
        return float(macd.iloc[-1]), float(sig.iloc[-1]), float((macd - sig).iloc[-1])
    except: return np.nan, np.nan, np.nan

def get_tv_rating(rsi, curr_p, sma50, macd_hist):
    score = 0
    if pd.notna(rsi):
        if rsi > 70: score -= 2
        elif rsi < 30: score += 2
        elif rsi > 60: score -= 1
        elif rsi < 40: score += 1
    if curr_p > sma50: score += 1
    else: score -= 1
    if pd.notna(macd_hist):
        if macd_hist > 0: score += 1
        else: score -= 1

    if score >= 3: return "Güçlü Al", "rating-strong-buy"
    if score > 0: return "Al", "rating-buy"
    if score <= -3: return "Güçlü Sat", "rating-strong-sell"
    if score < 0: return "Sat", "rating-sell"
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

@st.cache_data(ttl=600, show_spinner=True)
def fetch_tv_screener_data():
    end = datetime.today()
    # 52 Hafta (1 yıl) verisini çekerek TV'yi tam simüle ediyoruz
    start = end - timedelta(days=365)
    rows = []
    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 50: return None
            
            close = df["Close"].squeeze()
            volume = df["Volume"].squeeze()
            
            price = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            chg_val = price - prev
            chg_pct = (chg_val / prev) * 100
            
            vol = float(volume.iloc[-1])
            avg_vol = float(volume.rolling(20).mean().iloc[-1])
            rel_vol = (vol / avg_vol) if avg_vol > 0 else 0
            
            high_52 = float(close.max())
            low_52 = float(close.min())
            
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            _, _, macd_h = compute_macd(close)
            
            rating, rating_cls = get_tv_rating(rsi, price, sma50, macd_h)
            
            return {
                "Sembol": name, "Fiyat": price, "Değişim %": chg_pct, "Değişim": chg_val,
                "Teknik": rating, "Teknik_Class": rating_cls, "Hacim": vol, "Göreceli Hacim": rel_vol, 
                "RSI": rsi, "52H Yüksek": high_52, "52H Düşük": low_52
            }
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            if f.result(): rows.append(f.result())
    return pd.DataFrame(rows)

# ==========================================
# 4. ÜST BAR & TEMA BUTONU
# ==========================================
header_col, theme_col, macro_col = st.columns([1.5, 0.5, 3])

with header_col:
    st.markdown(f'<div style="font-size:1.8rem; font-weight:700; color:{text_main}; display:flex; align-items:center; gap:10px;"><span style="color:#2962ff;">B</span> Terminal v11.0</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.75rem; color:#089981;">⚡ THE ULTIMATE SÜRÜM (LIGHT/DARK)</div>', unsafe_allow_html=True)

with theme_col:
    st.markdown("<br>", unsafe_allow_html=True)
    theme_icon = "☀️ Gündüz Modu" if st.session_state.theme == "dark" else "🌙 Gece Modu"
    st.button(theme_icon, on_click=toggle_theme, use_container_width=True)

with macro_col:
    macro = get_macro_data()
    cols = st.columns(4)
    for i, name in enumerate(["BIST 100", "USD/TRY", "EUR/TRY", "ALTIN"]):
        data = macro.get(name, {"price": 0, "chg": 0})
        val = data["price"]
        chg = data["chg"]
        color = "#089981" if chg >= 0 else "#f23645"
        sign = "+" if chg >= 0 else ""
        fmt = f"{val:,.0f}" if name == "BIST 100" else f"{val:,.2f}"
        
        cols[i].markdown(f"""
        <div class="macro-box">
            <div class="macro-title">{name}</div>
            <div class="macro-val">{fmt}</div>
            <div class="macro-chg" style="color:{color};">{sign}{chg:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"<hr style='border-color: {border_color}; margin: 1rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. ANA EKRAN (BÖLÜNMÜŞ YAPI)
# ==========================================
# Ekranı ikiye bölüyoruz: Sol %60 Tarayıcı, Sağ %40 Özel X-Ray ve İleri Düzey Grafikler
col_screener, col_xray = st.columns([2.0, 1.4])

# --- SOL PANEL: DEV TABLO ---
with col_screener:
    st.markdown(f'<div style="font-size:1.2rem; font-weight:600; color:{text_main}; margin-bottom:10px;">Hisse Takipçisi (Screener)</div>', unsafe_allow_html=True)
    
    df_screener = fetch_tv_screener_data()
    
    if df_screener.empty:
        st.error("Veri çekilemedi.")
    else:
        html_table = """
        <div class="tv-screener-container">
            <table class="tv-table">
                <thead>
                    <tr>
                        <th>TICKER</th>
                        <th>SON</th>
                        <th>DEĞİŞİM %</th>
                        <th>TEKNİK SİNYAL</th>
                        <th>HACİM</th>
                        <th>52H YÜKSEK</th>
                        <th>52H DÜŞÜK</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in df_screener.sort_values("Değişim %", ascending=False).iterrows():
            c_class = "tv-green" if row["Değişim %"] >= 0 else "tv-red"
            sign = "+" if row["Değişim %"] >= 0 else ""
            first_letter = row["Sembol"][0]
            
            html_table += "<tr>"
            # Ticker Kolonu
            html_table += f"""
            <td>
                <div class="tv-ticker-col">
                    <div class="tv-logo-circle">{first_letter}</div>
                    <div class="tv-ticker-info">
                        <span class="tv-ticker-symbol">{row['Sembol']}</span>
                    </div>
                </div>
            </td>
            """
            html_table += f"<td>{row['Fiyat']:,.2f}</td>"
            html_table += f"<td class='{c_class}'>{sign}{row['Değişim %']:.2f}%</td>"
            html_table += f"<td><span class='tv-rating {row['Teknik_Class']}'>{row['Teknik']}</span></td>"
            html_table += f"<td>{format_volume(row['Hacim'])}</td>"
            html_table += f"<td>{row['52H Yüksek']:,.2f}</td>"
            html_table += f"<td>{row['52H Düşük']:,.2f}</td>"
            html_table += "</tr>"
            
        html_table += "</tbody></table></div>"
        st.markdown(html_table, unsafe_allow_html=True)

# --- SAĞ PANEL: ORİJİNAL TRADINGVIEW X-RAY & ADVANCED CHART ---
with col_xray:
    st.markdown(f'<div style="font-size:1.2rem; font-weight:600; color:{text_main}; margin-bottom:10px;">Profesyonel İnceleme Paneli</div>', unsafe_allow_html=True)
    
    secilen_hisse = st.selectbox("Grafik ve Analiz İçin Hisse Seç:", sorted(bist_symbols), index=bist_symbols.index("THYAO") if "THYAO" in bist_symbols else 0)
    tv_symbol = f"BIST:{secilen_hisse}"
    
    # 1. TRADINGVIEW ADVANCED CHART (GERÇEK ÇİZİM GRAFİĞİ)
    st.markdown(f"**{secilen_hisse} İnteraktif Çizim Grafiği**")
    components.html(
        f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
          "width": "100%",
          "height": 450,
          "symbol": "{tv_symbol}",
          "interval": "D",
          "timezone": "Europe/Istanbul",
          "theme": "{tv_theme_str}",
          "style": "1",
          "locale": "tr",
          "enable_publishing": false,
          "hide_top_toolbar": false,
          "hide_legend": false,
          "save_image": false,
          "container_id": "tradingview_chart"
        }}
          );
          </script>
        </div>
        <!-- TradingView Widget END -->
        """,
        height=450,
        scrolling=False
    )

    st.markdown(f"<hr style='border-color: {border_color};'>", unsafe_allow_html=True)
    
    # 2. TRADINGVIEW ŞİRKET PROFİLİ WIDGETI (HATA VERMEYEN ANA HİSSELER)
    st.markdown(f"**{secilen_hisse} Finansallar ve Profil**")
    components.html(
        f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-profile.js" async>
          {{
          "width": "100%",
          "height": "400",
          "colorTheme": "{tv_theme_str}",
          "isTransparent": true,
          "symbol": "{tv_symbol}",
          "locale": "tr"
        }}
          </script>
        </div>
        <!-- TradingView Widget END -->
        """,
        height=400,
        scrolling=False
    )
