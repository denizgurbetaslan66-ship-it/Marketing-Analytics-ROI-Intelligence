import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from core.data import generate_demo_data, add_metrics, totals, summarize, validate_upload
from core.ml import train_model, predict_roas

# Sayfa Konfigürasyonu
st.set_page_config(
    page_title="Marketing Analytics & Campaign Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Yardımcı Fonksiyonlar (Hata alan eksik tanımlar eklendi)
def fmt_money(val):
    return f"{val:,.2f} TL"

def kpi_card(color, title, value):
    return f"""
    <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid {color};">
        <p style="color: #666; margin: 0; font-size: 14px;">{title}</p>
        <h3 style="color: #111; margin: 5px 0 0 0; font-size: 24px;">{value}</h3>
    </div>
    """

# Veri Yükleme
df = generate_demo_data()

# Sidebar Filtreleri
st.sidebar.header("🎛️ Kontrol Paneli & Filtreler")
secilen_kampanya = st.sidebar.multiselect("Kampanya Seçin", options=df['Kampanya'].unique(), default=df['Kampanya'].unique())
secilen_kanal = st.sidebar.multiselect("Kanal Seçin", options=df['Kanal'].unique(), default=df['Kanal'].unique())

# Filtreleme
fist_df = df[df['Kampanya'].isin(secilen_kampanya) & df['Kanal'].isin(secilen_kanal)]

# Ana Başlık
st.title("📊 Marketing Analytics & Campaign Intelligence")
st.markdown("Dijital kampanyalarınızı ölçümleyin, bütçe senaryoları simüle edin ve yapay zeka destekli içgörüler elde edin.")

if fist_df.empty:
    st.warning("Seçilen filtrelerde veri bulunamadı. Lütfen filtreleri genişletin.")
else:
    # Üst KPI Kartları (Hata veren kısım düzeltildi)
    top_gelir, top_harcama, ort_roas, ort_donusum = totals(fist_df)

    k = st.columns(4)
    k[0].markdown(kpi_card("#4F46E5", "Toplam Gelir (Revenue)", fmt_money(top_gelir)), unsafe_allow_html=True)
    k[1].markdown(kpi_card("#E11D48", "Toplam Harcama (Spend)", fmt_money(top_harcama)), unsafe_allow_html=True)
    k[2].markdown(kpi_card("#10B981", "Ortalama ROAS (ROI)", f"{ort_roas:.2f}x"), unsafe_allow_html=True)
    k[3].markdown(kpi_card("#F59E0B", "Dönüşüm Oranı", f"%{ort_donusum:.2f}"), unsafe_allow_html=True)

    st.markdown("---")

    # Sekmeler
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Performans Analizi", "🏆 Monthly Top Perform", "🤖 ML & ROAS Tahmini", "💰 Bütçe Simülasyonu"])

    with tab1:
        st.subheader("Kampanya ve Kanal Bazlı Performans")
        c1, c2 = st.columns(2)
        
        with c1:
            kampanya_ozeti = fist_df.groupby('Kampanya')['ROAS'].mean().reset_index()
            fig_roas = px.bar(kampanya_ozeti, x='Kampanya', y='ROAS', title="Kampanyalara Göre Ortalama ROAS", color='ROAS', color_continuous_scale='Blues', text_auto='.2f')
            st.plotly_chart(fig_roas, use_container_width=True)
            
        with c2:
            kanal_ozeti = fist_df.groupby('Kanal')[['Gelir_TL', 'Harcama_TL']].sum().reset_index()
            fig_kanal = px.bar(kanal_ozeti, x='Kanal', y=['Gelir_TL', 'Harcama_TL'], barmode='group', title="Kanal Bazlı Gelir vs Harcama (TL)")
            st.plotly_chart(fig_kanal, use_container_width=True)

        st.subheader("Detaylı Metrik Tablosu")
        st.dataframe(summarize(fist_df), use_container_width=True)

    with tab2:
        st.subheader("🏆 Monthly Top Perform (Yönetici Özeti)")
        st.markdown("Yapay zeka analiz modülü tarafından otomatik olarak derlenen en başarılı kampanyalar:")
        
        top_kampanyalar = fist_df.groupby('Kampanya').agg({'ROAS': 'mean', 'Gelir_TL': 'sum', 'Tiklama': 'sum', 'CPA': 'mean'}).reset_index()
        top_kampanyalar = top_kampanyalar.sort_values(by='ROAS', ascending=False).head(3)
        
        for idx, row in top_kampanyalar.iterrows():
            st.success(f"""
            ### 🚀 {row['Kampanya']}
            - **Ortalama ROAS:** `{row['ROAS']:.2f}x`
            - **Toplam Gelir:** `{row['Gelir_TL']:,.2f} TL`
            - **Toplam Tıklama:** `{row['Tiklama']:,}`
            - **Ortalama CPA (Dönüşüm Maliyeti):** `{row['CPA']:.2f} TL`
            """)

    with tab3:
        st.subheader("🤖 Makine Öğrenmesi ile ROAS Tahmin Modülü")
        st.markdown("Geçmiş kampanya verileriyle eğitilen **Random Forest** modeli üzerinden yeni bir kampanyanın ROAS değerini öngörün.")
        
        ml_model = train_model(df)
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            p_gosterim = st.number_input("Tahmini Gösterim", value=250000, step=10000)
            p_tiklama = st.number_input("Tahmini Tıklama", value=12000, step=500)
        with col_m2:
            p_harcama = st.number_input("Tahmini Harcama (TL)", value=25000.0, step=1000.0)
            p_donusum = st.number_input("Tahmini Dönüşüm", value=900, step=50)
            
        if st.button("🚀 ROAS Tahmini Yap"):
            tahmin = predict_roas(ml_model, p_gosterim, p_tiklama, p_harcama, p_donusum)
            st.info(f"✨ Model Tahmini ROAS (Yatırımın Geri Dönüşü): **{tahmin:.2f}x**")
            if tahmin > 3.5:
                st.success("Mükemmel performans öngörülüyor! Bu kampanya bütçe artışına uygun.")
            elif tahmin > 2.0:
                st.warning("Orta seviye performans. Optimizasyon yapılması önerilir.")
            else:
                st.error("Düşük ROAS riski! Kreatifleri ve hedef kitleyi gözden geçirin.")

    with tab4:
        st.subheader("💰 Bütçe Senaryo Simülasyonu (What-If Analysis)")
        st.markdown("Toplam pazarlama bütçesini artırdığınızda veya azalttığınızda elde edeceğiniz tahmini gelir projeksiyonu.")
        
        artis_orani = st.slider("Bütçe Değişim Oranı (%)", min_value=-50, max_value=100, value=20, step=5) / 100.0
        
        mevcut_harcama = top_harcama
        mevcut_gelir = top_gelir
        ortalama_roas_val = ort_roas
        
        yeni_harcama = mevcut_harcama * (1 + artis_orani)
        tahmini_gelir = yeni_harcama * ortalama_roas_val
        fark_gelir = tahmini_gelir - mevcut_gelir
        
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Mevcut Bütçe / Gelir", f"{mevcut_harcama:,.0f} TL", f"{mevcut_gelir:,.0f} TL Gelir")
        sc2.metric("Simüle Edilen Bütçe", f"{yeni_harcama:,.0f} TL", f"%{artis_orani*100:+.0f} Değişim")
        sc3.metric("Tahmini Yeni Gelir", f"{tahmini_gelir:,.0f} TL", f"{fark_gelir:+,.0f} TL Fark")
