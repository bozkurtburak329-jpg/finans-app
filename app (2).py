# ╔══════════════════════════════════════════╗
# ║  SEKME 1: BÖLÜNMÜŞ EKRAN (SCREENER + X-RAY)
# ╚══════════════════════════════════════════╝
with tab_screener:
    col_scr, col_xray = st.columns([2.0, 1.4])
    
    # --- SOL: GELİŞMİŞ SCREENER ---
    with col_scr:
        df_screener = fetch_tv_screener_data()
        if df_screener.empty:
            st.error("Veri çekilemedi.")
        else:
            # Markdown'un 4 boşluk kuralına takılmamak için HTML'i boşluksuz birleştiriyoruz
            html_table = '<div class="tv-screener-container"><table class="tv-table"><thead><tr><th>TICKER</th><th>SON</th><th>DEĞİŞİM %</th><th>1 HAFTA %</th><th>1 AY %</th><th>TEKNİK SİNYAL</th><th>HACİM</th><th>RSI</th></tr></thead><tbody>'
            
            for _, row in df_screener.sort_values("Değişim %", ascending=False).iterrows():
                c_d = "tv-green" if row["Değişim %"] >= 0 else "tv-red"
                c_w = "tv-green" if row["1H %"] >= 0 else "tv-red"
                c_m = "tv-green" if row["1A %"] >= 0 else "tv-red"
                
                # Başında boşluk (indent) olmadan satırları ekliyoruz
                html_table += "<tr>"
                html_table += f"<td><div class='tv-ticker-col'><div class='tv-logo-circle'>{row['Sembol'][0]}</div><div class='tv-ticker-info'><span class='tv-ticker-symbol'>{row['Sembol']}</span></div></div></td>"
                html_table += f"<td>{row['Fiyat']:,.2f}</td>"
                html_table += f"<td class='{c_d}'>{'+' if row['Değişim %']>=0 else ''}{row['Değişim %']:.2f}%</td>"
                html_table += f"<td class='{c_w}'>{'+' if row['1H %']>=0 else ''}{row['1H %']:.2f}%</td>"
                html_table += f"<td class='{c_m}'>{'+' if row['1A %']>=0 else ''}{row['1A %']:.2f}%</td>"
                html_table += f"<td><span class='tv-rating {row['Teknik_Class']}'>{row['Teknik']}</span></td>"
                html_table += f"<td>{format_volume(row['Hacim'])}</td>"
                html_table += f"<td>{row['RSI']:.1f}</td>"
                html_table += "</tr>"
                
            html_table += "</tbody></table></div>"
            st.markdown(html_table, unsafe_allow_html=True)

    # --- SAĞ: 3'LÜ X-RAY WIDGET PANELİ ---
    with col_xray:
        secilen_hisse = st.selectbox("X-Ray Röntgeni İçin Hisse Seç:", sorted(bist_symbols), index=0)
        tv_symbol = f"BIST:{secilen_hisse}"
        
        # 1. Advanced Chart
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div id="tradingview_chart"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({{"width": "100%", "height": 300, "symbol": "{tv_symbol}", "interval": "D", "timezone": "Europe/Istanbul", "theme": "{tv_theme_str}", "style": "1", "locale": "tr", "hide_top_toolbar": true, "container_id": "tradingview_chart"}});
              </script>
            </div>
            """, height=300, scrolling=False
        )
        
        # 2. Teknik Analiz Kadranı
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        components.html(
            f"""
            <div class="tradingview-widget-container">
              <div class="tradingview-widget-container__widget"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
              {{"interval": "1D", "width": "100%", "isTransparent": true, "height": "250", "symbol": "{tv_symbol}", "showIntervalTabs": true, "displayMode": "single", "locale": "tr", "colorTheme": "{tv_theme_str}"}}
              </script>
            </div>
            """, height=250, scrolling=False
        )
