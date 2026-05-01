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
        html_table += '<tr style="border-bottom: 1px solid #2B3139; color:#848E9C; font-size:0.85rem;"><th style="padding-bottom:0.5rem;">Sembol</th><th style="padding-bottom:0.5rem;">Fiyat</th><th style="padding-bottom:0.5rem;">Değişim</th><th style="padding-bottom:0.5rem;">RSI</th><th style="padding-bottom:0.5rem;">Aksiyon</th></tr>'
        
        for _, row in df_market.sort_values("Değişim %", ascending=False).iterrows():
            c_color = "#0ECB81" if row["Değişim %"] >= 0 else "#F6465D"
            sign = "+" if row["Değişim %"] >= 0 else ""
            
            # Markdown hatasını önlemek için f-string'leri satır başından, boşluksuz tanımlıyoruz
            html_table += f'<tr style="border-bottom: 1px solid #1E2329; font-weight:600;">'
            html_table += f'<td style="padding: 0.8rem 0;">{row["Sembol"]}</td>'
            html_table += f'<td>{row["Fiyat (TL)"]:,.2f} TL</td>'
            html_table += f'<td style="color:{c_color};">{sign}{row["Değişim %"]:.2f}%</td>'
            html_table += f'<td>{row["RSI"]:.1f}</td>'
            html_table += f'<td><span class="signal-badge {row["Sinyal_Class"]}">{row["Sinyal"]}</span></td>'
            html_table += f'</tr>'
            
        html_table += '</table>'
        
        # unsafe_allow_html=True parametresi tablonun düzgün render edilmesini sağlar
        st.markdown(html_table, unsafe_allow_html=True)
