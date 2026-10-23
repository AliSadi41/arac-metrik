# Veri Temizleme ve Kalite Kontrol Karar Günlüğü

> **Durum: taslak.** Sayılar `src/temizle.py` çıktısı (`reports/satir_akisi.csv`) ve veri üzerinde doğrulanmıştır.
> Gerekçe cümlelerini kendi sözlerinle gözden geçir; tezde kullanılacak metin senin olmalı.
> `⚠` işaretli maddeler senin karar vermen gereken ya da doğrulanması gereken noktalardır.

**Veri:** Kaggle, *Turkey Used Cars Marketplace December 2025* (253.344 ilan, Aralık 2025 kesiti). Ayrıntı: `veri_kaynagi.md`.
**Çıktı:** `data/processed/arac_temiz_v3.csv` — 250.955 satır, 12 sütun. Tek üretim yolu: `python src/temizle.py`.

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
- **Ön işlem:** `variant` metnindeki çift boşluklar tek boşluğa indirildi (ham veride 9.590 ilan; örn. "525d xDrive  Premium"). Bu işlem mükerrer sayısını değiştirmez (yine 288), benzersiz varyant sayısını 2.094'ten 2.061'e indirir.
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
- **Yöntem:** `variant` metninden kural tabanlı türetme (`src/temizle.py`). Sınıflar: Dizel, Benzin, LPG, Hibrit/Elektrik, Bilinmiyor.
- **Dağılım:** Dizel 109.476 (%43,6) · Benzin 69.400 (%27,7) · Bilinmiyor 65.685 (%26,2) · LPG 4.056 (%1,6) · Hibrit/Elektrik 2.338 (%0,9).
- **Eklenen motor işaretleri:** Dizel: `Mjet` (Fiat Multijet kısaltması). Benzin: `Ti-VCT` (Ford), `Twinport` (Opel), `CVVT` (Hyundai/Kia), `Komp.` (Mercedes Kompressor kısaltması), `ie` (Fiat, tam kelime). Bu işaretlerin hiçbiri önceden başka bir sınıfa düşmüyordu; 5.892 ilan Bilinmiyor'dan çıktı (Benzin 5.448, Dizel 444). 60 ilanlık doğrulamada sınıflanan 48/48 doğru.
- **BMW kuralları:** BMW varyantlarında yakıt, model kodunun son ekinde yazar. `330e`/`225xe` → Hibrit/Elektrik (plug-in hibrit); `320d`/`530xd`/`525tds` → Dizel; `520i`/`318Ci`/`520Li`/`316ti`/`318is` → Benzin. M ve Z modelleri → Benzin (veride en yeni M modeli 2021; 2024 sonrası M5 plug-in hibrittir, veri güncellenirse kural gözden geçirilmeli). 17.580 BMW ilanı Bilinmiyor'dan çıktı (Benzin 13.143, Dizel 4.410, Hibrit/Elektrik 27). Eksiz kodlar Bilinmiyor bırakıldı: "550 xDrive" (11 ilan, 550i mi M550d mi belirsiz) ve 2025 model "220 Gran Coupe" (7 ilan; yeni adlandırmada ek kullanılmıyor). 60 ilanlık doğrulamadaki 2 BMW ilanı doğru sınıflandı (sınıflanan 46/46 doğru). Kurallar asıl olarak `yakit_dogrulama_2.csv` (32 BMW ilanı) ile doğrulanacak.
- **Düzeltme (dizel deseni):** Önceki sürümde `\s D\b` deseninde fazladan bir boşluk vardı; bu yüzden "C 200 D", "1.6 D" gibi ayrı yazılmış "D" eki yakalanmıyordu. `\sD\b` olarak düzeltildi; 6.876 ilan Bilinmiyor'dan Dizel'e geçti (Mercedes 4.956, Volvo 1.229, Opel 230, Chevrolet 222, Mini 203, Mazda 33, VW 3). Satır sayıları değişmedi; aşağıdaki 60 ilanlık doğrulamada hiçbir etiket değişmedi.
- **Doğrulama (elle etiketli 60 ilan, `yakit_dogrulama.csv`):** Sınıflananlarda (n=44) tüm etiketler doğru. "Bilinmiyor" sınıfındaki 16 ilanın 14'ü gerçekte benzinli, 2'si dizel (Opel DTI, BMW 525d). n küçük olduğu için "hatasız" değil, "örneklemde hatasız" denmelidir.
- ⚠ **Bilinen zayıflıklar (modelleme öncesi çözülmeli):**
  - Bilinmiyor oranı en yüksek markalar: Toyota %61,1 · Opel %54,9 · Mercedes %45,9 (adet olarak ilk üç: Opel, Renault, Toyota; Bilinmiyor'un %41,6'sı). Kalanların çoğu yalnızca "motor hacmi + donanım" içerir ("1.6 Edition", "1.4 Comfortline"); yakıt işareti yoktur.
  - **Karar (Bilinmiyor sınıfı):** Bu ilanlar tahminle Benzin'e atanmadı; "Bilinmiyor" modelde ayrı bir kategori olarak kullanılacak. Gerekçe: yakıt işareti olmayan ilanların çoğunun benzinli olması muhtemel (doğrulamada 16'nın 14'ü) ama kanıt dolaylı; etiketin kesin bilgiyle tahmini karıştırmaması tercih edildi. Model "Bilinmiyor"un fiyat etkisini kendisi öğrenir.
- **LPG kararı (Honda Civic Eco):** `variant` metninde "LPG" hiç geçmiyor. LPG sınıfı yalnızca Honda Civic "VTEC Eco" varyantlarından oluşur (4.056 ilan; 1.6i VTEC Eco 3.665, 1.5 VTEC Eco 391; model yılları 2012–2025). Türkiye'de "Eco" adıyla satılan Civic'ler fabrika çıkışlı LPG'lidir (1.6 i-VTEC Eco ve 1.5 VTEC Turbo Eco, BRC otogaz sistemi). Kaynaklar: Motor1 Türkiye, "Honda Civic Eco neden almalı?" (https://tr.motor1.com/reviews/626586/honda-civic-eco-neden-almali/); Cumhuriyet, yenilenen Civic fiyat haberi (https://www.cumhuriyet.com.tr/otomotiv/hondanin-yenilenen-civic-modeli-satisa-sunuldu-fiyatlar-ortaya-2293853). Bu ilanlar daha önce VTEC kuralı nedeniyle Benzin sayılıyordu; Eco kuralı VTEC kuralından önce uygulanır.
  - ⚠ Kural 60 ilanlık doğrulama örnekleminde test edilmedi (örneklemde Honda yok); gerekçesi üretici bilgisidir. Tezde kaynakları kendin kontrol edip künyeyle ver.
  - **Sınırlılık:** Bu araçlar çift yakıtlıdır (benzin + LPG). Sonradan LPG taktırılmış araçlar `variant` metninden anlaşılamaz; bunlar Benzin ya da Bilinmiyor sınıfındadır. Dolayısıyla "LPG" sınıfı "fabrika çıkışlı LPG'li Honda Civic" anlamına gelir, piyasadaki tüm LPG'li araçları temsil etmez.
  - MHEV (hafif hibrit) "Hibrit/Elektrik" sınıfında; bu bir modelleme kararıdır, belgelenmeli.

## 10. Motor hacmi (`motor_hacmi`)
- **Yöntem:** `variant` metnindeki "1.6", "1.33" gibi litre ifadesi çıkarıldı (`src/temizle.py`).
- **Kapsam:** İlanların %85,0'inde bulundu. Boş kalanlar ağırlıkla motoru model koduyla yazan markalar: BMW 17.933, Mercedes 13.873, Audi 3.543, Tesla 784 (elektrikli). Değerler 0,8–3,2 litre aralığında; en sık 1,6 (73.124) ve 1,4 (42.953).
- **Karar:** Hacmi yazmayan ilanlar boş (NaN) bırakıldı; tahmin edilmedi.
- ⚠ **Modelleme notu:** Ağaç tabanlı modeller (LightGBM/XGBoost) boş değeri doğrudan kullanabilir. Lineer regresyon için doldurma (ör. marka-model medyanı) ve "hacim_bilinmiyor" bayrağı gerekir; boşluk markaya bağlı olduğu için rastgele değildir, bu tezde belirtilmeli.

