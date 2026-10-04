from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import pandas as pd

def train_roas_model(df):
    """
    Geçmiş verileri kullanarak ROAS tahminlemesi yapan Random Forest modelini eğitir.
    """
    X = df[['Gosterim', 'Tiklama', 'Harcama_TL', 'Donusum']]
    y = df['ROAS']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    return model

def evaluate_model(model, df):
    X = df[['Gosterim', 'Tiklama', 'Harcama_TL', 'Donusum']]
    y = df['ROAS']
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return r2, rmse
