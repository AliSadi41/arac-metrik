# OtoPuls — Türkiye İkinci El Araç Piyasa Analizi

<p align="center">
  <a href="https://arac-metrik-pnvt2xmpxif4wsjwewvsvt.streamlit.app/" target="_blank">
    <img src="https://img.shields.io/badge/Canlı_Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit App">
  </a>
  <a href="https://AliSadi41.github.io/arac-metrik/" target="_blank">
    <img src="https://img.shields.io/badge/Teknik_Rehber-GitHub_Pages-0ea5e9?style=for-the-badge&logo=github&logoColor=white" alt="Teknik Rehber">
  </a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/LightGBM-R²_0.97-success?style=for-the-badge" alt="R²">
  <img src="https://img.shields.io/badge/Veri-250.955_ilan-blue?style=for-the-badge" alt="Veri">
</p>

<p align="center">
  Türkiye ikinci el otomobil piyasasını makine öğrenmesi ile derinlemesine analiz eden interaktif portföy projesi.<br>
  250 bin+ ilan · LightGBM (R²=0.97, ortanca hata %5.9) · 6 analiz sekmesi · Hover tooltip detayları
</p>

---

## Özellikler

| Sekme | Ne yapar |
|---|---|
| 🔍 **Fiyat Tahmini** | Marka / model / varyant + yıl / km / şehir / renk gir → LightGBM tahmini + %80 güven aralığı + özellik katkı grafiği |
| 📉 **Değer Kaybı** | Seçilen araç için yıl bazında medyan fiyat eğrisi; q25–q75 bant, toplam ve yıllık kayıp metrikleri |
| 💡 **Fırsat Dedektörü** | İlan fiyatını gir → benzer araçların dağılımına karşı fırsat skoru (Harika Fırsat → Pahalı) |
| 📊 **Piyasa Genel Bakış** | 250 bin ilanın marka / yakıt / yıl / şehir dağılımı; interaktif grafikler |
| 🏆 **En İyi Fırsatlar** | Piyasa ortancasından ≥%15 ucuz ilanlar; marka/indirim filtresi, hover tooltip detayları |
| ✨ **Karşılaştırma** | Birden fazla marka için yıl bazında fiyat eğrilerini yan yana karşılaştır |

---

## Model Sonuçları

Test kümesi — 50.191 ilan (rastgele %20 ayrım):

| Model | R² | Ortanca hata |
|---|---:|---:|
| Taban (yalnızca yıl) | 0.549 | %24.5 |
| Ridge | 0.944 | %8.4 |
| Random Forest | 0.965 | %6.3 |
| **LightGBM** | **0.968** | **%5.9** |

---

## Veri

- **Kaynak:** Kaggle · *Turkey Used Cars Marketplace December 2025* · CC0
- **Kapsam:** Aralık 2025 kesiti · 250.955 temiz ilan (ham: 253.344)
- **Temizleme:** `src/temizle.py` — eksik değer, aykırı fiyat, km kırpma (300k), yakıt türü çıkarımı
- Ham veri repoda **yer almaz** — Kaggle'dan indir, `data/raw/arac_verisi.csv` olarak kaydet

---

## Yerel Kurulum

```bash
# 1. Ortam
python -m venv .venv_win          # Windows
.venv_win\Scripts\activate
pip install -r requirements.txt

# 2. Veriyi hazırla
python src/temizle.py             # data/processed/arac_temiz_v3.csv

# 3. Modeli eğit
# notebooks/05_modelleme.ipynb → models/ klasörü oluşur

# 4. Uygulamayı başlat
streamlit run app/panel.py        # http://localhost:8501
```

macOS/Linux: `python3.12 -m venv .venv` ve `source .venv/bin/activate`.

---

## Klasör Yapısı

```
app/         panel.py — Streamlit uygulaması (6 sekme)
src/         temizle.py · ozellikler.py
models/      lgbm_model.txt · lgbm_meta.json · katalog.csv
data/        raw/ [git dışı] · processed/ · archive/ [git dışı]
notebooks/   01_ham_veri → 05_modelleme
tests/       test_ozellikler.py
reports/     veri_kaynagi.md · temizleme_kararlari.md
```

---

## Teknoloji

`Python 3.12` · `LightGBM 4.7` · `pandas 3.0` · `Streamlit 1.66` · `Altair` · `scikit-learn` · `Pillow`

---

## Sınırlılıklar

- Tek zaman kesiti (Aralık 2025) — canlı veri akışı yok
- Fiyatlar ilan fiyatıdır; gerçekleşen satışı yansıtmayabilir
- Hasar/boya geçmişi, vites tipi ve ilan tarihi modelde yer almıyor
- Yakıt tipi `variant` metninden türetilmiş; ~%26 ilanda belirlenemedi
- Kilometre 300.000'de kırpılmış

---

> **Not:** Bu proje eğitim/portföy amaçlıdır; yatırım tavsiyesi değildir.
