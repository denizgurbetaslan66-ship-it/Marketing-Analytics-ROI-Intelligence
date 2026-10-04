"""Veri üretimi, doğrulama ve metrik hesaplama katmanı."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

BASE_COLS = ["Gosterim", "Tiklama", "Harcama_TL", "Donusum", "Gelir_TL"]
REQUIRED_COLS = ["Tarih", "Kampanya", "Kanal", "Icerik_Turu", *BASE_COLS]

# kampanya: (ortalama CTR %, ortalama dönüşüm oranı %, ortalama sepet tutarı TL)
CAMPAIGNS = {
    "Spooky Savings": (4.8, 5.0, 95),
    "Harvest Discounts": (3.6, 4.0, 80),
    "Octoberfest Offers": (4.5, 6.0, 120),
    "Fall Flash Deals": (2.8, 3.5, 70),
    "Black Friday Early": (4.0, 4.5, 110),
}
# kanal: (CTR çarpanı, CPC çarpanı)
CHANNELS = {
    "Sosyal Medya": (1.00, 1.00),
    "Google Arama": (1.25, 1.35),
    "E-posta": (0.80, 0.45),
    "Influencer": (1.10, 1.10),
}
CONTENT_TYPES = ["Video", "Görsel", "Carousel"]


def safe_div(a, b):
    """Sıfıra bölmeye karşı güvenli bölme (ikisi de Series ya da ikisi de skaler)."""
    if isinstance(a, pd.Series) and isinstance(b, pd.Series):
        out = a / b.replace(0, np.nan)
        return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return float(a) / float(b) if b else 0.0


def _derive(g: pd.DataFrame) -> pd.DataFrame:
    """Toplam değerlerden ağırlıklı (doğru) türev metrikleri hesaplar."""
    g["CTR_Yuzde"] = safe_div(g["Tiklama"], g["Gosterim"]) * 100
    g["CPC"] = safe_div(g["Harcama_TL"], g["Tiklama"])
    g["CPA"] = safe_div(g["Harcama_TL"], g["Donusum"])
    g["ROAS"] = safe_div(g["Gelir_TL"], g["Harcama_TL"])
    g["CVR_Yuzde"] = safe_div(g["Donusum"], g["Tiklama"]) * 100
    g["RPM"] = safe_div(g["Gelir_TL"], g["Gosterim"]) * 1000
    g["AOV"] = safe_div(g["Gelir_TL"], g["Donusum"])
    return g


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return _derive(df.copy())


def summarize(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    g = df.groupby(by, observed=True)[BASE_COLS].sum().reset_index()
    return _derive(g)


def totals(df: pd.DataFrame) -> dict:
    s = df[BASE_COLS].sum()
    row = _derive(pd.DataFrame([s.to_dict()]))
    return row.iloc[0].to_dict()


@st.cache_data(show_spinner=False)
def generate_demo_data(seed: int = 42) -> pd.DataFrame:
    """Son 3 tam ay için tutarlı bir huni (gösterim → tıklama → dönüşüm → gelir) üretir."""
    rng = np.random.default_rng(seed)
    end = pd.Timestamp.today().normalize().replace(day=1) - pd.Timedelta(days=1)
    start = (end - pd.DateOffset(months=2)).replace(day=1)
    dates = pd.date_range(start, end, freq="D")

    per_day = len(CAMPAIGNS) * 2
    df = pd.DataFrame({
        "Tarih": np.repeat(dates, per_day),
        "Kampanya": np.tile(np.repeat(list(CAMPAIGNS), 2), len(dates)),
    })
    n = len(df)
    df["Kanal"] = rng.choice(list(CHANNELS), n)
    df["Icerik_Turu"] = rng.choice(CONTENT_TYPES, n, p=[0.4, 0.35, 0.25])

    ctr_base = df["Kampanya"].map(lambda k: CAMPAIGNS[k][0]).to_numpy()
    cvr_base = df["Kampanya"].map(lambda k: CAMPAIGNS[k][1]).to_numpy()
    aov_base = df["Kampanya"].map(lambda k: CAMPAIGNS[k][2]).to_numpy()
    ctr_mult = df["Kanal"].map(lambda k: CHANNELS[k][0]).to_numpy()
    cpc_mult = df["Kanal"].map(lambda k: CHANNELS[k][1]).to_numpy()
    video_boost = np.where(df["Icerik_Turu"] == "Video", 1.12, 1.0)
    trend = np.linspace(0.92, 1.12, n)  # zamanla hafif büyüme

    impressions = rng.integers(20_000, 120_000, n)
    ctr = np.clip(ctr_base * ctr_mult * video_boost * rng.normal(1, 0.18, n), 0.5, 9) / 100
    clicks = np.maximum((impressions * ctr).astype(int), 1)
    cvr = np.clip(cvr_base * trend * rng.normal(1, 0.22, n), 0.5, 15) / 100
    conversions = np.maximum((clicks * cvr).astype(int), 1)
    cpc = rng.uniform(0.5, 1.6, n) * cpc_mult
    aov = aov_base * rng.normal(1, 0.12, n)

    df["Gosterim"] = impressions
    df["Tiklama"] = clicks
    df["Harcama_TL"] = (clicks * cpc).round(2)
    df["Donusum"] = conversions
    df["Gelir_TL"] = (conversions * aov).round(2)
    return df


def validate_upload(raw: pd.DataFrame) -> tuple[pd.DataFrame | None, str | None]:
    """Yüklenen CSV'yi doğrular ve temizler. (df, hata_mesajı) döndürür."""
    missing = [c for c in REQUIRED_COLS if c not in raw.columns]
    if missing:
        return None, f"Eksik sütunlar: {', '.join(missing)}"
    df = raw[REQUIRED_COLS].copy()
    df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
    for c in BASE_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna()
    df = df[(df[BASE_COLS] >= 0).all(axis=1)]
    for c in ["Kampanya", "Kanal", "Icerik_Turu"]:
        df[c] = df[c].astype(str).str.strip()
    if len(df) < 10:
        return None, "Geçerli satır sayısı en az 10 olmalı."
    return df.reset_index(drop=True), None
