"""
╔══════════════════════════════════════════════════════════════╗
║  MİDAS KLONU  ·  BİST KANTİTATİF ANALİZ & HABER TERMİNALİ    ║
║  Sürüm: v6.0 (BIST Focus & Midas UI Edition)                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures

# ─────────────────────────────────────────────────────────────
#  SAYFA YAPISI
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BIST Analiz & Haber Terminali",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  GLOBAL STİL (MİDAS TEMASI)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d0d0d; /* Midas Koyu Arka Plan */
    color: #e5e5e5;
}

/* ── Midas Renk Paleti ── */
:root {
    --midas-green: #00c853;
    --midas-red: #ff3d00;
    --midas-bg: #0d0d0d;
    --midas-card: #1c1c1e;
    --midas-text-gray: #8e8e93;
    --midas-border: #2c2c2e;
}

/* ── Başlıklar ── */
.app-header {
    font-size: 2.2rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.2rem;
    letter-spacing: -0.03em;
}
.app-subheader {
    font-size: 0.9rem;
    color: var(--midas-text-gray);
    font-weight: 500;
    margin-bottom: 2rem;
}

/* ── Kart Yapıları ── */
.midas-card {
    background-color: var(--midas-card);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid var(--midas-border);
    margin-bottom: 1rem;
}
.midas-card-title {
    font-size: 0.85rem;
    color: var(--midas-text-gray);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.midas-card-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #ffffff;
}
.midas-green-text { color: var(--midas-green) !important; }
.midas-red-text { color: var(--midas-red) !important; }

/* ── Haber Yapısı ── */
.news-item {
    background-color: #1a1a1c;
    border-left: 3px solid #3a3a3c;
    padding: 1rem;
    margin-bottom: 0.8rem;
    border-radius: 6px;
    transition: 0.2s;
}
.news-item:hover { background-color: #242426; border-left-color: var(--midas-green); }
.news-title { font-size: 1rem; font-weight: 600; color: #ffffff; text-decoration: none; display: block; margin-bottom: 0.3rem;}
.news-title:hover { color: var(--midas-green); }
.news-meta { font-size: 0.75rem; color: var(--midas-text-gray); }

/* ── Butonlar & Sidebar ── */
.stButton>button {
    background-color: var(--midas-card);
    color: #ffffff;
    border: 1px solid var(--midas-border);
    border-radius: 8px;
    font-weight: 600;
    transition: 0.2s;
}
.stButton>button:hover { border-color: var(--midas-green); color: var(--midas-green); }
[data-testid="stSidebar"] { background-color: #121212; border-right: 1px solid var(--midas-border); }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
#  BIST HİSSE HAVUZU (GENİŞLETİLMİŞ)
# ═════════════════════════════════════════════════════════════
# Sadece BIST hisseleri. Hatalı olanlar çıkarıldı, en çok işlem gören 60+ hisse eklendi.
TICKERS_BIST = {
    # Bankalar
    "AKBNK.IS": "Akbank", "GARAN.IS": "Garanti BBVA", "ISCTR.IS": "İş Bankası (C)", 
    "YKBNK.IS": "Yapı Kredi", "VAKBN.IS": "Vakıfbank", "HALKB.IS": "Halkbank", "ALBRK.IS": "Albaraka Türk",
    # Holdingler & Konglomeralar
    "KCHOL.IS": "Koç Holding", "SAHOL.IS": "Sabancı Holding", "DOHOL.IS": "Doğan Holding", 
    "ALARK.IS": "Alarko Holding", "ENKAI.IS": "Enka İnşaat", "AGHOL.IS": "AG Anadolu Grubu",
    # Sanayi & Üretim
    "EREGL.IS": "Ereğli Demir Çelik", "KRDMD.IS": "Kardemir (D)", "TUPRS.IS": "Tüpraş", 
    "PETKM.IS": "Petkim", "SASA.IS": "Sasa Polyester", "HEKTS.IS": "Hektaş", "GUBRF.IS": "Gübre Fabrikaları",
    "SISE.IS": "Şişecam", "ARCLK.IS": "Arçelik", "VESTL.IS": "Vestel", "BRISA.IS": "Brisa",
    # Otomotiv
    "FROTO.IS": "Ford Otosan", "TOASO.IS": "Tofaş", "DOAS.IS": "Doğuş Otomotiv", "OTKAR.IS": "Otokar",
    # Havacılık & Ulaşım
    "THYAO.IS": "Türk Hava Yolları", "PGSUS.IS": "Pegasus", "TAVHL.IS": "TAV Havalimanları",
    # Perakende & Gıda
    "BIMAS.IS": "BİM Mağazalar", "MGROS.IS": "Migros", "SOKM.IS": "Şok Marketler", 
    "AEFES.IS": "Anadolu Efes", "CCOLA.IS": "Coca-Cola İçecek", "ULKER.IS": "Ülker Bisküvi",
    # Teknoloji, İletişim & Enerji
    "TCELL.IS": "Turkcell", "TTKOM.IS": "Türk Telekom", "ASELS.IS": "Aselsan", 
    "ASTOR.IS": "Astor Enerji", "KONTR.IS": "Kontrolmatik", "ALFAS.IS": "Alfa Solar Enerji",
    "ENJSA.IS": "Enerjisa", "AKSEN.IS": "Aksa Enerji", "ODAS.IS": "Odaş Elektrik", 
    "SMARTG.IS": "Smart Güneş Teknolojileri", "EUPWR.IS": "Europower Enerji", "MIATK.IS": "MIA Teknoloji",
    # GYO
    "EKGYO.IS": "Emlak Konut GYO", "ISGYO.IS": "İş GYO", "TRGYO.IS": "Torunlar GYO"
}

# ═════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ═════════════════════════════════════════════════════════════
def fmt_tl(val: float) -> str:
    if pd.isna(val) or val == 0: return "—"
    return f"₺{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_number(num):
    if pd.isna(num): return "—"
    if num >= 1_000_000_000: return f"₺{num/1_000_000_000:.2f} Milyar"
    if num >= 1_000_000: return f"₺{num/1_000_000:.2f} Milyon"
    return f"₺{num:,.2f}"

def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    val = (100 - (100 / (1 + rs))).iloc[-1]
    return round(float(val), 1) if pd.notna(val) else np.nan

def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> float:
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    return round(float(atr), 4) if pd.notna(atr) else np.nan

def get_midas_action(rsi, price, sma50):
    if pd.isna(rsi): return "TUT", "#8e8e93"
    if rsi < 35 and price > sma50: return "GÜÇLÜ AL", "#00c853"
    if rsi < 40: return "AL", "#00c853"
    if rsi > 70: return "SAT", "#ff3d00"
    if rsi > 65 and price < sma50: return "GÜÇLÜ SAT", "#ff3d00"
    return "TUT", "#8e8e93"

# ═════════════════════════════════════════════════════════════
#  VERİ ÇEKME (MULTI-THREADING)
# ═════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def fetch_screener_data() -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=365)
    rows = []

    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 60: return None
            
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            chg_pct = (price - prev_price) / prev_price * 100
            
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            
            action, _ = get_midas_action(rsi, price, sma50)
            
            return {
                "Sembol": ticker.replace(".IS", ""), "Şirket": name, "Fiyat (₺)": price, 
                "Değişim %": chg_pct, "RSI": rsi, "Aksiyon": action
            }
        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None: rows.append(res)

    return pd.DataFrame(rows)

# ═════════════════════════════════════════════════════════════
#  DETAYLI HİSSE BİLGİSİ VE HABERLER ÇEKİMİ
# ═════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def get_stock_details(ticker: str):
    stock = yf.Ticker(ticker)
    info = {}
    news = []
    hist = pd.DataFrame()
    try:
        info = stock.info
        news = stock.news
        hist = stock.history(period="6mo")
    except:
        pass
    return info, news, hist

# ═════════════════════════════════════════════════════════════
#  SİDEBAR & ARAYÜZ
# ═════════════════════════════════════════════════════════════
st.markdown('<div class="app-header">BIST Terminal</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subheader">Gerçek Zamanlı Piyasa Analizi ve Haber Akışı</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Filtreler")
    sinyal_filtre = st.multiselect("Aksiyon", ["GÜÇLÜ AL", "AL", "SAT", "GÜÇLÜ SAT", "TUT"], default=["GÜÇLÜ AL", "AL", "SAT", "GÜÇLÜ SAT", "TUT"])
    st.markdown("---")
    st.markdown("BIST Verileri **Yahoo Finance** üzerinden gecikmeli olarak sağlanmaktadır. Yatırım tavsiyesi içermez.")

# ═════════════════════════════════════════════════════════════
#  ANA PİYASA TABLOSU (SCREENER)
# ═════════════════════════════════════════════════════════════
with st.spinner("Piyasa verileri taranıyor..."):
    df_screener = fetch_screener_data()

if df_screener.empty:
    st.error("Veri çekilemedi. İnternet bağlantınızı kontrol edin.")
else:
    # Filtreleme
    if sinyal_filtre: df_screener = df_screener[df_screener["Aksiyon"].isin(sinyal_filtre)]
    
    st.markdown("#### 📋 Borsa İstanbul Görünümü")
    
    # Tablo Stili
    def style_table(df):
        s = pd.DataFrame("", index=df.index, columns=df.columns)
        for i, row in df.iterrows():
            chg = row.get("Değişim %")
            if pd.notna(chg): s.loc[i, "Değişim %"] = "color:#00c853; font-weight:bold" if chg >= 0 else "color:#ff3d00; font-weight:bold"
            
            act = row.get("Aksiyon")
            if "AL" in act: s.loc[i, "Aksiyon"] = "color:#00c853; font-weight:bold"
            elif "SAT" in act: s.loc[i, "Aksiyon"] = "color:#ff3d00; font-weight:bold"
            else: s.loc[i, "Aksiyon"] = "color:#8e8e93"
        return s

    display_df = df_screener.copy()
    styled = display_df.style.apply(style_table, axis=None).format({"Değişim %": "{:+.2f}%", "Fiyat (₺)": "₺{:,.2f}", "RSI": "{:.1f}"}, na_rep="—")
    st.dataframe(styled, use_container_width=True, height=250, hide_index=True)

# ═════════════════════════════════════════════════════════════
#  DETAYLI HİSSE ANALİZİ VE HABERLER (MİDAS STİLİ)
# ═════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("#### 🔍 Hisse Detayı ve Şirket Haberleri")

# Hisse Seçimi
ticker_list = [f"{t} - {n}" for t, n in TICKERS_BIST.items()]
selected_option = st.selectbox("İncelemek istediğiniz hisseyi seçin:", ticker_list)
selected_ticker = selected_option.split(" - ")[0]
company_name = selected_option.split(" - ")[1]

if selected_ticker:
    with st.spinner(f"{company_name} detayları ve haberleri yükleniyor..."):
        info, news, hist = get_stock_details(selected_ticker)
        
    if not hist.empty:
        current_price = float(hist["Close"].iloc[-1])
        prev_price = float(hist["Close"].iloc[-2])
        price_chg = current_price - prev_price
        pct_chg = (price_chg / prev_price) * 100
        
        color_class = "midas-green-text" if price_chg >= 0 else "midas-red-text"
        sign = "+" if price_chg >= 0 else ""

        # Üst Panel: Fiyat ve Grafik
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div class="midas-card" style="height: 100%;">
                <div style="font-size: 1.2rem; font-weight: 700;">{selected_ticker.replace('.IS', '')}</div>
                <div style="font-size: 0.9rem; color: #8e8e93; margin-bottom: 1rem;">{company_name}</div>
                <div style="font-size: 2.5rem; font-weight: 800;">{fmt_tl(current_price)}</div>
                <div class="{color_class}" style="font-size: 1.1rem; font-weight: 600;">
                    {sign}{fmt_tl(price_chg)} ({sign}{pct_chg:.2f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            # Mini Grafik
            fig = go.Figure()
            line_color = "#00c853" if price_chg >= 0 else "#ff3d00"
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', line=dict(color=line_color, width=3), fill='tozeroy', fillcolor=f"rgba({0 if price_chg >=0 else 255}, {200 if price_chg >=0 else 61}, {83 if price_chg >=0 else 0}, 0.1)"))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0), height=180,
                xaxis=dict(visible=False), yaxis=dict(visible=False)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Orta Panel: Şirket Çarpanları ve Analiz
        st.markdown("##### Şirket Çarpanları & Kantitatif Veriler")
        
        # YFinance'dan Temel Verileri Alma (Türkiye için bazen eksik olabilir, güvenli alma)
        market_cap = info.get("marketCap", np.nan)
        pe_ratio = info.get("trailingPE", np.nan)
        pb_ratio = info.get("priceToBook", np.nan)
        volume = hist["Volume"].iloc[-1] if "Volume" in hist.columns else np.nan
        high_52 = info.get("fiftyTwoWeekHigh", hist["High"].max())
        low_52 = info.get("fiftyTwoWeekLow", hist["Low"].min())
        
        # Kuantitatif Veriler
        rsi_val = compute_rsi(hist["Close"])
        atr_val = compute_atr(hist["High"], hist["Low"], hist["Close"])
        sma50_val = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else np.nan
        
        action_lbl, action_color = get_midas_action(rsi_val, current_price, sma50_val)
        
        t1_hedef = current_price + (1.5 * atr_val) if pd.notna(atr_val) else np.nan
        stop_los = current_price - (1.2 * atr_val) if pd.notna(atr_val) else np.nan

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">Piyasa Değeri</div><div class="midas-card-value" style="font-size:1.3rem;">{format_number(market_cap)}</div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">RSI (14)</div><div class="midas-card-value" style="font-size:1.3rem;">{rsi_val:.1f}</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">F/K Oranı</div><div class="midas-card-value" style="font-size:1.3rem;">{pe_ratio if pd.notna(pe_ratio) else '—'}</div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">Algoritma Sinyali</div><div class="midas-card-value" style="font-size:1.3rem; color:{action_color}">{action_lbl}</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">PD/DD Oranı</div><div class="midas-card-value" style="font-size:1.3rem;">{pb_ratio if pd.notna(pb_ratio) else '—'}</div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">Kısa Vade Hedef</div><div class="midas-card-value" style="font-size:1.3rem; color:#00c853;">{fmt_tl(t1_hedef)}</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">52 Hafta Zirve/Dip</div><div style="font-size:1rem; color:#fff; font-weight:600;">{fmt_tl(high_52)} / {fmt_tl(low_52)}</div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="midas-card"><div class="midas-card-title">Teknik Stop-Loss</div><div class="midas-card-value" style="font-size:1.3rem; color:#ff3d00;">{fmt_tl(stop_los)}</div></div>""", unsafe_allow_html=True)

        # Alt Panel: Şirket Haberleri
        st.markdown("<br>##### 📰 Şirket Haberleri", unsafe_allow_html=True)
        
        if news and len(news) > 0:
            for n in news[:6]: # Son 6 haberi göster
                pub_time = datetime.fromtimestamp(n.get('providerPublishTime', 0)).strftime('%d %B %Y, %H:%M')
                title = n.get('title', 'Başlık Bulunamadı')
                link = n.get('link', '#')
                publisher = n.get('publisher', 'Haber Kaynağı')
                
                st.markdown(f"""
                <div class="news-item">
                    <a href="{link}" target="_blank" class="news-title">{title}</a>
                    <div class="news-meta">{publisher} • {pub_time}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Bu şirket için Yahoo Finance kaynaklı güncel haber bulunamadı.")
            
    else:
        st.warning("Seçilen hisse için fiyat verisi çekilemedi.")

st.markdown("""<div style="font-family:'Inter',sans-serif;font-size:0.75rem;color:#555;text-align:center;border-top:1px solid #2c2c2e;padding-top:1.5rem;margin-top:3rem;">
Bu platform sadece bilgilendirme ve eğitim amaçlıdır. Veriler gecikmeli olabilir. Yatırım tavsiyesi değildir.
</div>""", unsafe_allow_html=True)
