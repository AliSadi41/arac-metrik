"""
temizle.py — Ham ilan verisinden analiz verisini tek seferde, adım adım ve kayıt tutarak üretir.

Girdi : data/raw/arac_verisi.csv
Çıktı : data/processed/arac_temiz_v3.csv   (temiz veri + km_kirpildi, log_price, yakit_tipi, motor_hacmi)
        reports/satir_akisi.csv            (her adımda kaç satır silindi; tezdeki akış tablosu)

Kullanım (proje kökünde, sanal ortam açıkken):
    python src/temizle.py

Her çalıştırmada ham veriden baştan başlar; aynı girdi her zaman aynı çıktıyı verir.
Karar gerekçeleri reports/temizleme_kararlari.md içinde belgelenmiştir.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Özellik türetme kuralları (yakıt, motor hacmi, km bayrağı) uygulama ile ortak: src/ozellikler.py
from ozellikler import KM_CAP, temel_ozellikler, varyant_duzelt

# ----------------------------------------------------------------------
# YOLLAR — script hangi klasörden çalıştırılırsa çalıştırılsın proje köküne göre çalışır
# ----------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "arac_verisi.csv"
OUT = ROOT / "data" / "processed" / "arac_temiz_v3.csv"
FLOW = ROOT / "reports" / "satir_akisi.csv"

# ----------------------------------------------------------------------
# AYARLAR — reports/temizleme_kararlari.md ile aynı olmalı
# ----------------------------------------------------------------------
MIN_YEAR = 1995            # bundan eski araçlar kapsam dışı
PRICE_FLOOR = 50_000       # fiyat tabanı kontrolü (ham veride min 100.000 olduğu için 0 satır etkiler)
PRICE_CAP = 10_000_000     # fiyat tavanı; bu değer ve üstü ilanlar güvenilir fiyat içermiyor
ZERO_KM_BEFORE_YEAR = 2023 # km=0 olup model yılı bundan eski olan ilanlar şüpheli sayılır
DROP_PRICE_CAP = True
INVALID_CITIES = ["Diğer", "Kardzhali"]   # Türkiye'de il olmayan kayıtlar


# ----------------------------------------------------------------------
# Boru hattı
# ----------------------------------------------------------------------
def main():
    df = pd.read_csv(RAW)
    # "525d xDrive  Premium" gibi çift boşluklar aynı varyantı iki kategori yapmasın (mükerrer sayısını değiştirmez)
    df["variant"] = varyant_duzelt(df["variant"])
    akis = [("Ham veri", len(df))]

    def adim(ad, yeni):
        akis.append((ad, len(yeni)))
        return yeni

    # 1) Tekrarlar ve geçersiz kayıtlar
    df = adim("Mükerrer satırlar çıkarıldı", df.drop_duplicates())
    df = adim(f"Geçersiz şehir kayıtları çıkarıldı ({', '.join(INVALID_CITIES)})",
              df[~df["city"].isin(INVALID_CITIES)])

    # 2) Fiyat ve km kontrolleri
    df = adim(f"Fiyat tabanı kontrolü (< {PRICE_FLOOR:,} TL)", df[df["price"] >= PRICE_FLOOR])
    df = adim(f"Şüpheli km=0 ilanlar çıkarıldı (model yılı < {ZERO_KM_BEFORE_YEAR})",
              df[~((df["year"] < ZERO_KM_BEFORE_YEAR) & (df["km"] == 0))])
    df = adim(f"km tavan kontrolü (> {KM_CAP:,})", df[df["km"] <= KM_CAP])

    # 3) Kapsam
    df = adim(f"{MIN_YEAR} öncesi araçlar çıkarıldı", df[df["year"] >= MIN_YEAR])
    if DROP_PRICE_CAP:
        df = adim(f"Fiyatı {PRICE_CAP:,} TL ve üstü olan ilanlar çıkarıldı", df[df["price"] < PRICE_CAP])

    # 4) Türetilen özellikler (km_kirpildi, yakit_tipi, motor_hacmi) ve hedef
    df = temel_ozellikler(df)
    df.insert(df.columns.get_loc("km_kirpildi") + 1, "log_price", np.log(df["price"]))

    # --- Güvenlik kontrolleri: biri bozulursa script durur ---
    assert df.duplicated().sum() == 0, "Mükerrer satır kaldı"
    assert (df["year"] >= MIN_YEAR).all(), "Eski araç kaldı"
    assert (df["price"] >= PRICE_FLOOR).all(), "Fiyat tabanının altında ilan kaldı"
    assert not df["city"].isin(INVALID_CITIES).any(), "Geçersiz şehir kaldı"
    if DROP_PRICE_CAP:
        assert (df["price"] < PRICE_CAP).all(), "Fiyat tavanında ilan kaldı"
    assert df.drop(columns="motor_hacmi").isna().sum().sum() == 0, "Boş değer var"
    assert df["motor_hacmi"].dropna().between(0.6, 6.5).all(), "Akla yatkın olmayan motor hacmi"

    # --- Kaydet ---
    OUT.parent.mkdir(parents=True, exist_ok=True)
    FLOW.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    tablo = pd.DataFrame(akis, columns=["adım", "kalan_satır"])
    tablo["silinen"] = (-tablo["kalan_satır"].diff()).abs().astype("Int64")
    tablo.to_csv(FLOW, index=False)

    print(tablo.to_string(index=False))
    print(f"\nKaydedildi: {OUT}  ({len(df):,} satır, {df.shape[1]} sütun)")
    print("km=0 kalan ilan:", int((df["km"] == 0).sum()))
    print("km_kirpildi = 1:", int(df["km_kirpildi"].sum()))
    print("\nyakit_tipi dağılımı:")
    print(df["yakit_tipi"].value_counts().to_string())
    print(f"Bilinmiyor oranı: %{(df['yakit_tipi'] == 'Bilinmiyor').mean() * 100:.1f}")


if __name__ == "__main__":
    main()
