# Draft Survey Items: Stage II Soft Criteria (TR / EN)

**Status:** DRAFT. Not yet deployed. Based on `docs/reviews/soft_criteria_literature_review.md` (criterion codes T1–S2 refer to §5 of that review).

**Design rules applied**

1. **Only criteria without objective data go to experts.** These are S1, S2, E2 and T3. The six data-derived criteria (T1, T2, E1, N1, N2, R1) are computed by the authors and are **not** rated by experts.
2. **Experts give importance weights for all 10 criteria.** This is needed for combined subjective + CRITIC weighting.
3. **No performance numbers are shown.** No distances, capacity factors, costs, hazard values or rankings appear in the items. The only site information is a neutral **site fact card** (Part B). It carries verified, purely descriptive fields that are identical in structure for all five sites.
4. **The direction is uniform.** For every item, 7 = most favourable. All expert-judged criteria are benefit-type, so no reverse coding is needed.
5. **A "no basis to judge" option is offered on every site-rating row.** It is treated as missing data, not as "4 – Medium", so that uninformed answers do not dilute informed ones.
6. **Site order is shuffled** for each respondent (Google Forms grid option "Satır sırasını karıştır / Shuffle row order"). This reduces order effects.

**Response burden:** 4 criteria × 5 sites = 20 site ratings, plus 10 importance ratings. The current form has 55 site ratings.

---

## 1. Keep / remove / add (mapping from the current form)

| Current item | Decision | New code | Note |
|---|---|---|---|
| C1a Wind CF | **Remove** from the survey | (T1 descriptor) | Measured from GWA. Delete the "Muş %25.4 …" text, which anchors experts |
| C1b GHI | **Remove** | (T1 descriptor) | Measured from PVGIS. Delete the GHI values in the text |
| C2 Water access | **Remove** | N1 (data) | Replaced by water *stress* (Aqueduct 4.0) |
| C3 Distance to protected areas | **Remove** | N2 (data) | Current text ("all ≥5 km") reflects the old Stage I |
| C4 Grid connectivity | **Remove** | T2 (data) | Distance to ≥154 kV substation |
| C5 LCOH | **Remove** | T1 (data, cost) | Computed. This removes the "low cost = high score" direction conflict |
| C6 Demand proximity | **Remove** | E1 (data) | Current distances (12/18/11/14 km) are unverified. Delete them |
| C7 Social acceptance | **Keep, rewrite** | S1 | Anchored 1–7 item below |
| C8 CO₂ abatement | **Remove** | (Stage III output) | Not a site attribute |
| C9 Underground storage | **Keep, rewrite** | T3 | With a "no basis to judge" option |
| C10 Incentive zone | **Remove** | (fact card + S2) | Decree 2012/3305 repealed by Decree 9903 (RG 30.05.2025) |
| — | **Add** | S2 Permitting and land readiness | New site-rating item |
| — | **Add** | E2 Industrial-logistics ecosystem and workforce | New site-rating item |
| — | **Add** | Importance block (10 criteria) | For subjective weights |
| — | **Add** | Expert profile: regional familiarity per site, sector | For expert weighting and filtering |

Also correct the intro text. The Google Forms version says "11 stratejik kriter" while the TR/EN forms say "10".

---

## 2. Linguistic scale (shared by Parts C and D)

The same seven terms are used for importance (Part C) and for site performance (Part D). The SFN triplets below are the ones in the current forms.

**Before deployment:**
- replace them with a published spherical-fuzzy scale cited verbatim (e.g., Kutlu Gündoğdu & Kahraman), or justify the current asymmetry: L has π = 0.3 but H has π = 0.2;
- confirm that the score function is monotone along 1 → 7.

| Puan / Score | Terim (TR) | Term (EN) | Kod | (μ, ν, π) currently used |
|---|---|---|---|---|
| 1 | Kesinlikle düşük | Absolutely low | AL | (0.1, 0.9, 0.1) |
| 2 | Çok düşük | Very low | VL | (0.2, 0.8, 0.2) |
| 3 | Düşük | Low | L | (0.4, 0.6, 0.3) |
| 4 | Orta | Medium | M | (0.5, 0.5, 0.4) |
| 5 | Yüksek | High | H | (0.7, 0.3, 0.2) |
| 6 | Çok yüksek | Very high | VH | (0.8, 0.2, 0.1) |
| 7 | Kesinlikle yüksek | Absolutely high | AH | (0.9, 0.1, 0.1) |
| — | Bu konuda değerlendirme yapacak bilgim yok | No basis to judge | NB | Treated as missing |

---

## 3. Part A: Expert profile (additions to the existing section)

**A1. Kurum türü / Organisation type** (choose one)
- Akademi / Academia
- Kamu–bakanlık / Public administration–ministry
- Düzenleyici veya iletim sistemi işletmecisi (EPDK, TEİAŞ vb.) / Regulator or TSO
- Enerji–hidrojen sanayi / Energy–hydrogen industry
- Proje geliştirici–EPC / Developer–EPC
- Kalkınma ajansı–yerel yönetim / Development agency–local government
- STK–çevre / NGO–environment
- Finans / Finance
- Diğer / Other

**A2. Aday bölgelere aşinalık / Familiarity with each candidate region** (one row per site; scale 1–5)

- **TR:** "Aşağıdaki her bir aday sahanın bulunduğu bölgeyi (il/ilçe ölçeğinde) ne kadar tanıyorsunuz?"
- **EN:** "How familiar are you with the region (province/district level) of each candidate site?"
- **Scale:** 1 = Hiç tanımıyorum / Not at all … 5 = Çok iyi tanıyorum (bölgede çalıştım veya proje yürüttüm) / Very well (worked in or ran projects in the region).
- *Use:* weighting or filtering of the site ratings in Part D.

**A3. ÇED, imar veya şebeke bağlantısı izin süreçlerinde doğrudan deneyiminiz var mı? / Do you have direct experience with EIA, zoning or grid-connection permitting?**
- Evet / Yes
- Hayır / No

**A4. Onam / Consent**
- **TR:** "Yanıtlarım yalnızca toplu ve anonim olarak akademik amaçla kullanılacaktır; kişisel verilerim 6698 sayılı KVKK kapsamında korunacaktır."
- **EN:** "My responses will be used only in aggregated, anonymised form for academic purposes; personal data are protected under Law No. 6698 (KVKK)."
- *The data controller, retention period and contact details must be added. Name and e-mail should be optional unless justified.*

---

## 4. Part B: Neutral site fact card

The same fields are given for all five sites. Every value must come from a verified source, cited on the card. **Do not include** values of the data-derived criteria: LCOH, CF/GHI, distances to grid, demand, water or protected areas, water-stress score, or PGA. Experts would otherwise fold measured data into their qualitative judgements, which double counts them.

| Field (TR / EN) | S1 | S2 | S3 | S4 | S5 | Source |
|---|---|---|---|---|---|---|
| İl / ilçe — Province / district | | | | | | Administrative boundaries |
| Konum haritası — Location map (same scale and style for all) | | | | | | Authors' GIS |
| Uygun alanın baskın arazi örtüsü — Dominant land cover of the eligible area | | | | | | CORINE / ESA WorldCover |
| Bölgesel teşvik bölgesi (Karar 9903, EK-2) — Incentive region (Decree 9903, Annex 2) | | | | | | Resmî Gazete 30.05.2025, **verified** |
| 6 Şubat 2023 deprem afet bölgesi ilçesi mi? (Karar 9903, Geçici Md. 3) — District in the 6 Feb 2023 disaster area? | | | | | | Decree 9903 Temp. Art. 3 / 2018/11201 Annex 2, **verified** |
| İlde organize sanayi bölgesi var mı? — Organised industrial zone in the province? (yes/no) | | | | | | OSBÜK / Ministry. *Optional; omit if judged to anchor E2* |

---

## 5. Part C: Criterion importance (all 10 criteria)

**Instruction (TR):** "Türkiye'de yeşil hidrojen üretim tesisi için aday sahaların sıralanmasında aşağıdaki her bir kriterin ne kadar önemli olması gerektiğini değerlendiriniz. Bu bölümde herhangi bir sahayı değil, yalnızca kriterin genel önemini puanlayınız. Bazı kriterler araştırmacılar tarafından veriyle hesaplanmaktadır; yine de önem derecesine ilişkin görüşünüz gereklidir."

**Instruction (EN):** "Please rate how important each criterion should be when ranking candidate sites for green-hydrogen production in Türkiye. Rate only the general importance of the criterion, not any particular site. Some criteria are computed by the research team from data; your view on their importance is still needed."

**Anchors:**

| Score | TR | EN |
|---|---|---|
| 1 | Kesinlikle önemsiz: sıralamada dikkate alınmasa da olur | Absolutely unimportant: could be ignored in the ranking |
| 4 | Orta derecede önemli | Moderately important |
| 7 | Kesinlikle önemli: sıralamada belirleyici olmalı | Absolutely important: should be decisive in the ranking |

Scores 2, 3, 5 and 6 are intermediate.

**Criterion definitions** (shown to experts; no site data). The (Veri / Data) and (Uzman / Expert) tags are author-side notes and need not be shown in the form.

| Kod | Kriter ve tanım (TR) | Criterion and definition (EN) |
|---|---|---|
| T1 | **Hidrojen üretim maliyeti (LCOH):** Sahadaki rüzgâr ve güneş kaynağına göre boyutlandırılmış bir sistemde, tüm sahalar için aynı varsayımlarla hesaplanan seviyelendirilmiş hidrojen maliyeti. (Veri) | **Levelised cost of hydrogen (LCOH):** cost of hydrogen from a wind/PV-electrolyser system sized to the site's resource, computed with identical assumptions for all sites. (Data) |
| T2 | **Şebeke bağlantı yakınlığı:** Sahanın 154 kV ve üzeri en yakın trafo merkezine uzaklığı. (Veri) | **Grid-connection proximity:** distance from the site to the nearest ≥154 kV substation. (Data) |
| T3 | **Yeraltı hidrojen depolamasına erişim:** Bölgede tuz mağarası veya tükenmiş gaz sahası gibi büyük ölçekli depolama olanaklarına gelecekte erişilebilirlik. (Uzman) | **Access to underground hydrogen storage:** future accessibility of large-scale geological storage (salt caverns, depleted gas fields) in the region. (Expert) |
| E1 | **Talep merkezlerine erişim:** Hidrojen tüketen sanayi tesislerine (rafineri, amonyak, çelik), talep miktarıyla ağırlıklandırılmış ortalama karayolu uzaklığı. (Veri) | **Demand accessibility:** demand-weighted mean road distance to hydrogen-consuming plants (refineries, ammonia, steel). (Data) |
| E2 | **Sanayi-lojistik ekosistemi ve nitelikli iş gücü:** Nitelikli teknik iş gücü, mühendislik/bakım hizmetleri, OSB'ler ve çok modlu lojistik olanakları. (Uzman) | **Industrial-logistics ecosystem and skilled workforce:** skilled technical labour, engineering/O&M services, industrial zones and multimodal logistics. (Expert) |
| N1 | **Su stresi:** Sahayı besleyen havzada su talebinin yenilenebilir su arzına oranı; yüksek stres olumsuzdur. (Veri) | **Water stress:** ratio of water demand to renewable supply in the supplying basin; higher stress is unfavourable. (Data) |
| N2 | **Ekolojik hassasiyet:** Sahanın korunan alanlara ve önemli doğa alanlarına yakınlığı (yasal tampon dışındaki ek hassasiyet). (Veri) | **Ecological sensitivity:** proximity of the site to protected areas and Key Biodiversity Areas beyond the legal buffer. (Data) |
| R1 | **Deprem tehlikesi:** Sahadaki deprem yer hareketi tehlikesi ve aktif faylara yakınlık. (Veri) | **Seismic hazard:** earthquake ground-motion hazard at the site and proximity to active faults. (Data) |
| S1 | **Yerel toplumsal kabul:** Tesisin yerel halk ve yerel yönetimlerce çatışmasız kabul görme olasılığı. (Uzman) | **Local social acceptance:** likelihood that the facility is accepted by the local community and local authorities without conflict. (Expert) |
| S2 | **İzin, arazi edinimi ve mevzuat hazırlığı:** ÇED, imar, arazi mülkiyeti, şebeke ve su izinleri ile idari kapasite açısından sürecin elverişliliği. (Uzman) | **Permitting, land-acquisition and regulatory readiness:** favourability of EIA, zoning, land tenure, grid and water permits and administrative capacity. (Expert) |

---

## 6. Part D: Site ratings (expert-judged criteria only)

**General instruction (TR):** "Aşağıdaki dört kriterin her biri için beş aday sahayı 1–7 ölçeğinde değerlendiriniz. Ekteki saha bilgi kartı tüm sahalar için aynı bilgileri içermektedir. Bir saha hakkında yeterli bilginiz yoksa lütfen tahmin yürütmek yerine 'Bu konuda değerlendirme yapacak bilgim yok' seçeneğini işaretleyiniz."

**General instruction (EN):** "For each of the four criteria below, rate the five candidate sites on the 1–7 scale. The attached site fact card gives the same information for every site. If you lack sufficient knowledge about a site, please select 'No basis to judge' rather than guessing."

Grid layout: rows = S1–S5 (shuffled); columns = 1 … 7 and NB.

### D1. S1: Yerel toplumsal kabul / Local social acceptance

**TR soru:** "Aday sahada büyük ölçekli bir yeşil hidrojen üretim tesisinin (elektrolizör, ilişkili rüzgâr/güneş santrali ve şebeke bağlantısı) yerel halk ve yerel yönetimler tarafından, örgütlü muhalefet, dava süreci veya uzun süreli bir çatışma yaşanmadan kabul görme olasılığını nasıl değerlendirirsiniz?"

**EN item:** "How likely is it that a large-scale green-hydrogen production facility (electrolyser, associated wind/PV plant and grid connection) at this site would be accepted by the local community and local authorities without organised opposition, litigation or protracted conflict?"

**Göz önünde bulundurulabilecek hususlar / Aspects you may consider** (not exhaustive, no weighting implied):
- **TR:** bölgede önceki enerji ve sanayi yatırımlarına ilişkin deneyimler; yerel ekonominin tarım, hayvancılık veya turizme bağımlılığı; hidrojen güvenliğine ilişkin algılar; yatırımcıya ve kamu kurumlarına güven; arazi ve su kullanımında rekabet.
- **EN:** past local experience with energy and industrial investments; dependence of the local economy on agriculture, livestock or tourism; perceptions of hydrogen safety; trust in developers and public authorities; competition for land and water.

| Puan | TR çapa | EN anchor |
|---|---|---|
| 1 | Çok güçlü muhalefet beklenir: örgütlü itiraz, dava veya protesto çok olası; proje büyük olasılıkla engellenir veya ciddi biçimde gecikir. | Very strong opposition expected: organised objection, litigation or protest very likely; the project would probably be blocked or seriously delayed. |
| 2 | Güçlü muhalefet olası; kabul ancak çok kapsamlı tavizlerle mümkün. | Strong opposition likely; acceptance only with very extensive concessions. |
| 3 | Belirgin itirazlar olası; kabul koşullu ve belirsiz. | Noticeable objections likely; acceptance conditional and uncertain. |
| 4 | Karışık/nötr: belirgin bir destek ya da muhalefet beklentisi yok. | Mixed/neutral: no clear expectation of support or opposition. |
| 5 | Genel olarak kabul beklenir; kaygılar olağan katılım ve istişare süreçleriyle giderilebilir. | Generally accepted; concerns manageable through standard consultation. |
| 6 | Geniş yerel destek beklenir. | Broad local support expected. |
| 7 | Çok güçlü destek: yerel aktörler projeyi etkin biçimde destekler; çatışma olasılığı çok düşük. | Very strong support: local actors actively favour the project; conflict very unlikely. |

### D2. S2: İzin, arazi edinimi ve mevzuat hazırlığı / Permitting, land-acquisition and regulatory readiness

**TR soru:** "Aday sahada büyük ölçekli bir yeşil hidrojen tesisi için gerekli izinlerin ve arazi haklarının makul bir sürede elde edilebilmesine ilişkin koşulları nasıl değerlendirirsiniz? (ÇED süreci, imar/plan durumu, arazi mülkiyeti — ör. Hazine, mera veya özel mülk —, şebeke bağlantı onayı, su kullanım izni ve il/bölge düzeyindeki idari kapasite)"

**EN item:** "How favourable are the conditions for obtaining, within a reasonable time, the permits and land rights needed for a large-scale green-hydrogen facility at this site? (EIA process, zoning/plan status, land tenure — e.g., Treasury, pasture (*mera*) or private land —, grid-connection approval, water-use permit, and provincial/regional administrative capacity)"

| Puan | TR çapa | EN anchor |
|---|---|---|
| 1 | Çok elverişsiz: ciddi hukuki veya mülkiyet engelleri; izin süreci son derece uzun ya da belirsiz. | Very unfavourable: serious legal or tenure barriers; permitting extremely long or uncertain. |
| 2 | Elverişsiz: önemli engeller; uzun gecikmeler olası. | Unfavourable: major barriers; long delays likely. |
| 3 | Ortanın altında: bazı engeller; gecikme riski belirgin. | Below average: some barriers; clear risk of delay. |
| 4 | Ortalama: olağan izin süreci ve olağan riskler. | Average: standard permitting process and ordinary risks. |
| 5 | Ortanın üstünde: engeller sınırlı; süreç büyük ölçüde öngörülebilir. | Above average: limited barriers; process largely predictable. |
| 6 | Elverişli: arazi erişimi ve izin yolları açık; gecikme riski düşük. | Favourable: clear land access and permitting pathways; low risk of delay. |
| 7 | Çok elverişli: arazi hazır, izin yolları yerleşik; belirgin gecikme beklenmez. | Very favourable: land readily available, established permitting pathways; no material delay expected. |

### D3. E2: Sanayi-lojistik ekosistemi ve nitelikli iş gücü / Industrial-logistics ecosystem and skilled workforce

**TR soru:** "Aday sahanın çevresi, bir yeşil hidrojen tesisinin kurulması ve işletilmesi için gereken destekleyici ekosistemi ne ölçüde sunmaktadır? (nitelikli teknik iş gücü, mühendislik/EPC ve bakım-onarım hizmet sağlayıcıları, organize sanayi bölgeleri, çok modlu lojistik: karayolu, demiryolu, liman veya boru hattı erişimi)"

**EN item:** "To what extent does the area around this site provide the supporting ecosystem needed to build and operate a green-hydrogen facility? (skilled technical workforce, engineering/EPC and O&M service providers, organised industrial zones, multimodal logistics: road, rail, port or pipeline access)"

| Puan | TR çapa | EN anchor |
|---|---|---|
| 1 | Çok zayıf: nitelikli iş gücü ve hizmet sağlayıcıları büyük ölçüde bölge dışından getirilmeli; lojistik bağlantılar çok sınırlı. | Very weak: skilled labour and service providers must largely be brought in from outside; logistics links very limited. |
| 2 | Zayıf: temel hizmetler mevcut, uzmanlık büyük ölçüde dışarıdan. | Weak: basic services present; expertise mostly external. |
| 3 | Ortanın altında: bazı yerel kapasite, belirgin eksikler. | Below average: some local capacity with clear gaps. |
| 4 | Orta: kurulum için yeterli, işletmede kısmi dış destek gerekir. | Medium: adequate for construction; partial external support needed for operation. |
| 5 | Ortanın üstünde: yerel iş gücü ve hizmetler büyük ölçüde yeterli. | Above average: local labour and services largely adequate. |
| 6 | Güçlü: deneyimli iş gücü, OSB ve iyi lojistik bağlantılar mevcut. | Strong: experienced workforce, industrial zones and good logistics links available. |
| 7 | Çok güçlü: nitelikli iş gücü, EPC/bakım hizmetleri, OSB ve çok modlu lojistik bölgede hazır. | Very strong: skilled workforce, EPC/O&M services, industrial zones and multimodal logistics readily available. |

### D4. T3: Yeraltı hidrojen depolamasına erişim / Access to underground hydrogen storage

**TR soru:** "Bölgenin bilinen jeolojik yapısını dikkate aldığınızda (ör. tuz mağarası açılmasına uygun kaya tuzu formasyonları, tükenmiş doğal gaz sahaları veya diğer uygun rezervuarların boru hattıyla makul biçimde bağlanabilecek mesafede bulunması), aday saha gelecekte büyük ölçekli yeraltı hidrojen depolamasına erişim açısından ne kadar elverişlidir?"

**EN item:** "Considering the known geology of the wider region (e.g., rock-salt formations suitable for cavern construction, depleted gas fields or other suitable reservoirs within a distance that a pipeline could reasonably connect), how favourable is this site for future access to large-scale underground hydrogen storage?"

**Note to experts:**
- **TR:** "Bu kriter yüksek belirsizlik içerebilir. Bölgenin jeolojisine ilişkin bilginiz yoksa lütfen 'Bu konuda değerlendirme yapacak bilgim yok' seçeneğini işaretleyiniz."
- **EN:** "This criterion may involve high uncertainty. If you have no knowledge of the regional geology, please choose 'No basis to judge'."

| Puan | TR çapa | EN anchor |
|---|---|---|
| 1 | Makul bağlantı mesafesinde bilinen uygun depolama seçeneği yok. | No known suitable storage option within a reasonable connection distance. |
| 2 | Çok zayıf olasılık. | Very weak prospects. |
| 3 | Sınırlı/zayıf jeolojik belirtiler. | Limited or weak geological indications. |
| 4 | Belirsiz: bazı belirtiler var ancak kanıtlanmamış. | Uncertain: some indications, unproven. |
| 5 | Olası: umut verici jeoloji, ayrıntılı veri yok. | Possible: promising geology, no detailed data. |
| 6 | Güçlü olasılık: belgelenmiş uygun formasyonlar makul mesafede. | Strong prospects: documented suitable formations within reasonable distance. |
| 7 | Kanıtlanmış veya yüksek potansiyelli depolama jeolojisi makul bağlantı mesafesinde. | Proven or highly prospective storage geology within reasonable connection distance. |

---

## 7. Optional item: confidence per criterion

**Item (shown once per criterion, after the site grid):**
- **TR:** "Bu kriterdeki değerlendirmelerinize ne kadar güveniyorsunuz?"
- **EN:** "How confident are you in your ratings for this criterion?"
- **Options:** Düşük / Low; Orta / Medium; Yüksek / High.

*Authors' design option, not a literature requirement.* It could inform the hesitancy (π) component or expert weights. If used, the mapping rule must be fixed and reported before data collection.

---

## 8. Google Forms implementation notes

1. **One "Çoklu seçenek ızgarası / Multiple-choice grid" per criterion in Part D:**
   - rows S1–S5;
   - columns "1 … 7" plus "Bilgim yok / No basis";
   - turn on "Her satırda yanıt gerektir" and "Satır sırasını karıştır".
2. **Part C as one grid:**
   - rows = 10 criteria with their short definitions in the description;
   - columns 1–7;
   - shuffle the row order.
3. **Attach the fact card (Part B)** as an image or PDF link in the Part D section description. Use identical layout for all sites.
4. **Remove from all three current files** (`Google_Forms_Tam_Kopyala_Yapistir_Metni.md`, `Uzman_Anket_Formu_TR.md`, `Expert_Survey_Form_EN.md`):
   - every numerical site value (CF, GHI, km distances, zone numbers);
   - the C1a–C6, C8 and C10 items.
5. **Pilot first.** Run with 2–3 experts and check completion time, item clarity and use of "No basis". Fix the item wording before the main round.
