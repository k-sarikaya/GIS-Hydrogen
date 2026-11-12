# YEŞİL HİDROJEN ÜRETİM TESİSİ YER SEÇİMİ — UZMAN DEĞERLENDİRME FORMU

**Çalışma:** Türkiye için yeşil hidrojen tedarik zinciri ağ tasarımı ve üretim tesisi yer seçimi
**Kurum:** Tokat Gaziosmanpaşa Üniversitesi, Endüstri Mühendisliği Bölümü
**Sürüm:** 2.0 (Ekim 2026) — önceki 10/11 kriterli form yürürlükten kaldırılmıştır.
**Tahmini süre:** 15–20 dakika

---

## Giriş

Bu form, coğrafi bilgi sistemleri (CBS) analiziyle belirlenmiş beş aday yeşil hidrojen üretim sahasının değerlendirilmesi için hazırlanmıştır. Aday sahalar Türkiye genelinde, literatüre dayalı dışlama kriterleri uygulanarak belirlenmiştir. Bu kriterler; yükseklik, koruma alanları, yerleşim yerleri, havalimanları, su yüzeyleri, arazi örtüsü, eğim, rüzgâr ve güneş kaynağı, su ve şebeke erişimidir.

Sahaların değerlendirilmesinde yedi kriter kullanılmaktadır:

- **Dört kriter araştırma ekibi tarafından açık verilerden hesaplanır:** şebeke yakınlığı, su stresi, ekolojik hassasiyet ve deprem tehlikesi.
- **Üç kriter yalnızca uzman görüşüyle değerlendirilebilir:** yerel toplumsal kabul, izin ve mevzuat hazırlığı, sanayi-lojistik ekosistemi.

Sizden iki şey istenmektedir:

1. **Bölüm C:** Yedi kriterin genel önem derecesi.
2. **Bölüm D:** Uzman görüşü gerektiren üç kriter açısından beş sahanın değerlendirilmesi.

Değerlendirmeleriniz küresel bulanık kümelerle (spherical fuzzy sets) modellenecektir. Bu yaklaşım olumlu görüş (μ), olumsuz görüş (ν) ve tereddüt (π) derecelerini birbirinden bağımsız olarak temsil eder.

**Gizlilik ve onam.** Katılım gönüllüdür. Yanıtlar yalnızca toplu ve anonim olarak, akademik amaçla kullanılır. Ad-soyad isteğe bağlıdır; e-posta toplanmaz. Aydınlatma metninin tamamı: [KVKK_Aydinlatma_ve_Onam_Metni.md](KVKK_Aydinlatma_ve_Onam_Metni.md).

- [ ] Aydınlatma metnini okudum ve gönüllü olarak katılmayı kabul ediyorum.
- [ ] Yanıtlarımın Google Forms hizmeti aracılığıyla yurt dışındaki sunucularda saklanmasına açık rıza veriyorum.

---

## Bölüm A — Uzman profili

**A1. Ad-soyad (isteğe bağlı):** ____________________

**A2. Kurum türü** (birini seçiniz)
- [ ] Akademi
- [ ] Kamu / bakanlık
- [ ] Düzenleyici kurum veya iletim sistemi işletmecisi (EPDK, TEİAŞ vb.)
- [ ] Enerji / hidrojen sanayi
- [ ] Proje geliştirici / EPC
- [ ] Kalkınma ajansı / yerel yönetim
- [ ] STK / çevre
- [ ] Finans
- [ ] Diğer: ________

**A3. Uzmanlık alanı** (birden fazla seçilebilir)
- [ ] Yeşil hidrojen
- [ ] Yenilenebilir enerji
- [ ] Enerji politikası ve mevzuat
- [ ] Çevre ve ÇED
- [ ] Lojistik ve tedarik zinciri
- [ ] Bölgesel kalkınma
- [ ] Diğer: ________

**A4. Mesleki deneyim süresi**
- [ ] 1–5 yıl
- [ ] 6–10 yıl
- [ ] 11–15 yıl
- [ ] 16 yıl ve üzeri

**A5. ÇED, imar veya şebeke bağlantısı izin süreçlerinde doğrudan deneyiminiz var mı?**
- [ ] Evet
- [ ] Hayır

---

## Bölüm B — Saha bilgi kartı

Aşağıdaki bilgiler tüm sahalar için aynı yapıda ve doğrulanmış kaynaklardan verilmiştir. Bölüm C ve D'de değerlendirdiğiniz kriterlere ilişkin performans değerleri, yani mesafeler, kaynak değerleri ve tehlike değerleri, görüşlerinizi yönlendirmemesi için bilinçli olarak verilmemiştir.

| Alan | S1 | S2 | S3 | S4 | S5 | Kaynak |
|---|---|---|---|---|---|---|
| İl / ilçe | Karaman / Merkez | Kahramanmaraş / Afşin | Şanlıurfa / Viranşehir | Kayseri / Develi | Kırklareli / Pınarhisar | geoBoundaries; OSM Nominatim |
| Konum haritası | `assets/site_map.png` (beş saha, aynı ölçek) | | | | | Yazarların CBS analizi |
| Uygun alandaki baskın arazi örtüsü | Çayır-çalı / çıplak arazi | Çayır-çalı / çıplak arazi | Çayır-çalı / çıplak arazi | Çayır-çalı / çıplak arazi | Çayır-çalı / çıplak arazi | ESA WorldCover 2021 |
| Bölgesel teşvik bölgesi (1 = en gelişmiş … 6 = en yüksek destek) | 3 | 5 | 6 | 2 | 3 | Karar 9903, EK-2 (RG 30.05.2025) |

*Araştırmacı notu:*
- Saha koordinatları ve seçim gerekçesi `data/raw/gis/real/candidate_sites.csv` dosyasındadır.
- Teşvik bölgeleri, Karar 9903 EK-2 tablosunu aktaran iki bağımsız kaynaktan doğrulanmıştır (TÜRMOB ve RSM karar özetleri, 2025). 6 Şubat 2023 depremleri geçici maddesi ilçe listesine bağlı olduğundan karta konmamıştır.
- Saha sırası her katılımcı için karıştırılmalıdır.

**B1. Yukarıdaki aday sahaların bulunduğu bölgeleri (il/ilçe ölçeğinde) ne kadar tanıyorsunuz?**
1 = Hiç tanımıyorum … 5 = Çok iyi tanıyorum (bölgede çalıştım veya proje yürüttüm)

| Saha | 1 | 2 | 3 | 4 | 5 |
|---|:-:|:-:|:-:|:-:|:-:|
| S1 — Karaman / Merkez | ○ | ○ | ○ | ○ | ○ |
| S2 — Kahramanmaraş / Afşin | ○ | ○ | ○ | ○ | ○ |
| S3 — Şanlıurfa / Viranşehir | ○ | ○ | ○ | ○ | ○ |
| S4 — Kayseri / Develi | ○ | ○ | ○ | ○ | ○ |
| S5 — Kırklareli / Pınarhisar | ○ | ○ | ○ | ○ | ○ |

---

## Bölüm C — Kriterlerin önem derecesi

Türkiye'de yeşil hidrojen üretim tesisi için aday sahalar sıralanırken aşağıdaki her kriterin ne kadar önemli olması gerektiğini değerlendiriniz. Bu bölümde bir sahayı değil, yalnızca kriterin genel önemini puanlayınız. Bazı kriterler araştırma ekibi tarafından veriyle hesaplanmaktadır; bu kriterlerin önemine ilişkin görüşünüz de gereklidir.

**Ölçek:** 1 = Kesinlikle önemsiz … 5 = Eşit / orta derecede önemli … 9 = Kesinlikle önemli

| Kod | Kriter ve tanım | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| K1 | **Şebeke bağlantı yakınlığı:** Sahanın 154 kV ve üzeri en yakın trafo merkezine uzaklığı | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| K2 | **Su stresi:** Sahayı besleyen havzada su talebinin yenilenebilir su arzına oranı (yüksek stres olumsuzdur) | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| K3 | **Ekolojik hassasiyet:** Sahanın korunan alanlara ve önemli doğa alanlarına yakınlığı (yasal tamponun ötesindeki ek hassasiyet) | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| K4 | **Deprem tehlikesi:** Sahadaki deprem yer hareketi tehlikesi ve aktif faylara yakınlık | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| K5 | **Yerel toplumsal kabul:** Tesisin yerel halk ve yerel yönetimlerce çatışma yaşanmadan kabul görme olasılığı | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| K6 | **İzin, arazi edinimi ve mevzuat hazırlığı:** ÇED, imar, arazi mülkiyeti, şebeke ve su izinleri ile idari kapasite açısından sürecin elverişliliği | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| K7 | **Sanayi-lojistik ekosistemi ve nitelikli iş gücü:** Nitelikli teknik iş gücü, mühendislik ve bakım hizmetleri, OSB'ler ve çok modlu lojistik olanakları | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |

---

## Bölüm D — Sahaların değerlendirilmesi

Aşağıdaki üç kriterin her biri için beş aday sahayı 1–9 ölçeğinde değerlendiriniz. Puanlar 1, 3, 5, 7 ve 9 için açıklanmıştır; 2, 4, 6 ve 8 ara değerlerdir. **Tüm sorularda 9 en elverişli durumu gösterir.** Bir saha hakkında yeterli bilginiz yoksa tahmin yürütmek yerine **"Bilgim yok"** seçeneğini işaretleyiniz; bu yanıt eksik veri olarak işlenir.

### D1. Yerel toplumsal kabul (K5)

Aday sahada büyük ölçekli bir yeşil hidrojen üretim tesisinin (elektrolizör, ilişkili rüzgâr ve güneş santrali, şebeke bağlantısı) yerel halk ve yerel yönetimler tarafından örgütlü muhalefet, dava süreci veya uzun süreli bir çatışma yaşanmadan kabul görme olasılığını nasıl değerlendirirsiniz?

*Göz önünde bulundurulabilecek hususlar (sıralama önem göstermez):*
- bölgede önceki enerji ve sanayi yatırımlarına ilişkin deneyimler;
- yerel ekonominin tarım, hayvancılık veya turizme bağımlılığı;
- hidrojen güvenliğine ilişkin algılar;
- yatırımcıya ve kamu kurumlarına güven;
- arazi ve su kullanımında rekabet.

| Puan | Açıklama |
|:-:|---|
| 1 | Çok güçlü muhalefet beklenir; örgütlü itiraz, dava veya protesto çok olası, proje büyük olasılıkla engellenir ya da ciddi biçimde gecikir. |
| 3 | Belirgin itirazlar olası; kabul ancak kapsamlı tavizlerle ve belirsiz koşullarda mümkün. |
| 5 | Karışık veya nötr; belirgin bir destek ya da muhalefet beklentisi yok. |
| 7 | Genel olarak kabul ve geniş yerel destek beklenir; kaygılar olağan katılım süreçleriyle giderilebilir. |
| 9 | Çok güçlü destek; yerel aktörler projeyi etkin biçimde destekler, çatışma olasılığı çok düşük. |

| Saha | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | Bilgim yok |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| S1 — Karaman / Merkez | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S2 — Kahramanmaraş / Afşin | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S3 — Şanlıurfa / Viranşehir | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S4 — Kayseri / Develi | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S5 — Kırklareli / Pınarhisar | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |

### D2. İzin, arazi edinimi ve mevzuat hazırlığı (K6)

Aday sahada büyük ölçekli bir yeşil hidrojen tesisi için gerekli izinlerin ve arazi haklarının makul bir sürede elde edilebilmesine ilişkin koşulları nasıl değerlendirirsiniz? Değerlendirmede şu hususlar dikkate alınabilir:

- ÇED süreci;
- imar ve plan durumu;
- arazi mülkiyeti (Hazine, mera veya özel mülk);
- şebeke bağlantı onayı ve su kullanım izni;
- il ve bölge düzeyindeki idari kapasite.

| Puan | Açıklama |
|:-:|---|
| 1 | Çok elverişsiz; ciddi hukuki veya mülkiyet engelleri var, izin süreci son derece uzun ya da belirsiz. |
| 3 | Elverişsiz; önemli engeller ve belirgin gecikme riski var. |
| 5 | Ortalama; olağan izin süreci ve olağan riskler. |
| 7 | Elverişli; engeller sınırlı, arazi erişimi ve izin yolları büyük ölçüde açık ve öngörülebilir. |
| 9 | Çok elverişli; arazi hazır, izin yolları yerleşik, belirgin gecikme beklenmez. |

| Saha | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | Bilgim yok |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| S1 — Karaman / Merkez | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S2 — Kahramanmaraş / Afşin | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S3 — Şanlıurfa / Viranşehir | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S4 — Kayseri / Develi | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S5 — Kırklareli / Pınarhisar | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |

### D3. Sanayi-lojistik ekosistemi ve nitelikli iş gücü (K7)

Aday sahanın çevresi, bir yeşil hidrojen tesisinin kurulması ve işletilmesi için gereken destekleyici ekosistemi ne ölçüde sunmaktadır? Değerlendirmede şu hususlar dikkate alınabilir:

- nitelikli teknik iş gücü;
- mühendislik/EPC ve bakım-onarım hizmet sağlayıcıları;
- organize sanayi bölgeleri;
- çok modlu lojistik (karayolu, demiryolu, liman veya boru hattı erişimi).

| Puan | Açıklama |
|:-:|---|
| 1 | Çok zayıf; nitelikli iş gücü ve hizmet sağlayıcıları büyük ölçüde bölge dışından getirilmeli, lojistik bağlantılar çok sınırlı. |
| 3 | Zayıf; temel hizmetler mevcut, uzmanlık büyük ölçüde dışarıdan sağlanır. |
| 5 | Orta; kurulum için yeterli, işletmede kısmi dış destek gerekir. |
| 7 | Güçlü; deneyimli iş gücü, OSB ve iyi lojistik bağlantılar mevcut. |
| 9 | Çok güçlü; nitelikli iş gücü, EPC ve bakım hizmetleri, OSB ve çok modlu lojistik bölgede hazır. |

| Saha | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | Bilgim yok |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| S1 — Karaman / Merkez | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S2 — Kahramanmaraş / Afşin | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S3 — Şanlıurfa / Viranşehir | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S4 — Kayseri / Develi | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| S5 — Kırklareli / Pınarhisar | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |

---

## Bölüm E — Görüş ve öneriler (isteğe bağlı)

E1. Değerlendirmede kullanılan yedi kriter dışında, aday sahaların sıralanmasında dikkate alınması gerektiğini düşündüğünüz bir husus var mı?
______________________________________________________________________

E2. Türkiye'de yeşil hidrojen tedarik zinciri kurulumunda öngördüğünüz başlıca riskler nelerdir?
______________________________________________________________________

**Katkılarınız için teşekkür ederiz.**

---

### Araştırmacı notu (forma konmaz): dilsel ölçeğin küresel bulanık karşılıkları

Ölçek, Kutlu Gündoğdu ve Kahraman (2019, *Informatica* 30(2), Tablo 2) çalışmasından birebir alınmıştır. Skor fonksiyonu aynı çalışmadan alınmıştır: Skor = (μ − π)² − (ν − π)². Bu ölçekte skor 1'den 9'a kesin olarak artar.

| Puan | Terim | (μ, ν, π) | Skor |
|:-:|---|:-:|:-:|
| 1 | Kesinlikle düşük (ALI) | (0.1, 0.9, 0.1) | −0.64 |
| 2 | Çok düşük (VLI) | (0.2, 0.8, 0.2) | −0.36 |
| 3 | Düşük (LI) | (0.3, 0.7, 0.3) | −0.16 |
| 4 | Biraz düşük (SLI) | (0.4, 0.6, 0.4) | −0.04 |
| 5 | Eşit / orta (EI) | (0.5, 0.5, 0.5) | 0.00 |
| 6 | Biraz yüksek (SMI) | (0.6, 0.4, 0.4) | 0.04 |
| 7 | Yüksek (HI) | (0.7, 0.3, 0.3) | 0.16 |
| 8 | Çok yüksek (VHI) | (0.8, 0.2, 0.2) | 0.36 |
| 9 | Kesinlikle yüksek (AMI) | (0.9, 0.1, 0.1) | 0.64 |
| — | Bilgim yok | eksik veri | — |
