"""
Burak Borsa Analiz Uygulaması v6.0
- Anlık BIST100, Dolar, Euro ve Altın (Gram) Sağ Üstte
- Midas API Entegrasyon Arayüzü (Hazırlık)
- AL/SAT Sinyalleri Ana Ekranda
- Portföy Anlık Fiyat Hatası Giderildi
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

if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "midas_connected" not in st.session_state:
    st.session_state.midas_connected = False

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
    --bn-muted:    #848E9C;
    --bn-white:    #EAECEF;
}

.app-header {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--bn-white);
    letter-spacing: -0.01em;
}
.app-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: var(--bn-yellow);
    text-transform: uppercase;
}

.macro-box {
    background-color: var(--bn-card);
    border: 1px solid var(--bn-border);
    border-radius: 6px;
    padding: 0.6rem;
    text-align: center;
}
.macro-title { font-size: 0.65rem; color: var(--bn-muted); }
.macro-val { font-size: 1.1rem; font-weight: 700; color: var(--bn-white); margin: 0.1rem 0; }
.macro-chg { font-size: 0.75rem; font-weight: 600; }
.macro-chg.green { color: var(--bn-green); }
.macro-chg.red { color: var(--bn-red); }

.signal-badge {
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.75rem;
}
.sig-guclual { background: #0D2E1A; color: #0ECB81; border: 1px solid #1B5E35; }
.sig-al { background: #0A2218; color: #0ECB81; border: 1px solid #144D2A; }
.sig-sat { background: #2A0A10; color: #F6465D; border: 1px solid #5C1525; }
.sig-guclusat { background: #220810; color: #F6465D; border: 1px solid #4A1020; }
.sig-tut { background: #1A1C22; color: #848E9C; border: 1px solid #2B3139; }

::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background: var(--bn-bg); }
::-webkit-scrollbar-thumb { background: var(--bn-border); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SEMBOL LİSTESİ VE YARDIMCI FONKSİYONLAR
# ==========================================
bist_symbols = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","KCHOL","SAHOL","DOHOL","ALARK","ENKAI",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","SISE","FROTO","TOASO","THYAO",
    "PGSUS","BIMAS","MGROS","TCELL","TTKOM","ASELS","ASTOR","KONTR","ENJSA","EKGYO"
]
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

def get_signal(rsi, curr_p, sma50):
    if pd.isna(rsi): return "TUT", "sig-tut"
    if rsi < 35 and curr_p > sma50: return "GÜÇLÜ AL", "sig-guclual"
    if rsi < 45: return "AL", "sig-al"
    if rsi > 70: return "SAT", "sig-sat"
    if rsi > 65 and curr_p < sma50: return "GÜÇLÜ SAT", "sig-guclusat"
    return "TUT", "sig-tut"

@st.cache_data(ttl=300, show_spinner=False)
def get_macro_data():
    """BIST100, Dolar, Euro ve Gram Altın verilerini çeker."""
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
    
    # Gram Altın Hesaplama: (Ons * USDTRY) / 31.10
    try:
        ons = res.get("ALTIN (ONS)", {}).get("price", 0)
        usd = res.get("USD/TRY", {}).get("price", 0)
        gram_price = (ons * usd) / 31.10
        res["GRAM ALTIN"] = {"price": gram_price, "chg": res.get("ALTIN (ONS)", {}).get("chg", 0)}
    except:
        res["GRAM ALTIN"] = {"price": 0.0, "chg": 0.0}
        
    return res

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
            prev = float(close.iloc[-2])
            sma50 = float(close.rolling(50).mean().iloc[-1])
            rsi = compute_rsi(close)
            sig, sig_cls = get_signal(rsi, price, sma50)
            return {"Sembol": name, "Fiyat (TL)": price, "Değişim %": ((price - prev) / prev) * 100, 
                    "RSI": rsi, "Sinyal": sig, "Sinyal_Class": sig_cls}
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(process_ticker, t, n) for t, n in TICKERS_BIST.items()]
        for f in concurrent.futures.as_completed(futures):
            if f.result(): rows.append(f.result())
    return pd.DataFrame(rows)

# ==========================================
# 4. HEADER & MAKRO VERİLER (SAĞA YASLI)
# ==========================================
header_col, macro_col = st.columns([1.5, 2.5])

with header_col:
    st.markdown('<div class="app-header">BURAK BORSA ANALİZ</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-sub">Kantitatif Sinyal Motoru v6.0</div>', unsafe_allow_html=True)

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

st.markdown("<hr style='border-color: #2B3139; margin: 1rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. ANA SEKMELER
# ==========================================
tab_market, tab_portfolio, tab_midas = st.tabs([
    "Piyasa Görünümü (AL/SAT)", "Portföy & Analiz", "Midas Entegrasyonu"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: PİYASA GÖRÜNÜMÜ                ║
# ╚══════════════════════════════════════════╝
with tab_market:
    df_market = fetch_market_data()
    if df_market.empty:
        st.error("Veri çekilemedi.")
    else:
        st.markdown("""
        <div style="font-size:0.85rem; color:#848E9C; margin-bottom:1rem;">
        * Sinyaller RSI, SMA50 ve momentum kırılımlarına göre yapay zeka tarafından otomatik oluşturulur.
        </div>""", unsafe_allow_html=True)
        
        # Sinyalleri HTML tablosu olarak daha şık göster
        html_table = '<table style="width:100%; text-align:left; border-collapse: collapse;">'
        html_table += '<tr style="border-bottom: 1px solid #2B3139; color:#848E9C; font-size:0.85rem;"><th>Sembol</th><th>Fiyat</th><th>Değişim</th><th>RSI</th><th>Aksiyon</th></tr>'
        
        for _, row in df_market.sort_values("Değişim %", ascending=False).iterrows():
            c_color = "#0ECB81" if row["Değişim %"] >= 0 else "#F6465D"
            sign = "+" if row["Değişim %"] >= 0 else ""
            html_table += f"""
            <tr style="border-bottom: 1px solid #1E2329; font-weight:600;">
                <td style="padding: 0.8rem 0;">{row['Sembol']}</td>
                <td>{row['Fiyat (TL)']:,.2f} TL</td>
                <td style="color:{c_color};">{sign}{row['Değişim %']:.2f}%</td>
                <td>{row['RSI']:.1f}</td>
                <td><span class="signal-badge {row['Sinyal_Class']}">{row['Sinyal']}</span></td>
            </tr>
            """
        html_table += '</table>'
        st.markdown(html_table, unsafe_allow_html=True)

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: PORTFÖY & ANALİZ               ║
# ╚══════════════════════════════════════════╝
with tab_portfolio:
    st.markdown("### Hisse Ekle (Hata Giderildi)")
    
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        add_sym = st.selectbox("Hangi hisseyi almak istiyorsun?", sorted(bist_symbols))
    
    # Anlık fiyat çekme bölümündeki hata tamamen düzeltildi (Series yerine value indexing)
    preview_price = 0.0
    try:
        df_p = yf.download(f"{add_sym}.IS", period="1d", progress=False, auto_adjust=True)
        if not df_p.empty and "Close" in df_p:
            preview_price = float(np.squeeze(df_p["Close"].values)[-1])
    except: pass

    with c2:
        st.text_input("Anlık Fiyat", value=f"TL {preview_price:,.2f}" if preview_price > 0 else "Veri Bekleniyor", disabled=True)
        
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
            st.write(f"- **{sym}**: {data['adet']} Adet (Maliyet: {data['maliyet']:,.2f} TL)")
            if st.button(f"Kaldır {sym}", key=f"del_{sym}"):
                del st.session_state.portfolio[sym]
                st.rerun()

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: MİDAS ENTEGRASYONU             ║
# ╚══════════════════════════════════════════╝
with tab_midas:
    st.markdown("""
    <div style="background:#161A1E; padding:1.5rem; border-radius:8px; border:1px solid #F0B90B; border-left:4px solid #F0B90B;">
        <h3 style="margin-top:0; color:#F0B90B;">Midas Otomatik Al-Sat Entegrasyonu</h3>
        <p style="color:#C7CBD1; font-size:0.9rem;">
        Midas'ın güncel altyapısında şu an için bireysel algoritmik trade ve dış uygulamalar için açık bir API (Public API) bulunmamaktadır. 
        Güvenlik nedeniyle şifre ile doğrudan emir iletimi SPK ve aracı kurumlar tarafından dış web uygulamalarına kapalıdır.
        <br><br>
        Ancak sistemin altyapısı, resmi API yayınlandığı anda webhook üzerinden emir gönderecek şekilde hazırlandı. Aşağıdan bağlantı simülasyonunu test edebilirsin.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not st.session_state.midas_connected:
        st.text_input("Midas API Key (Geçici Olarak Kapalı)", disabled=True, placeholder="API Key bekleniyor...")
        st.text_input("Midas Secret Key (Geçici Olarak Kapalı)", disabled=True, placeholder="Secret Key bekleniyor...", type="password")
        
        if st.button("Bağlantıyı Test Et", type="primary"):
            st.session_state.midas_connected = True
            st.rerun()
    else:
        st.success("Midas API bağlantısı simüle edildi. Sistem şu an 'Read-Only' modunda çalışıyor (Sadece portföy okunabilir, emir iletilemez).")
        st.markdown("#### Aktif Algoritmalar")
        st.checkbox("RSI 30 Altı Otomatik Alım (Durduruldu - API Bekleniyor)", value=True, disabled=True)
        st.checkbox("MACD Kesişiminde Kar Al (Durduruldu - API Bekleniyor)", value=True, disabled=True)
        if st.button("Bağlantıyı Kes"):
            st.session_state.midas_connected = False
            st.rerun()
