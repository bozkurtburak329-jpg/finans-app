"""
╔══════════════════════════════════════════════════════════════╗
║  MİDAS KLONU v10.0 · BİST KANTİTATİF ANALİZ & TERMİNALİ      ║
║  Özellikler: Canlı Kur, Akıllı Swap Önerisi, Simülasyon      ║
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
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="BIST Analiz Terminali",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "market_filter" not in st.session_state:
    st.session_state.market_filter = "TÜMÜ"
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}

# ==========================================
# 2. MİDAS DARK TEMA CSS
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

/* ── Makro Veri Paneli (Top Bar) ── */
.macro-container {
    display: flex; justify-content: space-between; align-items: center;
    background: linear-gradient(135deg, #161A1E 0%, #0F1216 100%);
    border: 1px solid var(--bn-border); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;
}
.bist-box { display: flex; flex-direction: column; border-right: 1px solid var(--bn-border); padding-right: 2rem; }
.bist-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.9rem; color: var(--bn-muted); letter-spacing: 0.1em; }
.bist-price { font-size: 3rem; font-weight: 800; color: var(--bn-white); line-height: 1.1; }
.bist-chg { font-size: 1.2rem; font-weight: 600; }

.currency-box { display: flex; gap: 2rem; padding-left: 1rem; flex-wrap: wrap;}
.cur-item { display: flex; flex-direction: column; }
.cur-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: var(--bn-muted); }
.cur-price { font-size: 1.4rem; font-weight: 700; color: var(--bn-white); }
.cur-chg { font-size: 0.85rem; font-weight: 600; }

/* ── Diğer Stiller ── */
.section-title { font-size: 1.2rem; font-weight: 700; color: var(--bn-white); border-bottom: 1px solid var(--bn-border); padding-bottom: 0.5rem; margin: 2rem 0 1rem 0; }
div.stButton > button { border-radius: 8px; border: 1px solid var(--bn-border); background-color: var(--bn-card2); color: var(--bn-white); font-weight: 600; transition: all 0.2s; }
div.stButton > button:hover { border-color: var(--bn-yellow); color: var(--bn-yellow); }

.bn-card { background-color: var(--bn-card); border-radius: 8px; padding: 1.2rem; border: 1px solid var(--bn-border); margin-bottom: 0.8rem; }
.bn-card-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: var(--bn-muted); text-transform: uppercase; margin-bottom: 0.4rem; }
.bn-card-value { font-size: 1.5rem; font-weight: 700; color: var(--bn-white); }

.forecast-card { background: linear-gradient(135deg, #0D1F12 0%, #0B1A10 100%); border: 1px solid #1B4332; border-radius: 8px; padding: 1.4rem; margin: 0.5rem 0; }
.forecast-card.base { background: linear-gradient(135deg, #0D1525 0%, #0B1220 100%); border-color: #1A3A6B; }
.forecast-card.bear { background: linear-gradient(135deg, #1A0A0D 0%, #160810 100%); border-color: #4A1020; }

/* Akıllı Swap Öneri Kartı */
.swap-card { background: linear-gradient(135deg, #2A0A10 0%, #160810 100%); border: 1px solid #5C1525; border-left: 4px solid var(--bn-red); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }

[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input { background-color: var(--bn-card2) !important; border: 1px solid var(--bn-border) !important; color: var(--bn-white) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. BIST SEMBOL LİSTESİ VE FONKSİYONLAR
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","HALKB","KCHOL","SAHOL","DOHOL","ALARK",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","SISE","ARCLK","VESTL",
    "FROTO","TOASO","DOAS","OTKAR","THYAO","PGSUS","BIMAS","MGROS","SOKM","AEFES",
    "TCELL","TTKOM","ASELS","ASTOR","KONTR","ALFAS","ENJSA","AKSEN","ZOREN","EKGYO"
]
TICKERS_BIST = {f"{sym}.IS": sym for sym in bist_symbols}

def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain / loss.replace(0, np.nan)
        return round(float((100 - (100 / (1 + rs))).iloc[-1]), 1)
    except: return np.nan

def compute_macd(series, fast=12, slow=26, signal=9):
    try:
        ema_f = series.ewm(span=fast, adjust=False).mean()
        ema_s = series.ewm(span=slow, adjust=False).mean()
        macd  = ema_f - ema_s
        sig   = macd.ewm(span=signal, adjust=False).mean()
        return float(macd.iloc[-1]), float(sig.iloc[-1]), float((macd - sig).iloc[-1])
    except: return np.nan, np.nan, np.nan

def get_action_signal(rsi, price, sma50):
    if pd.isna(rsi): return "TUT"
    if rsi < 35 and price > sma50: return "GUCLU AL"
    if rsi < 45: return "AL"
    if rsi > 70: return "SAT"
    if rsi > 65 and price < sma50: return "GUCLU SAT"
    return "TUT"

def yil_sonu_tahmini(close_series, rsi, macd_hist, price, sma50):
    if len(close_series) < 60: return None
    returns = close_series.pct_change().dropna()
    mu, sigma = float(returns.mean()), float(returns.std())
    n_days = max(1, (datetime(datetime.today().year, 12, 31) - datetime.today()).days)
    
    score = 0.0
    if pd.notna(rsi):
        if rsi < 35: score += 0.4
        elif rsi > 70: score -= 0.4
    if pd.notna(macd_hist): score += 0.3 if macd_hist > 0 else -0.3
    if pd.notna(price) and pd.notna(sma50) and sma50 > 0: score += 0.3 if price > sma50 else -0.3
    
    mu_adj = mu + (score * 0.0008)
    np.random.seed(42)
    sim_returns = np.random.normal(mu_adj, sigma, (n_days, 1000))
    sim_paths = price * np.exp(np.cumsum(sim_returns, axis=0))
    final_prices = sim_paths[-1]
    
    return {
        "bull": float(np.percentile(final_prices, 75)),
        "base": float(np.percentile(final_prices, 50)),
        "bear": float(np.percentile(final_prices, 25))
    }

# ==========================================
# 4. VERİ ÇEKME FONKSİYONLARI (Makro + BIST)
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_macro_data():
    macro = {}
    tickers = {"XU100.IS": "BIST100", "TRY=X": "USD", "EURTRY=X": "EUR", "GC=F": "GOLD_ONS"}
    
    def get_data(t):
        try:
            df = yf.download(t, period="5d", progress=False)
            if not df.empty and len(df) >= 2:
                c, p = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2])
                return {"price": c, "chg": (c - p) / p * 100}
        except: return {"price": 0, "chg": 0}
        return {"price": 0, "chg": 0}

    with concurrent.futures.ThreadPoolExecutor() as ex:
        results = list(ex.map(get_data, tickers.keys()))
    
    for i, t in enumerate(tickers.values()): macro[t] = results[i]
    
    # Gram Altın Hesaplama
    try:
        ons, usd = macro["GOLD_ONS"]["price"], macro["USD"]["price"]
        gram = (ons / 31.1034768) * usd
        macro["GRAM_ALTIN"] = {"price": gram, "chg": macro["GOLD_ONS"]["chg"] + macro["USD"]["chg"]} # Yaklaşık değişim
    except: macro["GRAM_ALTIN"] = {"price": 0, "chg": 0}
    
    return macro

@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data():
    end, start = datetime.today(), datetime.today() - timedelta(days=90)
    rows = []
    def process_ticker(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 55: return None
            close = df["Close"].squeeze()
            price, prev = float(close.iloc[-1]), float(close.iloc[-2])
            sma50, rsi = float(close.rolling(50).mean().iloc[-1]), compute_rsi(close)
            _, _, macd_h = compute_macd(close)
            return {"Sembol": name, "Fiyat (TL)": price, "Degisim %": (price - prev) / prev * 100, 
                    "RSI": rsi, "MACD_H": macd_h, "Aksiyon": get_action_signal(rsi, price, sma50), "SMA50": sma50}
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: rows.append(res)
    return pd.DataFrame(rows)

@st.cache_data(ttl=60, show_spinner=False)
def get_current_price(ticker: str):
    try:
        df = yf.download(ticker, period="2d", progress=False, auto_adjust=True)
        if not df.empty: return float(df["Close"].squeeze().iloc[-1])
    except: return 0.0
    return 0.0

@st.cache_data(ttl=900, show_spinner=False)
def get_historical_close(ticker: str):
    try:
        df = yf.download(ticker, period="1y", progress=False, auto_adjust=True)
        if not df.empty: return df["Close"].squeeze()
    except: return pd.Series(dtype=float)
    return pd.Series(dtype=float)

# ==========================================
# 5. UI RENDER: MAKRO BAR & SEKMELER
# ==========================================
macro = fetch_macro_data()

def render_cur(title, data, prefix=""):
    c = "#0ECB81" if data['chg'] >= 0 else "#F6465D"
    s = "+" if data['chg'] >= 0 else ""
    return f"""<div class="cur-item">
        <div class="cur-title">{title}</div>
        <div class="cur-price">{prefix}{data['price']:,.2f}</div>
        <div class="cur-chg" style="color:{c}">{s}{data['chg']:.2f}%</div>
    </div>"""

bist = macro.get("BIST100", {"price":0, "chg":0})
b_c = "#0ECB81" if bist['chg'] >= 0 else "#F6465D"
b_s = "+" if bist['chg'] >= 0 else ""

st.markdown(f"""
<div class="macro-container">
    <div class="bist-box">
        <div class="bist-title">BIST 100 ENDEKSİ</div>
        <div class="bist-price">{bist['price']:,.2f}</div>
        <div class="bist-chg" style="color:{b_c}">{b_s}{bist['chg']:.2f}%</div>
    </div>
    <div class="currency-box">
        {render_cur("USD/TRY", macro.get("USD", {"price":0, "chg":0}), "₺")}
        {render_cur("EUR/TRY", macro.get("EUR", {"price":0, "chg":0}), "₺")}
        {render_cur("GRAM ALTIN", macro.get("GRAM_ALTIN", {"price":0, "chg":0}), "₺")}
    </div>
</div>
""", unsafe_allow_html=True)

tab_portfolio, tab_recommend = st.tabs(["📂 Portföy Simülatörü", "🤖 Akıllı Öneri Motoru"])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PORTFÖY SİMÜLATÖRÜ            ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    st.markdown('<div class="section-title">Hisse Satın Al</div>', unsafe_allow_html=True)

    pa, pb, pc = st.columns([2, 1, 1])
    with pa:
        add_sym = st.selectbox("Hangi hisseyi almak istiyorsun?", sorted(bist_symbols))
    
    # Anlık Fiyatı Çek ve Dev Ekranda Göster
    anlik_fiyat = get_current_price(f"{add_sym}.IS")
    
    with pb:
        st.markdown(f"""
        <div style="background:#1A1C24; border:1px solid var(--bn-border); border-radius:8px; padding:0.5rem 1rem; margin-top:1.8rem; text-align:center;">
            <div style="font-size:0.7rem; color:#848E9C;">O ANKİ FİYAT</div>
            <div style="font-size:1.6rem; font-weight:700; color:#0ECB81;">₺{anlik_fiyat:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with pc:
        add_adet = st.number_input("Kaç adet alacaksın?", min_value=1, value=10, step=5)
        add_maliyet = anlik_fiyat # Otomatik olarak anlık fiyatı maliyet kabul et
        
    if st.button("Portföye Ekle", type="primary", use_container_width=True):
        st.session_state.portfolio[add_sym] = {"adet": add_adet, "maliyet": add_maliyet}
        st.success(f"{add_sym} portföyüne başarıyla eklendi!")
        st.rerun()

    # PORTFÖY ÖZETİ VE SAT/DEĞİŞTİR ÖNERİLERİ
    if st.session_state.portfolio:
        st.markdown('<div class="section-title">Mevcut Portföyüm</div>', unsafe_allow_html=True)
        
        df_market = fetch_market_data() # Güncel sinyaller için
        
        total_yatirim = 0
        total_guncel = 0
        bad_stocks = [] # Satılması önerilecek hisseler
        
        for sym, data in st.session_state.portfolio.items():
            adet, maliyet = data["adet"], data["maliyet"]
            t_yatirim = adet * maliyet
            
            # Güncel fiyat ve sinyali market datasından çek
            market_row = df_market[df_market["Sembol"] == sym]
            if not market_row.empty:
                guncel_f = market_row.iloc[0]["Fiyat (TL)"]
                aksiyon = market_row.iloc[0]["Aksiyon"]
                rsi = market_row.iloc[0]["RSI"]
                
                # SAT sinyali varsa kara listeye al
                if "SAT" in aksiyon or rsi > 70:
                    bad_stocks.append({"sym": sym, "aksiyon": aksiyon, "rsi": rsi, "deger": adet * guncel_f})
            else:
                guncel_f = get_current_price(f"{sym}.IS")
                
            t_guncel = adet * guncel_f
            total_yatirim += t_yatirim
            total_guncel += t_guncel
            
            kar = t_guncel - t_yatirim
            kar_pct = (kar / t_yatirim * 100) if t_yatirim > 0 else 0
            k_c = "#0ECB81" if kar >= 0 else "#F6465D"
            
            st.markdown(f"""
            <div class="bn-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:1.4rem; font-weight:700; color:var(--bn-yellow);">{sym}</span>
                    <span style="color:#848E9C; margin-left:1rem;">{adet} Adet | Maliyet: ₺{maliyet:,.2f}</span>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.2rem; font-weight:700; color:#EAECEF;">₺{t_guncel:,.2f}</div>
                    <div style="color:{k_c}; font-weight:600;">{'+' if kar>=0 else ''}₺{kar:,.2f} ({'+' if kar_pct>=0 else ''}{kar_pct:.1f}%)</div>
                </div>
                <div style="width: 100px;">
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Silme butonu için yanına ufak bir alan
            if st.button(f"Sat ({sym})", key=f"del_{sym}"):
                del st.session_state.portfolio[sym]
                st.rerun()
                
        # --- AKILLI PORTFÖY OPTİMİZASYONU (DEĞİŞTİR ÖNERİSİ) ---
        if bad_stocks and not df_market.empty:
            st.markdown('<div class="section-title">🔄 Yapay Zeka Portföy Optimizasyonu</div>', unsafe_allow_html=True)
            
            # En iyi "GÜÇLÜ AL" veya "AL" hisselerini bul (portföyde olmayan)
            iyi_hisseler = df_market[
                (~df_market["Sembol"].isin(st.session_state.portfolio.keys())) & 
                (df_market["Aksiyon"].isin(["GUCLU AL", "AL"])) & 
                (df_market["RSI"] < 50)
            ].sort_values("RSI", ascending=True).head(3)
            
            for bad in bad_stocks:
                st.markdown(f"""
                <div class="swap-card">
                    <div style="color:#F6465D; font-weight:700; font-size:1.1rem; margin-bottom:0.5rem;">
                        ⚠️ {bad['sym']} Hissesinde Bozulma Tespit Edildi!
                    </div>
                    <div style="color:#EAECEF; font-size:0.9rem; margin-bottom:1rem;">
                        Portföyündeki <b>{bad['sym']}</b> teknik olarak yorgunluk belirtileri gösteriyor (Sinyal: {bad['aksiyon']}, RSI: {bad['rsi']:.1f}). 
                        Bu hisseyi satarak <b>₺{bad['deger']:,.0f}</b> nakite geçebilir ve yükseliş trendine yeni başlayan aşağıdaki hisselerden birine geçiş yapabilirsin:
                    </div>
                """, unsafe_allow_html=True)
                
                if not iyi_hisseler.empty:
                    for _, iyi in iyi_hisseler.iterrows():
                        st.markdown(f"""
                        <div style="background:#161A1E; padding:0.8rem; border-radius:6px; border:1px solid #2B3139; margin-bottom:0.5rem; display:flex; justify-content:space-between;">
                            <div><span style="color:#0ECB81; font-weight:700;">{iyi['Sembol']}</span> (RSI: {iyi['RSI']:.1f})</div>
                            <div style="color:#848E9C;">Sinyal: <span style="color:#0ECB81;">{iyi['Aksiyon']}</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


# ╔══════════════════════════════════════════╗
# ║  SEKME 2: AKILLI ÖNERİ MOTORU           ║
# ╚══════════════════════════════════════════╝
with tab_recommend:
    st.markdown('<div class="section-title">Yapay Zeka Destekli Hisse Taraması & Yıl Sonu Simülasyonu</div>', unsafe_allow_html=True)

    r1, r2 = st.columns([1, 1])
    with r1:
        butce = st.number_input("Yatırım Bütçen Ne Kadar? (TL)", min_value=1000, value=25000, step=1000)
    with r2:
        risk = st.selectbox("Risk Profilin", ["Düşük Risk (Büyük Şirketler)", "Yüksek Risk (Fırsat Hisseleri)"])
        
    if st.button("Benim İçin En İyi Hisseleri Bul", type="primary", use_container_width=True):
        with st.spinner("Piyasa taranıyor ve yıl sonu ihtimalleri hesaplanıyor..."):
            df_scan = fetch_market_data().copy()
            
            if "Düşük" in risk:
                guvenli = ["AKBNK","GARAN","ISCTR","YKBNK","KCHOL","SAHOL","EREGL","FROTO","THYAO","TCELL","BIMAS","TUPRS"]
                df_scan = df_scan[df_scan["Sembol"].isin(guvenli)]
            else:
                kucuk = ["ASTOR","SMARTG","EUPWR","GESAN","CWENE","YEOTK","GWIND","MIATK","KONTR","ALFAS"]
                df_scan = df_scan[df_scan["Sembol"].isin(kucuk)]
                
            # Filtrele: RSI düşük ve Al sinyali verenler
            df_scan = df_scan[df_scan["RSI"] < 55]
            df_scan = df_scan.sort_values("RSI", ascending=True).head(3) # En iyi 3 hisse
            
            if df_scan.empty:
                st.warning("Şu anki piyasa koşullarında bu profile uygun güvenli bir 'AL' fırsatı bulunamadı.")
            else:
                hisse_basi_butce = butce / len(df_scan)
                
                st.success(f"Yapay Zeka {len(df_scan)} adet fırsat hissesi buldu! Her birine ₺{hisse_basi_butce:,.0f} ayırabilirsin.")
                
                for _, row in df_scan.iterrows():
                    sym = row["Sembol"]
                    fiyat = row["Fiyat (TL)"]
                    
                    # O hisse için geçmiş veriyi çekip Yıl Sonu Tahmini Yap
                    close_hist = get_historical_close(f"{sym}.IS")
                    fc = yil_sonu_tahmini(close_hist, row["RSI"], row["MACD_H"], fiyat, row["SMA50"])
                    
                    st.markdown(f"""
                    <div style="background:#161A1E; border:1px solid #2B3139; border-left:4px solid #0ECB81; border-radius:8px; padding:1.5rem; margin-bottom:1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                            <span style="font-size:1.6rem; font-weight:800; color:#EAECEF;">{sym}</span>
                            <span style="font-size:1.2rem; font-weight:600; color:#0ECB81;">Alım Fiyatı: ₺{fiyat:,.2f}</span>
                        </div>
                        <div style="color:#848E9C; font-size:0.9rem; margin-bottom:1rem;">
                            <b>Neden Önerildi?</b> RSI seviyesi {row['RSI']:.1f} ile oldukça uygun. Teknik indikatörler <b>{row['Aksiyon']}</b> sinyali veriyor.
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if fc:
                        b_val = (hisse_basi_butce / fiyat) * fc["base"]
                        bl_val = (hisse_basi_butce / fiyat) * fc["bull"]
                        br_val = (hisse_basi_butce / fiyat) * fc["bear"]
                        
                        st.markdown(f"""
                        <div style="font-size:0.8rem; color:#848E9C; text-transform:uppercase; margin-bottom:0.5rem;">Yıl Sonuna Kadar Kazanç Olasılıkları (₺{hisse_basi_butce:,.0f} Yatırım İçin)</div>
                        <div style="display:flex; gap:1rem;">
                            <div class="forecast-card" style="flex:1;">
                                <div style="color:#0ECB81; font-size:0.8rem;">İyimser Senaryo</div>
                                <div style="font-size:1.3rem; font-weight:700; color:#EAECEF;">₺{bl_val:,.0f}</div>
                            </div>
                            <div class="forecast-card base" style="flex:1;">
                                <div style="color:#1E90FF; font-size:0.8rem;">Ortalama Beklenti</div>
                                <div style="font-size:1.3rem; font-weight:700; color:#EAECEF;">₺{b_val:,.0f}</div>
                            </div>
                            <div class="forecast-card bear" style="flex:1;">
                                <div style="color:#F6465D; font-size:0.8rem;">Kötü Senaryo</div>
                                <div style="font-size:1.3rem; font-weight:700; color:#EAECEF;">₺{br_val:,.0f}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
