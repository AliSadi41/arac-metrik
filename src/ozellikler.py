"""
ozellikler.py — Özellik türetme kodunun TEK kaynağı.

Temizleme (src/temizle.py), modelleme (notebooks/05_modelleme.ipynb) ve uygulama (app/) bu dosyayı kullanır.
Böylece uygulama, kullanıcının girdiği araç bilgisinden modelin eğitimde gördüğü özellikleri birebir aynı
şekilde üretir. Bir kuralı değiştirirsen: python src/temizle.py, modeli yeniden eğit, pytest çalıştır.

Kuralların gerekçeleri: reports/temizleme_kararlari.md (madde 9 yakıt, madde 10 motor hacmi).
"""

import re

import numpy as np
import pandas as pd

KM_CAP = 300_000        # km bu değerde kırpılmış (censoring); bu değer ve üstü "300.000+" sayılır
REFERANS_YILI = 2025    # veri Aralık 2025 kesiti; yaş = REFERANS_YILI - model yılı

# Modelin kullandığı özellikler
KAT = ["brand", "model", "variant", "color", "city", "yakit_tipi"]
SAY = ["yas", "km", "km_kirpildi", "motor_hacmi", "hacim_yok"]


# ----------------------------------------------------------------------
# Yakıt tipi (variant metninden, kural tabanlı)
# ----------------------------------------------------------------------
BENZIN = ["TSI", "TFSI", "VTI", "CGI", "PURETECH", "ECOBOOST", "MPI", "IG-T",
          "T-GDI", "TCE", "FSI", "GDI", "KOMPRESSOR", "KOMP.", "VTEC", "FIRE", "SCE", "CVVT",
          "TI-VCT", "TWINPORT"]
DIZEL = ["TDI", "DCI", "HDI", "CDTI", "CRDI", "BLUEHDI", "MULTIJET", "MJET", "D-4D",
         "TDCI", "ECOBLUE", "SKYACTIV-D", "CDI", "DIESEL"]


def yakit_turet(brand, model, variant):
    v = str(variant).upper()

    if "LPG" in v or "ECOG" in v:
        return "LPG"
    # Honda Civic "Eco" varyantları Türkiye'de fabrika çıkışlı LPG'li satılır (1.6 i-VTEC Eco, 1.5 VTEC Turbo Eco).
    # VTEC kuralından (Benzin) önce gelmeli.
    if str(brand).lower() == "honda" and str(model).lower() == "civic" and re.search(r"\bECO\b", v):
        return "LPG"
    # \bEV\b: yalnızca tam kelime (LEVEL, EVOLUTION gibi kelimeleri yakalamaz)
    if re.search(r"HYBRID|HIBRIT|ELECTRIC|E-TRON|PHEV|MHEV|E-TECH|\bEV\b", v):
        return "Hibrit/Elektrik"
    if str(brand).lower() == "bmw":
        m = str(model).lower()
        if m == "i":                                    # BMW i serisi elektriklidir
            return "Hibrit/Elektrik"
        # Model kodunun son eki yakıtı verir: 330e/225xe plug-in hibrit, 320d/530xd/525tds dizel,
        # 520i/318Ci/520Li/316ti/318is benzin. Eksiz kodlar (550 xDrive, 220) Bilinmiyor kalır.
        if re.search(r"\d{3}X?E\b", v):
            return "Hibrit/Elektrik"
        if re.search(r"\d{3}(X?D|TDS)\b", v):
            return "Dizel"
        if re.search(r"\d{3}(I|CI|LI|TI|IS)\b", v):
            return "Benzin"
        # M ve Z modellerinin hepsi benzinli (veride en yeni M 2021 model; 2024 sonrası M5 hibrittir)
        if m in ("m", "z"):
            return "Benzin"
    # \bIE\b: Fiat "1.4 ie" (injection elettronica); alt dizgi olarak aranamaz
    if any(k in v for k in BENZIN) or re.search(r"\bIE\b", v):
        return "Benzin"
    if any(k in v for k in DIZEL) or re.search(r"\sD\b|\bD$", v):
        return "Dizel"
    return "Bilinmiyor"   # emin değilsek "Benzin" demiyoruz


# ----------------------------------------------------------------------
# Metin ve sayısal özellikler
# ----------------------------------------------------------------------
def varyant_duzelt(variant):
    """"525d xDrive  Premium" gibi çift boşlukları teke indirir (Series ya da tek metin)."""
    if isinstance(variant, pd.Series):
        return variant.astype(str).str.split().str.join(" ")
    return " ".join(str(variant).split())


def motor_hacmi_cikar(variant):
    """variant metnindeki "1.6", "1.33" gibi litre ifadesi; yoksa NaN (BMW "320i", Mercedes "C 200" gibi)."""
    s = pd.Series(variant) if not isinstance(variant, pd.Series) else variant
    return s.astype(str).str.extract(r"(?<![\d.])(\d\.\d{1,2})(?![\d.])")[0].astype(float)


def temel_ozellikler(df):
    """Temiz veri dosyasına yazılan türetilmiş sütunlar: km_kirpildi, yakit_tipi, motor_hacmi."""
    df = df.copy()
    df["km_kirpildi"] = (df["km"] >= KM_CAP).astype(int)
    df["yakit_tipi"] = [yakit_turet(b, m, v) for b, m, v in zip(df["brand"], df["model"], df["variant"])]
    df["motor_hacmi"] = motor_hacmi_cikar(df["variant"]).values
    return df


def model_ozellikleri(df):
    """Modelden hemen önce eklenen sütunlar: yas, hacim_yok."""
    df = df.copy()
    df["yas"] = REFERANS_YILI - df["year"]
    df["hacim_yok"] = df["motor_hacmi"].isna().astype(int)
    return df


def ham_girdiden(brand, model, variant, year, km, color, city):
    """Uygulama için: kullanıcının girdiği tek aracı modelin beklediği satıra çevirir.
    km tavanın üstündeyse eğitimdeki gibi KM_CAP'te kırpılır ve bayrak 1 olur."""
    d = pd.DataFrame([{"brand": brand, "model": model, "variant": varyant_duzelt(variant),
                       "year": int(year), "km": min(int(km), KM_CAP), "color": color, "city": city}])
    return model_ozellikleri(temel_ozellikler(d))


def lgbm_girdisi(d, kategoriler, ozellikler=None):
    """LightGBM girdisi: kategorik sütunlar eğitimdeki kategori listesine sabitlenir
    (eğitimde görülmeyen değer → boş). kategoriler: {sütun: eğitimdeki değerler listesi}."""
    ozellikler = KAT + SAY if ozellikler is None else ozellikler
    x = d[ozellikler].copy()
    for k in [k for k in KAT if k in ozellikler]:
        x[k] = pd.Categorical(x[k].where(x[k].isin(kategoriler[k])), categories=kategoriler[k])
    return x
