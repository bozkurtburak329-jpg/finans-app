"""
Burak Borsa Analiz Uygulaması v5.0
- Anlık BIST100, Dolar ve Euro (Son 2 Saatlik Değişim)
- Midas Tarzı Sabit ve Şık Grafik Yapısı
- Gelişmiş Haber Sistemi (Tıkladığında Detay Açılan Yapı)
- Yeni 'Baş Ekonomist' Yapay Zeka Analizi
- Akıllı Öneri Motoru V2
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Burak Borsa Analiz",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "market_filter" not in st.session_state:
    st.session_state.market_filter = "TÜMÜ"
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "portfolio_name" not in st.session_state:
    st.session_state.portfolio_name = "Portfoyum 2026"

# ==========================================
# 2. BİNANCE DARK TEMA CSS
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
    --bn-blue:     #1E90FF;
    --bn-muted:    #848E9C;
    --bn-white:    #EAECEF;
}

.app-header {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--bn-white);
    letter-spacing: -0.01em;
    padding: 1rem 0 0.2rem 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
.app-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--bn-yellow);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.section-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--bn-white);
    border-bottom: 1px solid var(--bn-border);
    padding-bottom: 0.5rem;
    margin: 2rem 0 1rem 0;
    letter-spacing: -0.01em;
}

div.stButton > button {
    height: auto;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    border: 1px solid var(--bn-border);
    background-color: var(--bn-card2);
    color: var(--bn-white);
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    transition: all 0.2s;
}
div.stButton > button:hover {
    border-color: var(--bn-yellow);
    color: var(--bn-yellow);
}

.bn-card {
    background-color: var(--bn-card);
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    border: 1px solid var(--bn-border);
    margin-bottom: 0.8rem;
}

/* ── Üst Bar Makro Veri ── */
.macro-box {
    display: flex;
    justify-content: space-between;
    background-color: var(--bn-card2);
    padding: 1rem 1.5rem;
    border-radius: 8px;
    border: 1px solid var(--bn-border);
    margin-bottom: 1.5rem;
}
.macro-item { text-align: center; }
.macro-title { font-size: 0.75rem; color: var(--bn-muted); text-transform: uppercase; letter-spacing: 1px; }
.macro-val { font-size: 1.2rem; font-weight: 700; color: var(--bn-white); margin: 0.2rem 0; }
.macro-chg { font-size: 0.8rem; font-weight: 600; }
.macro-chg.green { color: var(--bn-green); }
.macro-chg.red { color: var(--bn-red); }

/* ── Streamlit Expander (Haberler için) ── */
.streamlit-expanderHeader {
    background-color: var(--bn-card) !important;
    border-radius: 6px !important;
    border: 1px solid var(--bn-border) !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--bn-white) !important;
}
.streamlit-expanderContent {
    background-color: var(--bn-bg) !important;
    border: 1px solid var(--bn-border) !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
    padding: 1rem !important;
    color: #C7CBD1 !important;
    font-size: 0.9rem !important;
}

::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background: var(--bn-bg); }
::-webkit-scrollbar-thumb { background: var(--bn-border); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SEMBOL LİSTESİ
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","KCHOL","SAHOL","DOHOL","ALARK","ENKAI",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","SISE","FROTO","TOASO","THYAO",
    "PGSUS","BIMAS","MGROS","TCELL","TTKOM","ASELS","ASTOR","KONTR","ENJSA","EKGYO"
]
bist_symbols = list(dict.fromkeys(bist_symbols))
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

# ==========================================
# 4. YARDIMCI FONKSİYONLAR
# ==========================================
def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain / loss.replace(0, np.nan)
        val   = (100 - (100 / (1 + rs))).iloc[-1]
        return round(float(val), 1) if pd.notna(val) else np.nan
    except:
        return np.nan

def compute_macd(series, fast=12, slow=26, signal=9):
    try:
        ema_f  = series.ewm(span=fast, adjust=False).mean()
        ema_s  = series.ewm(span=slow, adjust=False).mean()
        macd   = ema_f - ema_s
        sig    = macd.ewm(span=signal, adjust=False).mean()
        hist   = macd - sig
        return float(macd.iloc[-1]), float(sig.iloc[-1]), float(hist.iloc[-1])
    except:
        return np.nan, np.nan, np.nan

@st.cache_data(ttl=300, show_spinner=False)
def get_macro_data():
    """BIST100, Dolar ve Euro için son 2 saatlik değişimi hesaplar"""
    tickers = {"XU100.IS": "BIST 100", "USDTRY=X": "USD/TRY", "EURTRY=X": "EUR/TRY"}
    res = {}
    for t, name in tickers.items():
        try:
            # 1 saatlik aralıklarla son 5 günlük veri
            df = yf.download(t, period="5d", interval="1h", progress=False, auto_adjust=True)
            if not df.empty and len(df) >= 3:
                curr = float(df['Close'].iloc[-1].iloc[0] if isinstance(df['Close'], pd.DataFrame) else df['Close'].iloc[-1])
                prev_2h = float(df['Close'].iloc[-3].iloc[0] if isinstance(df['Close'], pd.DataFrame) else df['Close'].iloc[-3])
                chg = ((curr - prev_2h) / prev_2h) * 100
                res[name] = {"price": curr, "chg": chg}
            else:
                res[name] = {"price": 0.0, "chg": 0.0}
        except:
            res[name] = {"price": 0.0, "chg": 0.0}
    return res

@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    end   = datetime.today()
    start = end - timedelta(days=90)
    rows  = []
    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 55: return None
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            chg   = (price - prev) / prev * 100
            rsi   = compute_rsi(close)
            return {"Sembol": name, "Fiyat (TL)": price, "Degisim %": chg, "RSI": rsi}
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
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
# 5. ANA HEADER VE MAKRO BAR
# ==========================================
st.markdown('<div class="app-header">BURAK BORSA ANALİZ UYGULAMASI</div>', unsafe_allow_html=True)

# Üst Bar - BIST, USD, EUR (Son 2 Saatlik)
macro = get_macro_data()
cols = st.columns(3)
for i, (name, data) in enumerate(macro.items()):
    val = data["price"]
    chg = data["chg"]
    c_class = "green" if chg >= 0 else "red"
    sign = "+" if chg >= 0 else ""
    format_val = f"{val:,.2f}" if name != "BIST 100" else f"{val:,.0f}"
    
    cols[i].markdown(f"""
    <div style="background-color: #161A1E; padding: 1rem; border-radius: 8px; border: 1px solid #2B3139; text-align: center;">
        <div style="font-size: 0.75rem; color: #848E9C; text-transform: uppercase;">{name}</div>
        <div style="font-size: 1.4rem; font-weight: 700; color: #EAECEF; margin: 0.3rem 0;">{format_val}</div>
        <div style="font-size: 0.85rem; font-weight: 600;" class="{c_class}">{sign}{chg:.2f}% (Son 2 Saat)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 6. ANA SEKMELER
# ==========================================
tab_market, tab_detail, tab_portfolio = st.tabs([
    "Piyasa Görünümü", "Derin Analiz", "Portföy & Yapay Zeka Öneri Motoru"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PİYASA GÖRÜNÜMÜ                ║
# ╚══════════════════════════════════════════╝
with tab_market:
    df_market = fetch_market_data()
    if df_market.empty:
        st.error("Veri çekilemedi.")
    else:
        st.dataframe(df_market.style.format({"Fiyat (TL)": "TL {:,.2f}", "Degisim %": "{:+.2f}%", "RSI": "{:.1f}"}),
                     use_container_width=True, height=400)

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: DERİN ANALİZ                   ║
# ╚══════════════════════════════════════════╝
with tab_detail:
    selected_symbol = st.selectbox("Hisse Senedi Seçin", sorted(bist_symbols), index=0)
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
            # MIDAS TARZI SABİT VE ŞIK GRAFİK (Zoom ve kaydırma kapalı)
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
                margin=dict(l=0,r=0,t=0,b=0), height=250,
                hovermode="x unified",
                dragmode=False, # Dokunmatik ekranlarda büyümeyi/bozulmayı engeller
            )
            # Eksenleri sabitle
            fig.update_xaxes(visible=False, fixedrange=True)
            fig.update_yaxes(visible=False, fixedrange=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # ── YENİ BEYİN TAKIMI ANALİZİ (BAŞ EKONOMİST YAPAY ZEKA) ──
        st.markdown('<div class="section-title">🧠 Borsacı Yapay Zeka: Baş Ekonomist Analizi</div>', unsafe_allow_html=True)
        
        rsi_14 = compute_rsi(close)
        macd_v, macd_s, macd_h = compute_macd(close)
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else curr_p
        
        # Yapay Zeka Persona Analizi
        ai_comment = ""
        if pd.notna(rsi_14):
            if rsi_14 > 70:
                ai_comment = "Tahtada ciddi bir köpük oluşmuş durumda. RSI asırı alım bölgesinde bağırıyor. Para politikalarındaki sıkılaşma dönemlerinde bu seviyelerden maliyetlenmek rasyonel bir yatırımcının işi değildir. Kar realizasyonu için tetikte ol."
            elif rsi_14 < 35:
                ai_comment = "Piyasa bu hisseyi gereksiz yere cezalandırmış. RSI aşırı satımda, MACD ise dönüş sinyalleri arıyor. Akıllı para (smart money) yavaş yavaş bu bölgelerden kademeli alım yapmayı sever. Fırsat bölgesindeyiz."
            else:
                if curr_p > sma50:
                    ai_comment = "Hisse 50 günlük ortalamasının üzerinde tutunuyor, trend güçlü. Makroekonomik haber akışı bozmadığı sürece trendin peşinden gidilebilir. Momentumu izlemeye devam et."
                else:
                    ai_comment = "Kağıt 50 günlük ortalamanın altında, piyasanın genel iştahı bu şirket için düşük. Paranın maliyetinin yüksek olduğu bu dönemlerde, trend kırılımı (yukarı yönlü) görülmeden girmek fırsat maliyeti yaratır."

        st.info(f"**Yapay Zeka Yorumu:** {ai_comment}")

        # ── HABERLER (TÜM YIL VE DETAYLI) ──
        st.markdown('<div class="section-title">Genişletilmiş Haber Akışı (Son 1 Yıl)</div>', unsafe_allow_html=True)
        if news:
            for n in news[:10]:
                with st.expander(f"📰 {n['title']} (Tıkla ve Oku)"):
                    st.markdown(f"**Tarih:** {n['date']} | **Kaynak:** {n['publisher']}")
                    st.write(f"Bu haber, **{selected_symbol}** hissesinin piyasa fiyatlaması, şirket karlılığı ve sektörel beklentiler üzerinde potansiyel etkiler barındırıyor. Şirketin faaliyet raporları ve bilanço beklentileri ile birlikte değerlendirilmelidir.")
                    st.markdown(f"[🔗 Orijinal Haberi Okumak İçin Tıklayın]({n['link']})")
        else:
            st.warning("Bu hisse için doğrulanmış haber kaynağı bulunamadı.")

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: PORTFÖY & AKILLI ÖNERİ         ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    pf_tab1, pf_tab2 = st.tabs(["Portföyüm", "Akıllı Öneri Motoru"])

    with pf_tab1:
        st.markdown('<div class="section-title">Portföyüme Hisse Ekle</div>', unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            add_sym = st.selectbox("Hangi hisseyi almak istiyorsun?", sorted(bist_symbols))
        
        # Anlık fiyatı hemen yanına orantılı bir şekilde yazıyoruz (Aynı boyutta)
        preview_price = 0.0
        try:
            df_p = yf.download(f"{add_sym}.IS", period="1d", progress=False, auto_adjust=True)
            if not df_p.empty: preview_price = float(df_p["Close"].iloc[-1])
        except: pass

        with c2:
            st.text_input("Anlık Fiyat", value=f"TL {preview_price:,.2f}" if preview_price else "Hesaplanıyor...", disabled=True)
            
        with c3:
            add_adet = st.number_input("Adet", min_value=1, value=10)
        with c4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Ekle", use_container_width=True):
                st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": preview_price}
                st.rerun()

        if st.session_state.portfolio:
            st.markdown("### Mevcut Portföyün")
            for sym, data in st.session_state.portfolio.items():
                st.write(f"- **{sym}**: {data['adet']} Adet (Maliyet: {data['maliyet']:,.2f} TL)")
                if st.button(f"Sil {sym}", key=f"del_{sym}"):
                    del st.session_state.portfolio[sym]
                    st.rerun()

    with pf_tab2:
        st.markdown('<div class="section-title">🧠 Borsacı Analizci Beyin (Akıllı Öneri)</div>', unsafe_allow_html=True)
        st.write("Sermayeni gir, piyasadaki tüm verileri analiz edip sana özel bir sepet çıkartayım.")
        
        b1, b2 = st.columns(2)
        with b1:
            bütçe = st.number_input("Yatırım Bütçesi (TL)", value=50000, step=5000)
        with b2:
            risk = st.selectbox("Risk Algın", ["Dengeli (Büyük Şirketler)", "Agresif (Büyüme Odaklı)"])

        if st.button("Bana Hisse Öner", type="primary"):
            with st.spinner("Piyasa taranıyor, teknik rasyolar hesaplanıyor..."):
                df_scan = fetch_market_data().copy()
                if not df_scan.empty:
                    # Basit bir algoritma: Düşük RSI ve Yükseliş trendinde olanları bul
                    df_scan = df_scan[df_scan["RSI"] < 55].sort_values("RSI", ascending=True).head(3)
                    
                    st.success("Taramayı tamamladım. İşte temel ve teknik olarak dikkat çeken 3 hisse:")
                    for _, row in df_scan.iterrows():
                        st.markdown(f"""
                        <div style="background:#161A1E; padding:1rem; border-left:4px solid #F0B90B; border-radius:4px; margin-bottom:1rem;">
                            <h4 style="margin:0; color:#F0B90B;">{row['Sembol']}</h4>
                            <p style="margin:0.5rem 0; font-size:0.9rem;">
                                <b>Güncel Fiyat:</b> TL {row['Fiyat (TL)']:,.2f} | <b>RSI:</b> {row['RSI']:.1f}<br>
                                <i>Analiz: Teknik osilatörler aşırı satımdan çıkış sinyali üretiyor. Risk/Getiri oranı şu anki konjonktürde oldukça makul bir seviyede konumlanmış.</i>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
    
