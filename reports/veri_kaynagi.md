# Veri Kaynağı Künyesi

| Alan | Değer |
|---|---|
| Veri seti adı | Turkey Used Cars Marketplace December 2025 |
| Platform | Kaggle |
| Yükleyen | Eyup Yilmaz |
| Kapsam | Türkiye geneli, Aralık 2025 dönemi (253.344 ilan) |
| Toplama yöntemi | sahibinden.com üzerinden Python Selenium kazıyıcı (scraper) ile otomatik toplama (yükleyenin açıklamasına göre) |
| Lisans | CC0: Public Domain (yükleyenin belirttiği etiket) |
| Yerel dosya | `data/raw/arac_verisi.csv` (değiştirilmez, git'e eklenmez) |

## Sütunlar (ham veri)

| Sütun | Açıklama |
|---|---|
| `brand` | Araç markası |
| `model` | Araç modeli |
| `variant` | Varyant / donanım paketi |
| `year` | Üretim yılı |
| `km` | Kilometre |
| `color` | Renk |
| `price` | TL cinsinden ilan fiyatı |
| `city` | İlanın verildiği şehir |

## Veriyle ilgili notlar ve sınırlılıklar

- **Zaman:** Tek bir zaman kesiti (Aralık 2025). Fiyatları enflasyona göre düzeltmeye gerek yoktur; model yalnızca bu dönemin piyasasını temsil eder.
- **İlan fiyatı:** `price` satıcının istediği fiyattır, gerçekleşen satış fiyatı değildir.
- **İkincil veri:** Veri bu çalışmada toplanmamıştır; üçüncü bir kişinin Kaggle'a yüklediği veridir. Toplama sürecini ve tamlığını doğrulayamıyoruz.
- **Yasal not:** CC0 etiketi yükleyene aittir; verinin kaynağı sahibinden.com olduğundan sitenin kullanım şartları ve veri tabanı hakları ayrıca geçerli olabilir. Bu nedenle ham veri bu depoda **paylaşılmaz**; akademik analiz amacıyla kullanılır. Model ticari bir ürüne bağlanacaksa bu konu yeniden değerlendirilmelidir.
- **Eksik değişkenler:** Hasar/boya kaydı, vites, yakıt tipi ve ilan tarihi sütunları yoktur. Yakıt tipi `variant` metninden türetilmiştir (bkz. `temizleme_kararlari.md`, madde 9).
- **km kırpılması:** `km` değerleri 300.000'de kırpılmış görünmektedir.
