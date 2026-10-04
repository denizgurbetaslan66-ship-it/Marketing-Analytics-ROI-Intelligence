"""Marketing Analytics & Campaign Intelligence — Streamlit dashboard."""
from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data import (REQUIRED_COLS, add_metrics, generate_demo_data, summarize,
                       totals, validate_upload)
from core.ml import predict_roas, train_model

st.set_page_config(page_title="Marketing Analytics & Campaign Intelligence",
                   page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(Path(__file__).parent / 'assets' / 'style.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)

TR_MONTHS = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
COLORS = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#a855f7", "#14b8a6"]


# ---------- Yardımcılar ----------
def fmt_money(v: float) -> str:
    if abs(v) >= 1e6:
        return f"{v / 1e6:,.2f}M TL"
    if abs(v) >= 1e3:
        return f"{v / 1e3:,.1f}k TL"
    return f"{v:,.0f} TL"


def delta_text(cur: float, prev: float | None, suffix: str) -> tuple[str, bool]:
    if prev is None or prev == 0:
        return "Karşılaştırma verisi yok", True
    ch = (cur - prev) / abs(prev) * 100
    return f"%{abs(ch):.0f} {'artış' if ch >= 0 else 'düşüş'} {suffix}", ch >= 0


def kpi_card(theme: str, label: str, value: str, delta: tuple[str, bool]) -> str:
    arrow = "↗" if delta[1] else "↘"
    return (f'<div class="kpi {theme}"><div class="kpi-top"><span>{label}</span><span>{arrow}</span></div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-delta">{delta[0]}</div></div>')


def style_fig(fig: go.Figure, dark: bool = False, height: int = 340) -> go.Figure:
    fg = "#f5f5f7" if dark else "#1f2430"
    grid = "rgba(255,255,255,.14)" if dark else "rgba(0,0,0,.07)"
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=fg, size=12), margin=dict(l=8, r=8, t=24, b=8),
                      legend=dict(orientation="h", y=-0.22, x=0, title=None))
    fig.update_xaxes(gridcolor=grid, zeroline=False, title=None)
    fig.update_yaxes(gridcolor=grid, zeroline=False, title=None)
    return fig


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, width="stretch", key=key, config={"displayModeBar": False})


def section(title: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


# ---------- Veri ----------
df_all = generate_demo_data()
with st.sidebar:
    st.markdown('<div class="brand"><span>📈</span>Campaign Intelligence</div>', unsafe_allow_html=True)
    upload = st.file_uploader("Kendi CSV verinizi yükleyin", type="csv",
                              help="Gerekli sütunlar: " + ", ".join(REQUIRED_COLS))
    if upload is not None:
        try:
            parsed, err = validate_upload(pd.read_csv(upload))
        except Exception as exc:  # bozuk dosya
            parsed, err = None, f"Dosya okunamadı: {exc}"
        if err:
            st.error(err)
        else:
            df_all = parsed
            st.success(f"{len(df_all):,} satır yüklendi.")
    st.caption("Yüklenmezse örnek (demo) veri kullanılır.")
    st.markdown("### 🎛️ Filtreler")
    camp_opts = sorted(df_all["Kampanya"].unique())
    chan_opts = sorted(df_all["Kanal"].unique())
    cont_opts = sorted(df_all["Icerik_Turu"].unique())
    sel_camp = st.multiselect("Kampanya", camp_opts, default=camp_opts)
    sel_chan = st.multiselect("Kanal", chan_opts, default=chan_opts)
    sel_cont = st.multiselect("İçerik Türü", cont_opts, default=cont_opts)

# ---------- Üst bar: arama + dönem ----------
query = st.text_input("Ara", placeholder="🔍  Ne arıyorsunuz? (Örnek: Flash Sale)", label_visibility="collapsed")

periods = sorted(df_all["Tarih"].dt.to_period("M").unique(), reverse=True)
labels = {f"{TR_MONTHS[p.month]} {p.year}": p for p in periods}
h1, h2 = st.columns([4, 1.2], vertical_alignment="center")
h1.markdown('<p class="page-title">Genel Bakış</p>', unsafe_allow_html=True)
period_label = h2.selectbox("Dönem", ["Tüm Dönem", *labels], index=1 if labels else 0,
                            label_visibility="collapsed")

mask = (df_all["Kampanya"].isin(sel_camp) & df_all["Kanal"].isin(sel_chan)
        & df_all["Icerik_Turu"].isin(sel_cont))
if query.strip():
    mask &= df_all["Kampanya"].str.contains(query.strip(), case=False, regex=False)
base = df_all[mask]

month_col = base["Tarih"].dt.to_period("M")
if period_label == "Tüm Dönem":
    cur, prev, cmp_label = base, base.iloc[0:0], "önceki döneme"
else:
    p = labels[period_label]
    cur, prev, cmp_label = base[month_col == p], base[month_col == p - 1], "geçen aya"

if cur.empty:
    st.warning("Seçilen filtrelerde veri bulunamadı. Lütfen filtreleri genişletin.")
    st.stop()

T = totals(cur)
P = totals(prev) if not prev.empty else None
g = (lambda k: P[k]) if P else (lambda k: None)

# ---------- KPI kartları ----------
k = st.columns(4)
k[0].markdown(kpi_card("black", "Gelir", fmt_money(T["Gelir_TL"]),
                       delta_text(T["Gelir_TL"], g("Gelir_TL"), cmp_label)), unsafe_allow_html=True)
k[1].markdown(kpi_card("pink", "Harcama", fmt_money(T["Harcama_TL"]),
                       delta_text(T["Harcama_TL"], g("Harcama_TL"), cmp_label)), unsafe_allow_html=True)
k[2].markdown(kpi_card("peach", "ROAS", f"{T['ROAS']:.2f}x  ·  ROI %{(T['ROAS'] - 1) * 100:,.0f}",
                       delta_text(T["ROAS"], g("ROAS"), cmp_label)), unsafe_allow_html=True)
k[3].markdown(kpi_card("blue", "Dönüşüm Oranı", f"%{T['CVR_Yuzde']:.2f}",
                       delta_text(T["CVR_Yuzde"], g("CVR_Yuzde"), cmp_label)), unsafe_allow_html=True)

section("Analiz Performansı")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Genel Bakış", "🎯 Kampanya Analizi", "📡 Kanal & İçerik",
                                         "🤖 ML ROAS Tahmini", "💰 Bütçe Simülasyonu"])

camp_cur = summarize(cur, "Kampanya")

# ===== TAB 1 =====
with tab1:
    c1, c2 = st.columns([1.15, 1])
    with c1.container(key="eng_card"):
        st.markdown(f'<div class="card-title">Etkileşim</div><div class="card-sub">Ortalama CTR: '
                    f'%{T["CTR_Yuzde"]:.2f} · haftalık kampanya bazlı</div>', unsafe_allow_html=True)
        w = cur.assign(Hafta=cur["Tarih"].dt.to_period("W").dt.start_time)
        wk = w.groupby(["Hafta", "Kampanya"])[["Tiklama", "Gosterim"]].sum().reset_index()
        wk["CTR (%)"] = wk["Tiklama"] / wk["Gosterim"].replace(0, np.nan) * 100
        order = {d: f"Hafta {i + 1}" for i, d in enumerate(sorted(wk["Hafta"].unique()))}
        wk["Hafta"] = wk["Hafta"].map(order)
        fig = px.line(wk, x="Hafta", y="CTR (%)", color="Kampanya", markers=True, line_shape="spline",
                      color_discrete_sequence=COLORS, category_orders={"Hafta": list(order.values())})
        show(style_fig(fig, dark=True, height=330), "eng")

    with c2.container(key="aov_card"):
        st.markdown('<div class="card-title">Ortalama Sipariş Değeri (AOV)</div>'
                    '<div class="card-sub">Sipariş başına gelir potansiyeli (TL)</div>', unsafe_allow_html=True)
        fig = go.Figure()
        if not prev.empty:
            pv = summarize(prev, "Kampanya").set_index("Kampanya")["AOV"].reindex(camp_cur["Kampanya"]).fillna(0)
            fig.add_bar(y=camp_cur["Kampanya"], x=pv.values, orientation="h", name="Önceki dönem",
                        marker_color="#ef4444")
        fig.add_bar(y=camp_cur["Kampanya"], x=camp_cur["AOV"], orientation="h", name="Bu dönem",
                    marker_color="#3b82f6")
        fig.update_layout(barmode="group")
        fig.update_yaxes(autorange="reversed")
        show(style_fig(fig, height=330), "aov")

    m1, m2 = st.columns([2.2, 1])
    with m1.container(key="metrics_card"):
        st.markdown('<div class="card-title">Metrikler</div>', unsafe_allow_html=True)
        tbl = camp_cur.sort_values("RPM", ascending=False)[
            ["Kampanya", "CPA", "RPM", "Tiklama", "CTR_Yuzde", "ROAS"]]
        st.dataframe(tbl, hide_index=True, width="stretch", column_config={
            "CPA": st.column_config.NumberColumn("Müşteri Edinme Maliyeti", format="%.2f TL"),
            "RPM": st.column_config.NumberColumn("Bin Gösterim Geliri", format="%.2f TL"),
            "Tiklama": st.column_config.NumberColumn("Toplam Tıklama", format="%d"),
            "CTR_Yuzde": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "ROAS": st.column_config.ProgressColumn("ROAS", format="%.2fx", min_value=0,
                                                    max_value=float(max(tbl["ROAS"].max(), 1))),
        })
    with m2.container(key="top_card"):
        st.markdown('<div class="card-title">Ayın En İyileri</div><div class="card-sub">AI analizine göre</div>',
                    unsafe_allow_html=True)
        best_ctr = camp_cur.loc[camp_cur["CTR_Yuzde"].idxmax(), "Kampanya"]
        items = ""
        for i, r in enumerate(camp_cur.sort_values("RPM", ascending=False).head(3).itertuples(), 1):
            note = " En yüksek CTR." if r.Kampanya == best_ctr else ""
            items += (f'<div class="top-item"><span class="badge b{i}">{i}.</span>'
                      f'<span class="top-name">{html.escape(str(r.Kampanya))}</span>'
                      f'<div class="top-desc">Bin gösterim geliri {r.RPM:,.2f} TL, {r.Tiklama:,.0f} tıklama, '
                      f'AOV {r.AOV:,.2f} TL, ROAS {r.ROAS:.2f}x.{note}</div></div>')
        st.markdown(items, unsafe_allow_html=True)

# ===== TAB 2 =====
with tab2:
    a, b = st.columns(2)
    with a:
        fig = px.scatter(camp_cur, x="Harcama_TL", y="Gelir_TL", size="Tiklama", color="Kampanya",
                         color_discrete_sequence=COLORS, size_max=45,
                         labels={"Harcama_TL": "Harcama (TL)", "Gelir_TL": "Gelir (TL)"})
        st.markdown("**Harcama vs Gelir** (baloncuk = tıklama)")
        show(style_fig(fig), "scatter")
    with b:
        daily = cur.groupby("Tarih")[["Gelir_TL", "Harcama_TL"]].sum().reset_index()
        fig = px.area(daily, x="Tarih", y=["Gelir_TL", "Harcama_TL"],
                      color_discrete_sequence=["#a855f7", "#f472b6"])
        st.markdown("**Günlük Gelir ve Harcama Trendi**")
        show(style_fig(fig), "trend")
    st.markdown("**Detaylı Metrik Tablosu**")
    detail = camp_cur.sort_values("ROAS", ascending=False).round(2)
    st.dataframe(detail, hide_index=True, width="stretch")
    st.download_button("⬇️ Tabloyu CSV indir", detail.to_csv(index=False).encode("utf-8-sig"),
                       "kampanya_ozeti.csv", "text/csv")

# ===== TAB 3 =====
with tab3:
    ch = summarize(cur, "Kanal")
    a, b, c = st.columns(3)
    with a:
        st.markdown("**Harcama Dağılımı**")
        fig = px.pie(ch, names="Kanal", values="Harcama_TL", hole=0.55, color_discrete_sequence=COLORS)
        show(style_fig(fig), "pie")
    with b:
        st.markdown("**Kanal Bazlı ROAS**")
        fig = px.bar(ch.sort_values("ROAS"), x="ROAS", y="Kanal", orientation="h", text_auto=".2f",
                     color_discrete_sequence=["#c26bf5"])
        show(style_fig(fig), "chan_roas")
    with c:
        st.markdown("**Kanal Bazlı CPA (TL)**")
        fig = px.bar(ch.sort_values("CPA"), x="CPA", y="Kanal", orientation="h", text_auto=".2f",
                     color_discrete_sequence=["#3b82f6"])
        show(style_fig(fig), "chan_cpa")
    st.markdown("**Kanal × İçerik Türü ROAS Isı Haritası**")
    hm = summarize(cur, ["Kanal", "Icerik_Turu"]).pivot(index="Kanal", columns="Icerik_Turu", values="ROAS")
    fig = px.imshow(hm, text_auto=".2f", aspect="auto", color_continuous_scale="Purples")
    show(style_fig(fig, height=300), "heat")

# ===== TAB 4 =====
with tab4:
    st.markdown("Geçmiş kampanya verisiyle eğitilen **Random Forest** modeliyle yeni bir kampanyanın ROAS değerini öngörün.")
    bundle = train_model(df_all)
    if bundle is None:
        st.warning("Model için en az 30 satır veri gerekir.")
    else:
        q1, q2, q3 = st.columns(3)
        q1.metric("Model R² (test)", f"{bundle['r2']:.3f}")
        q2.metric("Ortalama Mutlak Hata", f"{bundle['mae']:.3f}x")
        q3.metric("Eğitim Satırı", f"{bundle['n_train']:,}")
        left, right = st.columns([1, 1])
        with left:
            i1, i2 = st.columns(2)
            gos = i1.number_input("Tahmini Gösterim", 1000, 10_000_000, 250_000, 10_000)
            tik = i2.number_input("Tahmini Tıklama", 1, 1_000_000, 10_000, 500)
            har = i1.number_input("Tahmini Harcama (TL)", 1.0, 10_000_000.0, 10_000.0, 1000.0)
            don = i2.number_input("Tahmini Dönüşüm", 1, 1_000_000, 500, 50)
            kanal = i1.selectbox("Kanal", sorted(df_all["Kanal"].unique()))
            icerik = i2.selectbox("İçerik Türü", sorted(df_all["Icerik_Turu"].unique()))
            go_btn = st.button("🚀 ROAS Tahmini Yap")
        with right:
            fi = bundle["importance"]
            fig = px.bar(fi, x="Önem", y="Özellik", orientation="h", color_discrete_sequence=["#c26bf5"])
            st.markdown("**Özellik Önem Dereceleri**")
            show(style_fig(fig, height=300), "fi")
        if go_btn:
            if tik > gos or don > tik:
                st.error("Tutarsız giriş: Tıklama ≤ Gösterim ve Dönüşüm ≤ Tıklama olmalıdır.")
            else:
                r = predict_roas(bundle, {"Gosterim": gos, "Tiklama": tik, "Harcama_TL": har,
                                          "Donusum": don, "Kanal": kanal, "Icerik_Turu": icerik})
                st.info(f"✨ Model tahmini ROAS: **{r:.2f}x**")
                if r > 3.5:
                    st.success("Mükemmel performans öngörülüyor. Bütçe artışına uygun.")
                elif r > 2.0:
                    st.warning("Orta seviye performans. Optimizasyon önerilir.")
                else:
                    st.error("Düşük ROAS riski. Kreatifleri ve hedef kitleyi gözden geçirin.")

# ===== TAB 5 =====
with tab5:
    st.markdown("Bütçeyi değiştirdiğinizde tahmini gelir projeksiyonu. Esneklik < 1 ise azalan getiri varsayılır.")
    s1, s2 = st.columns(2)
    change = s1.slider("Bütçe Değişim Oranı (%)", -50, 100, 20, 5) / 100
    elast = s2.slider("Getiri Esnekliği", 0.5, 1.0, 0.85, 0.05,
                      help="1.0 = doğrusal getiri, daha düşük değerler = azalan getiri")
    spend0, rev0 = T["Harcama_TL"], T["Gelir_TL"]
    spend1 = spend0 * (1 + change)
    rev1 = rev0 * (1 + change) ** elast
    sc = st.columns(4)
    sc[0].metric("Mevcut Bütçe", fmt_money(spend0), f"{fmt_money(rev0)} gelir", delta_color="off")
    sc[1].metric("Simüle Bütçe", fmt_money(spend1), f"%{change * 100:+.0f}")
    sc[2].metric("Tahmini Gelir", fmt_money(rev1), f"{'+' if rev1 >= rev0 else '-'}{fmt_money(abs(rev1 - rev0))}")
    sc[3].metric("Tahmini ROAS", f"{rev1 / spend1:.2f}x", f"{rev1 / spend1 - T['ROAS']:+.2f}x")
    xs = np.linspace(-0.5, 1.0, 31)
    fig = go.Figure()
    fig.add_scatter(x=xs * 100, y=rev0 * (1 + xs) ** elast, name="Azalan getiri", line=dict(color="#a855f7", width=3))
    fig.add_scatter(x=xs * 100, y=rev0 * (1 + xs), name="Doğrusal", line=dict(color="#9ca3af", dash="dash"))
    fig.add_scatter(x=[change * 100], y=[rev1], name="Seçili senaryo", mode="markers",
                    marker=dict(size=14, color="#ef4444"))
    fig.update_xaxes(title="Bütçe değişimi (%)")
    fig.update_yaxes(title="Gelir (TL)")
    show(style_fig(fig, height=360), "sim")

st.caption("© Marketing Analytics & Campaign Intelligence · Streamlit · Plotly · scikit-learn")
