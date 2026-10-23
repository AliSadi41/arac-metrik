# Türkiye İkinci El Otomobil Piyasasında Fiyat Analizi ve Tahmin Modeli

Bitirme tezi projesi. Türkiye'deki ikinci el otomobil ilan fiyatlarını belirleyen etkenleri analiz eder ve
makine öğrenmesi ile fiyat tahmin modeli kurar.

## Araştırma soruları
1. Hangi özellikler (yaş, km, marka, model, şehir, renk, yakıt) fiyatı en çok etkiliyor?
2. Hangi makine öğrenmesi modeli fiyatı en düşük hatayla tahmin ediyor?
3. Marka ve model bazında yaş–fiyat (değer kaybı) profili nasıl değişiyor?
4. Şehir, diğer özellikler sabitken fiyatı anlamlı biçimde etkiliyor mu?

## Veri
- Kaynak: Kaggle, *Turkey Used Cars Marketplace December 2025* (Eyup Yilmaz), Aralık 2025 kesiti, CC0 etiketli;
  veri sahibinden.com'dan otomatik toplanmıştır. Ayrıntı ve yasal not: `reports/veri_kaynagi.md`.
- Ham veri bu depoda **paylaşılmaz**. Kaggle'dan indirip `data/raw/arac_verisi.csv` olarak koyun.

## Yeniden üretme
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/temizle.py      # data/processed/arac_temiz_v3.csv ve reports/satir_akisi.csv üretir
# ardından notebooks/05_modelleme.ipynb: model sonuçları ve models/lgbm_model.txt
```
Beklenen sonuç: 253.344 ham satırdan 250.955 temiz satır.

## Klasör yapısı
```
data/        raw (ham, değiştirilmez) · processed (script üretir) · archive (eski sürümler)   [git dışı]
notebooks/   01_ham_veri_kesfi · 02_temizleme_dogrulama · 03_eda · 04_yakit_kurallari · 05_modelleme · arsiv/
src/         temizle.py — temizleme boru hattı
reports/     tez_plani · veri_kaynagi · temizleme_kararlari · satir_akisi.csv · yakit_dogrulama.csv
models/      eğitilmiş LightGBM modeli (05 notebook'u üretir)   [git dışı]
app/         Streamlit paneli (henüz yok)
```

## İlerleme
| Aşama | Durum |
|---|---|
| Veri edinme ve kalite kontrol | Tamam |
| Temizleme boru hattı (`src/temizle.py`) | Tamam |
| Keşifsel analiz (EDA) | Tamam (bulgu metinleri taslak) |
| Modelleme | Tamam (ilk sürüm, `05_modelleme`) |
| SHAP, panel, tez metni | Sırada |

## Sonuçlar
Test kümesi (50.191 ilan, rastgele %20). Ayrıntı: `reports/model_sonuclari.csv`, `notebooks/05_modelleme.ipynb`.

| Model | MAE (log) | R² (log) | Ortanca yüzde hata |
|---|---:|---:|---:|
| Taban (yalnızca model yılı) | 0,318 | 0,549 | %24,5 |
| Doğrusal (Ridge) | 0,111 | 0,944 | %8,4 |
| Random Forest | 0,086 | 0,965 | %6,3 |
| LightGBM | 0,082 | 0,968 | %5,9 |

Şehir sütunu çıkarıldığında LightGBM'in MAE'si %2,9 artıyor (`reports/sehir_karsilastirma.csv`).

## Sınırlılıklar
Tek zaman kesiti (Aralık 2025); fiyatlar ilan fiyatıdır; hasar, vites ve ilan tarihi yoktur; `km` 300.000'de kırpılmıştır;
yakıt tipi `variant` metninden türetilmiş ve ilanların yaklaşık %26'sında belirlenememiştir. Ayrıntılar: `reports/temizleme_kararlari.md`.

## Yapay zekâ desteği
_(Üniversitenin yapay zekâ kullanım kuralına göre bu bölümü doldur: hangi araçlar, hangi amaçla kullanıldı.)_
