"""ROAS tahmin modeli (Random Forest)."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from .data import add_metrics

NUM_FEATURES = ["Gosterim", "Tiklama", "Harcama_TL", "Donusum"]
CAT_FEATURES = ["Kanal", "Icerik_Turu"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    return pd.get_dummies(df[NUM_FEATURES + CAT_FEATURES], columns=CAT_FEATURES, dtype=int)


@st.cache_resource(show_spinner="Model eğitiliyor...")
def train_model(df: pd.DataFrame) -> dict | None:
    data = add_metrics(df)
    if len(data) < 30:
        return None
    X, y = build_features(data), data["ROAS"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    imp = (pd.Series(model.feature_importances_, index=X.columns)
           .sort_values(ascending=True).reset_index())
    imp.columns = ["Özellik", "Önem"]
    return {"model": model, "columns": list(X.columns), "r2": r2_score(y_te, pred),
            "mae": mean_absolute_error(y_te, pred), "importance": imp, "n_train": len(X_tr)}


def predict_roas(bundle: dict, row: dict) -> float:
    X = build_features(pd.DataFrame([row])).reindex(columns=bundle["columns"], fill_value=0)
    return float(bundle["model"].predict(X)[0])
