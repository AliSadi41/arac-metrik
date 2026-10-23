# Türkiye İkinci El Otomobil Piyasasında Fiyat Analizi ve Tahmin Modeli — Tez Planı

## 1. Giriş
- Problem nedir? Alıcı ve satıcı adil fiyatı bilmiyor; piyasada bilgi asimetrisi var.
- Neden önemli? Enflasyonist ortamda doğru fiyatlama ihtiyacı.

## 2. Literatür
- (Doldurulacak: ikinci el araç fiyat tahmini üzerine 3–5 çalışma. Örnek: arabam.com verisiyle regresyon ve ağaç tabanlı modelleri karşılaştıran yüksek lisans tezi, MEF Üniversitesi, 2018.)

## 3. Veri
- **Kaynak:** Kaggle, *Turkey Used Cars Marketplace December 2025* (Eyup Yilmaz); sahibinden.com'dan otomatik toplanmış, Aralık 2025 kesiti, 253.344 ilan, CC0 etiketli. Ayrıntı: `veri_kaynagi.md`.
- **Temizleme:** `src/temizle.py` boru hattı; 250.955 ilan kaldı. Karar günlüğü: `temizleme_kararlari.md`.
- **Sınırlılıklar:**
  - Fiyat, gerçekleşen satış fiyatı değil ilan fiyatıdır.
  - Tek zaman kesiti (Aralık 2025); model bu dönemi temsil eder.
  - İkincil veri; hasar/boya, vites ve ilan tarihi bilgisi yok.
  - `km` değeri 300.000'de kırpılmış (bayrakla işaretlendi).
  - Yakıt tipi `variant` metninden türetildi; ilanların yaklaşık %36'sında belirlenemedi.
  - 1995 öncesi araçlar ve fiyatı 10 milyon TL ve üstü ilanlar kapsam dışı.

## 4. Yöntem
- Veri temizleme ve özellik türetme (`src/temizle.py`)
- Keşifsel veri analizi (EDA)
- Modelleme: taban çizgisi (yalnızca model yılı), Linear Regression, Random Forest, XGBoost/LightGBM; hedef `log_price`
- Yorumlama: SHAP
- Ölçüm: MAE, RMSE, R² (log ve TL cinsinden)

## 5. Bulgular
- (Modelleme sonrası doldurulacak.)

## 6. Uygulama
- Streamlit ile anlık fiyat tahmini yapan panel.

## 7. Sonuç
- (Doldurulacak.)

## Araştırma soruları
1. Hangi özellikler (yaş, km, marka, model, şehir, renk, yakıt) ikinci el otomobil fiyatını en çok etkiliyor?
2. Hangi makine öğrenmesi modeli fiyatı en düşük hatayla tahmin ediyor?
3. Marka ve model bazında yaş–fiyat (değer kaybı) profili nasıl değişiyor?
4. Şehir, diğer özellikler sabitken fiyatı anlamlı biçimde etkiliyor mu?
