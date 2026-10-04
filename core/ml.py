import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

def train_model(df):
    """
    Geçmiş kampanya verilerini kullanarak ROAS tahmini için Random Forest modelini eğitir.
    """
    X = df[['Gosterim', 'Tiklama', 'Harcama_TL', 'Donusum']]
    y = df['ROAS']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    return model

def predict_roas(model, gosterim, tiklama, harcama, donusum):
    """
    Yeni girilen kampanya parametrelerine göre tahmini ROAS değeri üretir.
    """
    yeni_veri = pd.DataFrame([[gosterim, tiklama, harcama, donusum]], columns=['Gosterim', 'Tiklama', 'Harcama_TL', 'Donusum'])
    tahmin = model.predict(yeni_veri)
    return tahmin[0]
