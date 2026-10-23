# Veri Temizleme ve Kalite Kontrol Karar Günlüğü

> **Durum: taslak.** Sayılar `src/temizle.py` çıktısı (`reports/satir_akisi.csv`) ve veri üzerinde doğrulanmıştır.
> Gerekçe cümlelerini kendi sözlerinle gözden geçir; tezde kullanılacak metin senin olmalı.
> `⚠` işaretli maddeler senin karar vermen gereken ya da doğrulanması gereken noktalardır.

**Veri:** Kaggle, *Turkey Used Cars Marketplace December 2025* (253.344 ilan, Aralık 2025 kesiti). Ayrıntı: `veri_kaynagi.md`.
**Çıktı:** `data/processed/arac_temiz_v3.csv` — 250.955 satır, 11 sütun. Tek üretim yolu: `python src/temizle.py`.

## Satır akış tablosu

| # | Adım | Kalan satır | Silinen |
|---|---|---:|---:|
| 0 | Ham veri | 253.344 | — |
| 1 | Mükerrer satırlar | 253.056 | 288 |
| 2 | Geçersiz şehir kayıtları (Diğer, Kardzhali) | 253.053 | 3 |
| 3 | Fiyat tabanı kontrolü (< 50.000 TL) | 253.053 | 0 |
| 4 | Şüpheli km=0 ilanlar (model yılı < 2023) | 253.046 | 7 |
| 5 | km tavan kontrolü (> 300.000) | 253.046 | 0 |
| 6 | 1995 öncesi araçlar | 251.453 | 1.593 |
| 7 | Fiyatı 10.000.000 TL ve üstü ilanlar | 250.955 | 498 |

Adımların **sırası** sonucu etkiler (örneğin bazı km=0 ilanlar hem mükerrer hem tavan fiyatlıdır); tabloyu bu sırayla raporla.

---

## 1. Mükerrer satırlar (288)
- **Bulgu:** Tüm sütunları (marka, model, varyant, yıl, km, renk, fiyat, şehir) aynı olan 288 satır.
- **Karar:** `drop_duplicates()` ile tekilleştirildi.
- **Gerekçe:** İlan numarası olmadığı için bunların gerçekten aynı ilan olduğu kesin değildir; ancak km ve fiyatın da birebir aynı olması mükerrer kayıt ya da toplama hatası olasılığını güçlü kılar.
- **Sınırlılık:** Aynı özelliklere sahip farklı ilanların tesadüfen silinmiş olması mümkündür (ihmal edilebilir düzeyde varsayılmıştır).

## 2. Geçersiz şehir kayıtları (3)
- **Bulgu:** `city` sütununda Türkiye'de il olmayan iki değer: "Diğer" ve "Kardzhali".
- **Karar:** Bu kayıtlar çıkarıldı. Sonuçta 81 il kaldı.

## 3. Fiyat tabanı
- **Bulgu:** Ham veride minimum fiyat 100.000 TL; 50.000 TL altı ilan yok (filtre 0 satır siler, savunma amaçlı kontrol olarak tutuldu). 150.000 TL altındaki 232 ilan incelendi: yıl ortalaması 1998, en yeni model 2006 (Fiat Albea/Palio gibi), km'ler 200.000 üzeri.
- **Karar:** Düşük fiyatlı ilanlar **tutuldu**.
- **Gerekçe:** Düşük fiyatlar eski ve yüksek km'li araçlarla tutarlı; yer tutucu ya da hata belirtisi yok.

## 4. km = 0 ilanlar
- **Bulgu:** Ham veride 101, mükerrerler çıkarıldıktan sonra 72 ilan km=0; hepsi 2022–2025 model. Bu ilanların büyük bölümünün fiyatı tam 10.000.000 TL (aşağıda madde 7).
- **Karar:** Model yılı 2023'ten eski km=0 ilanlar (7 adet) çıkarıldı. Fiyatı 10M olan km=0 ilanlar madde 7 ile çıkarıldı (59 adet). **Geriye 6 ilan kaldı** (2023: 3, 2025: 3).
- ⚠ **Karar gerekiyor:** Tez "ikinci el" kapsamında olduğundan kalan 6 sıfır km ilan da çıkarılabilir (`df["km"] > 0`). Etkisi ihmal edilebilir; hangisini seçersen gerekçesini yaz ve `temizle.py` ile bu belgeyi aynı tut.

## 5. km tavanı (300.000)
- **Bulgu:** Ham veride 1.784 ilan tam 300.000 km (temiz veride 1.685). Gerçek bir dağılımda bu yığılma beklenmez; değerin kırpıldığı (censoring) düşünülmektedir. Kırpılmanın nedeni platform kaynaklıdır varsayımı doğrulanmamıştır.
- **Karar:** Satırlar **silinmedi**; `km_kirpildi` (0/1) bayrağı eklendi.
- **Gerekçe:** Bu araçların gerçek km'si "300.000 ya da daha fazla" bilgisinden ibarettir; bayrak, modelin bu yığılmayı gerçek bir değer sanmasını engeller.

## 6. 1995 öncesi araçlar (1.593)
- **Bulgu:** Veride en eski model 1972; 1995 öncesi ilanlar toplamın yaklaşık %0,6'sı.
- **Karar:** `year >= 1995` kapsamı.
- **Gerekçe:** Çok az sayıda ve ayrı bir pazar segmenti (klasik/koleksiyon araçlar) oluşturuyorlar; normal yaş–fiyat ilişkisini temsil etmeyebilirler.
- ⚠ 1995 eşiği keyfidir. Model aşamasında eşiği değiştirerek (örn. 2000) sonuçların duyarlılığına bak ve tezde belirt.

## 7. Fiyatı 10.000.000 TL ve üstü ilanlar (498)
- **Bulgu:** Ham veride maksimum fiyat tam 10.000.000 TL ve bu değerde yığılma var (ham veride 546 ilan). Aynı marka-model-yıldaki diğer ilanlarla kıyaslayabildiğimiz 88 ilanda (≥5 karşılaştırma ilanı olanlar) 10M fiyatın o grubun medyanına oranı medyanda 1,59, en yüksekte 14,29 (VW Golf 1.6 Trendline, 2009, 240.000 km, medyan 700.000 TL). Geri kalan ilanlar için karşılaştırma yapılamadı.
- **Karar:** Fiyatı 10.000.000 TL ve üstü olan tüm ilanlar çıkarıldı.
- **Gerekçe:** En az bir kısmı açıkça gerçek dışı (yer tutucu) fiyat; kalanının gerçek fiyatı doğrulanamıyor ve hiçbirinin gerçek fiyatı bilinmiyor (olsa bile yalnızca "≥ 10 milyon" bilgisi var).
- **Sınırlılık:** Model, fiyatı 10 milyon TL altındaki araçlar için geçerlidir; ultra lüks segment kapsam dışıdır. ⚠ Duyarlılık analizi (bu ilanlar bayrakla tutulduğunda sonuçlar) tezde ek bölüm olabilir.

## 8. Hedef değişkenin logaritması
- **Bulgu:** Fiyat sağa çarpık (çarpıklık 3,28); logaritması simetrik (0,24).
- **Karar:** `log_price` türetildi; orijinal `price` sütunu da korundu.
- **Gerekçe:** Log fiyat, hatayı yüzde cinsinden ölçmeyi sağlar ve uç değerlerin etkisini azaltır. Ağaç tabanlı modeller için zorunlu değildir; sonuçlar TL'ye geri çevrilerek de raporlanacaktır.

## 9. Yakıt tipi (`yakit_tipi`)
- **Yöntem:** `variant` metninden kural tabanlı türetme (`src/temizle.py`). Sınıflar: Dizel, Benzin, Hibrit/Elektrik, Bilinmiyor.
- **Dağılım:** Dizel 97.746 (%39,0) · Bilinmiyor 96.033 (%38,3) · Benzin 54.865 (%21,9) · Hibrit/Elektrik 2.311 (%0,9).
- **Doğrulama (elle etiketli 60 ilan, `yakit_dogrulama.csv`):** Sınıflananlarda (n=44) tüm etiketler doğru. "Bilinmiyor" sınıfındaki 16 ilanın 14'ü gerçekte benzinli, 2'si dizel (Opel DTI, BMW 525d). n küçük olduğu için "hatasız" değil, "örneklemde hatasız" denmelidir.
- ⚠ **Bilinen zayıflıklar (modelleme öncesi çözülmeli):**
  - Bilinmiyor oranı en çok premium markalarda: BMW %98,1 · Mercedes %88,2 · Opel %66,9 · Toyota %61,1 (ilk üç marka Bilinmiyor'un %45'i). BMW'de `520i`/`320d` gibi kodlar için kural yok.
  - **LPG sınıfı boş.** `variant` metninde "LPG" geçmiyor. Önceki sürümde LPG diye sayılan 4.056 ilan aslında Honda Civic "VTEC Eco" varyantlarıydı; şimdi Benzin sayılıyor. Honda Civic Eco'nun yakıtının ne olduğu doğrulanmalı ve tezde tek bir yöntem seçilmeli.
  - MHEV (hafif hibrit) "Hibrit/Elektrik" sınıfında; bu bir modelleme kararıdır, belgelenmeli.
