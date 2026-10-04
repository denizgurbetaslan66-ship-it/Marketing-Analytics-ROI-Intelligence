# 📈 Marketing Analytics & Campaign Intelligence

Dijital pazarlama kampanyalarını ölçümleyen, bütçe senaryoları simüle eden ve makine öğrenmesiyle ROAS tahmini yapan interaktif bir **Streamlit** dashboard'u.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.50%2B-ff4b4b) ![License](https://img.shields.io/badge/License-MIT-green)

> 📸 Ekran görüntüsünü `docs/screenshot.png` olarak ekleyip buraya bağlayabilirsiniz: `![Dashboard](docs/screenshot.png)`

## ✨ Özellikler

- **Genel Bakış:** Gelir, Harcama, ROAS/ROI ve Dönüşüm Oranı kartları; önceki döneme göre **gerçek** değişim oranları
- **Etkileşim grafiği:** Haftalık, kampanya bazlı CTR trendi
- **AOV analizi:** Bu dönem vs önceki dönem ortalama sipariş değeri
- **Metrik tablosu & "Ayın En İyileri":** CPA, RPM, tıklama, CTR, ROAS
- **Kampanya Analizi:** Harcama–gelir baloncuk grafiği, günlük trend, CSV indirme
- **Kanal & İçerik:** Harcama dağılımı, kanal ROAS/CPA, Kanal × İçerik ısı haritası
- **ML ROAS Tahmini:** Random Forest, model başarımı (R², MAE), özellik önemleri, girdi doğrulama
- **Bütçe Simülasyonu:** Azalan getiri (esneklik) destekli what-if analizi
- **Kendi verinizi yükleyin:** CSV yükleme, doğrulama ve temizleme
- Arama kutusu, çoklu filtreler (kampanya / kanal / içerik türü), dönem seçici

## 🚀 Kurulum

```bash
git clone https://github.com/<kullanici-adi>/marketing-analytics.git
cd marketing-analytics
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Uygulama `http://localhost:8501` adresinde açılır.

## 📁 Proje Yapısı

```
marketing-analytics/
├── app.py                  # Streamlit arayüzü
├── core/
│   ├── data.py             # Veri üretimi, doğrulama, metrik hesapları
│   └── ml.py               # Random Forest modeli
├── assets/style.css        # Özel tasarım (kartlar, sekmeler, tema)
├── data/sample_campaigns.csv  # Örnek veri seti
├── .streamlit/config.toml  # Tema ayarları
├── test_app.py             # Smoke test
└── requirements.txt
```

## 📊 Kendi Verinizi Kullanma

Kenar çubuğundan bir CSV yükleyin. Gerekli sütunlar (örnek: `data/sample_campaigns.csv`):

| Sütun | Açıklama |
|---|---|
| `Tarih` | Tarih (YYYY-MM-DD) |
| `Kampanya`, `Kanal`, `Icerik_Turu` | Kategorik alanlar |
| `Gosterim`, `Tiklama`, `Donusum` | Sayısal huni metrikleri |
| `Harcama_TL`, `Gelir_TL` | Para değerleri (TL) |

## 🧮 Metrik Tanımları

Tüm oranlar satır ortalaması yerine **toplamlardan** hesaplanır (ağırlıklı, doğru sonuç):

`CTR = Tıklama / Gösterim` · `CPA = Harcama / Dönüşüm` · `ROAS = Gelir / Harcama` · `Dönüşüm Oranı = Dönüşüm / Tıklama` · `RPM = Gelir / Gösterim × 1000` · `AOV = Gelir / Dönüşüm`

## ⚠️ Not

Varsayılan veri **sentetik (demo)** veridir. ML modeli ve simülasyon sonuçları gerçek karar süreçleri için değil, gösterim amaçlıdır; gerçek veriyle yeniden değerlendirilmelidir.

## ☁️ Yayınlama (Streamlit Community Cloud)

1. Projeyi GitHub'a yükleyin
2. [share.streamlit.io](https://share.streamlit.io) → *New app* → repo ve `app.py` seçin → *Deploy*

## 🧪 Test

```bash
python test_app.py
```

## 📄 Lisans

MIT — bkz. [LICENSE](LICENSE)
