# Techno-economic parameter set (triangular fuzzy numbers, 2030 investment year)

Green-hydrogen supply chain, Türkiye: onshore wind and utility PV feeding co-located PEM electrolysis, compression, pipeline or tube-trailer transport, and seasonal storage in the Tuz Gölü salt caverns.

Compiled 2026-10-18 from the sources listed in the table below.

**Conventions**
- Each value is a triangular fuzzy number (TFN) given as (low, mode, high).
- All money values are in EUR. A value published in another currency is converted at the ECB annual-average rate for the year of its price basis (rates in Note N1). No inflation escalation is applied, so the "basis year" column gives the price year. Escalate with euro-area HICP if you need one common price year.
- Unless stated otherwise, energy per kg H₂ uses the LHV (33.33 kWh/kg).
- Evidence levels: **FT** = full text (or the full relevant section) read; **Ex** = excerpt or search highlight only; **Abs** = abstract only. "FT-sec" means the full text of a secondary compilation was read (the PyPSA *technology-data* compilation of Danish Energy Agency (DEA) catalogue values), but not the original DEA datasheet.
- "D" in the low/mode/high cells marks a derived value. Every derivation is shown in the notes below.

---

## 1. Parameter table

| # | Parameter | Unit | Low | Mode | High | Basis year & currency | Source(s) (DOI / URL) | Evidence |
|---|---|---|---|---|---|---|---|---|
| **1 Onshore wind** | | | | | | | | |
| 1.1 | Onshore wind CAPEX (total installed) | €/kW | 796 (D) | 924 (D) | 1 533 (D) | 2024 USD→€ @1.0824 | Low: IRENA 2025, *Renewable Power Generation Costs in 2024*: global TIC expected to reach ~USD 861/kW "over the next five years" (https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2025/Jul/IRENA_TEC_RPGC_in_2024_2025.pdf). Mode (Türkiye): YEKA RES-2024, 1.2 GW for USD 1.2 bn (https://newsbase.com/story/turkey-awards-1-2-gw-of-wind-power-deals-in-tenders-364113); TÜREB, USD 1.3 bn for 1.3 GW in 2024 (https://aea-al.org/wind-power-investments-in-turkey-surge-as-major-plants-inaugurated-in-may/); PhillipCapital sector note, USD 1.0–1.1 M/MW (https://www.phillipcapital.com.tr/Files/IndustryReport/297d6b50-db0a-419a-95e3-8cf82a593c70.pdf). High: IRENA 2025, Table 2.1, Europe 2024 weighted average USD 1 659/kW | IRENA FT; Turkish items Ex |
| 1.2 | Onshore wind fixed O&M | €/kW/yr | 22.2 (D) | 34.5 (D) | 41.6 (D) | Low 2025 €; mode 2022 USD; high 2024 USD | Low: DEA cat. 20 (2030) via PyPSA technology-data `costs_2030.csv`: FOM 1.2167 %/yr × 1 383 €/kW, plus VOM 1.80 €/MWh at 2 978 h (https://github.com/PyPSA/technology-data). Mode (Türkiye): UNCTAD 2024, *Solar and wind power transition in Türkiye*, Table 2: USD 36.3/kW/yr (https://unctad.org/system/files/information-document/unda2030d13-turkieye-wind-solar%5Fen.pdf). High: IRENA 2025, Table A3, "Other OECD" USD 45/kW/yr | FT-sec / Ex / FT |
| 1.3 | Onshore wind lifetime | yr | 20 | 25 | 30 | – | Low: Demirkol et al. 2025, Energies 18:2632 (Türkiye case study), https://doi.org/10.3390/en18102632. Mode: IRENA 2025, Table A1 (economic life). High: DEA cat. 20 technical lifetime (via PyPSA) | Ex / FT / FT-sec |
| **2 Utility-scale PV** | | | | | | | | |
| 2.1 | Utility PV CAPEX (total installed) | €/kW | 359 (D) | 647 (D) | 954 (D) | 2024 USD→€ | Low: IRENA 2025, global TIC expected to reach ~USD 388/kW within five years. Mode (Türkiye): PhillipCapital, conventional and hybrid PV USD 0.4–0.7 M/MW (upper end used). High: IRENA 2025, Türkiye 2024 weighted-average TIC USD 1 033/kW (+41 % y/y). Cross-check: DEA cat. 22 (2030) 482 €/kW (2025 €) | IRENA FT; PhillipCapital Ex |
| 2.2 | Utility PV fixed O&M | €/kW/yr | 11.9 (D) | 13.8 (D) | 19.1 (D) | Low 2025 €; mode 2022 USD; high 2024 USD | Low: DEA cat. 22 via PyPSA (2.4757 %/yr × 482 €/kW). Mode: UNCTAD 2024, Table 2 (Türkiye, USD 14.5/kW/yr). High: IRENA 2025, Table A4, OECD 2024 USD 20.7/kW/yr | FT-sec / Ex / FT |
| 2.3 | Utility PV lifetime | yr | 25 | 25 | 40 | – | Low and mode: IRENA 2025, Table A1. High: DEA cat. 22 technical lifetime (via PyPSA) | FT / FT-sec |
| **3 PEM electrolyser system** | | | | | | | | |
| 3.1 | PEM installed CAPEX (system + BoP + EPC/indirects) | €/kW_el | 888 (D) | 1 249 (D) | 2 503 | Low and mode 2023 USD→€ @1.0813; high 2025 € | Low: IEA *Global Hydrogen Review 2024*, Assumptions annex: NZE-2030 global CAPEX USD 960/kWe, which includes electrolyser system, electrical equipment, gas treatment, BoP and EPC (https://iea.blob.core.windows.net/assets/c87963ad-339e-47be-8b50-fca1fbc3d4b8/GlobalHydrogenReview2024AssumptionsAnnex.pdf). Mode: IEA STEPS 2030 installed cost USD 1 250–1 450/kW, midpoint used, as reported by Argus (https://www.argusmedia.com/en/news-and-insights/latest-market-news/2614112-iea-raises-2030-renewable-h2-cost-estimates). High: European Hydrogen Observatory, *European hydrogen market landscape*, Nov 2025: PEM CAPEX 2 503 €/kW, 100 MW, incl. other CAPEX (https://observatory.clean-hydrogen.europa.eu/sites/default/files/2025-11/The%20European%20hydrogen%20market%20landscape_November%202025.pdf) | Ex / Ex / Ex |
| 3.2 | PEM fixed O&M (excl. electricity; excl. stack replacement where separated) | % CAPEX/yr | 2.0 (D) | 3.0 | 4.0 | – | Low: EHO Nov 2025, OPEX 50.1 €/kW/yr ÷ 2 503. Mode: IEA GHR 2024 annex, annual OPEX 3 % of CAPEX. High: DEA renewable-fuels catalogue, electrolysis FOM 4 %/yr (via PyPSA); Aalborg Univ. DEA-based data, PEM 4 %/yr (https://vbn.aau.dk/ws/files/80222058/Technology_data_for_SOEC_alkali_and_PEM_electrolysers.pdf) | Ex / Ex / FT-sec |
| 3.3 | Stack lifetime | h | 40 000 | 50 000 | 80 000 | – | Low: US DOE Hydrogen Program Record 24005, PEM (replacement interval) (https://www.hydrogen.energy.gov/docs/hydrogenprogramlibraries/pdfs/24005-clean-hydrogen-production-cost-pem-electrolyzer.pdf). Mode: IEA GHR 2024 annex, which notes the stack "can reach up to 95 000 h". High: IRENA 2020, *Green Hydrogen Cost Reduction*, Table 6, PEM state of the art 50 000–80 000 h (https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf); Siemens Energy Elyzer P-300, stack "optimized for 80k EOH" | Ex / Ex / FT |
| 3.4 | Stack replacement cost | % of installed CAPEX | 11 | 22.5 (D) | 45 | Low 2022 USD basis; others 2024–25 € | Low: DOE Record 24005, 11 % of total installed capital cost. Mode: EHO survey PEM stack 563 €/kW ÷ EHO total 2 503 €/kW, as quoted in JRC CETO 2025 (https://www.enagas.es/content/dam/enagas/en/files/transicion-energetica/red-hidrogeno/observatorio-tecnologico-hidrogeno/jrc-water-electrolysis-hydrogen.pdf). High: TNO 2024 (via JRC CETO 2025), stack = 20–45 % of project CAPEX | Ex |
| 3.5 | System lifetime | yr | 22 | 25 | 30 | – | Low: NREL 2019 (Ruth, Mayyas, Mann), PEM median 22 yr, range 10–30 (https://docs.nlr.gov/docs/fy19osti/70380.pdf). Mode: DEA renewable-fuels electrolysis technical lifetime (via PyPSA). High: DOE Record 24005, 30 yr | Ex / FT-sec / Ex |
| 3.6 | Minimum load | % of nominal | 3 | 5 | 10 | – | Low and high: NREL 2019, PEM minimum load 3–10 %. Mode: IRENA 2020 Table 6, load range 5–120 %; RVO 2021 memo, "most PEM manufacturers report 5–100 %" (https://english.rvo.nl/sites/default/files/2022/01/2021-12-Memo-minimum-last%20stop_start-en-degeneratie-van-elektrolysers.pdf). Caveat: single-stack minimum load is higher (H-TEC 20 %, Siemens P-300 40 % per stack) | Ex / FT / Ex |
| **4 Hydrogen compression** | | | | | | | | |
| 4.1 | Specific energy, 30 → 70–100 bar (pipeline injection) | kWh_el/kg | 0.39 (D) | 0.56 (D) | 0.97 (D) | – | Isothermal ideal-gas work scaled by two sourced real-machine efficiencies (Note N3): Neuman & Esser, 60→200 bar piston compressor, 15 MW at 300 000 Nm³/h (https://www.neuman-esser.com/en/news-media/magazine/storing-hydrogen/); Stöckl et al. 2021 via PyPSA, 30→250 bar, 1.707 kWh/kg (https://doi.org/10.48550/arXiv.2005.03464) | Ex / FT-sec |
| 4.2 | Specific energy, 30 → 150–200 bar (direct cavern injection) | kWh_el/kg | 0.74 (D) | 0.88 (D) | 1.53 (D) | – | Same method as 4.1 (Note N3) | Ex / FT-sec |
| 4.3 | Specific energy, pipeline (~60–100 bar) → 200 bar (cavern booster) | kWh_el/kg | 0.30 | 0.56 | 0.85 (D) | – | Low and mode: Neuman & Esser, reported 0.9 % (60→120 bar, mid-filling) and 15 MW / 300 000 Nm³/h (60→200 bar). High: 70→200 bar at the Stöckl-implied efficiency | Ex |
| 4.4 | Compressor CAPEX (installed station) | €/kW_el (shaft/electric) | 2 205 (D) | 3 400 | 6 700 | Low 2025 €; mode and high 2022 € | Low: Stöckl et al. via PyPSA, 110.26 €/kW_H2 ÷ 0.05 kW_el/kW_H2. Mode and high: European Hydrogen Backbone (EHB) 2022, Table 1, compressor station 2.2 / 3.4 / 6.7 M€/MWe (https://www.ehb.eu/files/downloads/ehb-report-220428-17h00-interactive-1.pdf); EHB 2023 update gives 4.0 M€/MWe (https://ehb.eu/files/downloads/EHB-2023-20-Nov-FINAL-design.pdf) | FT-sec / Ex |
| 4.5 | Compressor fixed O&M | % CAPEX/yr | 1.7 | 4 | 5 | – | EHB 2022 (1.7 %); Stöckl et al. via PyPSA (4 %); UK DESNZ 2023, *Hydrogen Transport and Storage Cost Report* (5 %) (https://assets.publishing.service.gov.uk/media/659e600b915e0b00135838a6/hydrogen-transport-and-storage-cost-report.pdf) | Ex / FT-sec / FT |
| 4.6 | Compressor lifetime | yr | 15 | 20 | 25 | – | Stöckl via PyPSA (15); DEA *Energy Transport* 2021, fill compressor (20, via PyPSA); EHB 2022 depreciation (25) | FT-sec / Ex |
| **5 Salt-cavern storage (generic, then Tuz Gölü)** | | | | | | | | |
| 5.1 | Cavern CAPEX per kg working gas (incl. cavern, brine, surface compressor, cushion gas) | €/kg WG | 11.2 (D) | 16.1 (D) | 30.1 (D) | Low 2018 USD @1.181; mode and high 2021 USD @1.1827 | Low (Türkiye-derived): AIIB project document, Tuz Gölü expansion, USD 2 735 M for 40 caverns (https://www.aiib.org/en/projects/approved/2018/_download/turkey/document/turkey-gas-storage-expansion.pdf), ÷ (40 × 5 168 t H₂ WG per cavern, Note N4). Mode: Papadias & Ahluwalia 2021, IJHE 46:34527, "<USD 19/kg at 3 000 t" (https://doi.org/10.1016/j.ijhydene.2021.08.028). High: same paper, Table 7, USD 35.6/kg at 500 t, 120 atm. Cross-check: GIE/Guidehouse 2021, €840/MWh = €28.0/kg (https://www.gie.eu/wp-content/uploads/filr/3517/Picturing%20the%20value%20of%20gas%20storage%20to%20the%20European%20hydrogen%20system_FINAL_140621.pdf) | Ex (OSTI manuscript tables) / Ex |
| 5.2 | Cavern fixed O&M | % CAPEX/yr | 0 | 2 | 3 | – | Low: DEA storage catalogue 151c, FOM 0 (via PyPSA). Mode: EnergyScope library, 2 % (https://library.energyscope.ch/v2.1.2/library/technologies/Chemical_storage/H2_STO/). High: Wassermann et al. 2022, 3 % (https://doi.org/10.1515/9783110705201-003) | FT-sec / Ex / Ex |
| 5.3 | Cavern lifetime | yr | 20 | 30 | 100 | – | Low: Lord et al. (Sandia), equipment lifetime 20 yr (https://www.osti.gov/servlets/purl/1325533). Mode: Tuz Gölü ESIA, economic life 30 yr (World Bank ESIA executive summary, https://documents1.worldbank.org/curated/en/424331497622953008/pdf/Turkey-Tuz-Golu-Gas-Storage-Expansion-Project-ESIA-Executive-Summary-06132017.pdf). High: DEA 151c technical lifetime (via PyPSA) | Ex / Ex / FT-sec |
| 5.4 | Cushion-gas share (of maximum H₂ inventory) | % | 30 | 33.3 | 38.3 | – | Low: Papadias & Ahluwalia 2021 (30 %). Mode: Neuman & Esser ("about 1/3"). High (Tuz Gölü-specific): Şan & Karakılçık, Table 3, 38 519 t ÷ 100 532 t (https://fbe.cu.edu.tr/storage/makaleler/2021/TUZ%20DOMLARINDA%20H%C4%B0DROJEN.pdf) | Ex / Ex / FT |
| 5.5 | Tuz Gölü H₂ working gas, 12 existing caverns | t H₂ | 62 013 | 62 013 | 63 436 (D) | – | Şan & Karakılçık, Table 3: Σmax 100 532 t − Σmin 38 519 t = 62 013 t (≈689.76 M Nm³; 2 446 GWh HHV). High: the rounded "≈2.5 TWh (HHV)" ÷ 39.41 kWh/kg. Note N4 | FT |
| 5.6 | Tuz Gölü H₂ working gas, after expansion | t H₂ | 268 723 (D) | 279 058 (D) | 310 065 (D) | – | Scaled from 5.5 by NG capacity or cavern count: 52/12 caverns (BOTAŞ, https://www.botas.gov.tr/Icerik/on-the-way-to-being-an-energy/193); 5.4/1.2 bcm (AIIB); 60/12 caverns (ESIA). Rough scaling: geometry and depth of the new caverns differ | Ex |
| 5.7 | Injection rate, 12 caverns (H₂) | t/day | 1 860 (D) | 1 860 (D) | 2 696 (D) | – | Derived from the NG design rate of 30 M Nm³/d for 12 caverns (ESIA; Özarslan TR paper, https://docplayer.biz.tr/1083316-yenilenebilir-enerji-kaynaklari-icin-buyuk-olcekli-enerji-depolama-yontemleri-ahmet-ozarslan-bulent-ecevit-universitesi-maden-muh.html). Low and mode keep the same share of working gas per day (3 %/d); high keeps the same volumetric flow (Note N4) | Ex |
| 5.8 | Withdrawal rate, 12 caverns (H₂) | t/day | 2 481 (D) | 2 481 (D) | 3 595 (D) | – | Same approach, NG 40 M Nm³/d (4 %/d of working gas) | Ex |
| **6 Hydrogen pipelines** | | | | | | | | |
| 6.1 | New pipeline CAPEX, 20″ (~1.2 GW; 180–315 kt/yr) | M€/km | 1.4 | 1.5 | 1.8 | 2022 € (high also = EHB 2023 value) | EHB 2022, Table 1 (low/medium/high); EHB 2023, Table 1 (1.80) | Ex |
| 6.2 | New pipeline CAPEX, 36″ (~4.7 GW; 705–1 235 kt/yr) | M€/km | 2.0 | 2.2 | 3.2 | 2022 €; high = EHB 2023 | EHB 2022 / EHB 2023 | Ex |
| 6.3 | New pipeline CAPEX, 48″ (~13 GW) | M€/km | 2.5 | 2.8 | 4.4 | 2022 €; high = EHB 2023 | EHB 2022 / EHB 2023 | Ex |
| 6.4 | Repurposed pipeline CAPEX, 20″ | M€/km | 0.2 | 0.3 | 0.54 | 2022 €; high = EHB 2023 | EHB 2022 / EHB 2023 | Ex |
| 6.5 | Repurposed pipeline CAPEX, 36″ (~3.6 GW) | M€/km | 0.2 | 0.4 | 0.64 | 2022 €; high = EHB 2023 | EHB 2022 / EHB 2023 | Ex |
| 6.6 | Repurposed pipeline CAPEX, 48″ | M€/km | 0.3 | 0.5 | 0.88 | 2022 €; high = EHB 2023 | EHB 2022 / EHB 2023 | Ex |
| 6.7 | Pipeline fixed O&M (excl. compressors) | % CAPEX/yr | 0.8 | 0.9 | 1.0 | – | EHB 2022, Table 1. DEA (via PyPSA) gives 3.17 %/yr including boosters, as an upper sensitivity | Ex |
| 6.8 | Pipeline lifetime | yr | 30 | 40 | 50 | – | Low: Guidehouse 2020 depreciation 30–55 yr (cited in SHURA 2022, https://shura.org.tr/wp-content/uploads/2022/01/rapor_ENG-.pdf). Mode: EHB 2022 depreciation 40 yr. High: DEA *Energy Transport* 2021 "H2 140" (via PyPSA) | Ex / Ex / FT-sec |
| 6.9 | Levelised transport cost, **new** pipeline, 50–500 kt/yr | €/kg per 1 000 km | 0.30 | 0.70 (D) | 0.98 (D) | 2021 € | EHB 2021, Table 4 (5 000 full-load hours): new 36″ at 4.7 GW = 0.30 €/kg/1 000 km; new 20″ at 1.2 GW = 0.14 €/kg/200 km → ×5. High = mode × 1.4, the EHB 2022 high/medium ratio (0.21/0.15) (https://ehb.eu/files/downloads/European-Hydrogen-Backbone-April-2021-V3.pdf) | FT |
| 6.10 | Levelised transport cost, **repurposed** pipeline, 50–500 kt/yr | €/kg per 1 000 km | 0.11 | 0.25 (D) | 0.35 (D) | 2021 € | EHB 2021, Table 4: repurposed 36″ (3.6 GW) = 0.11; repurposed 20″ = 0.05 €/kg/200 km → ×5; high × 1.4 as above. Backbone-wide average 0.11–0.21 (0.15 medium) (EHB 2022) | FT / Ex |
| 6.11 | In-line recompression energy | kWh_el/kg per 1 000 km | – | 0.63 (D) | – | – | DEA *Energy Transport* 2021 "H2 140", 0.019 MW_el per MW_H2 per 1 000 km (via PyPSA) × 33.33 | FT-sec |
| **7 Tube-trailer (CGH₂) road transport** | | | | | | | | |
| 7.1 | Payload per trailer | kg H₂ | 300 | 1 000 | 1 300 | – | UK DESNZ 2023, Table 4 (Type I 228 bar: 300 kg; Type III/IV 500 bar: >1 000 kg) and Calvera 517 bar unit (1 300 kg); Burke et al. 2024 (600–800 kg at 250 bar) (https://escholarship.org/content/qt83p5k54m/qt83p5k54m_noSplash_8bb1326c13cfb9aa3d0d376ec26d3e06.pdf) | FT |
| 7.2 | Trailer CAPEX per kg payload | €/kg payload | 779 (D) | 961 (D) | 1 227 (D) | Low and mode ~2020 €; high 2022 GBP @0.85276 | Low and mode: Lahnaoui et al. 2021, Energies 14:744, trailer cost table (885 kg → 689 k€; 1 100 kg → 1 057 k€) (https://www.mdpi.com/1996-1073/14/3/744). High: DESNZ 2023, £1 046/kg deliverable payload | Ex / FT |
| 7.3 | Trailer O&M / lifetime | %/yr ; yr | 5 % ; 10 | 5 % ; 15 | 5 % ; 30 | – | DESNZ 2023 (O&M 5 %/yr; lifetime "10–30 yr", 15 yr base) | FT |
| 7.4 | Tractor unit (diesel 40–50 t) CAPEX / VOM / lifetime | €/veh ; €/km ; yr | – | 178 557 ; 0.134 ; 10.5 | – | 2025 € | DEA *Commercial freight transport* datasheet via PyPSA ("Diesel Truck Semi-Trailer max 50 tons") | FT-sec |
| 7.5 | Distance-variable levelised cost (trailering only, excl. compression) | €/kg per 100 km | 0.14 (D) | 0.35 (D) | 0.58 (D) | Low 2023 GBP; others USD @1.0824 | Low: DESNZ 2023, Table A4 (1 300 kg, 300 trips/yr: £0.90 at 100 km → £1.14 at 300 km). Mode: Reddi et al. 2018, IJHE 43:4428 (via Burke et al. 2024, Table 4: $1.4 at 160 km → $2.6 at 480 km). High: Reuß et al. 2021, Energies 14:3166 (via Burke: $1.1 at 100 km → $4.9 at 700 km). Note N6 | FT (secondary for Reddi/Reuß) |
| 7.6 | Compression 30 → 500 bar for trailer filling | kWh_el/kg | 1.47 | 2.41 | 3.36 | – | DESNZ 2023, Annex (low / standard / high compression cases) | FT |
| **8 Finance and currency** | | | | | | | | |
| 8.1 | WACC for RE/H₂ projects in Türkiye (**real, hard-currency (EUR/USD) basis**) | % | 7.5 | 10 | 12 | – | Low: IRENA 2025, Table A1, real WACC "rest of world" 7.5 % from 2020 (Türkiye rated B3, Fig. S7). Mode: SHURA 2022, Türkiye green-H₂ study, discount rate 10 % in USD-real-2021 terms. High: Tagliapietra, Zachmann & Fredriksson 2019, Energy Policy 131:295, upper bound 12 % for Turkish wind (USD-denominated YEKDEM FiT; nominal, so ≈9.8 % real at 2 % USD inflation) (https://doi.org/10.1016/j.enpol.2019.05.011). Cross-check: IEA LCOH maps use a 9 % default | FT / Ex / Abs |
| 8.2 | EUR/USD conversion basis | USD per € | 1.0813 (2023) | 1.0824 (2024) | 1.1300 (2025) | ECB annual averages | ECB reference rates via OeNB table / Bundesbank BBEX3 (https://www.oenb.at/isawebstat/stabfrage/createReport?lang=EN&report=2.14; https://statistiken.bundesbank.de/statistiken-en/timeseries/BBEX3/A.USD.EUR.BB.AC.A04) | Ex |
| **9 Electricity export price (PTF, day-ahead)** | | | | | | | | |
| 9.1 | Annual-average PTF | €/MWh | 58.4 (D) | 60.6 (D) | 62.8 (D) | 2025 and 2024, TRY→€ (ECB: 35.5734 in 2024; 44.8161 in 2025) | 2024 arithmetic mean 2 235.52 TL/MWh (EPİAŞ 2024 annual report, https://www.epias.com.tr/wp-content/uploads/2025/04/E24FRp_LR.pdf); 2025 arithmetic mean 2 617.83 TL/MWh (myenerji / EnerjiVeri; EPDK reports a weighted average of 2 651.81, https://www.epdk.gov.tr/Detay/DownloadDocument?id=aetLyVmDSsI%3D). Mode = mean of the 2024 and 2025 € values | Ex |
| 9.2 | Hourly shape: PTF at hour 12:00 / 19:00 relative to the annual mean (2024) | – | 0.672 | 1.000 | 1.220 | 2024 | EPİAŞ 2024 annual report: lowest hourly mean 1 503.28 TL at 12:00 (= 42.3 €/MWh); highest 2 727.40 TL at 19:00 (= 76.7 €/MWh) | Ex |
| **10 Water** | | | | | | | | |
| 10.1 | Electrolyser water requirement | L/kg H₂ | 8.94 (D) | 17.5 | 26.5 | – | Low: stoichiometric 18.015/2.016. Mode: IRENA & Bluerisk 2023, PEM average consumption 17.52 L/kg. High: same source, PEM maximum withdrawal 26.46 L/kg (Table 2.1) (https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2023/Dec/IRENA_Bluerisk_Water_for_hydrogen_production_2023.pdf) | Ex |
| 10.2 | Water cost (Türkiye, industrial, excl. VAT) | €/m³ | 0.33 (D) | 1.12 (D) | 2.57 (D) | 2025 TL @44.8161 | Low: İSKİ 2025 "Toptan Hamsu" 14.81 TL/m³ (https://iski.istanbul/abone-hizmetleri/abone-rehberi/su-birim-fiyatlari/). Mode: Başkent OSB (Ankara), from July 2025, use-water tier 2 = 50 TL/m³ (https://www.baskentosb.org/tr/medya/duyurular/su-birim-fiyatlarinda-yapilan-guncelleme-hakkinda-duyuru). High: İSKİ OSB tier 4 (with own WWTP) 115.03 TL/m³ | Ex |
| **11 Battery (optional short-term buffer)** | | | | | | | | |
| 11.1 | Li-ion 4-h battery system CAPEX (2030) | €/kWh | 191 (D) | 258 (D) | 327 (D) | 2024 USD @1.0824 | NREL, Cole, Ramasamy & Turan 2025, *Cost Projections for Utility-Scale Battery Storage: 2025 Update*, Table 2, 2030 low/mid/high USD 207/279/354 per kWh (https://docs.nrel.gov/docs/fy25osti/93281.pdf). Cross-checks: IRENA 2025, 2024 actual USD 192/kWh; DEA 2030 189.9 €/kWh + inverter 213.9 €/kW (via PyPSA) | Ex / FT / FT-sec |
| 11.2 | Battery lifetime | yr | 10 (inverter) | 15 | 25 | – | DEA storage catalogue via PyPSA (storage 25 yr, inverter 10 yr). The mode of 15 yr is **not sourced**; it is an assumed value for an integrated system | FT-sec |

---

## 2. Tuz Gölü facility facts (deterministic data for the model)

| Item | Value | Source | Evidence |
|---|---|---|---|
| Location | Sultanhanı, Aksaray, ~40 km south of Lake Tuz; tied into the Kayseri–Konya–Seydişehir NG line | BOTAŞ vulnerability report; World Bank ESIA | Ex |
| Phase 1 caverns | 12 caverns (UGS-1 to UGS-12), ~630 000 m³ net (geometric) volume each; roof 1 100–1 230 m, floor 1 400–1 530 m | Şan & Karakılçık, Table 1 (after Melendizli & Akdağ 2015); ESIA | FT / Ex |
| Phase 1 NG working gas / cushion gas | ~1.0 bcm WG / ~0.5–0.6 bcm cushion (later quoted as 1.2 bcm total capacity) | Şan & Karakılçık (1 bcm / 0.5 bcm; their own calc 0.94 / 0.50 bcm); Özarslan TR paper Table 5 (1 000 / 600 M m³); BOTAŞ / AIIB (1.2 bcm) | FT / Ex |
| NG pressure range | 80–220 bar (alternative 70–200 bar) | Özarslan TR paper Table 5; Şan & Karakılçık | Ex / FT |
| NG max injection / withdrawal (12 caverns) | 30 / 40 million m³/day | ESIA Table 3.2.1; Özarslan TR paper | Ex |
| Expansion | +40 caverns (+ up to 8 spare), net 630 000–872 000 m³ each, total 5.4 bcm (AIIB, cost USD 2 735 M); BOTAŞ quotes 52 caverns / 5.4 bcm, 630 000–780 000 m³ each; ESIA quotes 48 new / 60 total, ~6 bcm WG, 60 / 80 M m³/d | AIIB PD; BOTAŞ; ESIA | Ex |
| Status | 680 M m³ capacity and 20 M m³/d withdrawal operating in 2019; 1.2 bcm stored by Oct 2023 | BOTAŞ; Anadolu Agency 2023-10-26 (https://www.aa.com.tr/en/energy/natural-gas/exclusive-turkiye-ready-for-winter-as-gas-storage-facilities-totally-full/39153) | Ex |
| **H₂ working gas, 12 caverns** | **62 013 t (≈2.45 TWh HHV = 2.07 TWh LHV); 5 168 t per cavern; cushion 38 519 t (38.3 %)** | Şan & Karakılçık (journal article from Şan's MSc thesis), Table 3; conversion in Note N4 | FT |
| Özarslan (2012), IJHE 37:14265, https://doi.org/10.1016/j.ijhydene.2012.07.111 | Pre-evaluation of Tuz Gölü for a solar-hydrogen-NG system; the full text reports about 6 million kg of working H₂ gas for a representative salt cavern, but no Tuz Gölü-specific H₂ capacity. The generic estimate is not used as a model input. | ScienceDirect, ADS | FT |

---

## 3. Notes on conversions and derivations

**N1. Exchange rates.** ECB annual averages, from the OeNB/ECB table and Bundesbank BBEX3, Eurostat ert_bil_eur_a for earlier years.
- USD per €: 2018 1.181; 2021 1.1827; 2022 1.0530; 2023 1.0813; 2024 1.0824; 2025 1.1300.
- GBP per €: 2022 0.85276; 2023 0.86979.
- TRY per €: 2024 35.5734; 2025 44.8161. TCMB mid rates agree to <0.1 %: 35.5389 and 44.8084; USD/TRY 32.8451 and 39.5418 (TCMB EVDS via altin.exchange).

Each value is converted at the rate for its price-basis year, with no CPI escalation.
- Examples: USD 861/kW (2024) ÷ 1.0824 = €795.5/kW; USD 960/kWe (2023) ÷ 1.0813 = €887.8/kWe; USD 1 350/kW ÷ 1.0813 = €1 248.5/kW.
- USD amounts with an unclear price year were treated as the publication year: Papadias 2021; Reddi and Reuß via Burke et al. 2024.

**N2. Wind and PV O&M.**
- DEA wind: fixed part 1.2167 % × 1 383.3 €/kW = 16.83 €/kW/yr. The variable part is VOM 1.8033 €/MWh × (0.34 × 8 760 h = 2 978 h, IRENA 2024 Türkiye capacity factor 34 %, Table 2.2) = 5.37 €/kW/yr. Total 22.2 €/kW/yr.
- DEA PV: 2.4757 % × 482.5 = 11.94 €/kW/yr.
- The PyPSA compilation reports DEA investment values in 2025 € (its `currency_year` column).

**N3. Compression energy.**
- Ideal isothermal work: W_iso = (R·T/M)·ln(p₂/p₁), with R·T/M = 8.314 × 303.15 / 0.002016 J/kg = 0.3473 kWh/kg per unit of ln.
- Two real-machine efficiencies, each derived from a published data point:
  - Neuman & Esser: 15 MW ÷ (300 000 Nm³/h × 0.0899 kg/Nm³) = 0.556 kWh/kg for 60→200 bar. W_iso = 0.3473 × ln(200/60) = 0.418, so η_NE = 0.752.
  - Stöckl et al. (via PyPSA): 1.707 kWh/kg for 30→250 bar. W_iso = 0.3473 × ln(250/30) = 0.736, so η_St = 0.431.
- Real energy = W_iso / η:

| Pressure step | W_iso (kWh/kg) | At η_NE (kWh/kg) | At η_St (kWh/kg) |
|---|---|---|---|
| 30→70 bar | 0.294 | 0.39 | 0.68 |
| 30→100 bar | 0.418 | 0.56 | 0.97 |
| 30→150 bar | 0.559 | 0.74 | 1.30 |
| 30→200 bar | 0.659 | 0.88 | 1.53 |
| 70→200 bar | 0.365 | 0.49 | 0.85 |

- Ideal gas is assumed. Z(H₂) ≈ 1.06–1.13 at 100–200 bar would raise the work by a few per cent.
- Low compressor CAPEX: 110.26 €/kW_H2 ÷ 0.05 kW_el/kW_H2 = 2 205 €/kW_el (Stöckl via PyPSA; 206 kg/h, 30→250 bar).
- **Avoid double counting:** the cavern CAPEX in row 5.1 (Papadias) already contains the cavern compressor (~18 % of capital) and the cushion gas (~4 %).

**N4. Tuz Gölü hydrogen capacity (12 caverns).**
- Şan & Karakılçık, Table 3: Σ maximum H₂ mass = 100 532 t and Σ minimum (cushion) = 38 519 t. Working gas = 100 532 − 38 519 = **62 013 t**.
- Volume check: 689.76 × 10⁶ Nm³ × 0.08988 kg/Nm³ = 61 996 t ✓.
- Energy check: 2 446.38 GWh (HHV) ÷ 39.41 kWh/kg = 62 075 t ✓. The rounded "≈2.5 TWh" gives 2.5 × 10⁹ / 39.41 = 63 436 t (used as the TFN high).
- LHV energy = 62 013 t × 33.33 kWh/kg = 2.07 TWh. Per cavern: 62 013 / 12 = 5 168 t. Cushion share = 38 519 / 100 532 = 38.3 %.
- Expansion (rough, assumes similar caverns): 62 013 × 52/12 = 268 723 t; × 5.4/1.2 = 279 058 t; × 60/12 = 310 065 t.
- Rates:
  - Same share of working gas per day: injection 30/1 000 = 3 %/d → 0.03 × 62 013 = 1 860 t/d; withdrawal 4 %/d → 2 481 t/d.
  - Same volumetric flow: 30 × 10⁶ Nm³/d × 0.08988 = 2 696 t/d; 40 × 10⁶ × 0.08988 = 3 595 t/d.
  - These are not published H₂ design values. Wells and surface plant would need H₂ re-rating.
- Low cavern CAPEX: USD 2 735 M ÷ (40 caverns × 5 168 t) = USD 13.23/kg, ÷ 1.181 (2018) = **€11.2/kg**. This assumes the new caverns hold as much H₂ as the Phase 1 caverns. It includes NG-specific surface plant, water and brine lines, and excludes H₂-specific equipment and cushion gas.
- Papadias: USD 19/kg ÷ 1.1827 = €16.1/kg; USD 35.6/kg ÷ 1.1827 = €30.1/kg.
- GIE: €840/MWh × 0.03333 MWh/kg = €28.0/kg.

**N5. Pipeline throughput (EHB design capacity, LHV).** kt/yr = GW × 10⁶ × h / 33.33 / 10⁶.

| Size | Design capacity | kt/yr at 5 000 h | kt/yr at 8 760 h |
|---|---|---|---|
| 20″ | 1.2 GW | 180 | 315 |
| 36″ repurposed | 3.6 GW | 540 | 946 |
| 36″ new | 4.7 GW | 705 | 1 235 |
| 48″ | 13 GW | 1 950 | 3 417 |

The study range of 50–500 kt/yr therefore maps onto 20″ to 36″ lines. Below ~150 kt/yr, per-kg costs exceed the 20″ value, and no source was found for that range. EHB levelised costs use 5 000 full-load hours and a 5 % WACC (EHB 2022, Table 1). Re-levelise with your own WACC from the CAPEX rows.

**N6. Tube-trailer cost per 100 km.**
- DESNZ: (£1.14 − £0.90) / 2 = £0.12 per kg per 100 km ÷ 0.86979 = €0.14.
- Reddi: ($2.6 − $1.4) / 320 km × 100 = $0.375 ÷ 1.0824 = €0.35.
- Reuß: ($4.9 − $1.1) / 600 km × 100 = $0.633 ÷ 1.0824 = €0.58.
- The distance-independent part (25 km trip) is £0.81–2.39/kg trailering plus £1.2–1.5/kg compression (DESNZ Tables A3/A4).
- At 270–1 400 km a fixed 300 trips/yr is infeasible (50 km/h, 4 h load and unload). Model the fleet size explicitly with rows 7.1–7.4 rather than using a linear €/kg/100 km.

**N7. PTF.**
- 2024: 2 235.52 TL ÷ 35.5734 = 62.84 €/MWh.
- 2025: 2 617.83 ÷ 44.8161 = 58.41 €/MWh (EPDK weighted average 2 651.81 → 59.17 €/MWh).
- Hourly-converted USD means (EnerjiVeri): 68.1 (2024) and 66.4 (2025) USD/MWh, consistent with the € values.
- Shape factors:
  - 2024 hour-of-day: 12:00 = 1 503.28/2 235.52 = 0.672; 19:00 = 2 727.40/2 235.52 = 1.220.
  - Sept 2025 time bands (EPİAŞ monthly report): night 22–06 = 1.079, day 06–17 = 0.840, peak 17–22 = 1.226 of the monthly mean.
- Price caps: 3 000 TL/MWh (2024), 3 400 TL/MWh (2025).
- Surplus sales from co-located PV happen mainly in midday hours, so apply the hourly shape. Do not use the flat mean.
- 2026 year-to-date (EnerjiVeri, 291 days) is 2 012 TL ≈ 43.8 USD/MWh, a downside signal outside the requested 2024–25 window.
- A full 8 760-h profile was **not** downloaded. Use the EPİAŞ Şeffaflık Platformu.

**N8. Water.** 1 kg H₂ needs 18.015/2.016 = 8.94 kg H₂O stoichiometrically. TL tariffs are converted at 44.8161 TL/€. The İSKİ PDF tariff (11.59 TL raw bulk; 90.08 TL OSB tier 4) differs from the web-page values (14.81; 115.03), probably a mid-2025 revision; the web-page values were used. Demineralisation cost is not included.

**N9. Scope differences in PEM CAPEX.**
- IEA: system + electrical + gas treatment + BoP + EPC.
- EHO 2025: stack + BoP + other utilities + other CAPEX (land, grid fees, permitting, contingency, EPC management).
- Clean Hydrogen JU SRIA 2030 targets (500 €/kW; O&M 21 €/(kg/d)/yr ≈ 9.2 €/kW/yr at 55 kWh/kg) exclude installation. They are **not** used as the low value.
- JRC CETO 2025 reports large European projects at 2 630–3 050 €/kW (TNO 2024), above the TFN high. Use it for a stress case.
- The DEA 2026 electrolysis update states that PEMEC costs were underestimated before; its figures could not be read as text.
- EHO OPEX may include stack replacement, so do not add row 3.4 on top of the EHO-based O&M.

**N10. WACC.** Model in real EUR or USD terms. A TRY-nominal WACC would embed Turkish inflation and is not comparable. IRENA 2023 (*The cost of financing for renewable power*) lists Türkiye in its survey, but only in figures, so no numeric value could be extracted.

---

## 4. Parameters not (fully) sourced or weakly sourced

1. **Türkiye-specific PEM, compressor, pipeline and tube-trailer costs.** None found; EU and US values used.
2. **Hydrogen injection/withdrawal rates at Tuz Gölü.** No published H₂ value; derived from NG design rates (rows 5.7–5.8).
3. **Özarslan (2012) Tuz Gölü-specific H₂ capacity.** The full text gives a generic estimate of about 6 million kg of working H₂ gas for a representative salt cavern, but does not report a numeric capacity for Tuz Gölü. The generic estimate is not used as a model input.
4. **Şan (2019) MSc thesis.** Verified record: Şan, S. (2019), *Tuz domlarında hidrojen depolama yöntemlerinin incelenmesi*, MSc thesis, Çukurova University, Institute of Natural and Applied Sciences, Dept. of Physics; YÖK National Thesis Centre No. 571921, 134 pp.; supervisor Prof. Dr. Mehmet Karakılçık. The thesis itself was not read; its summary article on the Ç.Ü. FBE site (Şan & Karakılçık, p. 80 ff.; journal, volume and year not printed in the PDF) was read in full and contains the 2.5 TWh / 12-cavern result. The manuscript cites the thesis. General salt-cavern context: Karakılçık, H., Karakılçık, M. (2020), Underground large-scale hydrogen storage, in: Uyar, T.S. (Ed.), Accelerating the Transition to a 100% Renewable Energy Era, Lecture Notes in Energy 74, Springer, pp. 375–392, doi:10.1007/978-3-030-40738-4_17.
5. **Full hourly PTF profile.** Not retrieved; only hour-of-day extremes (2024) and time-band factors (Sept 2025).
6. **Numeric Türkiye WACC from IRENA/IEA.** Figure only. The mode rests on SHURA's assumption, the high on a 2017-data estimate.
7. **PEM capital-cost mode.** Relies on a press report (Argus) of IEA STEPS figures, not the IEA document itself.
8. **Original DEA datasheets.** Values taken from the PyPSA compilation (secondary); DEA's own uncertainty bounds were not obtained.
9. **Battery integrated-system lifetime mode (15 yr) and battery fixed O&M.** Not sourced.
10. **Levelised pipeline cost below ~150 kt/yr.** Not found.
11. **Lazard.** Not consulted.

---

## 5. Additional inputs used in `params.yaml` (added 2026-10-18)

| Item | Value | Source | Evidence |
|---|---|---|---|
| Wind capacity density (total project area) | 3.0 MW/km² (34 ± 22 ha/MW) | Denholm, Hand, Jackson & Ong 2009, NREL/TP-6A2-45834, doi:10.2172/964608 | FT (Table 1 and Conclusions) |
| PV capacity density (total area) | 31 MWac/km² | Ong et al. 2013, NREL/TP-6A20-56290, doi:10.2172/1086349 | FT (already in the hard-criteria review) |
| Green-hydrogen share of on-purpose demand, ammonia nodes | (0.336, 0.42, 0.60) | Directive (EU) 2023/2413, Art. 22a (42 % by 2030, 60 % by 2035) and Art. 22b (reduction to 33.6 % in 2030); Commission guidance C/2025/2983 | FT (EUR-Lex guidance text) |
| National cross-check | 2 GW electrolysers by 2030, 5 GW by 2035, 70 GW by 2053 | MENR 2023, *Türkiye Hydrogen Technologies Strategy and Roadmap* (ETKB_Hydrogen_T_Strategies.pdf); IEA policy record 17216 | FT |
| Minimum electrolyser size if a site is opened | 50 MW | MENR 2023 roadmap, Fig. 3 (50–500 MW class for 2030) | Ex |
| Tube-trailer intercept (distance-independent, excl. compression) | (0.43, 0.74, 0.90) €/kg | Intercepts of the three cost lines in Note N6: DESNZ £0.78 @0.86979; Reddi $0.80 @1.0824; Reuß $0.47 @1.0824 | D |
| Tuz Gölü coordinates | 38.0966 N, 33.5865 E | Google Places record "BOTAŞ Tuz Gölü Doğal Gaz Depolama Tesisi" (Sultanhanı), via Exa; consistent with BOTAŞ "40 km south of Tuz Gölü" | Ex |

| RPP demand-violation penalty δ, ammonia nodes | 5.63 €/kg H₂-eq | H2Global pilot auction (Lot 1, Fertiglobe): renewable ammonia delivered to EU ports at 1 000 €/t (net FOB 811 €/t), https://hintco.eu/lot-1-renewable-ammonia/ ; ÷ 0.1776 t H₂/t NH₃. Excludes cracking | FT |
| Green-hydrogen share of on-purpose demand, refinery nodes (V4) | (0.158, 0.198, 0.395) | RED III Art. 25(1)(b) transport sub-target applied to TÜİK 2024 transport final energy (road, rail, domestic maritime); Note N11 | Ex (secondary summaries of the directive) / FT (TÜİK figures) |
| RPP demand-violation penalty δ, refinery nodes (V4) | 7.30 €/kg | Cracked RFNBO hydrogen landed in Europe, $7.50–9.00/kg (S&P Global Commodity Insights, 9 Jun 2025) at 1.1300 USD/EUR (ECB 2025 average); Note N15 | Ex |
| New pipeline CAPEX and capacity, 12″ (V4) | (1.045, 1.12, 1.344) M€/km; 222 t/d | Extrapolated from the EHB 2022 20″/36″/48″ classes; mode confirmed by DEA 2025 datasheet (1.14 M€/km); Note N12 | D |
| Trailer operating hours per year (V4) | 6 000 h (sensitivity 4 400 / 8 000) | Modelling assumption (two-shift operation) for the trip-feasibility correction; Note N13 | – |
| Trailer refill compression at the cavern (V4) | row 7.6 energy; rows 4.4–4.6 compressor | Note N14 | FT |

Modelling choices that are not literature values (sensitivity-tested): RPP weight γ = 0.2, Me parameter λ = 0.5, export connection ≤ electrolyser capacity, renewable plants co-located within the candidate's 0.1° cell (cluster level reported as a second baseline), modal demand supplied domestically (security-of-supply mandate; import diagnostic reported), trailer operating hours.

## 6. V4 additions (10 November 2026)

**N11. Sector-specific renewable share of demand.**
- Ammonia plants fall under the RED III industry target (Art. 22a): 33.6 % (Art. 22b reduced 2030 target) / 42 % (2030) / 60 % (2035).
- Hydrogen used in refineries as an intermediate for conventional transport fuels is excluded from the Art. 22a denominator "as it is covered by the transport target" (Hydrogen Europe, RED III position paper, June 2024, p. 3). The transport target (Art. 25(1)(b)) requires a combined 5.5 % share of advanced biofuels and RFNBOs in 2030, of which at least 1 percentage point RFNBO; RFNBOs count at twice their energy content outside aviation and maritime (Clean Hydrogen Observatory, RED page, Dec 2025).
- Turkish transport final energy 2024 (TÜİK, Ulaştırma Sektörü Nihai Enerji Tüketim İstatistikleri 2024, released 27 March 2026): road 1 103 279 TJ, rail 10 358 TJ, domestic maritime 11 020 TJ, aviation 287 106 TJ (84.5 % international). Aviation is excluded from the base because its international share and the 1.5 multiplier make it ambiguous, and because aviation fuels fall under the separate ReFuelEU obligation: 1 124 657 TJ.
- Mode: 1 % × 1 124.7 PJ / 2 (multiplier) = 5.623 PJ → 46.9 kt H₂ at 120 MJ/kg LHV.
- High: the same without the multiplier (the reading Hydrogen Europe recommends for the sub-target, guidance note 2025, Rec. 9): 93.7 kt.
- Low: 0.8 × mode = 37.5 kt, mirroring the 33.6/42 ratio of the industry target (a symmetry assumption).
- Shares of the 237 kt refinery on-purpose demand: 0.1582 / 0.1977 / 0.3954. The derivation assumes that the national transport RFNBO sub-target is met through refinery hydrogen, which is an upper estimate of the refinery role.
- Baseline modal demand: ammonia 0.42 × 138.9 kt = 58.3 kt + refineries 46.9 kt = 105.2 kt (v3: 157.9 kt); possibility range 84.2–177.0 kt.

**N12. 12-inch pipeline class.** EHB 2022 medium new-pipeline CAPEX: 20″ 1.5, 36″ 2.2, 48″ 2.8 M€/km (rows 6.1–6.3). A least-squares line in diameter gives 0.0463 M€/km per inch and 1.12 M€/km at 12″; the low/high vertices are the 20″ vertices scaled by 1.12/1.5 → 1.045 / 1.12 / 1.344 M€/km. Capacity: a log-log fit to the EHB design capacities (1.2 / 4.7 / 13 GW) gives an exponent of 2.66; anchored at 20″ (1.2 GW), 12″ = 0.31 GW = 222 t/d. Evidence level D: extrapolated below the smallest EHB class. Check (10 Nov 2026): the Danish Energy Agency technology brief (July 2025, Fig. 1, 20 m/s velocity limit) gives about 1 GW at 12" and 70 bar, i.e. a 12"/20" capacity ratio of about 0.38 against 0.26 here; a run with 311 t/d (D² scaling of the 20" class) leaves the design unchanged (9.96 €/kg, tag pipe12_cap311). The brief gives no cost figures; costs are in the catalogue datasheets. Its truck cost curve (about 0.18 €/kg + 0.31 €/kg per 100 km, 0–300 km) is close to row 7.5 (mode 0.35 €/kg per 100 km), and it states that road transport only makes sense below 200–300 km.
- *DEA datasheet check (10 Nov 2026).* Technology Data for Energy Transport, data sheet version 8 (2025 prices), sheets 4.1–4.3: new 12″ line 1.14 M€/km (lower 0.798, upper 1.71; Class 5 range −30 %/+50 %, note F) at 40 and 90 barg, 1.23 at 140 barg; 20″ 1.41 (40 barg) / 1.76 (90 barg) / 2.10 (140 barg). PLR and LV stations are included (about 20 % of the figure, note F). Additional costs for construction management and owner's costs, 35 % (30–40 %) of investment, "need to be added on top" (note G). Fixed O&M 1 %/yr, lifetime 50 yr, booster compressor stations 1.2 M€/MWe. Capacity at 20 m/s and full utilisation: 12″ 600 MW at 40 barg (= 432 t/d), 1 200 MW at 90 barg; 20″ 1 600 / 3 300 MW. The EHB reports do not state whether owner's costs are included ("pipeline (including gas metering) capex"), so the 35 % cannot be assigned unambiguously.
- *Decision:* the EHB-based values are kept as baseline; the DEA mode (1.14) confirms ours (1.12), and the DEA 12″/20″ cost ratio (0.81 at 40 barg, 0.65 at 90 barg) brackets ours (0.75). Two sensitivity runs: `pipe12_dea` (12″ triangle 0.798/1.14/1.71, 432 t/d) → 10.09 €/kg, Tuz Gölü→Aliağa line replaced by trailers, trailer share of final deliveries 39 %; `pipe_capex135` (both diameters ×1.35) → 10.45 €/kg, Aliağa and Kırklareli→Gemlik lines replaced, trailer share 60 %. The Karaman–Tuz Gölü–Körfez spine is built in every run. The cost is robust (+1.3 %, +4.9 %); the modal split is not.

**N13. Long-haul trailer correction.** The levelised trailer lines (row 7.5) assume about 300 trips per trailer and year (DESNZ 2023). A round trip takes 2L/v + t_lu (v = 50 km/h, t_lu = 4 h, as in N6). With H = 6 000 operating hours per year (two-shift operation; sensitivity 4 400 and 8 000 h), a trailer makes n(L) = min(300, H/(2L/v + t_lu)) trips, which binds above L = 400 km. The extra trailer capital per kg delivered is A_tr (1/n(L) − 1/300), with A_tr the annualised trailer CAPEX plus 5 %/yr O&M per kg payload (rows 7.2, 7.3; WACC row 8.1). Driver time and fuel per km are already in the distance term.

**N14. Trailer refilling at the cavern.** Hydrogen withdrawn from Tuz Gölü and dispatched by trailer is compressed to 500 bar on grid electricity. The 30 → 500 bar energy of row 7.6 (mode 2.41 kWh/kg) is used as a conservative upper value, because withdrawal pressure exceeds 30 bar. Compressor CAPEX and O&M follow rows 4.4–4.6; the electricity is charged at the day-ahead price and counted in the RFNBO emission check at the grid factor.

**N15. Sector-specific import parity δ.** Ammonia nodes: 5.63 €/kg H₂-equivalent (H2Global Lot 1, unchanged). Refinery nodes need gaseous hydrogen: RFNBO-compliant hydrogen landed in Europe after ammonia cracking costs $7.50–9.00/kg (S&P Global Commodity Insights, 9 June 2025, https://www.spglobal.com/commodity-insights/en/news-research/latest-news/energy-transition/060925-ammonia-cracking-costs-emissions-key-to-hydrogens-competitiveness-in-europe). At the ECB 2025 average of 1.1300 USD/EUR this is 6.64–7.96 €/kg; the midpoint 7.30 €/kg is used. Merged nodes weight the penalty by each facility's demand range.
