# Talep düğümleri envanteri

`demand_inventory.csv`: Türkiye'deki endüstriyel hidrojen tüketicileri. Derleme tarihi 16.10.2026; aday sahalardan bağımsız olarak hazırlanmıştır.

## Seçim kuralı (aday sahalardan bağımsız)

| Kural | Tanım | Düğüm sayısı |
|---|---|---|
| `rule_baseline` | Bugün faaliyette olan ve sahada H₂ kullanan/üreten tesisler (rafineri + sahada NH₃ sentezi), tahmini talebi ≥ 1,000 t H₂/yıl | 7 |
| `rule_2040` | `rule_baseline` + yol haritasında H₂-DRI'ye geçişi açıklanmış entegre çelik tesisleri (Erdemir, İsdemir) | 9 |

Kurala girmeyenler:

- **İthal amonyak kullanan gübre tesisleri:** Toros, BAGFAŞ, Gübretaş, Ege Gübre.
- **Petkim:** H₂ yan ürün olarak çıkıyor, miktarı yayımlanmamış.
- **Kardemir:** H₂/DRI projesi yok.
- **Tosyalı:** Türkiye için doğrulanmış H₂ talebi yok.
- **Habaş:** < 1,000 t/yıl.
- **HySouthMarmara:** Henüz proje aşamasında.

## Değer türleri

- `size_status` / `h2_value_type`: **P** = yayımlanmış değer, **E** = tahmin.
- Hiçbir şirket H₂ tüketimini ton olarak yayımlamıyor; rafineri ve amonyak talepleri kapasite × dönüşüm katsayısıyla tahmin edilmiştir.
- `h2_onpurpose_t_yr`: Rafinerilerde özel H₂ tesislerinden (SMR) gelen pay. Yeşil H₂'nin doğrudan ikame edebileceği kısım budur. Toplam tüketimin geri kalanı reformer/kraker yan ürünüdür.

## Dönüşüm katsayıları

| Katsayı | Değer | Kaynak |
|---|---|---|
| Amonyak | 0.1776 t H₂ / t NH₃ (stokiyometrik: 3·2.016 / 2·17.031) | — |
| Rafineri, toplam H₂ | ≈ 9.6 kg H₂ / t ham petrol (aralık 9.0–10.3) | CATF 2025: AB rafineri H₂ kullanımı 4,205 kt/yıl, AB kapasitesi 11.7 Mb/g; 7.33 varil/t ve %75 kapasite kullanımı varsayımıyla (S24) |
| Rafineri, amaca yönelik pay | ≈ 5.5 kg H₂ / t ham petrol (toplamın ~%60'ı) | CATF 2025 (S24) |
| H₂-DRI | 47–57 kg H₂ / t DRI | Vogl vd. 2018, J. Clean. Prod. 203:736, doi:10.1016/j.jclepro.2018.08.279; Rechberger vd. 2020, steel research int., doi:10.1002/srin.202000110 |
| Hacim → kütle | 1 Nm³ H₂ = 0.08988 kg | — |

**Sınırlama:** AB ortalama katsayıları karmaşık rafinerileri (İzmit, STAR) olduğundan düşük, basit Batman rafinerisini olduğundan yüksek gösterir. İzmit ve STAR'ın yayımlanmış H₂ ünite kapasitesi (her biri 160,000 Nm³/sa ≈ 126 kt/yıl nominal) katsayı tahmininin üzerindedir.

## Doğrulama

- İGSAŞ 396,000 t NH₃/yıl: yildiz.com tesis sayfası ile doğrulandı.
- Tüpraş kapasiteleri 11.3 / 11.9 / 5.4 / 1.4 Mt/yıl: tupras.com.tr ve Aralık 2024 yatırımcı sunumu ile doğrulandı.
- Doğrulama Exa ile 16.10.2026'da yapıldı.
- Diğer değerler alt ajan taramasından alınmış, ayrıca doğrulanmamıştır. Makaleye girmeden önce kontrol edilmeli.

## Eski taslaktaki düğümler (D1–D8): tümü değiştirildi

| Eski düğüm | Bulgu |
|---|---|
| Erzincan demir-çelik | Böyle bir tesis yok. Türkiye'de BF-BOF tesisi yalnızca üç tane: Erdemir, İsdemir, Kardemir (S26, S27). |
| Muş OSB gıda/kimya | 7–8 küçük firma; H₂ kullanımı yok (S28). |
| Denizli tekstil OSB | Tekstilde proses H₂ talebi yok (S32). |
| Ankara TCDD | H₂ filosu ya da istasyonu yok; tek H₂ tren projesi Eskişehir'de, Ar-Ge aşamasında (S29). |
| Kayseri OSB petrokimya | Kayseri'de petrokimya tesisi yok (S30). |
| Malatya OSB kimya | Kimya OSB yalnızca öneri aşamasında (S31). |
| Kardemir (D1) | Gerçek tesis, ancak bugün H₂ kullanmıyor ve H₂/DRI projesi yok. Kurala girmiyor. |
| TÜPRAŞ Kırıkkale (D5) | Gerçek; `TR_REF_KIRIKKALE` olarak envanterde. |

## Ulusal bağlam

- **Strateji hedefleri:** ETKB Hidrojen Teknolojileri Stratejisi ve Yol Haritası (Ocak 2023): elektrolizör kapasitesi 2030'da 2 GW, 2035'te 5 GW, 2053'te 70 GW. Tonaj cinsinden talep hedefi yok (S21).
- **Ulusal gri H₂ tabanı (tahmin):** Rafineri ≈ 0.41 Mt (≈ 0.24 Mt amaca yönelik) ve amonyak ≈ 0.08–0.14 Mt; toplam yaklaşık 0.5 Mt H₂/yıl. Resmi ulusal rakam bulunamadı.
- **Üçüncü taraf projeksiyonlar:** EBRD/Advisian: düşük karbonlu H₂ talebi 2030'da ≈ 60 kt/yıl, 2040'ta ≈ 725 kt/yıl (S22). SHURA 2022: 2050'de 3.4 Mt/yıl (S23).

## Kaynaklar

- S1 https://www.tupras.com.tr/en/about-us
- S2 https://www.tupras.com.tr/en/strategic-transformation ; https://www.tupras.com.tr/assets/uploads/integrated-report/tupras-2025-integrated-annual-report.pdf
- S3 https://www.ogj.com/refining-processing/article/17250889/tupras-commissions-unit-at-izmit-refinery
- S4 https://www.socar.com.tr/activity-fields/star-refinery ; STAR Refinery 2025 Sustainability Report
- S5 https://www.nsenergybusiness.com/projects/star-aegean-refinery/
- S6 https://www.yildiz.com/en/our-activity-areas/fertilizer-industry/igsas-kocaeli-plant ; https://www.gem.wiki/IGSAS_Kocaeli_Ammonia_Facility
- S7 https://www.gemlikgubre.com.tr/yilfert-en ; http://wikimapia.org/1296994/tr/Gemlik-g%C3%BCbre
- S8 https://www.sanayi.gov.tr/assets/pdf/birimler/turkiye-gubre-sektoru-icin-dusuk-karbonlu-yol-haritasiEN.pdf
- S9 https://futurefuels.imo.org/wp-content/uploads/2024/03/WorldAmmoniaMap2024.pdf
- S10 https://www.toros.com.tr/en/fertilizers/facilities/production-plants/mersin-production-plants
- S11 https://www.bagfas.com.tr/en/Fertilizer.aspx
- S12 https://www.yatirimx.com.tr/sirket-haberleri/gubretasin-2-yenilikci-projesine-turkpatent-tescili/25352
- S13 https://www.petkim.com.tr/assets/uploads/Petkim_2025_Integrated_Annual_Report.pdf
- S14 https://www.erdemir.com.tr/en/corporate/media/press-release/giant-step-for-green-steel-by-erdemir ; https://www.isdemir.com.tr/kurumsal/tarihce
- S15 https://www.steelradar.com/en/kardemir-increased-its-production-in-2024-2025-target-is-25-million-tons-of-sales/
- S16 https://www.tosyaliholding.com.tr/en/media-central/press-releases/tosyali-holding/2023/tosyali-holding-breaks-new-ground-in-the-world-with-green-steel-production
- S17 https://www.steelorbis.com/steel-news/latest-news/turkeys-habas-to-build-hydrogen-production-facility-in-izmir-1302955.htm ; https://habas.com.tr/en/s-gas/production
- S18 https://cordis.europa.eu/project/id/101112054 ; https://h2v.eu/hydrogen-valley-platform/hydrogen-valleys-glance/south-marmara-hydrogen-shore-hysouthmarmara
- S20 https://www.hidrojenhaber.com/tekfen-turkiyenin-ilk-yesil-amonyak-tesisini-kuruyor/
- S21 https://enerji.gov.tr/Media/Dizin/SGB/tr/Kurumsal_Politikalar/HSP/ETKB_Hidrojen_Stratejik_Plan2023.pdf
- S22 https://www.ebrd.com/content/dam/ebrd_dxp/assets/pdfs/green-economy-transition/Low%20Carbon%20Hydrogen%20Economy%20in%20Turkiye.pdf
- S23 https://shura.org.tr/wp-content/uploads/2026/02/SHURA-2026-02-Rapor-Hidrojen_TR.pdf
- S24 https://cdn.catf.us/wp-content/uploads/2025/02/04180154/eu-hydrogen-landscape.pdf
- S25 https://doi.org/10.1016/j.jclepro.2018.08.279 ; https://doi.org/10.1002/srin.202000110
- S26 https://www.malatyatso.org.tr/userfiles/yayinlar/fizibiliterapor/Demir%20%C3%87elik%20Sekt%C3%B6r%20Raporu%20(2021).pdf
- S27 https://www.kalkinmakutuphanesi.gov.tr/assets/upload/dosyalar/erzincan-ili-yuksek-karbonlu-ferrokrom-tesisi-yatirimi-on-fizibilite-raporu-2020.pdf
- S28 https://www.mustso.org.tr/userfiles/MU%C5%9E%20T%C4%B0CARET%20ODASI%20EKONOM%C4%B0K%20%C4%B0STAT%C4%B0ST%C4%B0K%20RAPORU_YEN%C4%B0.pdf
- S29 https://www.uab.gov.tr/haberler/hidrojen-yakitli-tren-icin-imzalar-atildi
- S30 https://doi.org/10.17100/nevbiltek.975225
- S31 https://www.malatyagercek.com/fendoglu-malatyada-kimya-organize-sanayi-kurulmasi-sarttir/1967242
- S32 https://osbgundem.com/osb-rehberi/denizli
- Koordinatlar: OSM Nominatim (CSV'deki way/relation kimlikleri)
