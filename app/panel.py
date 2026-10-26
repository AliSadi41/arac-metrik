import json
import sys
from pathlib import Path

import altair as alt
import lightgbm as lgb
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ozellikler import KM_CAP, REFERANS_YILI, ham_girdiden, lgbm_girdisi  # noqa: E402

MODELS = ROOT / "models"
DATA   = ROOT / "data" / "processed" / "arac_temiz_v3.csv"

# ── görünen adlar ────────────────────────────────────────────────────────────
MARKA_AD = {"bmw": "BMW", "mini": "MINI", "seat": "SEAT", "citroen": "Citroën",
            "skoda": "Škoda", "mercedes": "Mercedes-Benz", "volkswagen": "Volkswagen"}
RENK_AD  = {"White": "Beyaz", "Black": "Siyah", "Gray": "Gri", "Silver Gray": "Gümüş Gri",
            "Smoke Gray": "Füme", "Blue": "Mavi", "Navy": "Lacivert", "Red": "Kırmızı",
            "Burgundy": "Bordo", "Brown": "Kahverengi", "Beige": "Bej", "Green": "Yeşil",
            "Yellow": "Sarı", "Champagne": "Şampanya", "Orange": "Turuncu",
            "Turquoise": "Turkuaz", "Purple": "Mor", "Pink": "Pembe"}
OZELLIK_AD = {"brand": "Marka", "model": "Model", "variant": "Varyant", "color": "Renk",
              "city": "Şehir", "yakit_tipi": "Yakıt tipi", "yas": "Yaş",
              "km": "Kilometre", "km_kirpildi": "Kilometre",
              "motor_hacmi": "Motor hacmi", "hacim_yok": "Motor hacmi"}

RENK_FIRSAT = {
    "Harika Fırsat 🔥": "#1a7a4a",
    "İyi Fırsat ✅":    "#2d8f5a",
    "Piyasa Fiyatı ⚖️": "#6b7280",
    "Biraz Pahalı ⚠️":  "#c97a10",
    "Pahalı ❌":         "#c0392b",
}


def marka_ad(b): return MARKA_AD.get(b, b.title())
def model_ad(brand, m):
    if brand == "bmw" and m.isdigit():   return f"{m} Serisi"
    if brand == "mercedes" and len(m) <= 3: return f"{m.upper()}-Serisi"
    return m.upper() if len(m) <= 3 else m.title()
def tl(x): return f"{round(x / 5_000) * 5_000:,.0f} TL".replace(",", ".")


# ── model yükleme ────────────────────────────────────────────────────────────
@st.cache_resource
def yukle_model():
    eksik = [f for f in ["lgbm_model.txt", "lgbm_meta.json", "katalog.csv"]
             if not (MODELS / f).exists()]
    if eksik:
        return None, None, None, eksik
    lgbm   = lgb.Booster(model_file=str(MODELS / "lgbm_model.txt"))
    meta   = json.loads((MODELS / "lgbm_meta.json").read_text())
    katalog = pd.read_csv(MODELS / "katalog.csv", dtype={"model": str})
    return lgbm, meta, katalog, []


@st.cache_data(show_spinner="Fırsatlar hesaplanıyor…")
def hesapla_firsatlar(df):
    grup = df.groupby(["brand", "model", "year"])["price"].agg(
        grup_median="median", grup_ilan="count"
    ).reset_index()
    merged = df.merge(grup, on=["brand", "model", "year"])
    merged = merged[merged["grup_ilan"] >= 15]
    merged["indirim_pct"] = (merged["grup_median"] - merged["price"]) / merged["grup_median"] * 100
    # Cap at 60% — higher discounts are almost always scam/data-entry errors
    return merged[(merged["indirim_pct"] >= 15) & (merged["indirim_pct"] <= 60)].copy()


@st.cache_data(show_spinner="Veri yükleniyor…")
def yukle_veri():
    if not DATA.exists():
        return None
    df = pd.read_csv(DATA, dtype={"model": str, "variant": str}, encoding="utf-8")
    df["yas"] = REFERANS_YILI - df["year"]
    return df


def tahmin_et(lgbm, meta, satir):
    X          = lgbm_girdisi(satir, meta["kategoriler"], meta["ozellikler"])
    log_fiyat  = float(lgbm.predict(X)[0])
    katki      = lgbm.predict(X, pred_contrib=True)[0]
    return log_fiyat, pd.Series(katki[:-1], index=meta["ozellikler"]), float(katki[-1])


# ── sayfa yapılandırması ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AraçMetrik — Türkiye İkinci El Araç Piyasa Analizi",
    page_icon="🚗",
    layout="centered",
    menu_items={
        "Get help":          None,
        "Report a bug":      None,
        "About":             "AraçMetrik · 250 bin+ ilan · LightGBM (R²=0.97) · Aralık 2025 verisi",
    },
)

# ── Global CSS (st.html avoids markdown parser interfering with CSS syntax) ───
st.html("""<style>
  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }
  div[data-testid="stToolbar"] { display: none; }
  .araçmetrik-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    border-radius: 12px;
    padding: 2rem 2.4rem 1.6rem;
    margin-bottom: 1.4rem;
    color: #fff;
  }
  .araçmetrik-hero h1 { font-size: 2rem; font-weight: 800; margin: 0 0 .3rem; letter-spacing: -.5px; }
  .araçmetrik-hero p  { font-size: .92rem; color: #94a3b8; margin: 0; line-height: 1.5; }
  .araçmetrik-hero .badges { margin-top: 1rem; display: flex; gap: .5rem; flex-wrap: wrap; }
  .araçmetrik-hero .badge {
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.15);
    border-radius: 20px; padding: .18rem .7rem;
    font-size: .78rem; color: #cbd5e1;
  }
  div[data-testid="metric-container"] {
    background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12);
    border-radius: 10px; padding: .8rem 1rem;
  }
  .araçmetrik-footer {
    margin-top: 2.5rem; padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,.12);
    font-size: .78rem; color: #94a3b8;
    text-align: center; line-height: 1.7;
  }
  .firsat-etiket {
    text-align: center; padding: 14px 0 6px;
    font-size: 1.9rem; font-weight: 700;
    border-radius: 10px;
    background: rgba(255,255,255,.04);
    margin-bottom: .5rem;
  }
</style>""")

# ── Hero banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="araçmetrik-hero">
  <h1>🚗 AraçMetrik</h1>
  <p>Türkiye ikinci el otomobil piyasasını yapay zeka ile analiz et.<br>
     Fiyat tahmini · Değer kaybı · Fırsat dedektörü · Piyasa analizi · En iyi fırsatlar · Marka karşılaştırma</p>
  <div class="badges">
    <span class="badge">250.955 ilan</span>
    <span class="badge">R² = 0.97</span>
    <span class="badge">Ortanca hata %5.9</span>
    <span class="badge">LightGBM</span>
    <span class="badge">Aralık 2025</span>
  </div>
</div>
""", unsafe_allow_html=True)

lgbm_model, meta, katalog, eksik_dosyalar = yukle_model()
veri = yukle_veri()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔍 Fiyat Tahmini", "📉 Değer Kaybı", "💡 Fırsat Dedektörü",
    "📊 Genel Bakış", "🏆 En İyi Fırsatlar", "🔄 Karşılaştırma",
])


# ════════════════════════════════════════════════════════════════════════════
#  TAB 1 — Fiyat Tahmini
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    if eksik_dosyalar:
        st.error("Model dosyaları bulunamadı: " + ", ".join(eksik_dosyalar)
                 + ". Önce `python src/temizle.py`, ardından `notebooks/05_modelleme.ipynb` çalıştırılmalı.")
        st.stop()

    sol, sag = st.columns(2)
    with sol:
        markalar  = sorted(katalog["brand"].unique(), key=marka_ad)
        marka     = st.selectbox("Marka", markalar, format_func=marka_ad,
                                 index=markalar.index("volkswagen") if "volkswagen" in markalar else 0,
                                 key="t1_marka")
        k_marka   = katalog[katalog["brand"] == marka]
        modeller  = sorted(k_marka["model"].unique(), key=lambda m: model_ad(marka, m))
        model_sec = st.selectbox("Model", modeller, format_func=lambda m: model_ad(marka, m), key="t1_model")
        k_model   = k_marka[k_marka["model"] == model_sec].sort_values("variant")
        varyantlar = k_model["variant"].tolist()
        varyant   = st.selectbox("Varyant", varyantlar,
                                 index=varyantlar.index(k_model.loc[k_model["ilan"].idxmax(), "variant"]),
                                 key="t1_varyant")
        v_bilgi   = k_model[k_model["variant"] == varyant].iloc[0]
        renkler  = sorted(meta["kategoriler"]["color"], key=lambda r: RENK_AD.get(r, r))
        renk     = st.selectbox("Renk", renkler, format_func=lambda r: RENK_AD.get(r, r),
                                index=renkler.index("White") if "White" in renkler else 0,
                                key="t1_renk")

    with sag:
        yil     = st.number_input("Model yılı", min_value=1995, max_value=REFERANS_YILI,
                                   value=int(v_bilgi["yil_max"]), step=1, key="t1_yil")
        km      = st.number_input("Kilometre", min_value=0, max_value=1_000_000,
                                   value=100_000, step=5_000, key="t1_km")
        sehirler = meta["kategoriler"]["city"]
        sehir    = st.selectbox("Şehir", sehirler,
                                index=sehirler.index("İstanbul") if "İstanbul" in sehirler else 0,
                                key="t1_sehir")

    satir      = ham_girdiden(marka, model_sec, varyant, yil, km, renk, sehir)
    log_tahmin, katki, taban = tahmin_et(lgbm_model, meta, satir)
    q10, q90   = meta["aralik_log"]

    st.divider()
    st.metric("Tahmini ilan fiyatı", tl(np.exp(log_tahmin)))
    st.write(
        f"Olası aralık: **{tl(np.exp(log_tahmin + q10))} – {tl(np.exp(log_tahmin + q90))}**  \n"
        f"<small>Benzer test ilanlarının %80'inin gerçek fiyatı bu aralıkta kaldı. "
        f"Modelin ortanca hatası %{meta['test_mdape']:.1f}.</small>",
        unsafe_allow_html=True,
    )

    hacim = satir["motor_hacmi"].iloc[0]
    st.caption(
        f"Varyant metninden türetilen bilgiler: yakıt **{satir['yakit_tipi'].iloc[0]}** · "
        f"motor hacmi **{'bilinmiyor' if pd.isna(hacim) else f'{hacim:.1f} L'}** · "
        f"yaş **{int(satir['yas'].iloc[0])}**"
    )

    if not (v_bilgi["yil_min"] <= yil <= v_bilgi["yil_max"]):
        st.warning(f"Bu varyant veride yalnızca {int(v_bilgi['yil_min'])}–{int(v_bilgi['yil_max'])} "
                   f"model yıllarında var; {yil} için tahmin daha belirsiz.")
    if v_bilgi["ilan"] < 20:
        st.warning(f"Bu varyant için eğitim verisinde yalnızca {int(v_bilgi['ilan'])} ilan var; tahmin daha belirsiz.")
    if km >= KM_CAP:
        st.info("Veride kilometre 300.000'de kırpılmış; 300.000 üstü araçlar \"300.000+\" olarak değerlendirildi.")

    st.subheader("Bu fiyata en çok ne etki etti?")
    gruplu = katki.groupby(lambda o: OZELLIK_AD[o]).sum()
    etki   = (np.exp(gruplu) - 1) * 100
    etki   = etki.reindex(etki.abs().sort_values(ascending=False).index).head(6)
    st.caption(
        f"Modelin tüm ilanlar için başlangıç noktası {tl(np.exp(taban))}. "
        "Her satır, o özelliğin tahmini yüzde kaç yukarı (+) ya da aşağı (−) çektiğini gösterir."
    )
    etki_df = pd.DataFrame({"Özellik": etki.index, "Etki": etki.values})
    etki_df["yon"] = etki_df["Etki"].apply(lambda x: "Artırır ↑" if x >= 0 else "Düşürür ↓")
    katki_bar = (
        alt.Chart(etki_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4,
                  cornerRadiusTopLeft=4, cornerRadiusBottomLeft=4)
        .encode(
            x=alt.X("Etki:Q", title="Fiyata etkisi (%)", axis=alt.Axis(format="+.0f")),
            y=alt.Y("Özellik:N", sort="-x", title=""),
            color=alt.Color(
                "yon:N",
                scale=alt.Scale(domain=["Artırır ↑", "Düşürür ↓"],
                                range=["#22c55e", "#ef4444"]),
                legend=alt.Legend(title=""),
            ),
            tooltip=[
                alt.Tooltip("Özellik:N", title="Özellik"),
                alt.Tooltip("Etki:Q",    title="Etki (%)", format="+.1f"),
            ],
        )
        .properties(height=240)
    )
    st.altair_chart(katki_bar, use_container_width=True)

    st.divider()
    st.caption(
        "⚠ Eğitim amaçlı bir modeldir. Aralık 2025 ilan fiyatlarından öğrenilmiştir; tahmin bir **ilan "
        "fiyatıdır**, gerçekleşen satış fiyatı değildir. Hasar/boya, vites ve donanım ayrıntıları modelde "
        "yoktur. Veri kaynağı: Kaggle, *Turkey Used Cars Marketplace December 2025*."
    )


# ════════════════════════════════════════════════════════════════════════════
#  TAB 2 — Değer Kaybı Analizi
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Değer Kaybı Analizi")
    st.write("Bir marka ve model seç — aynı araç farklı model yıllarında ne kadar ediyor görürsün.")

    if veri is None:
        st.warning("İşlenmiş veri bulunamadı. `python src/temizle.py` çalıştırılmalı.")
        st.stop()

    col_m, col_n = st.columns(2)
    with col_m:
        markalar2 = sorted(veri["brand"].unique(), key=marka_ad)
        marka2    = st.selectbox("Marka", markalar2, format_func=marka_ad,
                                 index=markalar2.index("volkswagen") if "volkswagen" in markalar2 else 0,
                                 key="t2_marka")
    with col_n:
        modeller2 = sorted(veri[veri["brand"] == marka2]["model"].unique(),
                           key=lambda m: model_ad(marka2, m))
        model2    = st.selectbox("Model", modeller2, format_func=lambda m: model_ad(marka2, m),
                                 key="t2_model")

    alt_veri = veri[(veri["brand"] == marka2) & (veri["model"] == model2)].copy()
    istatistik = (
        alt_veri.groupby("year")["price"]
        .agg(medyan="median", q25=lambda x: x.quantile(0.25),
             q75=lambda x: x.quantile(0.75), ilan="count")
        .reset_index()
    )
    istatistik = istatistik[istatistik["ilan"] >= 8].sort_values("year")

    if len(istatistik) < 2:
        st.info("Bu model için yeterli yıl verisi yok (en az 2 yıl, yılda en az 8 ilan gerekli).")
    else:
        # Özet metrikler
        en_yeni_yil    = istatistik["year"].max()
        en_eski_yil    = istatistik["year"].min()
        en_yeni_fiyat  = istatistik.loc[istatistik["year"] == en_yeni_yil, "medyan"].iloc[0]
        en_eski_fiyat  = istatistik.loc[istatistik["year"] == en_eski_yil, "medyan"].iloc[0]
        toplam_kayip   = (1 - en_eski_fiyat / en_yeni_fiyat) * 100
        yillik_kayip   = toplam_kayip / max(en_yeni_yil - en_eski_yil, 1)
        toplam_ilan    = istatistik["ilan"].sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("En yeni yıl",    str(en_yeni_yil),         f"{tl(en_yeni_fiyat)}")
        c2.metric("En eski yıl",    str(en_eski_yil),         f"{tl(en_eski_fiyat)}")
        c3.metric("Toplam değer kaybı", f"%{toplam_kayip:.0f}")
        c4.metric("Yıllık ortalama kayıp",                    f"%{yillik_kayip:.1f}")

        # Grafik — bant (q25–q75) + medyan çizgisi
        bant = (
            alt.Chart(istatistik)
            .mark_area(opacity=0.18, color="#3b82f6")
            .encode(
                x=alt.X("year:O", title="Model Yılı", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("q25:Q", title="Fiyat (TL)", axis=alt.Axis(format="~s")),
                y2="q75:Q",
            )
        )
        cizgi = (
            alt.Chart(istatistik)
            .mark_line(color="#3b82f6", strokeWidth=3, point=alt.OverlayMarkDef(color="#3b82f6", size=60))
            .encode(
                x=alt.X("year:O"),
                y=alt.Y("medyan:Q"),
                tooltip=[
                    alt.Tooltip("year:O",   title="Yıl"),
                    alt.Tooltip("medyan:Q", title="Ortanca Fiyat", format=",.0f"),
                    alt.Tooltip("q25:Q",    title="Alt %25",       format=",.0f"),
                    alt.Tooltip("q75:Q",    title="Üst %75",       format=",.0f"),
                    alt.Tooltip("ilan:Q",   title="İlan Sayısı"),
                ],
            )
        )
        st.altair_chart((bant + cizgi).properties(height=320), use_container_width=True)
        st.caption(
            "Mavi bant: ilanların orta %50'si (q25–q75). Çizgi: ortanca fiyat. "
            f"Toplam {toplam_ilan:,} ilan. Tek zaman kesiti (Aralık 2025) — "
            "farklı yıllardaki araçlar karşılaştırılıyor, zaman serisi değil."
        )

        # Detay tablosu
        with st.expander("Yıl bazında detay tablosu"):
            tablo = istatistik[["year", "medyan", "q25", "q75", "ilan"]].copy()
            tablo.columns = ["Yıl", "Ortanca Fiyat", "Alt %25", "Üst %75", "İlan"]
            tablo = tablo.sort_values("Yıl", ascending=False)
            for col in ["Ortanca Fiyat", "Alt %25", "Üst %75"]:
                tablo[col] = tablo[col].apply(lambda x: f"{x:,.0f} TL")
            st.dataframe(tablo.reset_index(drop=True), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
#  TAB 3 — Fırsat Dedektörü
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Fırsat Dedektörü")
    st.write(
        "Baktığın ilanın fiyatını gir — benzer araçların piyasadaki dağılımına göre "
        "ne kadar iyi bir fırsat olduğunu söyleyelim."
    )

    if veri is None:
        st.warning("İşlenmiş veri bulunamadı. `python src/temizle.py` çalıştırılmalı.")
        st.stop()

    fa, fb = st.columns(2)
    with fa:
        markalar3 = sorted(veri["brand"].unique(), key=marka_ad)
        marka3    = st.selectbox("Marka", markalar3, format_func=marka_ad,
                                 index=markalar3.index("volkswagen") if "volkswagen" in markalar3 else 0,
                                 key="t3_marka")
        modeller3 = sorted(veri[veri["brand"] == marka3]["model"].unique(),
                           key=lambda m: model_ad(marka3, m))
        model3    = st.selectbox("Model", modeller3, format_func=lambda m: model_ad(marka3, m),
                                 key="t3_model")
    with fb:
        yil3      = st.number_input("Model yılı", min_value=1995, max_value=REFERANS_YILI,
                                     value=2018, step=1, key="t3_yil")
        km3       = st.number_input("Kilometre", min_value=0, max_value=1_000_000,
                                     value=120_000, step=5_000, key="t3_km")

    ilan_fiyati = st.number_input(
        "İlandaki fiyat (TL)", min_value=50_000, max_value=50_000_000,
        value=500_000, step=10_000, key="t3_fiyat",
        help="Baktığın ilanın satıcının istediği fiyatı"
    )

    # Benzer araç filtresi — yıl ±2, km ±50k; yetmezse genişlet
    def benzer_bul(df, brand, mdl, year, km_val, yil_tolerans=2, km_tolerans=50_000):
        return df[
            (df["brand"] == brand) &
            (df["model"] == mdl) &
            (df["year"].between(year - yil_tolerans, year + yil_tolerans)) &
            (df["km"].between(max(0, km_val - km_tolerans), km_val + km_tolerans))
        ]

    benzer = benzer_bul(veri, marka3, model3, yil3, km3)

    # Yeterli veri yoksa kriterleri genişlet
    if len(benzer) < 15:
        benzer = benzer_bul(veri, marka3, model3, yil3, km3, yil_tolerans=3, km_tolerans=80_000)
    genisletildi = len(benzer_bul(veri, marka3, model3, yil3, km3)) < 15 and len(benzer) >= 15

    if len(benzer) < 5:
        st.warning(
            f"Bu marka/model/yıl kombinasyonu için yeterli benzer ilan bulunamadı "
            f"({len(benzer)} ilan). Farklı yıl veya model dene."
        )
    else:
        percentil = (benzer["price"] < ilan_fiyati).mean() * 100  # kaçından ucuz (0=en ucuz)

        # Etiket
        if percentil <= 15:
            etiket = "Harika Fırsat 🔥"
        elif percentil <= 35:
            etiket = "İyi Fırsat ✅"
        elif percentil <= 65:
            etiket = "Piyasa Fiyatı ⚖️"
        elif percentil <= 85:
            etiket = "Biraz Pahalı ⚠️"
        else:
            etiket = "Pahalı ❌"

        renk_etiket = RENK_FIRSAT[etiket]
        ortanca     = benzer["price"].median()
        fark_pct    = (ilan_fiyati - ortanca) / ortanca * 100
        fark_tl     = ilan_fiyati - ortanca

        # Büyük etiket
        st.markdown(
            f"<div class='firsat-etiket' style='color:{renk_etiket}'>{etiket}</div>",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("İlan fiyatı",      tl(ilan_fiyati))
        c2.metric("Benzer araç ortancası", tl(ortanca),
                  delta=f"{fark_pct:+.1f}%  ({tl(abs(fark_tl))} {'fazla' if fark_tl > 0 else 'az'})",
                  delta_color="inverse")
        c3.metric("Benzer ilanlar",   f"{len(benzer):,}",
                  delta="(kriter genişletildi)" if genisletildi else None,
                  delta_color="off")

        st.caption(
            f"Benzer ilan: {marka_ad(marka3)} {model_ad(marka3, model3)}, "
            f"{yil3 - (3 if genisletildi else 2)}–{yil3 + (3 if genisletildi else 2)} model yılı, "
            f"{max(0, km3 - (80_000 if genisletildi else 50_000)):,}–"
            f"{km3 + (80_000 if genisletildi else 50_000):,} km aralığı."
        )

        # Dağılım histogramı
        st.write("**Benzer araçların fiyat dağılımı**")
        _bins           = pd.cut(benzer["price"], bins=25)
        _bins.name      = "aralik"
        hist_df         = benzer.groupby(_bins, observed=True)["price"].count().reset_index()
        hist_df.columns = ["aralik", "ilan"]
        hist_df["merkez"]   = np.array([iv.mid for iv in hist_df["aralik"]], dtype=float)
        _dist               = (hist_df["merkez"] - ilan_fiyati).abs()
        hist_df["isaretli"] = (_dist == _dist.min())

        bar = (
            alt.Chart(hist_df)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("merkez:Q", title="Fiyat (TL)", axis=alt.Axis(format="~s")),
                y=alt.Y("ilan:Q",   title="İlan Sayısı"),
                color=alt.condition(
                    alt.datum.isaretli,
                    alt.value("#ef4444"),   # kırmızı = seçilen fiyat aralığı
                    alt.value("#3b82f6"),   # mavi = diğerleri
                ),
                tooltip=[
                    alt.Tooltip("merkez:Q", title="Fiyat (~)", format=",.0f"),
                    alt.Tooltip("ilan:Q",   title="İlan"),
                ],
            )
            .properties(height=280)
        )

        # Dikey çizgi — ilan fiyatı
        cizgi_df = pd.DataFrame({"fiyat": [ilan_fiyati]})
        cizgi = (
            alt.Chart(cizgi_df)
            .mark_rule(color="#ef4444", strokeWidth=2, strokeDash=[6, 3])
            .encode(x=alt.X("fiyat:Q"))
        )
        st.altair_chart(bar + cizgi, use_container_width=True)

        if fark_tl > 0:
            _pct_metin = f"%{percentil:.0f}'inden pahalı"
        else:
            _pct_metin = f"%{100 - percentil:.0f}'inden ucuz"
        st.caption(
            f"Kırmızı çizgi: girilen ilan fiyatı ({tl(ilan_fiyati)}). "
            f"Bu ilan, benzer araçların {_pct_metin}."
        )

        with st.expander("Benzer ilanların özeti"):
            ozet = benzer["price"].describe(percentiles=[.1, .25, .5, .75, .9])
            ozet_df = pd.DataFrame({
                "İstatistik": ["En ucuz", "Alt %10", "Alt %25", "Ortanca", "Üst %75", "Üst %90", "En pahalı"],
                "Fiyat": [
                    tl(ozet["min"]),  tl(ozet["10%"]),  tl(ozet["25%"]),
                    tl(ozet["50%"]),  tl(ozet["75%"]),  tl(ozet["90%"]),  tl(ozet["max"]),
                ]
            })
            st.dataframe(ozet_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
#  TAB 4 — Piyasa Genel Bakış
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Piyasa Genel Bakış")
    if veri is None:
        st.warning("İşlenmiş veri bulunamadı.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam ilan",  f"{len(veri):,}")
        c2.metric("Marka",        f"{veri['brand'].nunique()}")
        c3.metric("Model",        f"{veri['model'].nunique()}")
        c4.metric("Şehir",        f"{veri['city'].nunique()}")

        col_l, col_r = st.columns(2)

        with col_l:
            st.write("**En çok ilan veren 15 marka**")
            marka_df = veri["brand"].value_counts().head(15).reset_index()
            marka_df.columns = ["brand", "ilan"]
            marka_df["Marka"] = marka_df["brand"].apply(marka_ad)
            marka_chart = (
                alt.Chart(marka_df)
                .mark_bar(color="#3b82f6")
                .encode(
                    x=alt.X("ilan:Q", title="İlan Sayısı"),
                    y=alt.Y("Marka:N", sort="-x", title=""),
                    tooltip=[alt.Tooltip("Marka:N"), alt.Tooltip("ilan:Q", title="İlan")],
                )
                .properties(height=380)
            )
            st.altair_chart(marka_chart, use_container_width=True)

        with col_r:
            st.write("**Yakıt tipi dağılımı**")
            yakit_df = veri["yakit_tipi"].value_counts().reset_index()
            yakit_df.columns = ["yakit", "ilan"]
            pie = (
                alt.Chart(yakit_df)
                .mark_arc(innerRadius=55)
                .encode(
                    theta="ilan:Q",
                    color=alt.Color("yakit:N", legend=alt.Legend(title="")),
                    tooltip=[
                        alt.Tooltip("yakit:N", title="Yakıt"),
                        alt.Tooltip("ilan:Q", title="İlan"),
                    ],
                )
                .properties(height=240)
            )
            st.altair_chart(pie, use_container_width=True)

            st.write("**Yıl bazında ilan sayısı**")
            yil_df = veri[veri["year"] >= 2005]["year"].value_counts().sort_index().reset_index()
            yil_df.columns = ["yil", "ilan"]
            yil_chart = (
                alt.Chart(yil_df)
                .mark_bar(color="#6366f1")
                .encode(
                    x=alt.X("yil:O", title="Model Yılı", axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y("ilan:Q", title="İlan"),
                    tooltip=[alt.Tooltip("yil:O", title="Yıl"), alt.Tooltip("ilan:Q", title="İlan")],
                )
                .properties(height=220)
            )
            st.altair_chart(yil_chart, use_container_width=True)

        st.write("**Şehir bazında ilan sayısı (Top 15)**")
        sehir_df = veri["city"].value_counts().head(15).reset_index()
        sehir_df.columns = ["sehir", "ilan"]
        sehir_chart = (
            alt.Chart(sehir_df)
            .mark_bar(color="#10b981")
            .encode(
                x=alt.X("sehir:N", sort="-y", title="", axis=alt.Axis(labelAngle=-35)),
                y=alt.Y("ilan:Q", title="İlan Sayısı"),
                tooltip=[alt.Tooltip("sehir:N", title="Şehir"), alt.Tooltip("ilan:Q", title="İlan")],
            )
            .properties(height=260)
        )
        st.altair_chart(sehir_chart, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
#  TAB 5 — En İyi Fırsatlar
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("En İyi Fırsatlar")
    st.write(
        "Aynı marka/model/yıl grubunun piyasa medyanına göre en az %15 indirimli "
        "araçlar — en az 15 benzer ilandan oluşan gruplarda."
    )

    if veri is None:
        st.warning("İşlenmiş veri bulunamadı.")
    else:
        firsat_df = hesapla_firsatlar(veri)

        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            f_markalar = ["Tümü"] + sorted(firsat_df["brand"].unique(), key=marka_ad)
            f_marka = st.selectbox(
                "Marka filtrele", f_markalar,
                format_func=lambda x: "Tümü" if x == "Tümü" else marka_ad(x),
                key="f5_marka",
            )
        with cf2:
            min_indirim = st.slider("Min. indirim %", 15, 50, 20, key="f5_indirim")
        with cf3:
            goster_sayi = st.selectbox("Göster", [20, 50, 100], key="f5_sayi")

        goster_df = firsat_df.copy()
        if f_marka != "Tümü":
            goster_df = goster_df[goster_df["brand"] == f_marka]
        goster_df = goster_df[goster_df["indirim_pct"] >= min_indirim]
        goster_df = goster_df.sort_values("indirim_pct", ascending=False)
        toplam_firsat = len(goster_df)
        goster_df = goster_df.head(goster_sayi)

        st.metric(
            "Bulunan fırsat",
            f"{toplam_firsat:,}",
            delta=f"İlk {len(goster_df)} gösteriliyor" if toplam_firsat > goster_sayi else None,
            delta_color="off",
        )

        if len(goster_df) == 0:
            st.info("Bu kriterlerde fırsat bulunamadı — filtreleri gevşet.")
        else:
            tablo = goster_df.copy()
            tablo["Marka"]      = tablo["brand"].apply(marka_ad)
            tablo["Model"]      = tablo.apply(lambda r: model_ad(r["brand"], r["model"]), axis=1)
            tablo["Yıl"]        = tablo["year"].astype(int)
            tablo["KM"]         = tablo["km"].apply(lambda x: f"{x:,.0f}")
            tablo["Şehir"]      = tablo["city"]
            tablo["Yakıt"]      = tablo["yakit_tipi"]
            tablo["Fiyat"]      = tablo["price"].apply(tl)
            tablo["Piyasa Med."]= tablo["grup_median"].apply(tl)
            tablo["İndirim"]    = tablo["indirim_pct"].apply(lambda x: f"%{x:.0f}")
            st.dataframe(
                tablo[["Marka","Model","Yıl","KM","Şehir","Yakıt","Fiyat","Piyasa Med.","İndirim"]]
                .reset_index(drop=True),
                use_container_width=True, hide_index=True,
            )
            st.caption(
                "Aralık 2025 verisi. Fiyatlar ilan fiyatıdır; gerçek satış farklı olabilir. "
                "İndirim = (piyasa medyanı − ilan fiyatı) / piyasa medyanı."
            )


# ════════════════════════════════════════════════════════════════════════════
#  TAB 6 — Marka Karşılaştırma
# ════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Marka Karşılaştırma")
    st.write("2–4 markayı aynı grafikte karşılaştır — hangi marka daha az değer kaybediyor?")

    if veri is None:
        st.warning("İşlenmiş veri bulunamadı.")
    else:
        markalar_k = sorted(veri["brand"].unique(), key=marka_ad)
        default_k  = [m for m in ["volkswagen", "toyota", "renault"] if m in markalar_k][:2]
        secili     = st.multiselect(
            "Karşılaştırılacak markalar (2–4)",
            markalar_k,
            default=default_k,
            format_func=marka_ad,
            max_selections=4,
            key="k6_markalar",
        )

        if len(secili) < 2:
            st.info("En az 2 marka seç.")
        else:
            karsi_veri  = veri[veri["brand"].isin(secili)]
            karsi_istat = (
                karsi_veri.groupby(["brand", "year"])["price"]
                .agg(medyan="median", ilan="count")
                .reset_index()
            )
            karsi_istat = karsi_istat[karsi_istat["ilan"] >= 5]
            karsi_istat["Marka"] = karsi_istat["brand"].apply(marka_ad)

            cizgi = (
                alt.Chart(karsi_istat)
                .mark_line(point=True, strokeWidth=2.5)
                .encode(
                    x=alt.X("year:O", title="Model Yılı", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("medyan:Q", title="Ortanca Fiyat (TL)", axis=alt.Axis(format="~s")),
                    color=alt.Color(
                        "Marka:N",
                        legend=alt.Legend(title="Marka"),
                        scale=alt.Scale(scheme="tableau10"),
                    ),
                    tooltip=[
                        alt.Tooltip("Marka:N",  title="Marka"),
                        alt.Tooltip("year:O",   title="Yıl"),
                        alt.Tooltip("medyan:Q", title="Ortanca Fiyat", format=",.0f"),
                        alt.Tooltip("ilan:Q",   title="İlan Sayısı"),
                    ],
                )
                .properties(height=400)
            )
            st.altair_chart(cizgi, use_container_width=True)
            st.caption(
                "Tek zaman kesiti (Aralık 2025). Farklı model yıllarındaki araçların ilan fiyatları "
                "karşılaştırılıyor — zaman serisi değil."
            )

            with st.expander("Özet tablo"):
                ozet = (
                    karsi_veri.groupby("brand")["price"]
                    .agg(ilan="count", med_fiyat="median", min_fiyat="min", max_fiyat="max")
                    .reset_index()
                )
                ozet["Marka"]          = ozet["brand"].apply(marka_ad)
                ozet["Ortanca Fiyat"]  = ozet["med_fiyat"].apply(tl)
                ozet["En Ucuz"]        = ozet["min_fiyat"].apply(tl)
                ozet["En Pahalı"]      = ozet["max_fiyat"].apply(tl)
                st.dataframe(
                    ozet[["Marka","ilan","Ortanca Fiyat","En Ucuz","En Pahalı"]]
                    .rename(columns={"ilan": "İlan"})
                    .reset_index(drop=True),
                    use_container_width=True, hide_index=True,
                )


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="araçmetrik-footer">
  <strong>AraçMetrik</strong> · Veri: Kaggle <em>Turkey Used Cars Marketplace December 2025</em><br>
  250.955 ilan · Aralık 2025 kesiti · Eğitim amaçlı proje — yatırım tavsiyesi değildir.<br>
  Fiyatlar ilan fiyatıdır; gerçekleşen satış fiyatını yansıtmayabilir.
</div>
""", unsafe_allow_html=True)
