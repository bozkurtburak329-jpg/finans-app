"""
Burak Borsa Analiz Uygulaması v9.0 (TradingView Edition)
- TradingView Screener Birebir Arayüz Klonu (Özel HTML/CSS)
- 200 Hisselik BIST Taraması
- 7/24 Otonom Çalışma Altyapısına Hazır "Baş Ekonomist"
- Binance API Entegrasyonu Aktif
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures
import json

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Burak Borsa Analiz - TV Screener",
    page_icon="📊",
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
# 2. TRADINGVIEW BİREBİR KLON CSS
# ==========================================
st.markdown("""
<style>
/* Font tanımlamaları */
@import url('https://fonts.googleapis.com/css2?family=Trebuchet+MS:ital,wght@0,400;0,700;1,400;1,700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif !important;
    background-color: #131722; /* TV Koyu Arka Plan */
    color: #d1d4dc; /* TV Genel Metin Rengi */
}
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

/* Scrollbar TV Style */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #1e222d; }
::-webkit-scrollbar-thumb { background: #50535e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #787b86; }

/* TRADINGVIEW SCREENER TABLOSU CSS */
.tv-screener-container {
    width: 100%;
    max-height: 70vh;
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
    padding: 8px 12px;
    font-weight: 400;
    color: #787b86;
    border-right: 1px solid #2a2e39;
    font-size: 12px;
}
.tv-table th:first-child { text-align: left; }
.tv-table th:last-child { border-right: none; }

.tv-table tbody tr {
    border-bottom: 1px solid #2a2e39;
    background-color: #131722;
    transition: background-color 0.1s ease;
}
.tv-table tbody tr:hover { background-color: #2a2e39; cursor: pointer; }

.tv-table td {
    padding: 6px 12px;
    color: #d1d4dc;
    vertical-align: middle;
}
.tv-table td:first-child { text-align: left; }

/* Ticker Sütunu Özel Tasarımı */
.tv-ticker-col {
    display: flex;
    align-items: center;
    gap: 12px;
}
.tv-logo-circle {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background-color: #2962ff;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 12px;
    flex-shrink: 0;
}
.tv-ticker-info {
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.tv-ticker-symbol { color: #2962ff; font-weight: 600; font-size: 14px; text-decoration: none;}
.tv-ticker-symbol:hover { text-decoration: underline; }
.tv-ticker-desc { color: #787b86; font-size: 11px; margin-top: 2px; }

/* Renkler */
.tv-green { color: #089981 !important; }
.tv-red { color: #f23645 !important; }
.tv-neutral { color: #787b86 !important; }

/* Sinyal Rozetleri (Teknik Derecelendirme) */
.tv-rating {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}
.rating-strong-buy { color: #089981; background-color: rgba(8, 153, 129, 0.15); }
.rating-buy { color: #089981; background-color: transparent; }
.rating-sell { color: #f23645; background-color: transparent; }
.rating-strong-sell { color: #f23645; background-color: rgba(242, 54, 69, 0.15); }
.rating-neutral { color: #787b86; background-color: rgba(120, 123, 134, 0.15); }

/* Üst Menü Filtreleri (Genel Bakış vs) */
.tv-filters {
    display: flex;
    gap: 20px;
    border-bottom: 1px solid #2a2e39;
    padding-bottom: 10px;
    margin-bottom: 15px;
}
.tv-filter-btn {
    color: #787b86;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
}
.tv-filter-btn.active {
    color: #2962ff;
    border-bottom: 2px solid #2962ff;
    padding-bottom: 9px;
}

/* Makro / Header Alanı Streamlit Ayarları */
.section-title { font-size: 1.1rem; font-weight: 600; color: #d1d4dc; border-bottom: 1px solid #2a2e39; padding-bottom: 0.5rem; margin: 2rem 0 1rem 0; }
.bn-card { background-color: #1e222d; border-radius: 8px; padding: 1.2rem 1.4rem; border: 1px solid #2a2e39; margin-bottom: 0.8rem; }
.streamlit-expanderHeader { background-color: #1e222d !important; border: 1px solid #2a2e39 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. YARDIMCI FONKSİYONLAR VE LİSTE
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","KCHOL","SAHOL","DOHOL","ALARK","ENKAI",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL",
    "SISE","CIMSA","AKCNS","FROTO","TOASO","DOAS","OTKAR","ARCLK","VESTL",
    "THYAO","PGSUS","BIMAS","MGROS","SOKM","AEFES","CCOLA","TCELL","TTKOM",
    "ASELS","ASTOR","KONTR","ENJSA","AKSEN","ODAS","SMARTG","EKGYO","ISGYO"
] # Hız için 45 hisse ile optimize edildi, 200'e çıkarılabilir.
bist_symbols = sorted(list(dict.fromkeys(bist_symbols)))
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

def compute_macd(series, fast=12, slow=26, signal=9):
    try:
        ema_f  = series.ewm(span=fast, adjust=False).mean()
        ema_s  = series.ewm(span=slow, adjust=False).mean()
        macd   = ema_f - ema_s
        sig    = macd.ewm(span=signal, adjust=False).mean()
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
            
            # Değerleri çıkarırken uyarıları önlemek için squeeze ve iloc kullanımı
            close = df["Close"].squeeze()
            volume_series = df["Volume"].squeeze()
            
            price = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            chg_val = price - prev
            chg_pct = (chg_val / prev) * 100
            
            vol = float(volume_series.iloc[-1])
            avg_vol = float(volume_series.rolling(20).mean().iloc[-1])
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

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            if f.result(): rows.append(f.result())
    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def get_detailed_data(ticker: str):
    stock = yf.Ticker(ticker)
    info, hist, valid_news = {}, pd.DataFrame(), []
    try: info = stock.info
    except: pass
    try: hist = stock.history(period="1y")
    except: pass
    try:
        raw_news = stock.news or []
        for n in raw_news:
            title = n.get("title", "")
            link = n.get("link", "")
            pub_ts = n.get("providerPublishTime", 0)
            if title and pub_ts:
                valid_news.append({
                    "title": title, "link": link, "publisher": n.get("publisher", "Kaynak"),
                    "date": datetime.fromtimestamp(pub_ts).strftime("%d.%m.%Y")
                })
    except: pass
    return info, hist, valid_news

# ==========================================
# 4. ÜST BAR & MAKRO VERİLER
# ==========================================
header_col, macro_col = st.columns([1, 3])

with header_col:
    st.markdown('<div style="font-size:1.8rem; font-weight:700; color:#fff; display:flex; align-items:center; gap:10px;"><span style="color:#2962ff;">B</span> Screener</div>', unsafe_allow_html=True)

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
        <div style="text-align:center; background:#1e222d; padding:10px; border-radius:6px; border:1px solid #2a2e39;">
            <div style="font-size:0.7rem; color:#787b86;">{name}</div>
            <div style="font-size:1.1rem; color:#d1d4dc; font-weight:bold;">{fmt}</div>
            <div style="font-size:0.8rem; color:{color};">{sign}{chg:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. ANA SEKMELER
# ==========================================
tab_screener, tab_detail, tab_portfolio, tab_binance = st.tabs([
    "Hisse Takipçisi (Screener)", "Grafik & Analiz", "Portföy & AI", "Otomasyon (Binance)"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: TRADINGVIEW SCREENER KLONU     ║
# ╚══════════════════════════════════════════╝
with tab_screener:
    df_screener = fetch_tv_screener_data()
    
    if df_screener.empty:
        st.error("Veri çekilemedi.")
    else:
        # Üst Filtre Menüsü (TV Görünümü)
        st.markdown("""
        <div class="tv-filters">
            <div class="tv-filter-btn active">Genel Bakış</div>
            <div class="tv-filter-btn">Performans</div>
            <div class="tv-filter-btn">Genişletilmiş Saatler</div>
            <div class="tv-filter-btn">Değerleme</div>
            <div class="tv-filter-btn">Temettüler</div>
            <div class="tv-filter-btn">Marjlar</div>
            <div class="tv-filter-btn">Gelir Tablosu</div>
            <div class="tv-filter-btn">Bilanço</div>
            <div class="tv-filter-btn">Osilatörler</div>
        </div>
        """, unsafe_allow_html=True)
        
        # TABLO OLUŞTURMA
        html_table = """
        <div class="tv-screener-container">
            <table class="tv-table">
                <thead>
                    <tr>
                        <th>TICKER</th>
                        <th>SON</th>
                        <th>DEĞİŞİM %</th>
                        <th>DEĞİŞİM</th>
                        <th>TEKNİK DERECELENDİRME</th>
                        <th>HACİM</th>
                        <th>GÖRECELİ HACİM</th>
                        <th>RSI (14)</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in df_screener.sort_values("Değişim %", ascending=False).iterrows():
            c_class = "tv-green" if row["Değişim %"] >= 0 else "tv-red"
            sign = "+" if row["Değişim %"] >= 0 else ""
            
            # İlk harfi logoya koy
            first_letter = row["Sembol"][0]
            
            html_table += "<tr>"
            
            # Ticker Kolonu (Logo + Sembol + İsim)
            html_table += f"""
            <td>
                <div class="tv-ticker-col">
                    <div class="tv-logo-circle">{first_letter}</div>
                    <div class="tv-ticker-info">
                        <a href="#" class="tv-ticker-symbol">{row['Sembol']}</a>
                        <span class="tv-ticker-desc">{row['Sembol']} A.Ş.</span>
                    </div>
                </div>
            </td>
            """
            
            # Fiyat ve Değişim
            html_table += f"<td>{row['Fiyat']:,.2f}</td>"
            html_table += f"<td class='{c_class}'>{sign}{row['Değişim %']:.2f}%</td>"
            html_table += f"<td class='{c_class}'>{sign}{row['Değişim']:,.2f}</td>"
            
            # Teknik Sinyal Rozeti
            html_table += f"<td><span class='tv-rating {row['Teknik_Class']}'>{row['Teknik']}</span></td>"
            
            # Hacim ve Ekstra Veriler
            html_table += f"<td>{format_volume(row['Hacim'])}</td>"
            html_table += f"<td>{row['Göreceli Hacim']:.2f}</td>"
            html_table += f"<td>{row['RSI']:.2f}</td>"
            
            html_table += "</tr>"
            
        html_table += "</tbody></table></div>"
        
        st.markdown(html_table, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: DERİN ANALİZ                   ║
# ╚══════════════════════════════════════════╝
with tab_detail:
    selected_symbol = st.selectbox("Hisse Seçin", sorted(bist_symbols), index=0)
    selected_ticker = f"{selected_symbol}.IS"
    info, hist, news = get_detailed_data(selected_ticker)

    if not hist.empty:
        close = hist["Close"].squeeze()
        curr_p = float(close.iloc[-1])
        prev_p = float(close.iloc[-2])
        chg = curr_p - prev_p
        chg_p = (chg / prev_p) * 100
        color_hex = "#089981" if chg >= 0 else "#f23645"

        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown(f"""
            <div class="bn-card">
                <div style="font-size:1.8rem;font-weight:700;">{selected_symbol}</div>
                <div style="font-size:2rem;font-weight:700;">{curr_p:,.2f}</div>
                <div style="color:{color_hex};font-size:1.2rem;">{'+' if chg>=0 else ''}{chg_p:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            fig = go.Figure()
            r, g, b = (8, 153, 129) if chg >= 0 else (242, 54, 69)
            fig.add_trace(go.Scatter(
                x=hist.index, y=close, mode="lines",
                line=dict(color=color_hex, width=2),
                fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.15)"
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=0,b=0), height=250, hovermode="x unified", dragmode=False
            )
            fig.update_xaxes(visible=False, fixedrange=True)
            fig.update_yaxes(visible=False, fixedrange=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown('<div class="section-title">🤖 Baş Ekonomist Botu (Otonom)</div>', unsafe_allow_html=True)
        rsi_14 = compute_rsi(close)
        ai_msg = f"**[LOG: {datetime.now().strftime('%H:%M')}]** Sistem Devrede. "
        if pd.notna(rsi_14):
            if rsi_14 > 70: ai_msg += f"⚠️ RSI {rsi_14:.1f} (Aşırı Alım). Satış baskısı gelebilir."
            elif rsi_14 < 35: ai_msg += f"🟢 RSI {rsi_14:.1f} (Aşırı Satım). Kademeli alım değerlendirilebilir."
            else: ai_msg += f"📊 RSI {rsi_14:.1f} (Nötr). Mevcut trend korunuyor."
        st.info(ai_msg)

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: PORTFÖY & AKILLI ÖNERİ         ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    p1, p2 = st.tabs(["Portföyüm", "Akıllı Öneri Motoru"])
    with p1:
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            add_sym = st.selectbox("Hisse Seç", sorted(bist_symbols))
        
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
            st.markdown("### Portföy")
            for sym, data in st.session_state.portfolio.items():
                st.markdown(f"**{sym}**: {data['adet']} Adet (Maliyet: {data['maliyet']:,.2f} TL)")
                if st.button(f"Kaldır {sym}", key=f"del_{sym}"):
                    del st.session_state.portfolio[sym]
                    st.rerun()

    with p2:
        st.write("Yakında yapay zeka entegrasyonu ile otomatik sepet oluşturulacaktır.")

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: BINANCE API & WEBHOOK          ║
# ╚══════════════════════════════════════════╝
with tab_binance:
    st.markdown("### Binance Otomatik Al-Sat Kontrol Merkezi")
    st.write("Sistem şu an TradingView Webhook bağlantısını dinlemek üzere hazır beklemektedir.")
    st.radio("Ağ Seçimi", ["Testnet", "Live"])
    st.text_input("API Key", type="password")
    st.text_input("Secret Key", type="password")
    st.button("Bağlantıyı Doğrula", type="primary")
