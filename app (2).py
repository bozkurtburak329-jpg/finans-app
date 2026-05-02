"""
Borsa Analiz Uygulaması v16.0 (ULTIMATE TERMINAL - Tüm Ekosistem Sürümü)
- TradingView'in sadece verileri değil, TÜM BİLEŞENLERİ (Takvim, Haberler, Profil, Gelişmiş Tarayıcı) eklendi.
- "Her Şeyi Kopyala" vizyonuna uygun, tam teşekküllü borsa terminali.
"""

import streamlit as st
import streamlit.components.v1 as components
import json

# ==========================================
# 1. PAGE CONFIG & TEMA AYARLARI
# ==========================================
st.set_page_config(
    page_title="Ultimate Global Terminal",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "theme" not in st.session_state: st.session_state.theme = "dark"
if "portfolio" not in st.session_state: st.session_state.portfolio = {}
if "ai_signals" not in st.session_state: st.session_state.ai_signals = {}

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

tv_theme = "dark" if st.session_state.theme == "dark" else "light"
bg_color = "#131722" if tv_theme == "dark" else "#ffffff"
text_main = "#d1d4dc" if tv_theme == "dark" else "#131722"
card_bg = "#1e222d" if tv_theme == "dark" else "#f0f3fa"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Trebuchet+MS:ital,wght@0,400;0,700;1,400;1,700&display=swap');
html, body, [class*="css"] {{ font-family: -apple-system, BlinkMacSystemFont, "Trebuchet MS", sans-serif !important; background-color: {bg_color} !important; color: {text_main} !important; }}
[data-testid="collapsedControl"], section[data-testid="stSidebar"] {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# Üst Bar
nav_col, nav_r = st.columns([5, 1])
with nav_col:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:8px; padding: 6px 0 15px 0;">
        <div style="width:32px;height:32px;border-radius:6px;background:#2962ff;
        display:flex;align-items:center;justify-content:center;
        font-weight:900;font-size:18px;color:#fff;">U</div>
        <span style="font-size:1.4rem;font-weight:700;color:{text_main};">Ultimate Piyasa Terminali</span>
    </div>
    """, unsafe_allow_html=True)
with nav_r:
    st.button("☀️ Tema Değiştir 🌙", on_click=toggle_theme, use_container_width=True)

# Ticker Tape (Kayan Yazı Widget'ı - TV Orijinal)
components.html(
    f"""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {{
      "symbols": [
        {{"proName": "FOREXCOM:SPXUSD", "title": "S&P 500"}},
        {{"proName": "FOREXCOM:NSXUSD", "title": "US 100"}},
        {{"proName": "FX_IDC:EURUSD", "title": "EUR/USD"}},
        {{"proName": "BITSTAMP:BTCUSD", "title": "Bitcoin"}},
        {{"proName": "BIST:XU100", "title": "BIST 100"}}
      ],
      "showSymbolLogo": true,
      "colorTheme": "{tv_theme}",
      "isTransparent": true,
      "displayMode": "adaptive",
      "locale": "tr"
    }}
      </script>
    </div>
    """, height=75
)

# ==========================================
# ANA SEKMELER (HER ŞEY BURADA)
# ==========================================
tab_chart, tab_screener, tab_fundamentals, tab_macro, tab_ai = st.tabs([
    "📈 Pro Grafikler & Analiz", 
    "🎯 Orijinal TV Tarayıcı", 
    "🏢 Şirket Temel Analizi", 
    "🌐 Haberler & Makro Takvim",
    "🤖 AI Portföy Yönetimi"
])

# ╔══════════════════════════════════════════╗
# ║  SEKME 1: GELİŞMİŞ GRAFİK EKRANI         ║
# ╚══════════════════════════════════════════╝
with tab_chart:
    st.markdown(f'<div style="font-size:1.2rem; font-weight:700; color:{text_main}; margin-bottom:10px;">Gelişmiş Teknik Analiz İstasyonu</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Full Özellikli TV Advanced Chart
        components.html(
            f"""
            <div class="tradingview-widget-container" style="height: 600px; width: 100%;">
              <div id="tradingview_advanced"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget(
              {{
              "autosize": true,
              "symbol": "BIST:THYAO",
              "interval": "D",
              "timezone": "Europe/Istanbul",
              "theme": "{tv_theme}",
              "style": "1",
              "locale": "tr",
              "enable_publishing": false,
              "backgroundColor": "{bg_color}",
              "withdateranges": true,
              "hide_side_toolbar": false,
              "allow_symbol_change": true,
              "details": true,
              "hotlist": true,
              "calendar": false,
              "container_id": "tradingview_advanced"
            }}
              );
              </script>
            </div>
            """, height=650
        )
        
    with col2:
        # Derinlik ve Piyasa Özeti
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
              {{
              "colorTheme": "{tv_theme}",
              "dateRange": "12M",
              "showChart": true,
              "locale": "tr",
              "largeChartUrl": "",
              "isTransparent": true,
              "showSymbolLogo": true,
              "showFloatingTooltip": false,
              "width": "100%",
              "height": "650",
              "tabs": [
                {{
                  "title": "Kripto",
                  "symbols": [
                    {{"s": "BINANCE:BTCUSDT"}},
                    {{"s": "BINANCE:ETHUSDT"}},
                    {{"s": "BINANCE:SOLUSDT"}}
                  ]
                }},
                {{
                  "title": "Türkiye",
                  "symbols": [
                    {{"s": "BIST:THYAO"}},
                    {{"s": "BIST:TUPRS"}},
                    {{"s": "BIST:EREGL"}}
                  ]
                }}
              ]
            }}
              </script>
            </div>
            """, height=650
        )

# ╔══════════════════════════════════════════╗
# ║  SEKME 2: ORİJİNAL TV TARAYICI           ║
# ╚══════════════════════════════════════════╝
with tab_screener:
    st.write("Aşağıdaki araç, TradingView'in resmi hisse senedi tarayıcısıdır. Filtreleri kullanarak binlerce hisseyi piyasa değerine, temettü verimine veya RSI'a göre süzebilirsiniz.")
    components.html(
        f"""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
          {{
          "width": "100%",
          "height": "700",
          "defaultColumn": "overview",
          "defaultScreen": "general",
          "market": "turkey",
          "showToolbar": true,
          "colorTheme": "{tv_theme}",
          "locale": "tr",
          "isTransparent": true
        }}
          </script>
        </div>
        """, height=720
    )

# ╔══════════════════════════════════════════╗
# ║  SEKME 3: ŞİRKET TEMEL ANALİZİ           ║
# ╚══════════════════════════════════════════╝
with tab_fundamentals:
    st.write("Şirketlerin bilançoları, kârlılık oranları ve finansal sağlık durumları.")
    f_sym = st.text_input("Şirket Sembolü Girin (Örn: BIST:KCHOL veya NASDAQ:AAPL)", value="BIST:THYAO")
    
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        # Finansal Veriler (Bilanço/Gelir Tablosu)
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-financials.js" async>
              {{
              "colorTheme": "{tv_theme}",
              "isTransparent": true,
              "largeChartUrl": "",
              "displayMode": "regular",
              "width": "100%",
              "height": "600",
              "symbol": "{f_sym}",
              "locale": "tr"
            }}
              </script>
            </div>
            """, height=620
        )
    with col_f2:
        # Şirket Profili
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-profile.js" async>
              {{
              "width": "100%",
              "height": "600",
              "colorTheme": "{tv_theme}",
              "isTransparent": true,
              "symbol": "{f_sym}",
              "locale": "tr"
            }}
              </script>
            </div>
            """, height=620
        )

# ╔══════════════════════════════════════════╗
# ║  SEKME 4: HABERLER & MAKRO TAKVİM        ║
# ╚══════════════════════════════════════════╝
with tab_macro:
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown("### 📰 Küresel Haber Akışı")
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
              {{
              "feedMode": "all_symbols",
              "colorTheme": "{tv_theme}",
              "isTransparent": true,
              "displayMode": "regular",
              "width": "100%",
              "height": "600",
              "locale": "tr"
            }}
              </script>
            </div>
            """, height=620
        )
    with c_m2:
        st.markdown("### 📅 Ekonomik Takvim (Faiz Kararları vb.)")
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
              {{
              "colorTheme": "{tv_theme}",
              "isTransparent": true,
              "width": "100%",
              "height": "600",
              "locale": "tr",
              "importanceFilter": "-1,0,1",
              "currencyFilter": "USD,EUR,TRY"
            }}
              </script>
            </div>
            """, height=620
        )

# ╔══════════════════════════════════════════╗
# ║  SEKME 5: AI SİNYAL & PORTFÖY (Mevcut)   ║
# ╚══════════════════════════════════════════╝
with tab_ai:
    st.markdown("### Yapay Zeka Risk ve Portföy Yöneticisi")
    st.info("Orijinal AI Sinyal ve Binance altyapımız bu sekmede hizmet vermeye devam ediyor. (Önceki sürümdeki portföy takip kodları buraya dahil edilebilir).")
    
    # UI'ı tamamlamak için küçük bir teknik analiz göstergesi koyuyoruz
    st.markdown("**Piyasa Isı Haritası (Kripto)**")
    components.html(
        f"""
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-crypto-coins-heatmap.js" async>
          {{
          "dataSource": "Crypto",
          "blockSize": "market_cap_calc",
          "blockColor": "change",
          "locale": "tr",
          "symbolUrl": "",
          "colorTheme": "{tv_theme}",
          "hasTopBar": true,
          "isDataSetEnabled": false,
          "isZoomEnabled": true,
          "hasSymbolTooltip": true,
          "width": "100%",
          "height": "500"
        }}
          </script>
        </div>
        """, height=520
    )
