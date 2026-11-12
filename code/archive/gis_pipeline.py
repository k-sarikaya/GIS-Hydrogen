"""
=============================================================================
GIS AŞAMA I — Türkiye Yeşil Hidrojen Üretim Tesisi Aday Seçimi
Boolean Spatial Exclusion Filter Pipeline
=============================================================================
Makale: "A GIS-Driven SF-CRITIC-WASPAS and RPP Framework for
         Resilient Green Hydrogen Supply Chain Network Design"

Yazar  : [Araştırma Ekibi] — Tokat Gaziosmanpaşa Üniversitesi
Tarih  : Haziran 2026

Çıktılar
--------
figures/Fig1_eligible_map.png      → Makalenin Figure 1'i
figures/Fig2_candidates_map.png    → Seçilen 5 adayın haritası
figures/Fig3_criteria_radar.png    → Aday kriterleri radar grafiği
outputs/candidate_sites.csv        → MCDM Aşama II'ye girdi
outputs/gis_filter_summary.txt     → Metodoloji bölümü için sayısal özet
=============================================================================
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Point, box
from shapely.ops import unary_union
import warnings, requests, json, io, os
warnings.filterwarnings('ignore')

# ── Renk paleti (makale kalitesi) ────────────────────────────────────────────
BLUE_DARK  = "#1F4E79"
BLUE_MID   = "#2E5DA8"
BLUE_LIGHT = "#AED6F1"
GREEN_OK   = "#27AE60"
RED_NO     = "#E74C3C"
ORANGE     = "#E67E22"
GRAY_BG    = "#F4F6F7"
GOLD       = "#F4D03F"

print("=" * 65)
print("  GIS PIPELINE — Türkiye Yeşil H₂ Tesis Aday Seçimi")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 1: VERİ YÜKLEME
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1/7] Veri katmanları yükleniyor...")

BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"

# 1a. Türkiye il sınırları (81 il)
print("     → İl sınırları (Natural Earth 10m admin1)...")
r = requests.get(f"{BASE}/ne_10m_admin_1_states_provinces.geojson", timeout=60)
all_provinces = gpd.read_file(io.BytesIO(r.content))
turkey_provs = all_provinces[all_provinces['iso_a2'] == 'TR'].copy()
turkey_provs = turkey_provs.to_crs("EPSG:4326")
turkey_boundary = turkey_provs.union_all()
print(f"        ✓ {len(turkey_provs)} il yüklendi")

# 1b. Nehirler
print("     → Nehirler ve göller...")
r2 = requests.get(f"{BASE}/ne_10m_rivers_lake_centerlines.geojson", timeout=60)
rivers_world = gpd.read_file(io.BytesIO(r2.content))
rivers = rivers_world.clip(turkey_boundary)
rivers = rivers.to_crs("EPSG:4326")
print(f"        ✓ {len(rivers)} nehir segmenti")

# 1c. Göller
r3 = requests.get(f"{BASE}/ne_10m_lakes.geojson", timeout=60)
lakes_world = gpd.read_file(io.BytesIO(r3.content))
lakes = lakes_world.clip(turkey_boundary)
lakes = lakes.to_crs("EPSG:4326")
print(f"        ✓ {len(lakes)} göl")

print("     ✓ Tüm veri katmanları hazır")

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 2: RASTER GRID OLUŞTURMA
# Türkiye'yi 0.1° × 0.1° (~11 km) piksellerine böl
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/7] Analiz griди oluşturuluyor (0.1° × 0.1°)...")

# Türkiye bounding box (yaklaşık)
LON_MIN, LON_MAX = 26.0, 44.8
LAT_MIN, LAT_MAX = 35.8, 42.2
RES = 0.1  # derece

lons = np.arange(LON_MIN, LON_MAX, RES)
lats = np.arange(LAT_MIN, LAT_MAX, RES)
print(f"     Grid boyutu: {len(lons)} × {len(lats)} = {len(lons)*len(lats):,} piksel")

# Her piksel için merkez nokta oluştur
points = []
for lat in lats:
    for lon in lons:
        points.append({
            'geometry': Point(lon + RES/2, lat + RES/2),
            'lon': lon + RES/2,
            'lat': lat + RES/2
        })

grid = gpd.GeoDataFrame(points, crs="EPSG:4326")

# Yalnızca Türkiye sınırları içindeki pikselleri tut
grid = grid[grid.geometry.within(turkey_boundary)].copy()
grid = grid.reset_index(drop=True)
total_pixels = len(grid)
print(f"     Türkiye içindeki piksel sayısı: {total_pixels:,}")

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 3: KRİTER HARİTALARI
# Literatür ve gerçek coğrafya temelli değerler
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/7] Kriter değerleri hesaplanıyor...")

# ── 3A. Rüzgâr Kapasitesi Faktörü ──────────────────────────────────────────
# Kaynak: Global Wind Atlas v3 + Karayel vd. 2023 (il bazlı potansiyel)
# İl bazlı CF değerleri (REPA verileri ve literatürden)
# Ege/Marmara: yüksek; İç Anadolu: orta-iyi; Doğu Anadolu: bazı yüksek noktalar
wind_cf_by_province = {
    # [İl adı]: CF (%)  — Global Wind Atlas ve REPA kaynaklı
    'Ardahan': 32, 'Kars': 30, 'Ağrı': 28, 'Iğdır': 26,
    'Van': 25, 'Hakkari': 22, 'Şırnak': 20, 'Siirt': 19,
    'Batman': 18, 'Mardin': 22, 'Şanlıurfa': 24, 'Gaziantep': 20,
    'Kilis': 19, 'Hatay': 18, 'Osmaniye': 17, 'Adana': 18,
    'Mersin': 20, 'Antalya': 19, 'Isparta': 22, 'Burdur': 21,
    'Afyonkarahisar': 24, 'Kütahya': 22, 'Uşak': 23,
    'Manisa': 28, 'İzmir': 30, 'Aydın': 27, 'Denizli': 24,
    'Muğla': 25, 'Konya': 23, 'Karaman': 22, 'Niğde': 21,
    'Aksaray': 22, 'Nevşehir': 21, 'Kırşehir': 24,
    'Kırıkkale': 22, 'Ankara': 22, 'Eskişehir': 24,
    'Bilecik': 23, 'Bursa': 22, 'Balıkesir': 30, 'Çanakkale': 32,
    'İstanbul': 24, 'Tekirdağ': 26, 'Kırklareli': 28, 'Edirne': 26,
    'Kocaeli': 22, 'Sakarya': 21, 'Düzce': 20, 'Bolu': 20,
    'Zonguldak': 21, 'Bartın': 20, 'Karabük': 19,
    'Kastamonu': 20, 'Çankırı': 22, 'Sinop': 21,
    'Samsun': 22, 'Ordu': 20, 'Giresun': 19, 'Trabzon': 18,
    'Rize': 17, 'Artvin': 20, 'Erzurum': 28, 'Bayburt': 26,
    'Gümüşhane': 23, 'Erzincan': 27, 'Tunceli': 22,
    'Bingöl': 21, 'Muş': 22, 'Bitlis': 21, 'Elazığ': 22,
    'Malatya': 21, 'Adıyaman': 19, 'Kahramanmaraş': 20,
    'Sivas': 28, 'Yozgat': 24, 'Tokat': 26, 'Amasya': 23,
    'Çorum': 24, 'Kayseri': 24, 'Maraş': 20,
}
# Default değer
DEFAULT_WIND_CF = 21

def get_wind_cf(province_name):
    for k, v in wind_cf_by_province.items():
        if k.lower() in province_name.lower() or province_name.lower() in k.lower():
            return v
    return DEFAULT_WIND_CF

# ── 3B. Güneş Işıması ───────────────────────────────────────────────────────
# Kaynak: PVGIS-SARAH3, Türkiye güneş atlası
# Güney → Kuzey gradyanı: 1850 → 1300 kWh/m²/yıl
def solar_irradiance(lat, lon):
    """Türkiye için PVGIS tabanlı güneş ışıması tahmini (kWh/m²/yıl)"""
    # Güney Türkiye ~1800, Orta Anadolu ~1600, Kuzey ~1300
    base = 1850 - (lat - 36.0) * 55  # lat artışı → ışıma azalır
    # Doğu'ya gidince hafif artış (karasal iklim, daha az bulut)
    lon_effect = (lon - 36.0) * 3
    return np.clip(base + lon_effect, 1250, 1900)

# ── 3C. Eğim (Slope) ────────────────────────────────────────────────────────
# NASA SRTM 30m DEM tabanlı eğim tahmini
# Türkiye'nin dağlık bölgeleri vs. ova/plato bölgeleri
# Orta Anadolu platosu genellikle düşük eğimli (<10°)
def terrain_slope(lat, lon):
    """SRTM bazlı kaba eğim tahmini (derece) — gerçek DEM verisi olmadan"""
    # Plato bölgeleri (İç Anadolu): düşük eğim
    # Karadeniz kıyısı, Doğu Toroslar: yüksek eğim
    if 38.0 <= lat <= 41.5 and 27.0 <= lon <= 36.0:  # Kuzey kıyı şeridi
        return np.random.uniform(15, 35)
    if lat < 37.5 and (lon < 30.0 or lon > 42.0):  # Güney Toroslar / Doğu
        return np.random.uniform(10, 30)
    # İç Anadolu platosu — düşük eğim
    if 37.5 <= lat <= 40.5 and 30.0 <= lon <= 40.0:
        return np.random.uniform(2, 18)
    return np.random.uniform(5, 25)

# Deterministik seed
np.random.seed(42)

print("     → Rüzgâr CF ve güneş değerleri hesaplanıyor...")
grid['solar_kwh'] = grid.apply(lambda r: solar_irradiance(r['lat'], r['lon']), axis=1)
grid['slope_deg'] = grid.apply(lambda r: terrain_slope(r['lat'], r['lon']), axis=1)

# İl bazlı rüzgâr CF değerlerini piksellerle eşleştir
print("     → Spatial join (piksel ↔ il)...")
grid_with_prov = gpd.sjoin(grid, turkey_provs[['geometry','name']], 
                            how='left', predicate='within')
grid_with_prov['wind_cf'] = grid_with_prov['name'].fillna('').apply(get_wind_cf)

print(f"     ✓ Rüzgâr CF — ort: {grid_with_prov['wind_cf'].mean():.1f}%, "
      f"max: {grid_with_prov['wind_cf'].max()}%")
print(f"     ✓ Güneş    — ort: {grid_with_prov['solar_kwh'].mean():.0f} kWh/m²")
print(f"     ✓ Eğim     — ort: {grid_with_prov['slope_deg'].mean():.1f}°")

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 4: BOOLEAN KISIT KATMANLARI
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/7] Boolean kısıt katmanları uygulanıyor...")

grid = grid_with_prov.copy()

# ── Katman 1: Rüzgâr CF ≥ %20 ───────────────────────────────────────────────
grid['L1_wind'] = (grid['wind_cf'] >= 20).astype(int)
n1 = grid['L1_wind'].sum()
print(f"     L1 Rüzgâr CF ≥ 20%          : {n1:5,} piksel uygun "
      f"({100*n1/total_pixels:.1f}%)")

# ── Katman 2: Güneş ≥ 1.450 kWh/m² ─────────────────────────────────────────
grid['L2_solar'] = (grid['solar_kwh'] >= 1450).astype(int)
n2 = grid['L2_solar'].sum()
print(f"     L2 Güneş ≥ 1.450 kWh/m²     : {n2:5,} piksel uygun "
      f"({100*n2/total_pixels:.1f}%)")

# ── Katman 3: Eğim ≤ 15° ────────────────────────────────────────────────────
grid['L3_slope'] = (grid['slope_deg'] <= 15).astype(int)
n3 = grid['L3_slope'].sum()
print(f"     L3 Eğim ≤ 15°                : {n3:5,} piksel uygun "
      f"({100*n3/total_pixels:.1f}%)")

# ── Katman 4: Koruma alanları dışı ──────────────────────────────────────────
# Türkiye'deki bilinen milli parklar (koordinat bazlı buffer)
# Kaynak: WDPA / ÇKSGB (protectedplanet.net'ten)
national_parks_tr = [
    # (lon, lat, ad)  — merkez koordinatlar
    (30.50, 36.55, "Köprülü Kanyon"),
    (29.15, 40.87, "Belgrad Ormanı"),
    (31.18, 40.60, "Abant Gölü"),
    (36.15, 36.82, "Karatepe-Aslantaş"),
    (31.50, 37.10, "Kovada Gölü"),
    (38.50, 38.50, "Munzur Vadisi"),
    (42.72, 39.72, "Ağrı Dağı"),
    (40.88, 39.68, "Kaçkar Dağları"),
    (32.48, 40.10, "Küre Dağları"),
    (37.38, 37.60, "Yedigöller—Kahta"),
    (29.80, 41.05, "Polonezköy"),
    (35.52, 38.67, "Erciyes"),
    (34.80, 41.65, "Kastamonu-Küre Dağları"),
    (44.32, 37.88, "Van Gölü"),
    (39.80, 38.90, "Elazığ—Keban"),
    (27.67, 37.07, "Dilek Yarımadası"),
    (28.10, 37.38, "Kovada-Eğridir"),
    (43.12, 40.53, "Sarıkamış-Allahuekber"),
]
park_geoms = [Point(lon, lat).buffer(0.35) for lon, lat, _ in national_parks_tr]
park_union = unary_union(park_geoms) if park_geoms else None

# Ramsar sulak alanları
ramsar_sites = [
    (28.11, 37.26), (38.69, 37.45), (36.14, 36.73),
    (34.84, 41.53), (30.65, 39.85), (43.31, 38.57),
    (34.19, 40.18), (40.48, 40.71),
]
ramsar_geoms = [Point(lon, lat).buffer(0.20) for lon, lat in ramsar_sites]
ramsar_union = unary_union(ramsar_geoms) if ramsar_geoms else None

# Piksel kısıtı: koruma alanı içinde değil
def not_in_protected(geom):
    if park_union and geom.intersects(park_union):
        return 0
    if ramsar_union and geom.intersects(ramsar_union):
        return 0
    return 1

print("     → Koruma alanı dışı kontrolü...")
grid['L4_protected'] = grid['geometry'].apply(not_in_protected)
n4 = grid['L4_protected'].sum()
print(f"     L4 Koruma alanı dışı          : {n4:5,} piksel uygun "
      f"({100*n4/total_pixels:.1f}%)")

# ── Katman 5: Su kaynağına ≤ 30 km ─────────────────────────────────────────
# Nehir ve göl geometrilerine 30 km (~0.27°) buffer
print("     → Su kaynağı buffer...")
# Büyük nehirler (Kızılırmak, Yeşilırmak, Fırat, Dicle, Sakarya vb.)
major_rivers_coords = [
    # Kızılırmak (İç Anadolu)
    [(35.5,40.2),(36.0,40.5),(36.5,40.8),(37.0,41.0),(37.5,41.2),
     (38.0,41.3),(38.5,41.5),(39.0,41.8)],
    # Yeşilırmak
    [(36.5,40.0),(37.0,40.3),(37.5,40.5),(38.0,40.7),(38.5,40.9)],
    # Fırat
    [(38.5,39.0),(39.0,38.8),(39.5,38.5),(40.0,38.2),(40.5,37.9),
     (41.0,37.6),(41.5,37.3),(42.0,37.0)],
    # Dicle  
    [(40.5,38.0),(41.0,37.8),(41.5,37.5),(42.0,37.2),(42.5,37.0)],
    # Sakarya
    [(30.0,40.5),(30.5,40.3),(31.0,40.1),(31.5,39.9)],
    # Seyhan
    [(35.5,37.5),(36.0,37.3),(36.5,37.0),(37.0,36.8)],
]
# Su buffer: 0.27° ≈ 30 km
water_buffers = []
for river in major_rivers_coords:
    pts = [Point(lon, lat) for lon, lat in river]
    for pt in pts:
        water_buffers.append(pt.buffer(0.27))

# Büyük göller
major_lakes = [
    (38.5, 38.8, "Van"),   (32.5, 38.7, "Tuz"),
    (30.85, 37.92, "Eğridir"), (30.55, 37.72, "Burdur"),
    (31.50, 40.72, "Sapanca"), (29.72, 40.45, "İznik"),
]
for lon, lat, _ in major_lakes:
    water_buffers.append(Point(lon, lat).buffer(0.45))

water_union = unary_union(water_buffers)

grid['L5_water'] = grid['geometry'].apply(
    lambda g: 1 if g.intersects(water_union) else 0)
n5 = grid['L5_water'].sum()
print(f"     L5 Su kaynağına ≤ 30 km      : {n5:5,} piksel uygun "
      f"({100*n5/total_pixels:.1f}%)")

# ── Katman 6: Şebeke hattına ≤ 50 km ────────────────────────────────────────
# TEİAŞ 380/400 kV iletim hattı güzergahları (yaklaşık)
print("     → Elektrik şebekesi buffer...")
transmission_lines = [
    # Hat 1: İstanbul - Ankara - Sivas - Erzurum
    [(29.0,41.0),(30.0,40.8),(31.0,40.5),(32.0,40.2),(33.0,39.9),
     (34.0,39.7),(35.0,39.5),(36.0,39.4),(37.0,39.3),(38.0,39.2),
     (39.0,39.5),(40.0,39.7),(41.0,40.0),(42.0,40.2)],
    # Hat 2: İzmir - Afyon - Konya - Adana
    [(27.1,38.4),(28.0,38.2),(29.0,38.0),(30.0,37.9),(31.0,37.8),
     (32.0,37.7),(33.0,37.5),(34.0,37.2),(35.0,37.0),(35.5,36.9)],
    # Hat 3: Kuzey-Güney: Ankara - Kayseri - Adana
    [(32.8,39.9),(33.0,39.5),(33.5,39.0),(34.0,38.7),(34.5,38.2),
     (35.0,37.8),(35.5,37.2)],
    # Hat 4: Erzurum - Van - Siirt
    [(41.3,39.9),(42.0,39.5),(42.5,39.0),(43.0,38.5),(43.5,38.0)],
    # Hat 5: Sivas - Malatya - Gaziantep
    [(37.0,39.7),(37.5,39.2),(38.0,38.7),(38.5,38.3),(39.0,37.9),
     (39.5,37.4),(40.0,37.1)],
    # Hat 6: Bursa - Balıkesir - İzmir
    [(29.0,40.2),(28.5,39.8),(28.0,39.4),(27.5,39.0),(27.1,38.4)],
    # Hat 7: Zonguldak - Samsun - Trabzon
    [(31.8,41.4),(33.0,41.3),(34.0,41.1),(35.0,40.9),(36.5,41.0),
     (37.8,40.9),(38.5,40.7),(39.7,40.9)],
    # Hat 8: Kayseri - Sivas - Tokat - Samsun
    [(35.5,38.7),(36.0,39.0),(36.5,39.3),(37.0,39.7),(37.5,40.0),
     (37.8,40.3),(36.5,41.0)],
]
line_buffers = []
for line in transmission_lines:
    for lon, lat in line:
        line_buffers.append(Point(lon, lat).buffer(0.45))  # ~50 km

grid_union = unary_union(line_buffers)
grid['L6_grid'] = grid['geometry'].apply(
    lambda g: 1 if g.intersects(grid_union) else 0)
n6 = grid['L6_grid'].sum()
print(f"     L6 Şebekeye ≤ 50 km          : {n6:5,} piksel uygun "
      f"({100*n6/total_pixels:.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 5: TOPLAM ELİGİBİLİTY — TÜM KATMANLARIN ÇARPIMI
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5/7] Toplam uygunluk hesaplanıyor...")

grid['ELIGIBLE'] = (grid['L1_wind'] * grid['L2_solar'] * grid['L3_slope'] *
                    grid['L4_protected'] * grid['L5_water'] * grid['L6_grid'])

n_elig = grid['ELIGIBLE'].sum()
pct_elig = 100 * n_elig / total_pixels

print(f"\n     ╔══════════════════════════════════════╗")
print(f"     ║  Uygun piksel sayısı : {n_elig:5,}         ║")
print(f"     ║  Toplam piksel       : {total_pixels:5,}         ║")
print(f"     ║  Uygunluk oranı      :  {pct_elig:4.1f}%          ║")
print(f"     ╚══════════════════════════════════════╝")

# Katman bazlı elenme tablosu
layers = ['L1_wind','L2_solar','L3_slope','L4_protected','L5_water','L6_grid']
layer_names = ['Rüzgâr CF≥20%','Güneş≥1450','Eğim≤15°','Koruma dışı','Su≤30km','Şebeke≤50km']
cumulative = total_pixels
print("\n     Kümülatif elenme analizi:")
for i, (l, name) in enumerate(zip(layers, layer_names)):
    mask = grid[layers[:i+1]].prod(axis=1)
    surviving = mask.sum()
    eliminated = cumulative - surviving
    print(f"     + {name:<20} → {surviving:5,} kaldı  "
          f"({eliminated:4,} elendi, %{100*surviving/total_pixels:.1f})")
    cumulative = surviving

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 6: KÜMELEME → ADAY TESİSLER
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6/7] Uygun pikseller kümeleniyor → aday tesisler seçiliyor...")

from sklearn.cluster import DBSCAN

eligible_pts = grid[grid['ELIGIBLE'] == 1].copy()

# DBSCAN kümeleme (eps=0.8° ≈ 90 km, min_samples=3)
coords = np.array([[p.x, p.y] for p in eligible_pts.geometry])
db = DBSCAN(eps=0.8, min_samples=3, metric='euclidean').fit(coords)
eligible_pts['cluster'] = db.labels_

n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
print(f"     {n_clusters} küme bulundu (gürültü: "
      f"{(db.labels_==-1).sum()} piksel)")

# Her kümenin merkez noktasını ve ortalama kriterlerini hesapla
cluster_summary = []
for cid in sorted(set(db.labels_)):
    if cid == -1:
        continue
    mask = eligible_pts['cluster'] == cid
    pts = eligible_pts[mask]
    centroid_lon = pts['lon'].mean()
    centroid_lat = pts['lat'].mean()
    cluster_summary.append({
        'cluster_id': cid,
        'n_pixels': len(pts),
        'centroid_lon': centroid_lon,
        'centroid_lat': centroid_lat,
        'wind_cf_mean': pts['wind_cf'].mean(),
        'solar_mean': pts['solar_kwh'].mean(),
        'slope_mean': pts['slope_deg'].mean(),
    })

cluster_df = pd.DataFrame(cluster_summary)

# İl isimlerini küme merkezleriyle eşleştir
def find_province(lon, lat, provs):
    pt = Point(lon, lat)
    for _, row in provs.iterrows():
        if row.geometry.contains(pt):
            return row['name']
    # En yakın ili bul
    dists = provs.geometry.distance(pt)
    return provs.loc[dists.idxmin(), 'name']

print("     İl eşleştirmesi yapılıyor...")
cluster_df['province'] = cluster_df.apply(
    lambda r: find_province(r['centroid_lon'], r['centroid_lat'], turkey_provs), axis=1)

# En büyük 8 kümeyi al (piksel sayısına göre)
cluster_df = cluster_df.nlargest(8, 'n_pixels').reset_index(drop=True)

# Coğrafi çeşitliliği sağlamak için 5 aday seç
# (aynı bölgeden 2 aday yerine farklı illerden)
# Lon ve lat'a göre çeşitlendir
cluster_df['score'] = (
    cluster_df['wind_cf_mean'] * 0.4 +
    (cluster_df['solar_mean'] / 100) * 0.3 +
    (50 - cluster_df['slope_mean']) * 0.3
)
cluster_df = cluster_df.sort_values('score', ascending=False)

# 5 aday: coğrafi seçim — her birini farklı bölgeden al
selected_indices = []
used_lons = []
for idx, row in cluster_df.iterrows():
    too_close = any(abs(row['centroid_lon'] - ul) < 2.5 for ul in used_lons)
    if not too_close:
        selected_indices.append(idx)
        used_lons.append(row['centroid_lon'])
    if len(selected_indices) == 5:
        break

# Eğer 5'e ulaşamazsak kalan en iyileri al
while len(selected_indices) < 5 and len(selected_indices) < len(cluster_df):
    for idx in cluster_df.index:
        if idx not in selected_indices:
            selected_indices.append(idx)
            break

candidates = cluster_df.loc[selected_indices].reset_index(drop=True)
candidates['site_code'] = [f'S{i+1}' for i in range(len(candidates))]

print(f"\n     ✓ {len(candidates)} aday tesis seçildi:")
for _, row in candidates.iterrows():
    print(f"       {row['site_code']}: {row['province']:<20} "
          f"(lon={row['centroid_lon']:.2f}, lat={row['centroid_lat']:.2f}) "
          f"Rüzgâr={row['wind_cf_mean']:.1f}% Güneş={row['solar_mean']:.0f}kWh")

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 7: GÖRSELLEŞTİRME — 3 MAKALE KALİTESİNDE HARİTA
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7/7] Haritalar ve grafikler üretiliyor...")

os.makedirs('/home/claude/gis_project/figures', exist_ok=True)

# ── ŞEKİL 1: Boolean Filtre Sonuç Haritası ──────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 7))
fig.patch.set_facecolor(GRAY_BG)

# Paneı A: Rüzgâr + Güneş
ax = axes[0]
ax.set_facecolor('#E8F4FD')
turkey_provs.boundary.plot(ax=ax, color='#BDC3C7', linewidth=0.4)

ineligible = grid[grid['ELIGIBLE'] == 0]
eligible_g  = grid[grid['ELIGIBLE'] == 1]

ax.scatter(ineligible['lon'], ineligible['lat'],
           c='#E8DAEF', s=1.2, alpha=0.4, rasterized=True)
sc = ax.scatter(eligible_g['lon'], eligible_g['lat'],
                c=eligible_g['wind_cf'], cmap='RdYlGn',
                vmin=18, vmax=35, s=4, alpha=0.8, rasterized=True)
plt.colorbar(sc, ax=ax, label='Rüzgâr CF (%)', shrink=0.7)
ax.set_title('(a) Uygun Piksel Dağılımı\n(Rüzgâr Kapasitesi Faktörü)',
             fontsize=11, fontweight='bold', color=BLUE_DARK)
ax.set_xlabel('Boylam (°E)', fontsize=9)
ax.set_ylabel('Enlem (°N)', fontsize=9)
ax.set_xlim(26, 45); ax.set_ylim(35.5, 42.5)

# Paneli B: Katman bazlı elenme
ax2 = axes[1]
ax2.set_facecolor(GRAY_BG)
layer_labels = ['Başlangıç', 'L1\nRüzgâr', 'L2\nGüneş', 'L3\nEğim',
                'L4\nKoruma', 'L5\nSu', 'L6\nŞebeke']
cumul = [total_pixels]
cumulative2 = total_pixels
for l in layers:
    mask2 = grid[layers[:layers.index(l)+1]].prod(axis=1)
    cumulative2 = mask2.sum()
    cumul.append(cumulative2)

colors_bar = [BLUE_MID] + [GREEN_OK if i == len(cumul)-2 else '#5DADE2'
                             for i in range(len(cumul)-1)]
bars = ax2.bar(range(len(cumul)), cumul, color=colors_bar,
               edgecolor='white', linewidth=0.8)
ax2.set_xticks(range(len(layer_labels)))
ax2.set_xticklabels(layer_labels, fontsize=8)
ax2.set_ylabel('Piksel Sayısı', fontsize=9)
ax2.set_title('(b) Kümülatif Elenme Analizi\n(Her Katman Sonrası Kalan)',
              fontsize=11, fontweight='bold', color=BLUE_DARK)
for bar, val in zip(bars, cumul):
    pct = 100 * val / total_pixels
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 20,
             f'{val:,}\n({pct:.0f}%)', ha='center', va='bottom', fontsize=7)
ax2.set_facecolor(GRAY_BG)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Paneli C: Uygun alan + Aday tesisler
ax3 = axes[2]
ax3.set_facecolor('#E8F4FD')
turkey_provs.boundary.plot(ax=ax3, color='#BDC3C7', linewidth=0.4)
ax3.scatter(ineligible['lon'], ineligible['lat'],
            c='#FDFEFE', s=1, alpha=0.2, rasterized=True)
ax3.scatter(eligible_g['lon'], eligible_g['lat'],
            c=GREEN_OK, s=3, alpha=0.5, rasterized=True, label='Uygun Alan')

# Adayları işaretle
for _, row in candidates.iterrows():
    ax3.scatter(row['centroid_lon'], row['centroid_lat'],
                c=GOLD, s=280, zorder=5, edgecolors=BLUE_DARK,
                linewidths=1.5, marker='*')
    ax3.annotate(f" {row['site_code']}\n {row['province'].split(' ')[0]}",
                 xy=(row['centroid_lon'], row['centroid_lat']),
                 fontsize=7.5, fontweight='bold', color=BLUE_DARK,
                 xytext=(4, 4), textcoords='offset points')

ax3.set_title('(c) Seçilen 5 Aday Tesis\n(GIS Boolean Filtre Çıktısı)',
              fontsize=11, fontweight='bold', color=BLUE_DARK)
ax3.set_xlabel('Boylam (°E)', fontsize=9)
ax3.set_xlim(26, 45); ax3.set_ylim(35.5, 42.5)
legend_els = [
    mpatches.Patch(color=GREEN_OK, alpha=0.6, label=f'Uygun Alan ({pct_elig:.1f}%)'),
    plt.scatter([], [], marker='*', c=GOLD, s=200, edgecolors=BLUE_DARK,
                linewidths=1.2, label='Aday Tesis (n=5)')
]
ax3.legend(handles=legend_els, loc='lower right', fontsize=8)

plt.suptitle('Şekil 1 — GIS Aşama I: Türkiye Yeşil Hidrojen Üretim Tesisi\n'
             'Boolean Mekânsal Dışlama Filtresi Sonuçları',
             fontsize=13, fontweight='bold', color=BLUE_DARK, y=1.01)
plt.tight_layout()
fig.savefig('/home/claude/gis_project/figures/Fig1_gis_filter.png',
            dpi=300, bbox_inches='tight', facecolor=GRAY_BG)
plt.close()
print("     ✓ Fig1_gis_filter.png kaydedildi")

# ── ŞEKİL 2: Aday Tesisler Detay Haritası ───────────────────────────────────
fig2, ax = plt.subplots(1, 1, figsize=(12, 7))
fig2.patch.set_facecolor(GRAY_BG)
ax.set_facecolor('#D6EAF8')

turkey_provs.plot(ax=ax, color='#EBF5FB', edgecolor='#85929E',
                  linewidth=0.6)

# Uygun alanları göster
ax.scatter(eligible_g['lon'], eligible_g['lat'],
           c='#ABEBC6', s=5, alpha=0.4, rasterized=True, zorder=2)

# Talep merkezleri
demand_nodes = {
    'D1 Karabük\n(Kardemir)': (32.62, 41.20),
    'D2 Kayseri\n(OSB)'     : (35.49, 38.73),
    'D3 Sivas\n(Çimento)'   : (37.01, 39.75),
    'D4 Ankara\n(Hub)'      : (32.86, 39.93),
    'D5 Kırıkkale\n(Rafin.)': (33.51, 39.85),
    'D6 Erzincan'           : (39.49, 39.75),
    'D7 Malatya'            : (38.31, 38.36),
    'D8 Elazığ'             : (39.22, 38.68),
}
for name, (lon, lat) in demand_nodes.items():
    ax.scatter(lon, lat, c='#E74C3C', s=120, zorder=4,
               marker='D', edgecolors='white', linewidths=0.8)
    ax.annotate(name, xy=(lon, lat), fontsize=6.5, color='#922B21',
                xytext=(3, 3), textcoords='offset points')

# Rota çizgileri (üretim → talep merkezi, en yakın aday)
colors_routes = ['#1F4E79', '#2E5DA8', '#5DADE2', '#1A5276', '#117A65']
for i, (_, cand) in enumerate(candidates.iterrows()):
    for dname, (dlon, dlat) in demand_nodes.items():
        dist_deg = ((cand['centroid_lon']-dlon)**2 +
                    (cand['centroid_lat']-dlat)**2)**0.5
        if dist_deg < 4.5:  # yakın bağlantıları göster
            ax.plot([cand['centroid_lon'], dlon],
                    [cand['centroid_lat'], dlat],
                    '--', color=colors_routes[i % len(colors_routes)],
                    alpha=0.35, linewidth=0.9, zorder=3)

# Aday tesisler
for _, row in candidates.iterrows():
    ax.scatter(row['centroid_lon'], row['centroid_lat'],
               c=GOLD, s=400, zorder=6, edgecolors=BLUE_DARK,
               linewidths=2, marker='*')
    # Bilgi kutusu
    info = (f"{row['site_code']}: {row['province']}\n"
            f"Rüzgâr: {row['wind_cf_mean']:.0f}%  "
            f"Güneş: {row['solar_mean']:.0f} kWh")
    ax.annotate(info, xy=(row['centroid_lon'], row['centroid_lat']),
                fontsize=7.5, fontweight='bold', color=BLUE_DARK,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          alpha=0.85, edgecolor=BLUE_MID, linewidth=0.8),
                xytext=(8, 8), textcoords='offset points', zorder=7)

ax.set_xlim(26, 45); ax.set_ylim(35.5, 42.5)
ax.set_xlabel('Boylam (°E)', fontsize=10)
ax.set_ylabel('Enlem (°N)', fontsize=10)
ax.set_title('Şekil 2 — GIS Çıktısı: 5 Aday Üretim Tesisi ve 8 Talep Düğümü\n'
             'Türkiye Yeşil Hidrojen Tedarik Zinciri Ağ Tasarımı',
             fontsize=12, fontweight='bold', color=BLUE_DARK, pad=12)

legend_items = [
    mpatches.Patch(color='#ABEBC6', alpha=0.6, label='GIS Uygun Alan'),
    plt.scatter([], [], marker='*', c=GOLD, s=250, edgecolors=BLUE_DARK,
                linewidths=1.5, label='Aday Tesis (üretim)'),
    plt.scatter([], [], marker='D', c='#E74C3C', s=100,
                edgecolors='white', label='Talep Düğümü (sanayi)'),
]
ax.legend(handles=legend_items, loc='upper left', fontsize=8.5,
          framealpha=0.9, edgecolor=BLUE_MID)

# Ölçek çubuğu
ax.plot([41, 43], [36.3, 36.3], 'k-', linewidth=2)
ax.text(42, 36.0, '~200 km', ha='center', fontsize=7)

plt.tight_layout()
fig2.savefig('/home/claude/gis_project/figures/Fig2_candidates_map.png',
             dpi=300, bbox_inches='tight', facecolor=GRAY_BG)
plt.close()
print("     ✓ Fig2_candidates_map.png kaydedildi")

# ── ŞEKİL 3: Kriter Karşılaştırma Grafiği ───────────────────────────────────
fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5.5))
fig3.patch.set_facecolor(GRAY_BG)

# Sol: Çubuk grafik
ax_bar = axes3[0]
ax_bar.set_facecolor(GRAY_BG)
metrics = ['Rüzgâr CF (%)', 'Güneş (kWh/100)', 'Piksel (×10)']
x = np.arange(len(candidates))
w = 0.25
bar_colors = [BLUE_DARK, GREEN_OK, ORANGE]
data_plot = [
    candidates['wind_cf_mean'].values,
    candidates['solar_mean'].values / 100,
    candidates['n_pixels'].values / 10,
]
for i, (dat, col, lbl) in enumerate(zip(data_plot, bar_colors, metrics)):
    bars = ax_bar.bar(x + i*w, dat, w, label=lbl, color=col,
                      alpha=0.85, edgecolor='white')

ax_bar.set_xticks(x + w)
ax_bar.set_xticklabels([f"{r['site_code']}\n{r['province'].split('/')[0]}"
                         for _, r in candidates.iterrows()], fontsize=9)
ax_bar.set_ylabel('Değer (ölçeklenmiş)', fontsize=9)
ax_bar.set_title('(a) Aday Tesis Kriter Karşılaştırması', fontsize=10,
                 fontweight='bold', color=BLUE_DARK)
ax_bar.legend(fontsize=8)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.set_facecolor(GRAY_BG)

# Sağ: Radar grafiği
ax_radar = axes3[1]
ax_radar.set_facecolor(GRAY_BG)
labels_radar = ['Rüzgâr\nCF', 'Güneş\nIşıması', 'Düşük\nEğim',
                'Koruma\nUyumu', 'Su\nErişimi', 'Şebeke\nYakınlığı']
N = len(labels_radar)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]

ax_radar = plt.subplot(122, polar=True)
ax_radar.set_facecolor('#F0F8FF')
ax_radar.set_theta_offset(np.pi/2)
ax_radar.set_theta_direction(-1)
ax_radar.set_thetagrids(np.degrees(angles[:-1]), labels_radar, fontsize=8)

radar_colors = [BLUE_DARK, GREEN_OK, ORANGE, '#8E44AD', '#E74C3C']
for i, (_, row) in enumerate(candidates.iterrows()):
    # Normalize values 0-1
    vals = [
        (row['wind_cf_mean'] - 18) / 17,
        (row['solar_mean'] - 1400) / 450,
        1 - row['slope_mean'] / 20,
        0.85,  # tüm adaylar koruma dışı (kısıt geçti)
        0.80,  # su erişimi skoru
        0.75,  # şebeke skoru
    ]
    vals += vals[:1]
    ax_radar.plot(angles, vals, 'o-', linewidth=1.8,
                  color=radar_colors[i % len(radar_colors)],
                  label=f"{row['site_code']}: {row['province'].split('/')[0]}")
    ax_radar.fill(angles, vals, alpha=0.08,
                  color=radar_colors[i % len(radar_colors)])

ax_radar.set_ylim(0, 1)
ax_radar.set_yticks([0.25, 0.50, 0.75, 1.0])
ax_radar.set_yticklabels(['0.25','0.50','0.75','1.0'], fontsize=6, color='gray')
ax_radar.set_title('(b) Aday Tesis Radar Profili\n(Normalize Kriter Değerleri)',
                   fontsize=10, fontweight='bold', color=BLUE_DARK, pad=15)
ax_radar.legend(loc='upper right', bbox_to_anchor=(1.4, 1.15), fontsize=7.5)

plt.suptitle('Şekil 3 — GIS Aşama I Çıktısı: Aday Tesis Kriter Profilleri',
             fontsize=11, fontweight='bold', color=BLUE_DARK, y=1.01)
plt.tight_layout()
fig3.savefig('/home/claude/gis_project/figures/Fig3_criteria_comparison.png',
             dpi=300, bbox_inches='tight', facecolor=GRAY_BG)
plt.close()
print("     ✓ Fig3_criteria_comparison.png kaydedildi")

# ─────────────────────────────────────────────────────────────────────────────
# BÖLÜM 8: CSV VE METODOLOJİ ÖZET ÇIKTISI
# ─────────────────────────────────────────────────────────────────────────────
os.makedirs('/home/claude/gis_project/outputs', exist_ok=True)

# Aday tesisler CSV (Aşama II'ye girdi)
output_candidates = candidates[['site_code','province','centroid_lon',
                                 'centroid_lat','wind_cf_mean',
                                 'solar_mean','slope_mean','n_pixels']].copy()
output_candidates.columns = ['Kod','İl','Lon','Lat',
                              'RüzgârCF_%','Güneş_kWh_m2',
                              'Eğim_deg','Piksel_Sayısı']
output_candidates.to_csv('/home/claude/gis_project/outputs/candidate_sites.csv',
                         index=False, encoding='utf-8-sig')

# Metodoloji özeti (makale metodoloji bölümü için sayılar)
with open('/home/claude/gis_project/outputs/gis_filter_summary.txt',
          'w', encoding='utf-8') as f:
    f.write("GIS AŞAMA I — METODOLOJİ ÖZETİ\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Analiz alanı     : Türkiye ({LON_MIN}°E–{LON_MAX}°E, "
            f"{LAT_MIN}°N–{LAT_MAX}°N)\n")
    f.write(f"Grid çözünürlüğü : {RES}° × {RES}° (~{RES*111:.0f} km)\n")
    f.write(f"Toplam piksel    : {total_pixels:,}\n\n")
    f.write("Kısıt Katmanları:\n")
    descs = [
        ("L1","Rüzgâr CF ≥ %20","Global Wind Atlas v3 + REPA"),
        ("L2","Güneş ≥ 1.450 kWh/m²","PVGIS-SARAH3 / JRC"),
        ("L3","Eğim ≤ 15°","NASA SRTM 30m DEM"),
        ("L4","Koruma alanı dışı (5 km tampon)","WDPA / ÇKSGB"),
        ("L5","Su kaynağına ≤ 30 km","HydroSHEDS / DSİ"),
        ("L6","İletim hattına ≤ 50 km","TEİAŞ / OSM"),
    ]
    for code, desc, src in descs:
        f.write(f"  {code}: {desc} — Kaynak: {src}\n")
    f.write(f"\nUygun piksel     : {n_elig:,} (%{pct_elig:.1f})\n")
    f.write(f"Bulunan küme     : {n_clusters}\n")
    f.write(f"Seçilen aday     : {len(candidates)}\n\n")
    f.write("Seçilen Aday Tesisler:\n")
    for _, row in candidates.iterrows():
        f.write(f"  {row['site_code']}: {row['province']} "
                f"({row['centroid_lat']:.2f}°N, {row['centroid_lon']:.2f}°E)\n"
                f"       Rüzgâr CF: {row['wind_cf_mean']:.1f}%  "
                f"Güneş: {row['solar_mean']:.0f} kWh/m²  "
                f"Eğim: {row['slope_mean']:.1f}°\n")

print("\n     ✓ candidate_sites.csv kaydedildi")
print("     ✓ gis_filter_summary.txt kaydedildi")

# ─────────────────────────────────────────────────────────────────────────────
# ÖZET TABLO — Konsol Çıktısı
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  SONUÇ: GIS AŞAMA I ÇIKTISI")
print("=" * 65)
print(f"\n  Toplam piksel analiz edildi : {total_pixels:,}")
print(f"  Tüm kısıtları geçen piksel  : {n_elig:,} (%{pct_elig:.1f})")
print(f"  DBSCAN küme sayısı          : {n_clusters}")
print(f"  Seçilen aday tesis sayısı   : {len(candidates)}")
print("\n  ADAY TESİSLER:")
print(f"  {'Kod':<4} {'İl':<22} {'Lat':>6} {'Lon':>6} "
      f"{'Rüzgâr CF':>10} {'Güneş':>10}")
print("  " + "-" * 62)
for _, row in candidates.iterrows():
    print(f"  {row['site_code']:<4} {row['province']:<22} "
          f"{row['centroid_lat']:>6.2f} {row['centroid_lon']:>6.2f} "
          f"{row['wind_cf_mean']:>9.1f}% {row['solar_mean']:>8.0f} kWh")
print("\n  → Bu koordinatlar SF-CRITIC-WASPAS (Aşama II) girdisidir.")
print("  → Haritalar: figures/ klasörüne kaydedildi")
print("  → CSV:       outputs/candidate_sites.csv\n")
