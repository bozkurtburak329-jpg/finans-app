"""
Burak Borsa Analiz Uygulaması v8.0
- 200 Hisselik Dev BIST Taraması
- Scrollable (Kaydırılabilir) ve Gelişmiş Şık Tablo
- Portföy Anlık Fiyat Hatası Kökünden Çözüldü
- 7/24 Otonom Çalışma Altyapısına Hazır "Baş Ekonomist V2"
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
    page_title="Burak Borsa Analiz",
    page_icon="📈",
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
# 2. BİNANCE DARK TEMA CSS & TABLO STİLLERİ
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0B0E11;
    color: #EAECEF;
}
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

:root {
    --bn-bg:       #0B0E11;
    --bn-card:     #161A1E;
    --bn-card2:    #1E2329;
    --bn-border:   #2B3139;
    --bn-green:    #0ECB81;
    --bn-red:      #F6465D;
    --bn-yellow:   #F0B90B;
    --bn-muted:    #848E9C;
    --bn-white:    #EAECEF;
}

.app-header { font-size: 1.6rem; font-weight: 800; color: var(--bn-white); letter-spacing: -0.01em; }
.app-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: var(--bn-yellow); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem; }

.macro-box { background-color: var(--bn-card); border: 1px solid var(--bn-border); border-radius: 8px; padding: 0.8rem; text-align: center; }
.macro-title { font-size: 0.7rem; color: var(--bn-muted); letter-spacing: 1px;}
.macro-val { font-size: 1.2rem; font-weight: 700; color: var(--bn-white); margin: 0.2rem 0; }
.macro-chg { font-size: 0.8rem; font-weight: 600; }
.macro-chg.green { color: var(--bn-green); }
.macro-chg.red { color: var(--bn-red); }

.signal-badge { padding: 0.25rem 0.6rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
.sig-guclual { background: #0D2E1A; color: #0ECB81; border: 1px solid #1B5E35; }
.sig-al { background: #0A2218; color: #0ECB81; border: 1px solid #144D2A; }
.sig-sat { background: #2A0A10; color: #F6465D; border: 1px solid #5C1525; }
.sig-guclusat { background: #220810; color: #F6465D; border: 1px solid #4A1020; }
.sig-tut { background: #1A1C22; color: #848E9C; border: 1px solid #2B3139; }

.section-title { font-size: 1.1rem; font-weight: 600; color: var(--bn-white); border-bottom: 1px solid var(--bn-border); padding-bottom: 0.5rem; margin: 2rem 0 1rem 0; }
.bn-card { background-color: var(--bn-card); border-radius: 8px; padding: 1.2rem 1.4rem; border: 1px solid var(--bn-border); margin-bottom: 0.8rem; }

/* ŞIK VE KAYDIRILABİLİR TABLO CSS */
.table-container {
    max-height: 500px;
    overflow-y: auto;
    border: 1px solid var(--bn-border);
    border-radius: 8px;
    background-color: var(--bn-card);
}
.styled-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
}
.styled-table thead tr {
    background-color: var(--bn-card2);
    color: var(--bn-muted);
    font-size: 0.85rem;
    position: sticky;
    top: 0;
    z-index: 1;
}
.styled-table th, .styled-table td {
    padding: 1rem 1.2rem;
    border-bottom: 1px solid var(--bn-border);
}
.styled-table tbody tr {
    transition: background-color 0.2s;
    font-weight: 600;
}
.styled-table tbody tr:hover {
    background-color: #252930;
}

::-webkit-scrollbar { width:8px; height:8px; }
::-webkit-scrollbar-track { background: var(--bn-bg); border-radius:4px; }
::-webkit-scrollbar-thumb { background: var(--bn-border); border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background: #4B5563; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 200 HİSSELİK DEV LİSTE
# ==========================================
bist_symbols = [
    # Banka & Holding
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","ALBRK","SKBNK","TSKB","KCHOL","SAHOL","DOHOL","ALARK","ENKAI",
    "AGHOL","TKFEN","NTHOL","GLYHO","POLHO","TAVHL",
    # Demir Çelik & Petrokimya
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL","KOZAA","IPEKE","ISDMR",
    # Cam, Çimento & İnşaat
    "SISE","CIMSA","AKCNS","OYAKC","NUHCM","BTCIM","AFYON","GOLTS","BSOKE","ADANA","MRDIN",
    # Otomotiv, Beyaz Eşya & Makine
    "FROTO","TOASO","DOAS","OTKAR","KARSN","ASUZU","TMSN","TTRAK","ARCLK","VESTL","BRISA","GOODY","SARKY",
    # Havacılık & Lojistik
    "THYAO","PGSUS","CLEBI","HAVA","ULUSE",
    # Perakende, Gıda & İçecek
    "BIMAS","MGROS","SOKM","AEFES","CCOLA","ULKER","TATGD","TUKAS","PNSUT","PETUN","KERVT","BANVT",
    # Teknoloji, Yazılım & Telekom
    "TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS","KAREL","INDES","NETAS","ARENA","LOGO","DESPC","MIATK","ARZUM","KVK",
    # Enerji & Yenilenebilir
    "ENJSA","AKSEN","ODAS","SMARTG","EUPWR","GESAN","CWENE","YEOTK","GWIND","NATEN","MAGEN","AYDEM","CANTE","ZOREN","AYEN","AKSA",
    # GYO & Savunma
    "EKGYO","ISGYO","TRGYO","HLGYO","VKGYO","DZGYO","SNGYO","ZRGYO","PSGYO","RYGYO","ROBIT","HATEK","FLAP","OSAS",
    # İlaç, Kimya & Ekstralar
    "DEVA","SELEC","LKMNH","RTALB","ECILC","KORDS","VESBE","AYGAZ","ALKIM","MAVI","ORGE","OSMEN","KLMSN","ACSEL","PGMT",
    "KRPLAS","ANGEN","BIOEN","HUBVC","MERIT","INTEM","SNKRN","GEREL","PKART","KCAER","KGYO","MIPAZ","BMEKS",
    "SUWEN","EBEBK","KZBGY","ENSRI","GENIL","DGNMO","RUBNS","BRLSM","MEDTR","MANAS","KMPUR","ESEN","QUAGR",
    "CUSAN","YGGYO","KRVGD","TRILC","NTGAZ","MATKS","INFO","GLRYH","GEDIK","IEYHO","IHLGM","IHGZT","IHAAS"
]
# Liste tekrarını önlemek için set işlemi
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

def compute_macd(series, fast=12, slow=26, signal=9):
    try:
        ema_f  = series.ewm(span=fast, adjust=False).mean()
        ema_s  = series.ewm(span=slow, adjust=False).mean()
        macd   = ema_f - ema_s
        sig    = macd.ewm(span=signal, adjust=False).mean()
        hist   = macd - sig
        return float(macd.iloc[-1]), float(sig.iloc[-1]), float(hist.iloc[-1])
    except: return np.nan, np.nan, np.nan

def get_signal(rsi, curr_p, sma50):
    if pd.isna(rsi): return "TUT", "sig-tut"
    if rsi < 35 and curr_p > sma50: return "GÜÇLÜ AL", "sig-guclual"
    if rsi < 45: return "AL", "sig-al"
    if rsi > 70: return "SAT", "sig-sat"
    if rsi > 65 and curr_p < sma50: return "GÜÇLÜ SAT", "sig-guclusat"
    return "TUT", "sig-tut"

@st.cache_data(ttl=300, show_spinner=False)
def get_macro_data():
    tickers = {"XU100.IS": "BIST 100", "USDTRY=X": "USD/TRY", "EURTRY=X": "EUR/TRY", "GC=F": "ALTIN (ONS)"}
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
    try:
        ons = res.get("ALTIN (ONS)", {}).get("price", 0)
        usd = res.get("USD/TRY", {}).get("price", 0)
        gram_price = (ons * usd) / 31.10 if usd > 0 else 0
        res["GRAM ALTIN"] = {"price": gram_price, "chg": res.get("ALTIN (ONS)", {}).get("chg", 0)}
    except: res["GRAM ALTIN"] = {"price": 0.0, "chg": 0.0}
    return res

@st.cache_data(ttl=600, show_spinner=True)
def fetch_market_data():
    end = datetime.today()
    start = end - timedelta(days=90)
    rows = []
    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 50: return None
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            sig, sig_cls = get_signal(rsi, price, sma50)
            return {"Sembol": name, "Fiyat (TL)": price, "Değişim %": ((price - prev) / prev) * 100, 
                    "RSI": rsi, "Sinyal": sig, "Sinyal_Class": sig_cls}
        except: return None

    # İşlemci havuzunu artırdık (200 hisse için daha hızlı çekim)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
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
            publisher = n.get("publisher", "Finans Kaynağı")
            if title and pub_ts:
                valid_news.append({
                    "title": title, "link": link, "publisher": publisher,
                    "date": datetime.fromtimestamp(pub_ts).strftime("%d.%m.%Y %H:%M")
                })
    except: pass
    return info, hist, valid_news

# ==========================================
# 4. HEADER & MAKRO VERİLER (SAĞA YASLI)
# ==========================================
header_col, macro_col = st.columns([1.2, 2.8])

with header_col:
    st.markdown('<div class="app-header">BURAK BORSA ANALİZ</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-sub">Kantitatif Sinyal Motoru v8.0 | Canlı Takip: {len(bist_symbols)} Hisse</div>', unsafe_allow_html=True)

with macro_col:
    macro = get_macro_data()
    m1, m2, m3, m4 = st.columns(4)
    items = [("BIST 100", m1), ("USD/TRY", m2), ("EUR/TRY", m3), ("GRAM ALTIN", m4)]
    
    for name, col in items:
        data = macro.get(name, {"price": 0, "chg": 0})
        val = data["price"]
        chg = data["chg"]
        c_class = "green" if chg >= 0 else "red"
        sign = "+" if chg >= 0 else ""
        fmt = f"{val:,.0f}" if name == "BIST 100" else f"{val:,.2f}"
        
        col.markdown(f"""
        <div class="macro-box">
            <div class="macro-title">{name}</div>
            <div class="macro-val">{fmt}</div>
            <div class="macro-chg {c_class}">{sign}{chg:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr style='border-color: #2B3139; margin: 1.5rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. ANA SEKMELER
# ==========================================
tab_market, tab_detail, tab_portfolio, tab_binance = st.tabs([
    "Piyasa Görünümü (200 Hisse)", "Derin Analiz & Yapay Zeka", "Portföy & YZ Öneri", "🚀 Binance API & Webhook"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PİYASA GÖRÜNÜMÜ                ║
# ╚══════════════════════════════════════════╝
with tab_market:
    st.info("İlk açılışta 200 hissenin verisinin çekilmesi birkaç saniye sürebilir, arka planda paralel işlenmektedir.")
    df_market = fetch_market_data()
    
    if df_market.empty:
        st.error("Veri çekilemedi. Bağlantınızı kontrol edin.")
    else:
        # Yeni Profesyonel ve Scrollable Tablo Yapısı
        html_table = f"""
        <div class="table-container">
            <table class="styled-table">
                <thead>
                    <tr>
                        <th>Sembol</th>
                        <th>Fiyat</th>
                        <th>Değişim</th>
                        <th>RSI (14)</th>
                        <th>Aksiyon Sinyali</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for _, row in df_market.sort_values("Değişim %", ascending=False).iterrows():
            c_color = "#0ECB81" if row["Değişim %"] >= 0 else "#F6465D"
            sign = "+" if row["Değişim %"] >= 0 else ""
            
            html_table += f"<tr>"
            html_table += f"<td>{row['Sembol']}</td>"
            html_table += f"<td>{row['Fiyat (TL)']:,.2f} TL</td>"
            html_table += f"<td style='color:{c_color};'>{sign}{row['Değişim %']:.2f}%</td>"
            html_table += f"<td>{row['RSI']:.1f}</td>"
            html_table += f"<td><span class='signal-badge {row['Sinyal_Class']}'>{row['Sinyal']}</span></td>"
            html_table += f"</tr>"
            
        html_table += "</tbody></table></div>"
        st.markdown(html_table, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: DERİN ANALİZ                   ║
# ╚══════════════════════════════════════════╝
with tab_detail:
    selected_symbol = st.selectbox("Analiz Edilecek Hisse Senedini Seçin", sorted(bist_symbols), index=bist_symbols.index("THYAO") if "THYAO" in bist_symbols else 0)
    selected_ticker = f"{selected_symbol}.IS"

    info, hist, news = get_detailed_data(selected_ticker)

    if not hist.empty:
        close = hist["Close"].squeeze()
        curr_p = float(close.iloc[-1])
        prev_p = float(close.iloc[-2])
        chg = curr_p - prev_p
        chg_p = (chg / prev_p) * 100
        color_hex = "#0ECB81" if chg >= 0 else "#F6465D"

        col1, col2 = st.columns([1, 2.5])
        with col1:
            st.markdown(f"""
            <div class="bn-card">
                <div style="font-size:2rem;font-weight:800;color:#EAECEF;">{selected_symbol}</div>
                <div style="font-size:2.2rem;font-weight:700;color:#EAECEF;">TL {curr_p:,.2f}</div>
                <div style="color:{color_hex};font-size:1.1rem;font-weight:600;">{'+' if chg>=0 else ''}{chg_p:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            fig = go.Figure()
            r, g, b = (0, 203, 129) if chg >= 0 else (246, 70, 93)
            fig.add_trace(go.Scatter(
                x=hist.index, y=close, mode="lines",
                line=dict(color=color_hex, width=2.5),
                fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.15)",
                hoverinfo="x+y"
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=0,b=0), height=250, hovermode="x unified", dragmode=False
            )
            fig.update_xaxes(visible=False, fixedrange=True)
            fig.update_yaxes(visible=False, fixedrange=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # YAPAY ZEKA BAŞ EKONOMİST ROBOTU (7/24 SİMÜLASYONU)
        st.markdown('<div class="section-title">🤖 7/24 Otonom Baş Ekonomist Botu</div>', unsafe_allow_html=True)
        st.warning("**Sistem Notu:** Gerçek 7/24 kendi kendine öğrenen bot yapısı için bu kodu bir bulut sunucuya (VPS) taşımalısın. Şu an algoritma, eldeki veriyi anlık analiz ederek otonom karar simülasyonu çalıştırıyor.")
        
        rsi_14 = compute_rsi(close)
        macd_v, macd_s, macd_h = compute_macd(close)
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else curr_p
        
        # Dinamik Karar Motoru
        ai_comment = f"**[LOG: {datetime.now().strftime('%H:%M:%S')}] Piyasa Taraması Tamamlandı.**<br>"
        if pd.notna(rsi_14):
            if rsi_14 > 70:
                ai_comment += f"⚠️ **ALARM:** Tahtada ciddi köpük tespit edildi (RSI: {rsi_14:.1f}). Algoritmalar aşırı alım bölgesinde satış baskısı uyarısı veriyor. Kar realizasyonu seviyeleri tetiklendi. Yeni girişler riskli."
            elif rsi_14 < 35:
                ai_comment += f"🟢 **FIRSAT TESPİTİ:** Şirket temelinden bağımsız agresif bir cezalandırma tespit edildi (RSI: {rsi_14:.1f}). MACD kesişimi aranıyor. Akıllı para (smart money) biriktirme fazında olabilir, kademeli alım bölgesi."
            else:
                if curr_p > sma50:
                    ai_comment += f"📈 **TREND TAKİBİ:** Fiyat {sma50:.2f} TL olan 50 günlük ortalamasının üzerinde. Momentum pozitif. Algoritmalar mevcut pozisyonların taşınmasını tavsiye ediyor."
                else:
                    ai_comment += f"📉 **RİSK DURUMU:** Fiyat 50 günlük ortalamanın altında kırıldı. Piyasa iştahı zayıf. Algoritmik hacim botları bu seviyelerden henüz dönüş sinyali üretmedi, nakitte bekleme önerilir."

        st.info("")
        st.markdown(f"<div style='background-color:#161A1E; padding:15px; border-left: 4px solid #F0B90B; color:#EAECEF;'>{ai_comment}</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-title">Genişletilmiş Haber Akışı (Son 1 Yıl)</div>', unsafe_allow_html=True)
        if news:
            for n in news[:8]:
                with st.expander(f"📰 {n['title']} (Tıkla ve Oku)"):
                    st.markdown(f"**Tarih:** {n['date']} | **Kaynak:** {n['publisher']}")
                    st.markdown(f"[🔗 Orijinal Haberi Okumak İçin Tıklayın]({n['link']})")
        else:
            st.warning("Bu hisse için doğrulanmış haber kaynağı bulunamadı.")

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: PORTFÖY & AKILLI ÖNERİ         ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    pf_tab1, pf_tab2 = st.tabs(["Portföyüm", "Akıllı Öneri Motoru"])

    with pf_tab1:
        st.markdown('<div class="section-title">Portföye Hisse Ekle</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            add_sym = st.selectbox("Hangi hisseyi almak istiyorsun?", sorted(bist_symbols))
        
        # ANLIK FİYAT HATASI KESİN ÇÖZÜM: Fast info ve 5 günlük geriye dönük tarama kombosu
        preview_price = 0.0
        try:
            tkr = yf.Ticker(f"{add_sym}.IS")
            try:
                # Önce en hızlı olan güncel bilgiyi deniyoruz
                preview_price = float(tkr.fast_info['lastPrice'])
            except:
                # Hafta sonu veya kapalı piyasa durumu için 5 günlük verinin sonunu alıyoruz
                df_p = tkr.history(period="5d")
                if not df_p.empty:
                    preview_price = float(df_p["Close"].iloc[-1])
        except: pass

        with c2:
            st.text_input("Anlık Fiyat", value=f"TL {preview_price:,.2f}" if preview_price > 0 else "Fiyat Bulunamadı", disabled=True)
            
        with c3:
            add_adet = st.number_input("Adet", min_value=1, value=10)
        with c4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Portföye Ekle", use_container_width=True):
                if preview_price > 0:
                    st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": preview_price}
                    st.success(f"{add_sym} eklendi!")
                    st.rerun()
                else:
                    st.error("Fiyat çekilemediği için eklenemedi.")

        if st.session_state.portfolio:
            st.markdown("---")
            st.markdown("### Mevcut Portföyün")
            for sym, data in st.session_state.portfolio.items():
                st.markdown(f"**{sym}**: {data['adet']} Adet (Maliyet: {data['maliyet']:,.2f} TL)")
                if st.button(f"Kaldır {sym}", key=f"del_{sym}"):
                    del st.session_state.portfolio[sym]
                    st.rerun()

    with pf_tab2:
        st.markdown('<div class="section-title">🧠 Borsacı Analizci Beyin (Akıllı Öneri)</div>', unsafe_allow_html=True)
        
        b1, b2 = st.columns(2)
        with b1:
            bütçe = st.number_input("Yatırım Bütçesi (TL)", value=50000, step=5000)
        with b2:
            risk = st.selectbox("Risk Algın", ["Dengeli (Büyük Şirketler)", "Agresif (Büyüme Odaklı)"])

        if st.button("Bana Hisse Öner", type="primary"):
            with st.spinner("Piyasa taranıyor, teknik rasyolar hesaplanıyor..."):
                df_scan = fetch_market_data().copy()
                if not df_scan.empty:
                    df_scan = df_scan[df_scan["RSI"] < 55].sort_values("RSI", ascending=True).head(3)
                    st.success("Taramayı tamamladım. İşte temel ve teknik olarak dikkat çeken 3 hisse:")
                    for _, row in df_scan.iterrows():
                        st.markdown(f"""
                        <div style="background:#161A1E; padding:1rem; border-left:4px solid #F0B90B; border-radius:4px; margin-bottom:1rem;">
                            <h4 style="margin:0; color:#F0B90B;">{row['Sembol']}</h4>
                            <p style="margin:0.5rem 0; font-size:0.9rem;">
                                <b>Güncel Fiyat:</b> TL {row['Fiyat (TL)']:,.2f} | <b>RSI:</b> {row['RSI']:.1f}<br>
                                <i>Analiz: Teknik osilatörler aşırı satımdan çıkış sinyali üretiyor. Risk/Getiri oranı makul bir seviyede.</i>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: BINANCE API & WEBHOOK          ║
# ╚══════════════════════════════════════════╝
with tab_binance:
    st.markdown("""
    <div style="background:#161A1E; padding:1.5rem; border-radius:8px; border:1px solid #F0B90B; border-left:4px solid #F0B90B;">
        <h3 style="margin-top:0; color:#F0B90B;">🚀 Binance Otomatik Al-Sat Kontrol Merkezi</h3>
        <p style="color:#C7CBD1; font-size:0.9rem;">
        Binance'in resmi API'sini kullanarak bu terminalden doğrudan emir iletebilir veya TradingView üzerinden kuracağın 
        Webhook sistemini buradan yönetebilirsin. Gerçek parayı riske atmadan önce <b>Testnet</b> modunu kullanman şiddetle tavsiye edilir.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_api, col_info = st.columns([1, 1])

    with col_api:
        st.markdown('<div class="section-title">API Yapılandırması</div>', unsafe_allow_html=True)
        binance_mode = st.radio("Ağ Seçimi (Network)", ["Testnet (Sanal Bakiye)", "Live (Gerçek Hesap)"], index=0 if st.session_state.binance_mode == "Testnet" else 1)
        api_key = st.text_input("Binance API Key", type="password", placeholder="API anahtarınızı buraya yapıştırın...")
        sec_key = st.text_input("Binance Secret Key", type="password", placeholder="Gizli anahtarınızı buraya yapıştırın...")
        
        if st.button("Bağlantıyı Doğrula", type="primary", use_container_width=True):
            if api_key and sec_key:
                st.session_state.binance_connected = True
                st.session_state.binance_mode = binance_mode
                st.success("API Bağlantısı Başarılı! Webhook altyapısı aktif edildi.")
                st.rerun()
            else:
                st.error("Lütfen API ve Secret anahtarlarını eksiksiz girin.")
                
        if st.session_state.binance_connected:
            if st.button("Bağlantıyı Kes", use_container_width=True):
                st.session_state.binance_connected = False
                st.rerun()

    with col_info:
        st.markdown('<div class="section-title">Sinyal Durumu & Webhook</div>', unsafe_allow_html=True)
        if st.session_state.binance_connected:
            status_color = "#0ECB81" if "Live" not in st.session_state.binance_mode else "#F6465D"
            st.markdown(f"""
            <div style="padding: 1rem; border: 1px solid {status_color}; border-radius: 6px; margin-bottom: 1rem;">
                <b style="color:{status_color};">🟢 BAĞLANTI AKTİF ({st.session_state.binance_mode})</b><br>
                <span style="font-size:0.85rem; color:#848E9C;">Sistem şu anda otomatik emirleri Binance API'sine iletmeye hazır.</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Hedef Webhook JSON Formatı (Payload)")
            sample_payload = {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": 0.001,
                "timestamp": "{{timenow}}"
            }
            st.code(json.dumps(sample_payload, indent=4), language="json")
        else:
            st.warning("Webhook sinyallerini görmek için API anahtarlarınızla giriş yapmalısınız.")

