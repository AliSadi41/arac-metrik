# AraçMetrik — Türkiye İkinci El Araç Piyasa Analizi

Türkiye'deki ikinci el otomobil ilan fiyatlarını makine öğrenmesi ile analiz eden portföy projesi.
250.000+ ilan, LightGBM (R²=0.968, ortanca hata %5.9), interaktif Streamlit uygulaması.

## Özellikler

| Sekme | Ne yapar |
|---|---|
| 🔍 Fiyat Tahmini | Marka/model/varyant + yıl/km/şehir/renk gir → LightGBM tahmini + özellik katkı grafiği |
| 📉 Değer Kaybı | Seçilen araç için yıl bazında medyan fiyat eğrisi (q25–q75 bant) |
| 💡 Fırsat Dedektörü | İlan fiyatını gir → benzer araçların dağılımına göre fırsat skoru |

## Sonuçlar

Test kümesi (50.191 ilan, rastgele %20):

| Model | R² | Ortanca hata |
|---|---:|---:|
| Taban (yalnızca yıl) | 0,549 | %24,5 |
| Ridge | 0,944 | %8,4 |
| Random Forest | 0,965 | %6,3 |
| **LightGBM** | **0,968** | **%5,9** |

## Veri

- Kaggle · *Turkey Used Cars Marketplace December 2025* · CC0 · Aralık 2025 kesiti
- 250.955 temiz ilan (253.344 ham → `src/temizle.py`)
- Ham veri bu repoda **yer almaz** — Kaggle'dan indir, `data/raw/arac_verisi.csv` olarak koy
- Ayrıntı: `reports/veri_kaynagi.md`

## Yerel Kurulum

```bash
# Windows
python -m venv .venv_win
.venv_win\Scripts\activate
pip install -r requirements.txt

# Veriyi hazırla
python src/temizle.py           # data/processed/arac_temiz_v3.csv üretir

# Modeli eğit
# notebooks/05_modelleme.ipynb çalıştır → models/ klasörü oluşur

# Uygulamayı başlat
streamlit run app/panel.py      # http://localhost:8501
```

macOS/Linux için `python3.12 -m venv .venv` ve `source .venv/bin/activate`.

## Klasör Yapısı

```
data/        raw · processed · archive          [git dışı]
notebooks/   01_ham_veri · 02_temizleme · 03_eda · 04_yakit · 05_modelleme
src/         temizle.py · ozellikler.py
tests/       test_ozellikler.py
reports/     veri_kaynagi · temizleme_kararlari · satir_akisi.csv
models/      lgbm_model.txt · lgbm_meta.json · katalog.csv   [git dışı]
app/         panel.py — Streamlit uygulaması
```

## Sınırlılıklar

- Tek zaman kesiti (Aralık 2025) — canlı veri değil
- Fiyatlar ilan fiyatıdır, gerçekleşen satış değil
- Hasar/boya geçmişi, vites tipi ve ilan tarihi modelde yok
- Kilometre 300.000'de kırpılmış
- Yakıt tipi `variant` metninden türetilmiş; ~%26 ilanda belirlenemedi

## Teknoloji

Python 3.12 · LightGBM 4.7 · pandas 3.0 · Streamlit 1.66 · Altair · scikit-learn
