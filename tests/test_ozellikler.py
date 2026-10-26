"""
src/ozellikler.py testleri. Çalıştırma (proje kökünde): pytest

Yakıt kuralları değiştiğinde önceden doğru olan sonuçların bozulmadığını kontrol eder.
Her vaka, geliştirme sırasında karşılaşılan gerçek bir varyant ya da tuzaktır.
"""

import math
from pathlib import Path

import pandas as pd
import pytest

from ozellikler import KM_CAP, ham_girdiden, motor_hacmi_cikar, varyant_duzelt, yakit_turet

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("brand, model, variant, beklenen", [
    # Ayrı yazılmış "D" eki (eski \s D\b hatası bunları kaçırıyordu)
    ("mercedes", "c", "C 200 D AMG", "Dizel"),
    ("mercedes", "e", "E 200 d Exclusive", "Dizel"),
    ("volvo", "s60", "1.6 D Premium", "Dizel"),
    ("opel", "astra", "1.5 D Edition", "Dizel"),
    # BMW model kodu ekleri
    ("bmw", "3", "320d M Sport", "Dizel"),
    ("bmw", "5", "530xd Gran Turismo Premium", "Dizel"),
    ("bmw", "5", "525tds Standart", "Dizel"),
    ("bmw", "5", "520i M Sport", "Benzin"),
    ("bmw", "3", "318Ci", "Benzin"),
    ("bmw", "3", "316ti Compact", "Benzin"),
    ("bmw", "2", "230e xDrive Active Tourer Luxury Line", "Hibrit/Elektrik"),
    ("bmw", "m", "M4 Competition", "Benzin"),
    ("bmw", "i", "i5 eDrive 40", "Hibrit/Elektrik"),
    ("bmw", "5", "550 xDrive", "Bilinmiyor"),          # eksiz kod: bilerek belirsiz bırakıldı
    # Honda Civic Eco = fabrika LPG; Eco'suz VTEC benzin
    ("honda", "civic", "1.6i VTEC Eco Elegance", "LPG"),
    ("honda", "civic", "1.5 VTEC Eco Executive Plus", "LPG"),
    ("honda", "civic", "1.6i VTEC Executive", "Benzin"),
    # "EV" tam kelime olmalı: EVOLUTION / EVO hibrit sayılmamalı
    ("renault", "clio", "1.0 TCe Evolution", "Benzin"),
    ("fiat", "egea", "EVO 1.3 Multijet Dynamic", "Dizel"),
    ("renault", "clio", "1.5 Mhev Premium", "Hibrit/Elektrik"),
    # Sonradan eklenen işaretler
    ("fiat", "500", "500L 1.3 Mjet PopStar", "Dizel"),
    ("ford", "focus", "1.6 Ti-VCT Trend X", "Benzin"),
    ("opel", "corsa", "1.2 Twinport Essentia", "Benzin"),
    ("hyundai", "accent", "1.4 CVVT Jump", "Benzin"),
    ("mercedes", "c", "C 180 Komp. BlueEfficiency AMG", "Benzin"),
    ("fiat", "uno", "1.4 ie SX", "Benzin"),
    # İşaretsiz: tahmin edilmez (karar A)
    ("opel", "astra", "1.6 Edition", "Bilinmiyor"),
    ("toyota", "corolla", "1.33 Life", "Bilinmiyor"),
])
def test_yakit_turet(brand, model, variant, beklenen):
    assert yakit_turet(brand, model, variant) == beklenen


def test_elle_dogrulanmis_ornek():
    """reports/yakit_dogrulama.csv: elle etiketli 60 ilan. Sınıflanan her ilan doğru olmalı
    ve sınıflanan sayısı geriye gitmemeli (kural değişikliği öncesi 48)."""
    d = pd.read_csv(ROOT / "reports" / "yakit_dogrulama.csv")
    tahmin = [yakit_turet(b, m, v) for b, m, v in zip(d["brand"], d["model"], d["variant"])]
    d = d.assign(tahmin=tahmin)
    siniflanan = d[d["tahmin"] != "Bilinmiyor"]
    yanlis = siniflanan[siniflanan["tahmin"] != siniflanan["gercek_yakit"]]
    assert yanlis.empty, f"Yanlış sınıflanan ilanlar:\n{yanlis}"
    assert len(siniflanan) >= 48


@pytest.mark.parametrize("variant, beklenen", [
    ("1.6 TDI Comfortline", 1.6),
    ("1.33 Life", 1.33),
    ("500L 1.3 Mjet PopStar", 1.3),
    ("EVO 1.4 Fire Active", 1.4),
    ("2.0 D B5 Inscription", 2.0),
    ("320i M Sport", None),
    ("C 200 D AMG", None),
])
def test_motor_hacmi(variant, beklenen):
    sonuc = motor_hacmi_cikar(variant).iloc[0]
    if beklenen is None:
        assert math.isnan(sonuc)
    else:
        assert sonuc == beklenen


def test_varyant_duzelt():
    assert varyant_duzelt("525d xDrive  Premium") == "525d xDrive Premium"
    assert varyant_duzelt(pd.Series(["a  b", " c "])).tolist() == ["a b", "c"]


def test_ham_girdiden():
    """Uygulamanın kullanacağı yol: tek araçtan model satırı."""
    satir = ham_girdiden("bmw", "3", "320d  M Sport", 2019, 350_000, "White", "Ankara").iloc[0]
    assert satir["variant"] == "320d M Sport"
    assert satir["km"] == KM_CAP and satir["km_kirpildi"] == 1     # tavanın üstü eğitimdeki gibi kırpılır
    assert satir["yakit_tipi"] == "Dizel"
    assert satir["yas"] == 6
    assert math.isnan(satir["motor_hacmi"]) and satir["hacim_yok"] == 1

    satir = ham_girdiden("volkswagen", "passat", "1.5 TSI Impression", 2025, 0, "Black", "İstanbul").iloc[0]
    assert satir["km_kirpildi"] == 0 and satir["yas"] == 0
    assert satir["motor_hacmi"] == 1.5 and satir["hacim_yok"] == 0
