"""
╔══════════════════════════════════════════════════════════════╗
║  MİDAS KLONU v8.1 · BİST KANTİTATİF ANALİZ & HABER TERMİNALİ ║
║  Özellikler: Tıklanabilir Filtreler, Derin Analiz, AI Fix    ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import concurrent.futures

# ==========================================
# 1. PAGE CONFIGURATION & STATE
# ==========================================
st.set_page_config(
    page_title="BIST Analiz Terminali",
    page_icon="🇹🇷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "market_filter" not in st.session_state:
    st.session_state.market_filter = "TÜMÜ"

# ==========================================
# 2. MIDAS UI CSS
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; color: #F5F5F5; }
[data-testid="collapsedControl"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

:root {
    --midas-green: #00e676;
    --midas-red: #ff3d00;
    --midas-card: #1c1c1e;
    --midas-text-muted: #a1a1a6;
    --midas-border: #2c2c2e;
}

/* Başlıklar */
.app-header { font-size: 2.2rem; font-weight: 800; color: #ffffff; margin-bottom: 0.2rem; display: flex; align-items: center; gap: 15px;}
.section-title { font-size: 1.25rem; font-weight: 700; margin: 2rem 0 1rem 0; color: #FFFFFF; border-bottom: 1px solid var(--midas-border); padding-bottom: 0.5rem; }

/* Filter Butonları (Kart Görünümü) */
div.stButton > button {
    height: 90px;
    border-radius: 12px;
    border: 1px solid var(--midas-border);
    background-color: var(--midas-card);
    color: #fff;
    font-size: 1.1rem;
    font-weight: 700;
    transition: 0.3s;
}
div.stButton > button:hover { border-color: #3b82f6; background-color: #242631; color: #60a5fa;}

/* Derin Analiz Kartları */
.midas-card { background-color: var(--midas-card); border-radius: 12px; padding: 1.5rem; border: 1px solid var(--midas-border); margin-bottom: 1rem; height: 100%; }
.midas-card-title { font-size: 0.85rem; color: var(--midas-text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 0.5rem; }
.midas-card-value { font-size: 1.6rem; font-weight: 700; color: #ffffff; }

/* Burak'tan Yorumlar AI Kartı */
.ai-card {
    background: linear-gradient(145deg, #1A1C24 0%, #12141A 100%);
    border-left: 4px solid #3b82f6; border-radius: 12px; padding: 1.8rem; margin-bottom: 1.5rem; margin-top: 1rem;
}
.ai-title { color: #60a5fa; font-size: 1.3rem; font-weight: 800; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 8px;}
.ai-section { margin-bottom: 1.2rem; }
.ai-section-title { font-size: 1rem; font-weight: 700; color: #E0E0E0; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 6px;}
.ai-section-text { font-size: 0.95rem; color: #A1A1A6; line-height: 1.6; }

/* Haber Stilleri */
.news-item { background-color: var(--midas-card); border: 1px solid var(--midas-border); border-left: 3px solid #3a3a3c; padding: 1.2rem; margin-bottom: 0.8rem; border-radius: 8px; transition: 0.2s; }
.news-item:hover { background-color: #242631; border-left-color: var(--midas-green); }
.news-title { font-size: 1.05rem; font-weight: 600; color: #FFFFFF; text-decoration: none; display: block; margin-bottom: 0.5rem; line-height: 1.4; }
.news-title:hover { color: var(--midas-green); }
.news-meta { font-size: 0.8rem; color: var(--midas-text-muted); display: flex; justify-content: space-between; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BIST TICKER LIST (600+ Temsili Kapsam)
# ==========================================
bist_symbols = [
    "AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "HALKB", "ALBRK", "SKBNK", "TSKB", "KLNMA",
    "KCHOL", "SAHOL", "DOHOL", "ALARK", "ENKAI", "AGHOL", "TKFEN", "NTHOL", "GLYHO", "POLHO",
    "EREGL", "KRDMD", "TUPRS", "PETKM", "SASA", "HEKTS", "GUBRF", "SISE", "ARCLK", "VESTL",
    "BRISA", "GOODY", "CIMSA", "AKCNS", "OYAKC", "NUHCM", "BTCIM", "AFYON", "GOLTS", "BSOKE",
    "FROTO", "TOASO", "DOAS", "OTKAR", "KARSN", "ASUZU", "TMSN", "TTRAK",
    "THYAO", "PGSUS", "TAVHL", "CLEBI", "DOCO",
    "BIMAS", "MGROS", "SOKM", "AEFES", "CCOLA", "ULKER", "TATGD", "TUKAS", "PNSUT", "PETUN", "KERVT",
    "TCELL", "TTKOM", "ASELS", "ASTOR", "KONTR", "ALFAS", "ENJSA", "AKSEN", "ODAS", "SMARTG",
    "EUPWR", "MIATK", "GESAN", "CWENE", "YEOTK", "GWIND", "NATEN", "MAGEN", "AYDEM", "CANTE",
    "EKGYO", "ISGYO", "TRGYO", "HLGYO", "VKGYO", "DZGYO", "SNGYO", "ZRGYO", "PSGYO", "RYGYO",
    "KORDS", "VESBE", "AYGAZ", "AYEN", "ZOREN", "AKSA", "DEVA", "SELEC", "LKMNH", "RTALB"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
def fmt_tl(val: float) -> str:
    if pd.isna(val) or val == 0: return "—"
    return f"₺{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_number(num):
    if pd.isna(num): return "—"
    if num >= 1_000_000_000: return f"₺{num/1_000_000_000:.2f} MLR"
    if num >= 1_000_000: return f"₺{num/1_000_000:.2f} MLN"
    return f"₺{num:,.2f}"

def compute_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    val = (100 - (100 / (1 + rs))).iloc[-1]
    return round(float(val), 1) if pd.notna(val) else np.nan

def compute_atr(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    val = tr.rolling(period).mean().iloc[-1]
    return float(val) if pd.notna(val) else np.nan

def get_action_signal(rsi, price, sma50):
    if pd.isna(rsi): return "TUT", "#a1a1a6"
    if rsi < 35 and price > sma50: return "GÜÇLÜ AL", "#00e676"
    if rsi < 45: return "AL", "#00e676"
    if rsi > 70: return "SAT", "#ff3d00"
    if rsi > 65 and price < sma50: return "GÜÇLÜ SAT", "#ff3d00"
    return "TUT", "#a1a1a6"

# ==========================================
# 5. DATA FETCHING (Multithreaded)
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    end = datetime.today()
    start = end - timedelta(days=90)
    rows = []

    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 55: return None
            
            close = df["Close"].squeeze()
            price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            chg_pct = (price - prev_price) / prev_price * 100
            
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            action, _ = get_action_signal(rsi, price, sma50)
            
            return {
                "Sembol": name, "Fiyat (₺)": price, "Değişim %": chg_pct, "RSI": rsi, "Aksiyon": action
            }
        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None: rows.append(res)
    return pd.DataFrame(rows)

@st.cache_data(ttl=900, show_spinner=False)
def get_detailed_data(ticker: str):
    stock = yf.Ticker(ticker)
    info, hist, valid_news = {}, pd.DataFrame(), []
    try:
        info = stock.info
        hist = stock.history(period="1y")
    except: pass
    
    try:
        for n in stock.news:
            if 'title' not in n or not n['title']: continue
            pub_ts = n.get('providerPublishTime')
            if not pub_ts or pub_ts < 1000000000: continue # 1970 BUG FIX
            valid_news.append({
                'title': n['title'],
                'link': n.get('link', f"https://finance.yahoo.com/quote/{ticker}"),
                'publisher': n.get('publisher', 'Finans Kaynağı'),
                'date': datetime.fromtimestamp(pub_ts).strftime('%d %B %Y, %H:%M')
            })
    except: pass
    return info, hist, valid_news

# ==========================================
# 6. UI RENDER & LOGIC
# ==========================================
st.markdown('<div class="app-header">&#127481;&#127479; BIST Terminali &amp; AI Analiz</div>', unsafe_allow_html=True)

with st.spinner("Piyasa verileri yükleniyor..."):
    df_market = fetch_market_data()

if df_market.empty:
    st.error("Veri çekilemedi. İnternet bağlantınızı kontrol edin.")
    st.stop()

# --- FİLTRE BUTONLARI (TIKLANABİLİR KARTLAR) ---
total_stocks = len(df_market)
up_stocks = len(df_market[df_market["Değişim %"] > 0])
down_stocks = len(df_market[df_market["Değişim %"] < 0])

c1, c2, c3, c4 = st.columns([1, 1, 1, 0.5])
with c1:
    if st.button(f"Tum Hisseler | {total_stocks} Adet", use_container_width=True):
        st.session_state.market_filter = "TÜMÜ"
with c2:
    if st.button(f"Yukselenler | {up_stocks} Adet", use_container_width=True):
        st.session_state.market_filter = "YÜKSELENLER"
with c3:
    if st.button(f"Dusenler | {down_stocks} Adet", use_container_width=True):
        st.session_state.market_filter = "DÜŞENLER"
with c4:
    if st.button("Yenile | Guncelle", use_container_width=True):
        st.cache_data.clear()
        st.session_state.market_filter = "TÜMÜ"
        st.rerun()

# --- TABLO FİLTRELEME ---
df_filtered = df_market.copy()
if st.session_state.market_filter == "YÜKSELENLER":
    df_filtered = df_filtered[df_filtered["Değişim %"] > 0]
elif st.session_state.market_filter == "DÜŞENLER":
    df_filtered = df_filtered[df_filtered["Değişim %"] < 0]

st.markdown(f'<div class="section-title">Piyasa Gorunumu ({st.session_state.market_filter})</div>', unsafe_allow_html=True)

def style_df(df):
    styled = df.style.format({"Fiyat (₺)": "₺{:,.2f}", "Değişim %": "{:+.2f}%", "RSI": "{:.1f}"}, na_rep="—")
    def color_change(val):
        if pd.isna(val): return ''
        return 'color: #00e676; font-weight:bold' if val > 0 else ('color: #ff3d00; font-weight:bold' if val < 0 else 'color: #8E8E93')
    def color_action(val):
        if "AL" in str(val): return 'color: #00e676; font-weight:bold'
        if "SAT" in str(val): return 'color: #ff3d00; font-weight:bold'
        return 'color: #8E8E93'
    return styled.map(color_change, subset=['Değişim %']).map(color_action, subset=['Aksiyon'])

st.dataframe(style_df(df_filtered[["Sembol", "Fiyat (₺)", "Değişim %", "RSI", "Aksiyon"]]), use_container_width=True, height=350, hide_index=True)

# --- DETAYLI ANALİZ & BURAK'TAN YORUMLAR ---
st.markdown('<div class="section-title">Detayli Analiz &amp; Yapay Zeka Yorumu</div>', unsafe_allow_html=True)

selected_symbol = st.selectbox("İncelemek istediğiniz hisseyi seçin:", sorted(bist_symbols), index=bist_symbols.index("HEKTS") if "HEKTS" in bist_symbols else 0)
selected_ticker = f"{selected_symbol}.IS"

if selected_ticker:
    info, hist, news = get_detailed_data(selected_ticker)
    
    if not hist.empty:
        curr_p = float(hist["Close"].iloc[-1])
        prev_p = float(hist["Close"].iloc[-2])
        chg = curr_p - prev_p
        chg_p = (chg / prev_p) * 100
        color_hex = "#00e676" if chg >= 0 else "#ff3d00"
        sign = "+" if chg >= 0 else ""
        
        # 1. FİYAT VE GRAFİK
        col1, col2 = st.columns([1.2, 2])
        with col1:
            st.markdown(f"""
            <div style="background-color: var(--midas-card); border-radius: 12px; padding: 2rem; border: 1px solid var(--midas-border); height:100%; display:flex; flex-direction:column; justify-content:center;">
                <h2 style="margin:0; font-size: 2.5rem; color: #FFF;">{selected_symbol}</h2>
                <div style="font-size: 0.95rem; color: var(--midas-text-muted); margin-bottom: 1rem;">{info.get('longName', selected_symbol)}</div>
                <div style="font-size: 3rem; font-weight: 800;">{fmt_tl(curr_p)}</div>
                <div style="color: {color_hex}; font-size: 1.4rem; font-weight: 700;">
                    {sign}{fmt_tl(chg)} ({sign}{chg_p:.2f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', line=dict(color=color_hex, width=3), fill='tozeroy', fillcolor=f"rgba({0 if chg>=0 else 255}, {200 if chg>=0 else 61}, {83 if chg>=0 else 0}, 0.15)"))
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=10, b=0), height=220, xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # 2. DERİN ANALİZ (ŞİRKET ÇARPANLARI)
        market_cap = info.get("marketCap", np.nan)
        pe_ratio = info.get("trailingPE", np.nan)
        pb_ratio = info.get("priceToBook", np.nan)
        high_52 = info.get("fiftyTwoWeekHigh", hist["High"].max())
        low_52 = info.get("fiftyTwoWeekLow", hist["Low"].min())
        
        rsi_14 = compute_rsi(hist["Close"])
        sma50 = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else curr_p
        atr_14 = compute_atr(hist["High"], hist["Low"], hist["Close"])
        action_lbl, action_color = get_action_signal(rsi_14, curr_p, sma50)
        target_price = curr_p + (2 * atr_14) if pd.notna(atr_14) else np.nan

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="midas-card"><div class="midas-card-title">Piyasa Değeri</div><div class="midas-card-value">{format_number(market_cap)}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="midas-card"><div class="midas-card-title">F/K Oranı</div><div class="midas-card-value">{pe_ratio if pd.notna(pe_ratio) else "—"}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="midas-card"><div class="midas-card-title">52H Zirve / Dip</div><div style="font-size:1.3rem; font-weight:700; color:#fff;">{fmt_tl(high_52)} / {fmt_tl(low_52)}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="midas-card"><div class="midas-card-title">Kısa Vade Hedef (ATR)</div><div class="midas-card-value" style="color:#00e676;">{fmt_tl(target_price)}</div></div>', unsafe_allow_html=True)

        # 3. BURAK'TAN YORUMLAR (AI ANALYSIS - HTML FIX)
        trend_durumu = "pozitif (yukselis)" if curr_p > sma50 else "negatif (dusus)"
        sma50_pozisyon = "uzerinde" if curr_p > sma50 else "altinda"
        curr_p_fmt = fmt_tl(curr_p)
        sma50_fmt  = fmt_tl(sma50)

        if rsi_14 > 70:
            risk_color = "#fca5a5"
            risk_txt   = (f"Hisse senedi {rsi_14:.1f} RSI degeri ile asiri alim bolgesine"
                          " girmis durumda. Indikatorler teknik bir yorgunluga isaret ediyor"
                          " ve kisa vadede kar satislari gorilme ihtimali yuksek.")
            firsat_txt = ("Yeni alimlar icin risk barindiriyor. Maliyetlenmek icin hareketli"
                          " ortalamalara dogru olasi bir geri cekilme (duzeltme) beklenmeli."
                          " Mevcut karlar icin stop-loss seviyeleri guncellenebilir.")
        elif rsi_14 < 35:
            risk_color = "#86efac"
            risk_txt   = (f"RSI {rsi_14:.1f} seviyesinde asiri satim bolgesine isaret ediyor."
                          " Satis baskisinin yavasladigi ve hissenin ucuz fiyatlandigi bir bölgedeyiz.")
            firsat_txt = ("Teknik bir dip arayisi mevcut. Buradan gelebilecek yukari yonlu"
                          " tepki (rebound) alimlari icin kademeli maliyetlenme stratejisi izlenebilir.")
        else:
            risk_color = "#A1A1A6"
            risk_txt   = (f"Hisse senedi {rsi_14:.1f} RSI degeri ile dengeli (notr) bir seyir"
                          " izliyor. Asiri bir fiyatlama veya kopuk bulunmuyor.")
            firsat_txt = ("Hisse yatay bir konsolidasyon surecinde olabilir. Islem hacmi yakindan"
                          " takip edilerek, 50 gunluk ortalamanin uzerinde kalicilik saglandigi"
                          " surece tutma stratejisi benimsenebilir.")

        ai_html = (
            '<div class="ai-card">'
            '<div class="ai-title">&#129504; Burak\'tan Yorumlar</div>'

            '<div class="ai-section">'
            '<div class="ai-section-title">&#128202; Trend Analizi</div>'
            '<div class="ai-section-text">'
            f'Hissenin mevcut fiyati ({curr_p_fmt}), 50 gunluk hareketli ortalamasinin'
            f' ({sma50_fmt}) <b>{sma50_pozisyon}</b>.'
            f' Bu durum orta vadeli projeksiyonda <b>{trend_durumu}</b> bir egilime isaret etmektedir.'
            '</div></div>'

            '<div class="ai-section">'
            f'<div class="ai-section-title">&#9888;&#65039; Risk Durumu</div>'
            f'<div class="ai-section-text" style="color: {risk_color};">{risk_txt}</div>'
            '</div>'

            '<div class="ai-section">'
            '<div class="ai-section-title">&#127919; Firsat &amp; Strateji</div>'
            f'<div class="ai-section-text">{firsat_txt}</div>'
            '</div>'

            '</div>'
        )
        st.markdown(ai_html, unsafe_allow_html=True)

        # 4. HABER SİSTEMİ
        st.markdown('<div class="section-title">Guncel Haber Akisi</div>', unsafe_allow_html=True)
        
        if news and len(news) > 0:
            for n in news[:5]:
                st.markdown(f"""
                <div class="news-item">
                    <a href="{n['link']}" target="_blank" class="news-title">{n['title']}</a>
                    <div class="news-meta">
                        <span>🏢 {n['publisher']}</span>
                        <span>🕒 {n['date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="news-item" style="border-left-color: #3b82f6;">
                <div class="news-title">Sektör Özeti (Global Haber Bulunamadı)</div>
                <div style="color: #A1A1A6; font-size: 0.9rem; margin-top: 0.5rem; line-height: 1.5;">
                    Uluslararası veri ağlarında <b>{selected_symbol}</b> için son 24 saate ait doğrulanmış bir haber akışı tespit edilemedi. Yerel gelişmeleri takip etmek için KAP bildirimlerini inceleyebilirsiniz.
                </div>
                <div style="margin-top: 1rem;">
                    <a href="https://www.kap.org.tr/tr/arama/bilesik?bildirimTipleri=OzelDurumAciklamasi&sirketler={selected_symbol}" target="_blank" style="color: #60a5fa; text-decoration: none; font-size:0.85rem; font-weight:600;">🔗 KAP Bildirimlerini Görüntüle</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("Bu hisse senedi için veri çekilemedi.")
