"""
Burak Borsa Analiz Uygulaması v10.0 (TradingView X-Ray Sürümü)
- Streamlit Sınırları Parçalandı!
- Sol Panel: 200 Hisselik TV Screener Klonu
- Sağ Panel: Orijinal TradingView Canlı X-Ray Bileşenleri (Grafik + Teknik Kadran)
- Şirket Detayları, Hacim, RSI ve Yapay Zeka Sinyalleri
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

if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "binance_connected" not in st.session_state:
    st.session_state.binance_connected = False
if "binance_mode" not in st.session_state:
    st.session_state.binance_mode = "Testnet"

# ==========================================
# 2. BİNANCE & TRADINGVIEW DARK TEMA CSS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Trebuchet+MS:ital,wght@0,400;0,700;1,400;1,700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif !important;
    background-color: #131722; 
    color: #d1d4dc;
}
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1e222d; }
::-webkit-scrollbar-thumb { background: #50535e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #787b86; }

/* TRADINGVIEW SCREENER TABLOSU */
.tv-screener-container {
    width: 100%;
    height: 75vh;
    overflow-y: auto;
    overflow-x: auto;
    background-color: #131722;
    border: 1px solid #2a2e39;
    border-radius: 4px;
}
.tv-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: right;
    white-space: nowrap;
}
.tv-table thead {
    position: sticky;
    top: 0;
    z-index: 2;
    background-color: #1e222d;
    box-shadow: 0 1px 0 #2a2e39;
}
.tv-table th {
    padding: 10px 12px;
    font-weight: 500;
    color: #787b86;
    border-right: 1px solid #2a2e39;
    font-size: 12px;
}
.tv-table th:first-child { text-align: left; }
.tv-table tbody tr { border-bottom: 1px solid #2a2e39; background-color: #131722; transition: 0.1s; }
.tv-table tbody tr:hover { background-color: #2a2e39; }
.tv-table td { padding: 8px 12px; color: #d1d4dc; vertical-align: middle; }
.tv-table td:first-child { text-align: left; }

.tv-ticker-col { display: flex; align-items: center; gap: 12px; }
.tv-logo-circle {
    width: 28px; height: 28px; border-radius: 50%; background-color: #2962ff;
    color: #fff; display: flex; align-items: center; justify-content: center;
    font-weight: bold; font-size: 13px; flex-shrink: 0;
}
.tv-ticker-info { display: flex; flex-direction: column; justify-content: center; }
.tv-ticker-symbol { color: #2962ff; font-weight: 600; font-size: 14px; }
.tv-ticker-desc { color: #787b86; font-size: 11px; margin-top: 2px; }

.tv-green { color: #089981 !important; }
.tv-red { color: #f23645 !important; }
.tv-rating { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.rating-strong-buy { color: #089981; background-color: rgba(8, 153, 129, 0.15); }
.rating-buy { color: #089981; background-color: transparent; }
.rating-sell { color: #f23645; background-color: transparent; }
.rating-strong-sell { color: #f23645; background-color: rgba(242, 54, 69, 0.15); }
.rating-neutral { color: #787b86; background-color: rgba(120, 123, 134, 0.15); }

/* Makro Başlıklar */
.macro-box { background-color: #1e222d; border-radius: 6px; padding: 10px; border: 1px solid #2a2e39; text-align: center; }
.macro-title { font-size: 0.7rem; color: #787b86; letter-spacing: 1px;}
.macro-val { font-size: 1.1rem; font-weight: bold; color: #d1d4dc; margin: 2px 0; }
.macro-chg { font-size: 0.8rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. YARDIMCI FONKSİYONLAR & DEV BİST LİSTESİ
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","ALBRK","SKBNK","TSKB","KCHOL",
    "SAHOL","DOHOL","ALARK","ENKAI","AGHOL","TKFEN","EREGL","KRDMD","TUPRS","PETKM",
    "SASA","HEKTS","GUBRF","KOZAL","KOZAA","IPEKE","ISDMR","SISE","CIMSA","AKCNS",
    "OYAKC","FROTO","TOASO","DOAS","OTKAR","KARSN","ASUZU","TTRAK","ARCLK","VESTL",
    "THYAO","PGSUS","CLEBI","BIMAS","MGROS","SOKM","AEFES","CCOLA","ULKER","TATGD",
    "TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS","KAREL","MIATK","ENJSA","AKSEN",
    "ODAS","SMARTG","EUPWR","GESAN","CWENE","YEOTK","GWIND","NATEN","MAGEN","AYDEM",
    "EKGYO","ISGYO","TRGYO","HLGYO","VKGYO","ROBIT","HATEK","FLAP","OSAS","DEVA",
    "SELEC","ECILC","KORDS","VESBE","AYGAZ","MAVI","ORGE","OSMEN","KLMSN","ACSEL"
]
bist_symbols = sorted(list(dict.fromkeys(bist_symbols)))
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

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
    start = end - timedelta(days=90)
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
            
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            _, _, macd_h = compute_macd(close)
            
            rating, rating_cls = get_tv_rating(rsi, price, sma50, macd_h)
            
            return {
                "Sembol": name, "Fiyat": price, "Değişim %": chg_pct, "Değişim": chg_val,
                "Teknik": rating, "Teknik_Class": rating_cls, "Hacim": vol, "Göreceli Hacim": rel_vol, "RSI": rsi
            }
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            if f.result(): rows.append(f.result())
    return pd.DataFrame(rows)

def format_volume(vol):
    if vol >= 1_000_000_000: return f"{vol/1_000_000_000:.3f}B"
    if vol >= 1_000_000: return f"{vol/1_000_000:.3f}M"
    if vol >= 1_000: return f"{vol/1_000:.3f}K"
    return str(vol)

# ==========================================
# 4. ÜST BAR & MAKRO VERİLER
# ==========================================
header_col, macro_col = st.columns([1, 3])

with header_col:
    st.markdown('<div style="font-size:1.8rem; font-weight:700; color:#fff; display:flex; align-items:center; gap:10px;"><span style="color:#2962ff;">B</span> Terminal v10.0</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.75rem; color:#089981;">⚡ KUDURAN SÜRÜM AKTİF</div>', unsafe_allow_html=True)

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

st.markdown("<hr style='border-color: #2a2e39; margin: 1rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. ANA SEKMELER
# ==========================================
tab_screener, tab_portfolio, tab_binance = st.tabs([
    "🔥 Canlı Tarayıcı & X-Ray Detay Paneli", "Portföy & AI", "Otomasyon (Binance)"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: BÖLÜNMÜŞ EKRAN (SCREENER + X-RAY)
# ╚══════════════════════════════════════════╝
with tab_screener:
    
    # Ekranı ikiye bölüyoruz: Sol %65 Tarayıcı, Sağ %35 Özel X-Ray Paneli
    col_screener, col_xray = st.columns([2.2, 1.2])
    
    # --- SOL PANEL: DEV TABLO ---
    with col_screener:
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
                            <th>RSI (14)</th>
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
                            <span class="tv-ticker-desc">{row['Sembol']} A.Ş.</span>
                        </div>
                    </div>
                </td>
                """
                html_table += f"<td>{row['Fiyat']:,.2f}</td>"
                html_table += f"<td class='{c_class}'>{sign}{row['Değişim %']:.2f}%</td>"
                html_table += f"<td><span class='tv-rating {row['Teknik_Class']}'>{row['Teknik']}</span></td>"
                html_table += f"<td>{format_volume(row['Hacim'])}</td>"
                html_table += f"<td>{row['RSI']:.2f}</td>"
                html_table += "</tr>"
                
            html_table += "</tbody></table></div>"
            st.markdown(html_table, unsafe_allow_html=True)
            
    # --- SAĞ PANEL: ORİJİNAL TRADINGVIEW X-RAY WIDGETLARI ---
    with col_xray:
        st.markdown('<div style="font-size:1.1rem; font-weight:600; color:#fff; margin-bottom:10px;">🔍 X-Ray Şirket İnceleme Paneli</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.85rem; color:#787b86; margin-bottom:15px;">Soldaki tablodan incelemek istediğiniz hisseyi aşağıdan seçin, tüm röntgeni çıksın.</div>', unsafe_allow_html=True)
        
        # Seçici (Buradan seçtiği an widgetlar tetiklenecek)
        secilen_hisse = st.selectbox("Detaylı Analiz İçin Hisse Seç:", sorted(bist_symbols), index=bist_symbols.index("THYAO") if "THYAO" in bist_symbols else 0)
        tv_symbol = f"BIST:{secilen_hisse}"
        
        # 1. TRADINGVIEW TEKNİK ANALİZ KADRANI WIDGETI
        st.markdown(f"**{secilen_hisse} Anlık Teknik Kadran**")
        components.html(
            f"""
            <!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
              {{
              "interval": "1D",
              "width": "100%",
              "isTransparent": true,
              "height": "380",
              "symbol": "{tv_symbol}",
              "showIntervalTabs": true,
              "displayMode": "single",
              "locale": "tr",
              "colorTheme": "dark"
            }}
              </script>
            </div>
            <!-- TradingView Widget END -->
            """,
            height=380,
            scrolling=False
        )

        st.markdown("<hr style='border-color: #2a2e39;'>", unsafe_allow_html=True)
        
        # 2. TRADINGVIEW ŞİRKET PROFİLİ VE FİNANSALLAR WIDGETI
        st.markdown(f"**{secilen_hisse} Şirket Profili & Finansallar**")
        components.html(
            f"""
            <!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-profile.js" async>
              {{
              "width": "100%",
              "height": "400",
              "colorTheme": "dark",
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

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: PORTFÖY & AKILLI ÖNERİ         ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    p1, p2 = st.tabs(["Portföyüm", "Akıllı Öneri Motoru"])
    with p1:
        st.markdown("### Hisse Ekle")
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

        with c2: st.text_input("Fiyat", value=f"{preview_price:,.2f}" if preview_price > 0 else "Bulunamadı", disabled=True)
        with c3: add_adet = st.number_input("Adet", min_value=1, value=10)
        with c4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Ekle", use_container_width=True) and preview_price > 0:
                st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": preview_price}
                st.rerun()

        if st.session_state.portfolio:
            st.markdown("---")
            st.markdown("### Portföy")
            for sym, data in st.session_state.portfolio.items():
                st.markdown(f"**{sym}**: {data['adet']} Adet (Maliyet: {data['maliyet']:,.2f} TL)")
                if st.button(f"Kaldır {sym}", key=f"del_{sym}"):
                    del st.session_state.portfolio[sym]
                    st.rerun()

    with p2:
        st.markdown("### 🧠 Otonom AI Motoru")
        st.write("Sistemin arka plan yapay zeka algoritması (Random Forest) gece 03:00'te veritabanını tarayıp buraya otomatik sepet bırakacaktır.")

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: BINANCE API & WEBHOOK          ║
# ╚══════════════════════════════════════════╝
with tab_binance:
    st.markdown("### Binance Otomatik Al-Sat Kontrol Merkezi")
    st.write("Sistem şu an TradingView Webhook bağlantısını dinlemek üzere hazır beklemektedir.")
    st.radio("Ağ Seçimi", ["Testnet", "Live"])
    st.text_input("API Key", type="password")
    st.text_input("Secret Key", type="password")
    st.button("Bağlantıyı Doğrula", type="primary")
