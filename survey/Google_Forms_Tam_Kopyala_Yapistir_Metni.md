# Google Forms kurulum metni (sürüm 2.0, Ekim 2026)

> **Önerilen yol: otomatik kurulum.** [google_forms_builder.gs](google_forms_builder.gs) betiği formun tamamını Google Forms'ta oluşturur: onam, bölümler, ızgaralar, bilgi kartı ve harita. Kurulum adımları betiğin başında yazılıdır.
>
> Betik çalıştıktan sonra elle yapılacak tek iş, C, D1, D2 ve D3 ızgaralarında "Satır sırasını karıştır" ayarını açmaktır; Apps Script API'si bu ayarı desteklemiyor.
>
> Aşağıdaki elle kurulum rehberi yedek olarak korunmuştur.

Form içeriğinin tek kaynağı [Uzman_Anket_Formu_TR.md](Uzman_Anket_Formu_TR.md) dosyasıdır. Bu dosya, o içeriği Google Forms'a hangi soru tipi ve ayarla aktaracağınızı adım adım gösterir. Metinleri kaynak dosyadan kopyalayınız.

**Formu yayımlamadan önce kontrol edin:**

- [x] Bilgi kartı dolduruldu (il/ilçe, teşvik bölgesi; Karar 9903 EK-2) ve konum haritası üretildi (`assets/site_map.png`).
- [ ] KVKK aydınlatma metnindeki köşeli parantezli alanlar dolduruldu ve metin TOGÜ KVKK birimine onaylatıldı ([KVKK_Aydinlatma_ve_Onam_Metni.md](KVKK_Aydinlatma_ve_Onam_Metni.md)).
- [ ] 2–3 uzmanla pilot uygulama yapıldı; süre ve anlaşılırlık kontrol edildi.

---

## Genel ayarlar

- **Ayarlar → Yanıtlar:** E-posta toplama **kapalı**. Ad-soyad ve e-posta, A1'de isteğe bağlı toplanır.
- **Ayarlar → Sunu:** "İlerleme çubuğunu göster" **açık**.
- **Bölüm D'deki ızgaralar:** Soru menüsü (⋮) → "Satır sırasını karıştır" **açık**, "Her satırda yanıt gerektir" **açık**.

---

## Bölüm 0 — Başlık ve onam

- **Form başlığı:** Yeşil Hidrojen Üretim Tesisi Yer Seçimi — Uzman Değerlendirmesi
- **Form açıklaması:** [Anket_Davet_ve_Aciklama_Metni.md](Anket_Davet_ve_Aciklama_Metni.md), §3
- **Soru 0.1 — Onay kutuları (zorunlu):** "Bilgilendirmeyi ve KVKK aydınlatma metnini okudum, çalışmaya katılmayı kabul ediyorum."

## Bölüm A — Uzman profili

| No | Soru (kaynak: Bölüm A) | Soru tipi | Zorunlu |
|---|---|---|---|
| A1 | Ad-soyad | Kısa yanıt | Hayır |
| A2 | Kurum türü | Çoktan seçmeli | Evet |
| A3 | Uzmanlık alanı | Onay kutuları | Evet |
| A4 | Mesleki deneyim süresi | Çoktan seçmeli | Evet |
| A5 | ÇED / imar / şebeke izin deneyimi | Çoktan seçmeli (Evet/Hayır) | Evet |

## Bölüm B — Saha bilgi kartı

- **Bölüm açıklaması:** Bölüm B'nin giriş paragrafı.
- **Görsel:** Bilgi kartı tablosu ve konum haritası, tek bir görsel olarak ("Resim ekle").
- **B1 — Bölgeleri tanıma düzeyi** (zorunlu): çoktan seçmeli ızgara; satırlar `S1 — Karaman / Merkez` … `S5 — Kırklareli / Pınarhisar`, sütunlar 1–5. Soru, sahaların konumu gösterildikten sonra sorulur.

## Bölüm C — Kriterlerin önem derecesi

- **Bölüm açıklaması:** Bölüm C'nin giriş paragrafı ve ölçek tanımı: "1 = Kesinlikle önemsiz … 5 = Eşit / orta derecede önemli … 9 = Kesinlikle önemli".
- **Soru C — Çoktan seçmeli ızgara (zorunlu):**
  - **Satırlar:** K1–K7, tanımlarıyla birlikte. Ör. `K1 — Şebeke bağlantı yakınlığı: 154 kV ve üzeri en yakın trafo merkezine uzaklık`.
  - **Sütunlar:** `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`.
  - **Ayarlar:** "Satır sırasını karıştır" açık; "Her satırda yanıt gerektir" açık.

## Bölüm D — Sahaların değerlendirilmesi

- **Bölüm açıklaması:** Bölüm D'nin giriş paragrafı. "Tüm sorularda 9 en elverişli durumu gösterir" ve "Bilgim yok" açıklaması mutlaka yer almalıdır.

Aşağıdaki üç sorunun her biri ayrı bir **çoktan seçmeli ızgara** olarak kurulur. Ortak düzen:

- **Satırlar:** `S1 — Karaman / Merkez`, `S2 — Kahramanmaraş / Afşin`, `S3 — Şanlıurfa / Viranşehir`, `S4 — Kayseri / Develi`, `S5 — Kırklareli / Pınarhisar`.
- **Sütunlar:** `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `Bilgim yok`.
- **Ayarlar:** "Satır sırasını karıştır" açık; "Her satırda yanıt gerektir" açık.

| No | Soru başlığı | Soru açıklaması (kaynak) |
|---|---|---|
| D1 | Yerel toplumsal kabul | D1 soru metni + "Göz önünde bulundurulabilecek hususlar" + 1/3/5/7/9 açıklamaları |
| D2 | İzin, arazi edinimi ve mevzuat hazırlığı | D2 soru metni + 1/3/5/7/9 açıklamaları |
| D3 | Sanayi-lojistik ekosistemi ve nitelikli iş gücü | D3 soru metni + 1/3/5/7/9 açıklamaları |

## Bölüm E — Görüş ve öneriler

| No | Soru | Soru tipi | Zorunlu |
|---|---|---|---|
| E1 | Ek hususlar | Paragraf | Hayır |
| E2 | Başlıca riskler | Paragraf | Hayır |

---

## Yanıtların dışa aktarımı

1. **Yanıtlar → Sheets'e bağla → Dosya → İndir → CSV.**
2. Dosyayı `data/survey/expert_responses.csv` adıyla kaydedin. Sentetik test dosyası `expert_responses_SYNTHETIC.csv` ile karıştırılmamalıdır.
3. Analiz betiği yeni yapıya göre güncellenecektir (Faz 3: 7 kriter, 9 terimli ölçek, "Bilgim yok" = eksik veri, uzman + CRITIC birleşik ağırlık).
