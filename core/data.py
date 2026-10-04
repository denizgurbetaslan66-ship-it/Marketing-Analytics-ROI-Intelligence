import pandas as pd
import numpy as np

REQUIRED_COLS = ['Kampanya', 'Kanal', 'Icerik_Turu', 'Gosterim', 'Tiklama', 'Harcama_TL', 'Donusum', 'Gelir_TL']

def generate_demo_data():
    np.random.seed(42)
    n_rows = 200
    campaigns = ['Spooky Savings', 'Oktoberfest Offers', 'Flash Sale', 'Summer Vibes', 'Black Friday Early']
    channels = ['Sosyal Medya', 'Google Arama', 'E-posta', 'Influencer']
    content_types = ['Video', 'Görsel', 'Carousel']
    
    dates = pd.date_range(start='2026-01-01', periods=n_rows, freq='D')

    data = {
        'Tarih': np.random.choice(dates, n_rows),
        'Kampanya': np.random.choice(campaigns, n_rows),
        'Kanal': np.random.choice(channels, n_rows),
        'Icerik_Turu': np.random.choice(content_types, n_rows),
        'Gosterim': np.random.randint(10000, 500000, n_rows),
        'Tiklama': np.random.randint(500, 25000, n_rows),
        'Harcama_TL': np.random.uniform(5000, 50000, n_rows),
        'Donusum': np.random.randint(50, 2000, n_rows),
        'Gelir_TL': np.random.uniform(15000, 200000, n_rows)
    }
    df = pd.DataFrame(data)
    return add_metrics(df)

def add_metrics(df):
    df['CTR_Yuzde'] = (df['Tiklama'] / df['Gosterim']) * 100
    df['CPC'] = df['Harcama_TL'] / df['Tiklama']
    df['CPA'] = df['Harcama_TL'] / df['Donusum']
    df['ROAS'] = df['Gelir_TL'] / df['Harcama_TL']
    df['Donusum_Orani'] = (df['Donusum'] / df['Tiklama']) * 100
    df['RPM'] = (df['Gelir_TL'] / df['Gosterim']) * 1000
    return df

def totals(df):
    toplam_gelir = df['Gelir_TL'].sum()
    toplam_harcama = df['Harcama_TL'].sum()
    ortalama_roas = toplam_gelir / toplam_harcama if toplam_harcama > 0 else 0
    ortalama_donusum_orani = df['Donusum_Orani'].mean()
    return toplam_gelir, toplam_harcama, ortalama_roas, ortalama_donusum_orani

def summarize(df, group_by_col='Kampanya'):
    return df.groupby(group_by_col).agg({
        'Gosterim': 'sum',
        'Tiklama': 'sum',
        'Harcama_TL': 'sum',
        'Gelir_TL': 'sum',
        'Donusum': 'sum',
        'CPA': 'mean',
        'RPM': 'mean',
        'CTR_Yuzde': 'mean',
        'ROAS': 'mean'
    }).reset_index()

def validate_upload(df):
    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    return missing
