"""
GH2 — Aşama I: GIS dışlama filtresi (gerçek veri, literatüre dayalı, yeniden üretilebilir)
========================================================================================

TASARIM
-------
Literatürdeki dışlama tamponları (0.5–5 km) 0.1° hücreden (~11 km) küçük olduğu için dışlamalar
~90 m piksel düzeyinde uygulanır; her 0.1° hücre için rüzgâr ve GES/elektrolizör kurulumuna uygun
bitişik alan (km²) hesaplanır (Ryberg vd. 2018; Pfennig vd. 2023; Ishmam vd. 2024). Hücre düzeyi
kısıtlar (GHI, uygun alan, su, şebeke) bu alanlar üzerinden uygulanır.

Piksel düzeyi ortak dışlamalar (tüm teknolojiler)
  X1 yükseklik > 2000 m                                   Copernicus GLO-90
  X2 koruma alanı + 1 km                                  OSM (milli park, tabiat parkı, doğal sit, Ramsar …)
  X3 yerleşim (WorldCover 'built-up', ~80 m çoğunluk) + 1 km   ESA WorldCover 2021 v200
  X4 havalimanı (IATA/ICAO kodlu) + 5 km                  OSM aeroway=aerodrome
  X5 askeri alan                                          OSM landuse=military
  X6 kalıcı su / sulak alan + 0.5 km                      ESA WorldCover
  X7 orman, kar/buz, mangrov                              ESA WorldCover
Teknolojiye özgü
  Rüzgâr : eğim ≤ %30 (16.7°) ve brüt kapasite faktörü ≥ eşik (GWA v3 IEC2; %20/%25/%30 varyantları)
  GES+ELZ: eğim ≤ %10 (5.7°) ve tarım arazisi değil (5403 s. Kanun md. 13; 2023/6 Genelgesi)
  Bitişik yama şartı (8-komşuluk): rüzgâr ≥ 10 km² (Pfennig vd. 2023); GES ≥ 3 km² (~100 MWac, Ong vd. 2013)
Hücre düzeyi kısıtlar (B aşaması)
  C1 GHI ≥ 1450 kWh/m²/yıl (PVGIS-SARAH3)      C2 rüzgâra uygun alan ≥ 10 km²
  C3 GES'e uygun alan ≥ 3 km²                   C4 tatlı su kaynağı (nehir/göl) veya kıyı ≤ 50 km
  C5 ≥154 kV trafo merkezi ≤ 50 km

İKİ AŞAMA
---------
A) extract (ağ gerekir): veriyi bellekte işler, hücre bazlı özellik tablosunu ve alan dışlama
   tablosunu dondurur; OSM anlık kopyaları, URL'ler ve SHA-256 değerleri kaydedilir.
B) select (ağ gerekmez, deterministik): kısıtlar, DBSCAN kümeleme, aday seçimi; --set ile duyarlılık.

Kullanım
--------
python gis_pipeline_real.py --out gis_outputs                     # A + B, tüm Türkiye
python gis_pipeline_real.py --out test_outputs --test             # A + B, küçük test alanı
python gis_pipeline_real.py --from-features gis_outputs/grid_cells_features.csv --out run2 \
       --set C_wind_cf_variant=0.30                                # yalnız B, duyarlılık
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
os.environ.setdefault('CPL_VSIL_CURL_ALLOWED_EXTENSIONS', '.tif')
os.environ.setdefault('GDAL_HTTP_MAX_RETRY', '5')
os.environ.setdefault('GDAL_HTTP_RETRY_DELAY', '3')

# ── PARAMETRELER ─────────────────────────────────────────────────────────────
PARAMS = {
    'grid_res_deg': 0.1,
    'grid_bbox': [25.6, 35.8, 45.0, 42.2],            # lon_min, lat_min, lon_max, lat_max
    'test_bbox': [33.0, 39.0, 34.0, 40.5],            # --test: Kırıkkale çevresi
    'pixel_res_deg': 1 / 1200,                        # 3" (~90 m), Copernicus GLO-90 ile aynı
    'tile_pad_deg': 0.05,                             # tamponlar için karo kenar payı
    'worldcover_decimation': 8,                       # 10 m → ~80 m (COG overview), çoğunluk örneklemesi
    # piksel düzeyi ortak dışlamalar
    'X_elev_max_m': 2000.0,
    'X_protected_buffer_km': 1.0,
    'X_builtup_buffer_km': 1.0,
    'X_airport_buffer_km': 5.0,
    'X_water_setback_km': 0.5,
    'X_landcover_excluded': [10, 70, 95],             # orman, kar/buz, mangrov (WorldCover)
    'X_water_classes': [80, 90],                      # kalıcı su, otsu sulak alan
    'X_builtup_class': 50,
    # teknolojiye özgü
    'W_slope_max_deg': 16.70,                         # %30
    'W_cf_variants': [0.20, 0.25, 0.30],
    'PV_slope_max_deg': 5.71,                         # %10
    'PV_landcover_excluded': [40],                    # tarım arazisi
    'W_min_patch_km2': 10.0,                          # Pfennig vd. 2023
    'PV_min_patch_km2': 3.0,                          # ~100 MWac @ 31 MWac/km² (Ong vd. 2013)
    'PV_min_patch_alt_km2': 10.0,                     # duyarlılık: Pfennig vd. 2023
    # hücre düzeyi kısıtlar (B)
    'C_ghi_min_kwh_m2_yr': 1450.0,
    'C_wind_cf_variant': 0.25,
    'C_wind_area_min_km2': 10.0,
    'C_pv_area_min_km2': 3.0,
    'C_pv_variant': 'base',                           # base | p10 | withcrop
    'C_water_max_km': 50.0,
    'C_substation_max_km': 50.0,
    # vektör veriler
    'river_min_discharge_m3s': 1.0,                   # HydroRIVERS DIS_AV_CMS: sürekli akış
    'lake_classes': ['Lake', 'Reservoir'],            # Natural Earth; tuzlu/alkali göller hariç
    'substation_min_kv': 154,
    'substation_line_snap_km': 1.0,                   # voltaj etiketi yoksa ≥154 kV hatta ≤1 km olan merkez
    # kümeleme ve aday seçimi
    'dbscan_eps_deg': 0.15,                           # 8-komşuluk (köşegen 0.141°)
    'dbscan_min_samples': 3,
    'n_candidates': 5,
    'min_spacing_km': 100.0,                          # adaylar arası asgari büyük daire mesafesi
    'pvgis_years': [2005, 2023],
}
METRIC_CRS = '+proj=laea +lat_0=39 +lon_0=35 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs'

GB = 'https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/TUR'
URLS = {
    'adm0': f'{GB}/ADM0/geoBoundaries-TUR-ADM0.geojson',
    'adm1': f'{GB}/ADM1/geoBoundaries-TUR-ADM1.geojson',
    'wind': 'https://globalwindatlas.info/api/gis/country/TUR/capacity-factor_IEC2',
    'rivers': 'https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_eu_shp.zip',
    'lakes': 'https://naciscdn.org/naturalearth/10m/physical/ne_10m_lakes.zip',
    'coast': 'https://naciscdn.org/naturalearth/10m/physical/ne_10m_coastline.zip',
    'pvgis': 'https://re.jrc.ec.europa.eu/api/v5_3/MRcalc',
    'dem_tile': ('https://copernicus-dem-90m.s3.amazonaws.com/'
                 'Copernicus_DSM_COG_30_N{lat:02d}_00_E{lon:03d}_00_DEM/'
                 'Copernicus_DSM_COG_30_N{lat:02d}_00_E{lon:03d}_00_DEM.tif'),
    'worldcover': ('https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/'
                   'ESA_WorldCover_10m_2021_v200_N{lat:02d}E{lon:03d}_Map.tif'),
}
OVERPASS = [
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
]
TR = 'area["ISO3166-1"="TR"]["admin_level"="2"]->.tr;'
OSM_QUERIES = {
    'power_lines': f'[out:json][timeout:900];{TR}way["power"="line"]["voltage"](area.tr);out tags geom;',
    'substations': f'[out:json][timeout:900];{TR}nwr["power"="substation"](area.tr);out center tags;',
    'airports': f'[out:json][timeout:900];{TR}nwr["aeroway"="aerodrome"](area.tr);out center tags;',
    'military': f'[out:json][timeout:900];{TR}(way["landuse"="military"](area.tr);relation["landuse"="military"](area.tr););out tags geom;',
    'protected': (f'[out:json][timeout:900];{TR}('
                  'way["boundary"~"^(national_park|protected_area)$"](area.tr);'
                  'relation["boundary"~"^(national_park|protected_area)$"](area.tr);'
                  'way["leisure"="nature_reserve"](area.tr);'
                  'relation["leisure"="nature_reserve"](area.tr);'
                  ');out tags geom;'),
}
PROTECT_CLASSES = {'1', '1a', '1b', '2', '3', '4', '5', '6'}
PROTECT_TITLE_RE = re.compile(
    r'milli park|national park|tabiat park|tabiat[ıi] koruma|nature (park|reserve)|do[gğ]al s[iİı]t|'
    r'yaban hayat|wildlife|sulak alan|wetland|ramsar|özel çevre koruma|special environmental protection',
    re.IGNORECASE)

FEATURE_COLUMNS = {
    'cell_id': 'hücre kimliği "lon_lat" (hücre merkezi, 2 ondalık)',
    'row': 'ızgara satırı (kuzeyden güneye)', 'col': 'ızgara sütunu (batıdan doğuya)',
    'lon': 'hücre merkezi boylamı (°E)', 'lat': 'hücre merkezi enlemi (°N)',
    'province': 'il (geoBoundaries ADM1)',
    'land_km2': 'hücrenin Türkiye kara alanı (km²)',
    'buildable_km2': 'ortak dışlamalardan (X1–X7) sonra kalan alan (km²)',
    'wind_area_km2_cf20': 'rüzgâra uygun bitişik alan, CF ≥ %20 (km²)',
    'wind_area_km2_cf25': 'rüzgâra uygun bitişik alan, CF ≥ %25 (km²)',
    'wind_area_km2_cf30': 'rüzgâra uygun bitişik alan, CF ≥ %30 (km²)',
    'pv_area_km2': 'GES/elektrolizöre uygun bitişik alan, yama ≥ 3 km², tarım hariç (km²)',
    'pv_area_km2_p10': 'GES alanı, yama ≥ 10 km², tarım hariç (km²) — duyarlılık',
    'pv_area_km2_withcrop': 'GES alanı, yama ≥ 3 km², tarım dahil (km²) — duyarlılık',
    'wind_pv_overlap_km2': 'hem rüzgâra hem GES/elektrolizöre uygun ortak alan (km²); '
                           'ortak kullanım kısıtı için (params.yaml land.co_use_share)',
    'wind_cf_mean': 'kara alanında ortalama brüt KF (GWA IEC2, 0–1)',
    'wind_cf_eligible_mean': 'rüzgâra uygun alanda (CF ≥ %25) ortalama brüt KF (0–1)',
    'ghi': 'PVGIS-SARAH3 yatay düzlem yıllık ışınım, hücre merkezi (kWh/m²/yıl)',
    'elev_median': 'medyan yükseklik (m)', 'slope_median': 'medyan eğim (°)',
    'share_cropland': 'tarım arazisi payı', 'share_grass_shrub_bare': 'çayır/çalı/çıplak arazi payı',
    'share_tree': 'orman payı', 'share_builtup': 'yerleşim payı',
    'dist_freshwater_km': 'en yakın sürekli nehir veya tatlı su gölüne uzaklık (km)',
    'dist_coast_km': 'kıyı çizgisine uzaklık (km)',
    'dist_substation_km': 'en yakın ≥154 kV trafo merkezine uzaklık (km)',
    'dist_grid_line_km': 'en yakın ≥154 kV iletim hattına uzaklık (km)',
}
UA = {'User-Agent': 'GH2-SCN-research/1.0 (Tokat Gaziosmanpasa Univ.; academic use)'}
SOURCES = {}


def log(msg):
    print(f'[{dt.datetime.now():%H:%M:%S}] {msg}', flush=True)


def now_utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def append_rows(cache, rows, cols):
    frames = [f for f in (cache, pd.DataFrame(rows, columns=cols)) if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=cols)


def versions():
    import importlib
    out = {'python': sys.version.split()[0]}
    for m in ['numpy', 'pandas', 'scipy', 'geopandas', 'rasterio', 'shapely', 'pyogrio', 'pyproj',
              'sklearn', 'matplotlib', 'requests']:
        try:
            out[m] = importlib.import_module(m).__version__
        except Exception:
            pass
    return out


# ════════════════════════════════════════════════════════════════════════════
# A) EXTRACT
# ════════════════════════════════════════════════════════════════════════════
def fetch_bytes(name, url, retries=4):
    import requests
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=UA, timeout=300)
            r.raise_for_status()
            SOURCES[name] = {'url': url, 'bytes': len(r.content),
                             'sha256': hashlib.sha256(r.content).hexdigest(), 'retrieved_utc': now_utc()}
            log(f'  indirildi: {name} ({len(r.content) / 1e6:.1f} MB)')
            return r.content
        except Exception as e:
            if attempt == retries - 1:
                raise
            log(f'  {name} hata ({e}); yeniden deneniyor')
            time.sleep(10 * 2 ** attempt)


def overpass(name, query):
    import requests
    last = None
    for attempt in range(5):
        for ep in OVERPASS:
            try:
                r = requests.post(ep, data={'data': query}, headers=UA, timeout=1200)
                if r.status_code == 200 and r.text.lstrip().startswith('{'):
                    data = r.json()
                    SOURCES[f'osm_{name}'] = {'url': ep, 'query': query, 'bytes': len(r.content),
                                              'sha256': hashlib.sha256(r.content).hexdigest(),
                                              'osm_timestamp': data.get('osm3s', {}).get('timestamp_osm_base'),
                                              'n_elements': len(data['elements']), 'retrieved_utc': now_utc()}
                    log(f'  Overpass {name}: {len(data["elements"])} öğe ({ep.split("/")[2]})')
                    return data['elements']
                last = f'{ep}: HTTP {r.status_code}'
            except Exception as e:
                last = f'{ep}: {e}'
        wait = 30 * 2 ** attempt
        log(f'  Overpass {name} başarısız ({last}); {wait}s bekleniyor')
        time.sleep(wait)
    raise RuntimeError(f'Overpass {name} başarısız: {last}')


def read_zipped_vector(content, bbox):
    """Zip içindeki shapefile'ı diske yazmadan okur (parçalar bellekte düz zip'e yeniden paketlenir)."""
    import geopandas as gpd
    import pyogrio
    zin = zipfile.ZipFile(io.BytesIO(content))
    shp = [n for n in zin.namelist() if n.lower().endswith('.shp')][0]
    stem = shp[:-4]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zout:
        for n in zin.namelist():
            if n.startswith(stem + '.'):
                zout.writestr(Path(n).name, zin.read(n))
    df = pyogrio.read_dataframe(buf.getvalue(), bbox=tuple(bbox))
    return gpd.GeoDataFrame(df, geometry='geometry', crs=df.crs or 'EPSG:4326')


def write_geojson_gz(gdf, path):
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        f.write(gdf.to_json(drop_id=True))


def read_geojson_gz(path):
    import geopandas as gpd
    return gpd.read_file(io.BytesIO(gzip.decompress(Path(path).read_bytes())))


# ── OSM geometri yardımcıları ──
def _coords(geom_list):
    return [(p['lon'], p['lat']) for p in geom_list]


def osm_polygons(elements):
    import geopandas as gpd
    from shapely.geometry import LineString, Polygon
    from shapely.ops import linemerge, polygonize, unary_union
    rows = []
    for el in elements:
        tags = el.get('tags', {})
        try:
            if el['type'] == 'way':
                pts = _coords(el.get('geometry', []))
                if len(pts) >= 4 and pts[0] == pts[-1]:
                    rows.append((el['type'], el['id'], tags, Polygon(pts)))
            elif el['type'] == 'relation':
                members = [m for m in el.get('members', []) if m.get('type') == 'way' and len(m.get('geometry', [])) > 1]
                outer = [LineString(_coords(m['geometry'])) for m in members if m.get('role', 'outer') in ('outer', '')]
                inner = [LineString(_coords(m['geometry'])) for m in members if m.get('role') == 'inner']
                polys = list(polygonize(linemerge(outer))) if outer else []
                if polys:
                    geom = unary_union(polys)
                    holes = list(polygonize(linemerge(inner))) if inner else []
                    if holes:
                        geom = geom.difference(unary_union(holes))
                    rows.append((el['type'], el['id'], tags, geom))
        except Exception:
            continue
    gdf = gpd.GeoDataFrame({'osm_type': [r[0] for r in rows], 'osm_id': [r[1] for r in rows],
                            'tags': [r[2] for r in rows]}, geometry=[r[3] for r in rows], crs='EPSG:4326')
    gdf['geometry'] = gdf.geometry.make_valid()
    return gdf


def osm_points(elements):
    import geopandas as gpd
    from shapely.geometry import Point
    rows = []
    for el in elements:
        c = el.get('center') or ({'lat': el['lat'], 'lon': el['lon']} if 'lat' in el else None)
        if c:
            rows.append((el['type'], el['id'], el.get('tags', {}), Point(c['lon'], c['lat'])))
    return gpd.GeoDataFrame({'osm_type': [r[0] for r in rows], 'osm_id': [r[1] for r in rows],
                             'tags': [r[2] for r in rows]}, geometry=[r[3] for r in rows], crs='EPSG:4326')


def is_protected(tags):
    if tags.get('boundary') == 'national_park' or tags.get('leisure') == 'nature_reserve':
        return True
    if str(tags.get('protect_class', '')).lower() in PROTECT_CLASSES:
        return True
    text = ' '.join(str(tags.get(k, '')) for k in ('protection_title', 'name', 'name:en', 'designation'))
    return bool(PROTECT_TITLE_RE.search(text))


def max_kv(v):
    vals = [int(x) for x in re.findall(r'\d+', str(v))]
    return max(vals) / 1000 if vals else 0.0


def load_osm_layers(out):
    """OSM katmanlarını yükler; anlık kopya varsa onu kullanır (dondurulmuş girdi)."""
    import geopandas as gpd
    from shapely.geometry import LineString
    snaps = {k: out / f'snapshot_osm_{k}.geojson.gz' for k in
             ['protected', 'military', 'airports', 'substations', 'power_lines']}
    if all(p.exists() for p in snaps.values()):
        log('  OSM: dondurulmuş anlık kopyalar kullanılıyor')
        layers = {k: read_geojson_gz(p) for k, p in snaps.items()}
        for k, p in snaps.items():
            SOURCES[f'osm_{k}'] = {'snapshot': p.name, 'sha256': sha256_file(p), 'reused': True}
        return layers

    def tagcols(gdf, keys):
        for k in keys:
            gdf[k] = gdf.tags.apply(lambda t: t.get(k, ''))
        return gdf.drop(columns='tags')

    prot = osm_polygons(overpass('protected', OSM_QUERIES['protected']))
    prot = tagcols(prot[prot.tags.apply(is_protected)].copy(), ['name', 'protect_class', 'protection_title'])
    mil = tagcols(osm_polygons(overpass('military', OSM_QUERIES['military'])), ['name', 'military'])
    air = osm_points(overpass('airports', OSM_QUERIES['airports']))
    air = tagcols(air[air.tags.apply(lambda t: bool(t.get('iata') or t.get('icao')))].copy(), ['name', 'iata', 'icao'])

    lines = []
    for el in overpass('power_lines', OSM_QUERIES['power_lines']):
        kv = max_kv(el.get('tags', {}).get('voltage'))
        pts = _coords(el.get('geometry', []))
        if kv >= PARAMS['substation_min_kv'] and len(pts) > 1:
            lines.append((el['id'], kv, LineString(pts)))
    grid = gpd.GeoDataFrame({'osm_id': [l[0] for l in lines], 'kv': [l[1] for l in lines]},
                            geometry=[l[2] for l in lines], crs='EPSG:4326')

    sub = osm_points(overpass('substations', OSM_QUERIES['substations']))
    sub['kv'] = sub.tags.apply(lambda t: max_kv(t.get('voltage')))
    sub['name'] = sub.tags.apply(lambda t: t.get('name', ''))
    sub = sub.drop(columns='tags')
    sub_m, grid_m = sub.to_crs(METRIC_CRS), grid.to_crs(METRIC_CRS)
    near = gpd.sjoin_nearest(sub_m[['osm_id', 'geometry']], grid_m[['geometry']], distance_col='_d')
    near_line = near.groupby('osm_id')['_d'].min() <= PARAMS['substation_line_snap_km'] * 1000
    sub['basis'] = np.where(sub.kv >= PARAMS['substation_min_kv'], 'voltage_tag',
                            np.where((sub.kv == 0) & sub.osm_id.map(near_line).fillna(False), 'near_hv_line', ''))
    sub = sub[sub.basis != ''].copy()

    layers = {'protected': prot, 'military': mil, 'airports': air, 'substations': sub, 'power_lines': grid}
    for k, g in layers.items():
        g = g.sort_values('osm_id').reset_index(drop=True)
        layers[k] = g
        write_geojson_gz(g, snaps[k])
    log(f'  OSM: {len(prot)} koruma, {len(mil)} askeri, {len(air)} havalimanı, '
        f'{len(sub)} trafo (≥{PARAMS["substation_min_kv"]} kV), {len(grid)} hat')
    return layers


# ── Izgara ──
def build_grid(bbox, adm0, adm1):
    import geopandas as gpd
    res = PARAMS['grid_res_deg']
    lon_min, lat_min, lon_max, lat_max = bbox
    ncol = int(round((lon_max - lon_min) / res))
    nrow = int(round((lat_max - lat_min) / res))
    rows, cols = np.meshgrid(np.arange(nrow), np.arange(ncol), indexing='ij')
    lon = np.round(lon_min + res / 2 + cols.ravel() * res, 4)
    lat = np.round(lat_max - res / 2 - rows.ravel() * res, 4)
    cells = gpd.GeoDataFrame({'row': rows.ravel(), 'col': cols.ravel(), 'lon': lon, 'lat': lat},
                             geometry=gpd.points_from_xy(lon, lat), crs='EPSG:4326')
    cells = cells[cells.within(adm0.union_all())].copy()
    cells = gpd.sjoin(cells, adm1[['shapeName', 'geometry']], how='left', predicate='within')
    cells = cells.drop(columns='index_right').rename(columns={'shapeName': 'province'})
    cells = cells[~cells.index.duplicated()]
    cells['cell_id'] = [f'{a:.2f}_{b:.2f}' for a, b in zip(cells.lon, cells.lat)]
    return cells.sort_values(['row', 'col']).reset_index(drop=True)


# ── Güneş (PVGIS, hücre merkezi) ──
def pvgis_ghi(lat, lon):
    import requests
    y0, y1 = PARAMS['pvgis_years']
    params = {'lat': lat, 'lon': lon, 'horirrad': 1, 'raddatabase': 'PVGIS-SARAH3',
              'startyear': y0, 'endyear': y1, 'outputformat': 'json'}
    for attempt in range(6):
        try:
            r = requests.get(URLS['pvgis'], params=params, headers=UA, timeout=60)
            if r.status_code == 200:
                m = pd.DataFrame(r.json()['outputs']['monthly'])
                return float(m.groupby('year')['H(h)_m'].sum().mean())
            if r.status_code == 400:
                return np.nan
            time.sleep(2 * 2 ** attempt)
        except Exception:
            time.sleep(2 * 2 ** attempt)
    return np.nan


def layer_solar(cells, out, workers):
    cols = ['cell_id', 'ghi']
    cache_path = out / 'cache_pvgis_ghi.csv'
    cache = pd.read_csv(cache_path) if cache_path.exists() else pd.DataFrame(columns=cols)
    todo = cells[~cells.cell_id.isin(cache.cell_id)]
    log(f'  PVGIS: {len(cache)} önbellekte, {len(todo)} sorgulanacak')
    new = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(pvgis_ghi, r.lat, r.lon): r.cell_id for r in todo.itertuples()}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            new.append((futs[fut], fut.result()))
            if i % 250 == 0 or i == len(futs):
                append_rows(cache, new, cols).sort_values('cell_id').to_csv(cache_path, index=False)
                log(f'  PVGIS {i}/{len(futs)}')
    cache = append_rows(cache, new, cols)
    SOURCES['pvgis_sarah3'] = {'url': URLS['pvgis'], 'params': {'horirrad': 1, 'raddatabase': 'PVGIS-SARAH3',
                               'years': PARAMS['pvgis_years']}, 'n_points': int(len(cache)),
                               'n_missing': int(cache.ghi.isna().sum()), 'cache_sha256': sha256_file(cache_path)}
    cells['ghi'] = cells.cell_id.map(dict(zip(cache.cell_id, cache.ghi))).astype(float)
    return cells


# ── Piksel düzeyi karo işleme ──
EXCL_ORDER = ['X1_elevation', 'X2_protected', 'X3_builtup', 'X4_airport', 'X5_military', 'X6_water', 'X7_landcover']
TALLY_COLS = (['tile', 'land_km2'] + [f'{x}_alone_km2' for x in EXCL_ORDER] +
              [f'{x}_cum_remaining_km2' for x in EXCL_ORDER] +
              ['wind_slope_ok_km2', 'wind_cf25_ok_km2', 'wind_patch_cf25_km2', 'pv_slope_ok_km2',
               'pv_noncrop_ok_km2', 'pv_patch_km2'])
CELL_COLS = ['cell_id', 'land_km2', 'buildable_km2', 'wind_area_km2_cf20', 'wind_area_km2_cf25', 'wind_area_km2_cf30',
             'pv_area_km2', 'pv_area_km2_p10', 'pv_area_km2_withcrop', 'wind_pv_overlap_km2',
             'wind_cf_mean', 'wind_cf_eligible_mean', 'elev_median', 'slope_median',
             'share_cropland', 'share_grass_shrub_bare', 'share_tree', 'share_builtup']


def read_worldcover(shape, transform):
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import Affine, array_bounds
    from rasterio.warp import reproject
    from rasterio.windows import from_bounds
    dst = np.zeros(shape, dtype='uint8')
    w, s, e, n = array_bounds(shape[0], shape[1], transform)
    used = []
    for la in range(int(np.floor(s / 3) * 3), int(np.ceil(n / 3) * 3), 3):
        for lo in range(int(np.floor(w / 3) * 3), int(np.ceil(e / 3) * 3), 3):
            url = URLS['worldcover'].format(lat=la, lon=lo)
            try:
                with rasterio.open('/vsicurl/' + url) as src:
                    bw, bs = max(w, lo), max(s, la)
                    be, bn = min(e, lo + 3), min(n, la + 3)
                    if be <= bw or bn <= bs:
                        continue
                    win = from_bounds(bw, bs, be, bn, transform=src.transform).round_offsets().round_lengths()
                    k = PARAMS['worldcover_decimation']
                    oh, ow = max(1, int(win.height // k)), max(1, int(win.width // k))
                    arr = src.read(1, window=win, out_shape=(oh, ow), resampling=Resampling.mode)
                    tr = src.window_transform(win) * Affine.scale(win.width / ow, win.height / oh)
                    reproject(arr, dst, src_transform=tr, src_crs=src.crs, dst_transform=transform,
                              dst_crs='EPSG:4326', resampling=Resampling.nearest, src_nodata=0, dst_nodata=0,
                              init_dest_nodata=False)
                    used.append(Path(url).name)
            except rasterio.errors.RasterioIOError:
                continue
    return dst, used


def rasterize_on(gdf, shape, transform):
    from rasterio.features import rasterize
    from rasterio.transform import array_bounds
    w, s, e, n = array_bounds(shape[0], shape[1], transform)
    sub = gdf.cx[w:e, s:n] if len(gdf) else gdf
    if sub.empty:
        return np.zeros(shape, dtype=bool)
    return rasterize(((g, 1) for g in sub.geometry if g is not None and not g.is_empty), out_shape=shape,
                     transform=transform, fill=0, all_touched=True, dtype='uint8').astype(bool)


def buffer_mask(src_mask, dist_km, dy, dx):
    from scipy.ndimage import distance_transform_edt
    if not src_mask.any():
        return np.zeros_like(src_mask)
    if dist_km <= 0:
        return src_mask.copy()
    return distance_transform_edt(~src_mask, sampling=(dy, dx)) <= dist_km * 1000.0


def patch_filter(mask, px_area_km2, min_km2):
    """Bitişik (8-komşuluk) yamalardan alanı min_km2 altında olanları atar."""
    from scipy.ndimage import label, sum as nd_sum
    lab, n = label(mask, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return mask
    areas = nd_sum(px_area_km2, lab, index=np.arange(1, n + 1))
    keep = np.zeros(n + 1, dtype=bool)
    keep[1:] = areas >= min_km2
    return keep[lab]


def process_tile(lat0, lon0, tile_cells, ctx):
    """1°×1° karo: piksel dışlamaları, teknoloji maskeleri, hücre bazlı alanlar ve alan sayımları."""
    import requests
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    res = PARAMS['pixel_res_deg']
    P = int(round(PARAMS['tile_pad_deg'] / res))
    N = int(round(1 / res))
    shape = (N + 2 * P, N + 2 * P)
    tr = from_origin(lon0 - P * res, lat0 + 1 + P * res, res, res)
    inner = (slice(P, P + N), slice(P, P + N))

    # DEM → yükseklik ve eğim
    url = URLS['dem_tile'].format(lat=lat0, lon=lon0)
    r = None
    for attempt in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=180)
            break
        except Exception:
            time.sleep(5 * 2 ** attempt)
    if r is None or r.status_code != 200:
        return [], None, None
    dem = np.full(shape, np.nan, dtype='float32')
    with MemoryFile(r.content) as mf, mf.open() as src:
        reproject(rasterio.band(src, 1), dem, src_nodata=src.nodata, dst_nodata=np.nan, dst_transform=tr,
                  dst_crs='EPSG:4326', resampling=Resampling.bilinear)
    dem_sha = hashlib.sha256(r.content).hexdigest()
    lat_rows = (lat0 + 1 + P * res) - res * (np.arange(shape[0]) + 0.5)
    dy = res * 110574.0
    dx_rows = res * 111320.0 * np.cos(np.radians(lat_rows))
    dx = float(dx_rows.mean())
    gy, gx = np.gradient(dem)
    slope = np.degrees(np.arctan(np.hypot(gx / dx_rows[:, None], gy / dy)))
    px_area = (dx_rows * dy / 1e6)[:, None] * np.ones((1, shape[1]))

    # Arazi örtüsü ve Türkiye kara maskesi
    lc, wc_used = read_worldcover(shape, tr)
    land = rasterize_on(ctx['adm0'], shape, tr)

    # Rüzgâr KF (250 m → 90 m, bilineer)
    cfa = np.full(shape, np.nan, dtype='float32')
    reproject(ctx['cf_arr'], cfa, src_transform=ctx['cf_tr'], src_crs='EPSG:4326', src_nodata=np.nan,
              dst_transform=tr, dst_crs='EPSG:4326', dst_nodata=np.nan, resampling=Resampling.bilinear)

    # Ortak dışlamalar
    ex = {
        'X1_elevation': ~(dem <= PARAMS['X_elev_max_m']),
        'X2_protected': buffer_mask(rasterize_on(ctx['protected'], shape, tr), PARAMS['X_protected_buffer_km'], dy, dx),
        'X3_builtup': buffer_mask(lc == PARAMS['X_builtup_class'], PARAMS['X_builtup_buffer_km'], dy, dx),
        'X4_airport': buffer_mask(rasterize_on(ctx['airports'], shape, tr), PARAMS['X_airport_buffer_km'], dy, dx),
        'X5_military': rasterize_on(ctx['military'], shape, tr),
        'X6_water': buffer_mask(np.isin(lc, PARAMS['X_water_classes']), PARAMS['X_water_setback_km'], dy, dx),
        'X7_landcover': np.isin(lc, PARAMS['X_landcover_excluded']) | (lc == 0),
    }
    buildable = land.copy()
    for k in EXCL_ORDER:
        buildable &= ~ex[k]

    wind_slope = slope <= PARAMS['W_slope_max_deg']
    wind_masks = {v: patch_filter(buildable & wind_slope & (cfa >= v), px_area, PARAMS['W_min_patch_km2'])
                  for v in PARAMS['W_cf_variants']}
    pv_slope = slope <= PARAMS['PV_slope_max_deg']
    pv_noncrop = ~np.isin(lc, PARAMS['PV_landcover_excluded'])
    pv_mask = patch_filter(buildable & pv_slope & pv_noncrop, px_area, PARAMS['PV_min_patch_km2'])
    pv_mask_p10 = patch_filter(buildable & pv_slope & pv_noncrop, px_area, PARAMS['PV_min_patch_alt_km2'])
    pv_mask_crop = patch_filter(buildable & pv_slope, px_area, PARAMS['PV_min_patch_km2'])

    # Alan sayımları (yalnız karo içi, Türkiye karası)
    I = inner
    A = px_area[I]
    L = land[I]
    tally = {'tile': f'N{lat0:02d}E{lon0:03d}', 'land_km2': float(A[L].sum())}
    rem = L.copy()
    for k in EXCL_ORDER:
        tally[f'{k}_alone_km2'] = float(A[L & ex[k][I]].sum())
        rem &= ~ex[k][I]
        tally[f'{k}_cum_remaining_km2'] = float(A[rem].sum())
    b = buildable[I]
    tally['wind_slope_ok_km2'] = float(A[b & wind_slope[I]].sum())
    tally['wind_cf25_ok_km2'] = float(A[b & wind_slope[I] & (cfa[I] >= 0.25)].sum())
    tally['wind_patch_cf25_km2'] = float(A[wind_masks[0.25][I]].sum())
    tally['pv_slope_ok_km2'] = float(A[b & pv_slope[I]].sum())
    tally['pv_noncrop_ok_km2'] = float(A[b & pv_slope[I] & pv_noncrop[I]].sum())
    tally['pv_patch_km2'] = float(A[pv_mask[I]].sum())

    # Hücre bazlı özet (10×10 hücre)
    m = int(round(PARAMS['grid_res_deg'] / res))
    rows = []
    for c in tile_cells.itertuples():
        i = int(round((lat0 + 1 - (c.lat + PARAMS['grid_res_deg'] / 2)) / PARAMS['grid_res_deg']))
        j = int(round(((c.lon - PARAMS['grid_res_deg'] / 2) - lon0) / PARAMS['grid_res_deg']))
        win = (slice(P + i * m, P + (i + 1) * m), slice(P + j * m, P + (j + 1) * m))
        a, l = px_area[win], land[win]
        if not l.any():
            continue
        lcw = lc[win][l]
        cfw = cfa[win]
        w25 = wind_masks[0.25][win]
        rows.append((
            c.cell_id, float(a[l].sum()), float(a[buildable[win]].sum()),
            *[float(a[wind_masks[v][win]].sum()) for v in PARAMS['W_cf_variants']],
            float(a[pv_mask[win]].sum()), float(a[pv_mask_p10[win]].sum()), float(a[pv_mask_crop[win]].sum()),
            float(a[w25 & pv_mask[win]].sum()),
            float(np.nanmean(cfw[l])) if np.isfinite(cfw[l]).any() else np.nan,
            float(np.nanmean(cfw[w25])) if w25.any() else np.nan,
            float(np.nanmedian(dem[win][l])) if np.isfinite(dem[win][l]).any() else np.nan,
            float(np.nanmedian(slope[win][l])) if np.isfinite(slope[win][l]).any() else np.nan,
            float(np.isin(lcw, [40]).mean()), float(np.isin(lcw, [20, 30, 60, 100]).mean()),
            float(np.isin(lcw, [10]).mean()), float(np.isin(lcw, [50]).mean()),
        ))
    return rows, tally, {'dem': (Path(url).name, dem_sha), 'worldcover': wc_used}


def layer_tiles(cells, out, ctx, workers):
    cache_p, tally_p = out / 'cache_tiles_cells.csv', out / 'cache_tiles_tallies.csv'
    cache = pd.read_csv(cache_p) if cache_p.exists() else pd.DataFrame(columns=CELL_COLS)
    tallies = pd.read_csv(tally_p) if tally_p.exists() else pd.DataFrame(columns=TALLY_COLS)
    tiles_all = cells.assign(tlat=np.floor(cells.lat).astype(int), tlon=np.floor(cells.lon).astype(int))
    groups = [(k, g) for k, g in tiles_all.groupby(['tlat', 'tlon'])
              if f'N{k[0]:02d}E{k[1]:03d}' not in set(tallies.tile)]
    log(f'  Karo: {len(groups)} işlenecek ({len(tallies)} önbellekte)')
    new_rows, new_tallies, recs = [], [], {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process_tile, la, lo, g, ctx): (la, lo) for (la, lo), g in groups}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            rows, tally, rec = fut.result()
            new_rows.extend(rows)
            if tally:
                new_tallies.append(tally)
                recs[tally['tile']] = rec
            if i % 5 == 0 or i == len(futs):
                append_rows(cache, new_rows, CELL_COLS).sort_values('cell_id').to_csv(cache_p, index=False)
                append_rows(tallies, new_tallies, TALLY_COLS).sort_values('tile').to_csv(tally_p, index=False)
                log(f'  Karo {i}/{len(futs)}')
    cache = append_rows(cache, new_rows, CELL_COLS)
    tallies = append_rows(tallies, new_tallies, TALLY_COLS)
    SOURCES['copernicus_glo90'] = {'url_pattern': URLS['dem_tile'],
                                   'tile_sha256_this_run': {k: v['dem'][1] for k, v in sorted(recs.items())},
                                   'cache_sha256': sha256_file(cache_p)}
    SOURCES['esa_worldcover_2021_v200'] = {'url_pattern': URLS['worldcover'], 'read': 'COG overview, mode resampling',
                                           'decimation': PARAMS['worldcover_decimation'],
                                           'tiles': sorted({t for v in recs.values() for t in v['worldcover']})}
    return cells.merge(cache, on='cell_id', how='left'), tallies


def nearest_km(cells_m, feats_m):
    import geopandas as gpd
    if feats_m.empty:
        return pd.Series(np.inf, index=cells_m.index)
    j = gpd.sjoin_nearest(cells_m[['cell_id', 'geometry']], feats_m[['geometry']], distance_col='_d')
    return cells_m.cell_id.map(j.groupby('cell_id')['_d'].min() / 1000.0)


def extract(bbox, out, workers, test):
    import geopandas as gpd
    import rasterio
    from rasterio.io import MemoryFile
    log('L0 sınırlar')
    adm0 = gpd.read_file(io.BytesIO(fetch_bytes('geoboundaries_adm0', URLS['adm0'])))
    adm1 = gpd.read_file(io.BytesIO(fetch_bytes('geoboundaries_adm1', URLS['adm1'])))
    write_geojson_gz(adm1[['shapeName', 'geometry']].assign(geometry=adm1.geometry.simplify(0.01)),
                     out / 'snapshot_adm1_simplified.geojson.gz')
    cells = build_grid(bbox, adm0, adm1)
    log(f'  ızgara: {len(cells)} hücre (Türkiye sınırı içinde)')

    log('OSM katmanları'); osm = load_osm_layers(out)
    log('Güneş (PVGIS)');  cells = layer_solar(cells, out, workers)

    log('Rüzgâr (GWA IEC2)')
    with MemoryFile(fetch_bytes('gwa3_cf_IEC2', URLS['wind'])) as mf, mf.open() as src:
        cf_arr = src.read(1).astype('float32')
        if src.nodata is not None:
            cf_arr[cf_arr == src.nodata] = np.nan
        if np.nanmax(cf_arr) > 1.5:
            cf_arr /= 100.0
        SOURCES['gwa3_cf_IEC2'].update({'crs': str(src.crs), 'res': list(src.res)})
        cf_tr = src.transform
    ctx = {'adm0': adm0[['geometry']], 'protected': osm['protected'], 'military': osm['military'],
           'airports': osm['airports'], 'cf_arr': cf_arr, 'cf_tr': cf_tr}

    log('Piksel düzeyi dışlamalar (DEM + WorldCover + vektörler)')
    cells, tallies = layer_tiles(cells, out, ctx, workers)

    log('Hücre mesafeleri')
    pad = [bbox[0] - 1, bbox[1] - 1, bbox[2] + 1, bbox[3] + 1]
    rivers = read_zipped_vector(fetch_bytes('hydrorivers_v10_eu', URLS['rivers']), pad)
    rivers = rivers[rivers['DIS_AV_CMS'] >= PARAMS['river_min_discharge_m3s']]
    lakes = read_zipped_vector(fetch_bytes('ne_10m_lakes', URLS['lakes']), pad)
    lakes = lakes[lakes['featurecla'].isin(PARAMS['lake_classes'])]
    coast = read_zipped_vector(fetch_bytes('ne_10m_coastline', URLS['coast']), pad)
    SOURCES['hydrorivers_v10_eu']['n_segments_used'] = int(len(rivers))
    SOURCES['ne_10m_lakes']['lakes_used'] = sorted(map(str, lakes['name'].fillna('')))
    fresh = gpd.GeoDataFrame(pd.concat([rivers[['geometry']], lakes[['geometry']]], ignore_index=True), crs='EPSG:4326')
    cm = cells.to_crs(METRIC_CRS)
    cells['dist_freshwater_km'] = nearest_km(cm, fresh.to_crs(METRIC_CRS)).values
    cells['dist_coast_km'] = nearest_km(cm, coast.to_crs(METRIC_CRS)).values
    cells['dist_substation_km'] = nearest_km(cm, osm['substations'].to_crs(METRIC_CRS)).values
    cells['dist_grid_line_km'] = nearest_km(cm, osm['power_lines'].to_crs(METRIC_CRS)).values

    feats = cells[list(FEATURE_COLUMNS)].sort_values(['row', 'col']).reset_index(drop=True)
    path = out / 'grid_cells_features.csv'
    feats.to_csv(path, index=False, float_format='%.6f')
    area = area_exclusion_table(tallies)
    area.to_csv(out / 'area_exclusion.csv', index=False, float_format='%.1f')
    manifest = {
        'stage': 'extract', 'run_utc': now_utc(), 'mode': 'test' if test else 'full', 'bbox': bbox,
        'params': PARAMS, 'metric_crs': METRIC_CRS, 'columns': FEATURE_COLUMNS,
        'n_cells': int(len(feats)), 'missing_values': {c: int(feats[c].isna().sum()) for c in feats.columns},
        'features_sha256': sha256_file(path), 'area_exclusion_sha256': sha256_file(out / 'area_exclusion.csv'),
        'sources': SOURCES, 'versions': versions(),
    }
    (out / 'features_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
                                                encoding='utf-8')
    log(f'  özellik tablosu: {path} (sha256 {manifest["features_sha256"][:12]}…)')
    return path


def area_exclusion_table(tallies):
    t = tallies.drop(columns='tile').sum()
    land = t['land_km2']
    rows = [{'step': 'Land area (Türkiye)', 'excluded_alone_km2': 0.0, 'remaining_km2': land}]
    names = {'X1_elevation': 'X1 Elevation > 2000 m', 'X2_protected': 'X2 Protected areas + 1 km',
             'X3_builtup': 'X3 Built-up + 1 km', 'X4_airport': 'X4 Airports + 5 km', 'X5_military': 'X5 Military areas',
             'X6_water': 'X6 Water bodies/wetlands + 0.5 km', 'X7_landcover': 'X7 Forest, snow/ice'}
    for k in EXCL_ORDER:
        rows.append({'step': names[k], 'excluded_alone_km2': t[f'{k}_alone_km2'], 'remaining_km2': t[f'{k}_cum_remaining_km2']})
    rows += [
        {'step': 'Wind: slope ≤ 30%', 'excluded_alone_km2': np.nan, 'remaining_km2': t['wind_slope_ok_km2']},
        {'step': 'Wind: gross CF ≥ 25%', 'excluded_alone_km2': np.nan, 'remaining_km2': t['wind_cf25_ok_km2']},
        {'step': 'Wind: contiguous patches ≥ 10 km²', 'excluded_alone_km2': np.nan, 'remaining_km2': t['wind_patch_cf25_km2']},
        {'step': 'PV/ELZ: slope ≤ 10%', 'excluded_alone_km2': np.nan, 'remaining_km2': t['pv_slope_ok_km2']},
        {'step': 'PV/ELZ: not cropland', 'excluded_alone_km2': np.nan, 'remaining_km2': t['pv_noncrop_ok_km2']},
        {'step': 'PV/ELZ: contiguous patches ≥ 3 km²', 'excluded_alone_km2': np.nan, 'remaining_km2': t['pv_patch_km2']},
    ]
    df = pd.DataFrame(rows)
    df['remaining_pct'] = 100 * df.remaining_km2 / land
    return df


# ════════════════════════════════════════════════════════════════════════════
# B) SELECT (deterministik, ağ gerektirmez)
# ════════════════════════════════════════════════════════════════════════════
def wind_col():
    return f'wind_area_km2_cf{int(round(PARAMS["C_wind_cf_variant"] * 100))}'


def pv_col():
    return {'base': 'pv_area_km2', 'p10': 'pv_area_km2_p10', 'withcrop': 'pv_area_km2_withcrop'}[PARAMS['C_pv_variant']]


LAYERS = [
    ('C1', 'Solar GHI', lambda d: d.ghi >= PARAMS['C_ghi_min_kwh_m2_yr']),
    ('C2', 'Wind-eligible area', lambda d: d[wind_col()] >= PARAMS['C_wind_area_min_km2']),
    ('C3', 'PV-eligible area', lambda d: d[pv_col()] >= PARAMS['C_pv_area_min_km2']),
    ('C4', 'Water access', lambda d: np.fmin(d.dist_freshwater_km, d.dist_coast_km) <= PARAMS['C_water_max_km']),
    ('C5', 'Substation', lambda d: d.dist_substation_km <= PARAMS['C_substation_max_km']),
]


def apply_filters(cells):
    alive = pd.Series(True, index=cells.index)
    rows = [{'stage': 'Initial grid', 'surviving': len(cells), 'eliminated': 0, 'independent_pass': len(cells)}]
    cells['first_fail'] = ''
    for code, name, rule in LAYERS:
        ok = rule(cells).fillna(False).astype(bool)
        cells[f'pass_{code}'] = ok
        newly_out = alive & ~ok
        cells.loc[newly_out, 'first_fail'] = code
        alive &= ok
        rows.append({'stage': f'{code}: {name}', 'surviving': int(alive.sum()),
                     'eliminated': int(newly_out.sum()), 'independent_pass': int(ok.sum())})
    cells['eligible'] = alive
    tab = pd.DataFrame(rows)
    tab['pct_of_total'] = (100 * tab.surviving / len(cells)).round(1)
    return cells, tab


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return float(2 * 6371.0088 * np.arcsin(np.sqrt(a)))


def cluster_and_select(cells):
    """DBSCAN ile bitişik uygun hücre kümeleri; kümeler toplam uygun alana göre sıralanır (tercih
    değerlendirmesi Aşama II'ye bırakılır). Temsil noktası: kümede uygun alanı en büyük hücre."""
    from sklearn.cluster import DBSCAN
    el = cells[cells.eligible].sort_values(['row', 'col']).copy()
    if el.empty:
        return el, pd.DataFrame(), pd.DataFrame()
    el['cluster'] = DBSCAN(eps=PARAMS['dbscan_eps_deg'],
                           min_samples=PARAMS['dbscan_min_samples']).fit_predict(el[['lon', 'lat']].values)
    wc, pc = wind_col(), pv_col()
    # DİKKAT: eligible_area_km2 küme sıralaması ve temsil hücresi seçiminde kullanılır ve
    # rüzgâr ile PV maskelerinin örtüşmesini saymaz. Aday kümesinin yeniden üretilebilirliği
    # için tanımı değiştirilmedi; örtüşmeye duyarlı birleşim ayrı bir sütun olarak raporlanır.
    el['eligible_area_km2'] = el[wc] + el[pc]
    ov = 'wind_pv_overlap_km2'
    if ov not in el.columns:          # eski donmuş öznitelik tablosu: örtüşme ölçülmemiş
        el[ov] = np.nan
    el['union_area_km2'] = el[wc] + el[pc] - el[ov].fillna(0.0)
    g = el[el.cluster >= 0].groupby('cluster')
    cl = pd.DataFrame({
        'n_cells': g.size(), 'wind_area_km2': g[wc].sum(), 'pv_area_km2': g[pc].sum(),
        'wind_pv_overlap_km2': g[ov].sum(min_count=1), 'union_area_km2': g.union_area_km2.sum(),
        'eligible_area_km2': g.eligible_area_km2.sum(), 'wind_cf_eligible_mean': g.wind_cf_eligible_mean.mean(),
        'ghi_mean': g.ghi.mean(), 'lon_c': g.lon.mean(), 'lat_c': g.lat.mean(),
        'provinces': g.province.agg(lambda s: ', '.join(sorted(set(map(str, s))))),
    })
    if cl.empty:
        return el, cl, pd.DataFrame()
    cl = cl.reset_index().sort_values(['eligible_area_km2', 'cluster'], ascending=[False, True], kind='mergesort')
    cl['rank'] = np.arange(1, len(cl) + 1)

    # Temsil hücresi: kümede uygun alanı en büyük hücre
    reps = {}
    for c in cl.itertuples():
        members = el[el.cluster == c.cluster].sort_values(['eligible_area_km2', 'row', 'col'],
                                                          ascending=[False, True, True], kind='mergesort')
        reps[c.cluster] = members.iloc[0]

    # Sıralı seçim + asgari mesafe: bir kümenin temsil hücresi, önceden seçilenlerden en az
    # min_spacing_km uzaktaysa kabul edilir (rüzgâr çıktısı korelasyonu; Katzenstein vd. 2010;
    # St. Martin vd. 2015). Aksi halde atlanır ve sıradaki kümeye geçilir.
    chosen, status, nearest = [], [], []
    for c in cl.itertuples():
        r = reps[c.cluster]
        d = min((haversine_km(r.lat, r.lon, reps[k].lat, reps[k].lon) for k in chosen), default=np.inf)
        nearest.append(round(d, 1) if np.isfinite(d) else np.nan)
        if len(chosen) >= PARAMS['n_candidates']:
            status.append('not_needed')
        elif d < PARAMS['min_spacing_km']:
            status.append('skipped_spacing')
        else:
            chosen.append(c.cluster)
            status.append('selected')
    cl['selection'] = status
    cl['km_to_nearest_selected_before'] = nearest
    cl['selected'] = cl.selection == 'selected'

    cands = []
    for k, c in enumerate(cl[cl.selected].itertuples(), 1):
        rep = reps[c.cluster]
        cands.append({'code': f'S{k}', 'cluster': int(c.cluster), 'cell_id': rep.cell_id, 'province': rep.province,
                      'lat': rep.lat, 'lon': rep.lon, 'n_cells': int(c.n_cells),
                      'cluster_eligible_area_km2': round(c.eligible_area_km2, 1),
                      'cluster_wind_area_km2': round(c.wind_area_km2, 1), 'cluster_pv_area_km2': round(c.pv_area_km2, 1),
                      'cluster_wind_pv_overlap_km2': round(c.wind_pv_overlap_km2, 1),
                      'cluster_union_area_km2': round(c.union_area_km2, 1),
                      'cell_wind_area_km2': round(rep[wc], 1), 'cell_pv_area_km2': round(rep[pc], 1),
                      'cell_wind_pv_overlap_km2': round(rep[ov], 1),
                      'cell_union_area_km2': round(rep.union_area_km2, 1),
                      'cell_wind_cf_eligible_pct': round(100 * rep.wind_cf_eligible_mean, 1),
                      'cell_ghi_kwh_m2': round(rep.ghi, 0), 'cell_elev_m': round(rep.elev_median, 0),
                      'dist_freshwater_km': round(rep.dist_freshwater_km, 1), 'dist_coast_km': round(rep.dist_coast_km, 1),
                      'dist_substation_km': round(rep.dist_substation_km, 1),
                      'cluster_provinces': c.provinces})
    return el, cl, pd.DataFrame(cands)


def make_figure(cells, cands, adm1_path, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    palette = {'C1': '#d9d9d9', 'C2': '#c6dbef', 'C3': '#bcbddc', 'C4': '#fdd0a2', 'C5': '#fcbba1'}
    names = {c: f'{c}: {n}' for c, n, _ in LAYERS}
    fig, ax = plt.subplots(figsize=(13, 6.5))
    for code, color in palette.items():
        d = cells[cells.first_fail == code]
        ax.scatter(d.lon, d.lat, s=6, marker='s', color=color, linewidths=0)
    e = cells[cells.eligible]
    ax.scatter(e.lon, e.lat, s=6, marker='s', color='#08519c', linewidths=0)
    if adm1_path and Path(adm1_path).exists():
        read_geojson_gz(adm1_path).boundary.plot(ax=ax, color='#525252', linewidth=0.3)
    if not cands.empty:
        ax.scatter(cands.lon, cands.lat, s=140, marker='*', color='#e31a1c', edgecolor='k', zorder=5)
        for r in cands.itertuples():
            ax.annotate(f'{r.code} {r.province}', (r.lon, r.lat), xytext=(6, 6), textcoords='offset points',
                        fontsize=9, weight='bold')
    handles = [Patch(color=palette[c], label=f'Fails {names[c]}') for c in palette]
    handles.append(Patch(color='#08519c', label=f'Suitable ({int(cells.eligible.sum())} cells)'))
    ax.legend(handles=handles, loc='lower left', fontsize=8, frameon=True)
    ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
    ax.set_title(f'Cell-level suitability on a {PARAMS["grid_res_deg"]}° grid ({len(cells):,} cells) '
                 'after pixel-level exclusions, and candidate sites')
    ax.set_aspect(1 / np.cos(np.radians(39)))
    fig.tight_layout()
    fig.savefig(path, dpi=200, metadata={'Software': None, 'Creation Time': None})
    plt.close(fig)


def select(features_path, out, overrides):
    features_path = Path(features_path)
    cells = pd.read_csv(features_path, dtype={'cell_id': str})
    cells, elim = apply_filters(cells)
    el, clusters, cands = cluster_and_select(cells)
    log(f'Uygun hücre: {int(cells.eligible.sum())} / {len(cells)}; küme: {len(clusters)}; aday: {len(cands)}')

    cells.to_csv(out / 'grid_cells_layers.csv', index=False, float_format='%.6f')
    elim.to_csv(out / 'layer_elimination.csv', index=False)
    clusters.to_csv(out / 'clusters.csv', index=False, float_format='%.6f')
    cands.to_csv(out / 'candidate_sites.csv', index=False)
    make_figure(cells, cands, features_path.parent / 'snapshot_adm1_simplified.geojson.gz',
                out / 'Fig1_GIS_filter_results.png')
    outputs = ['grid_cells_layers.csv', 'layer_elimination.csv', 'clusters.csv', 'candidate_sites.csv']
    summary = {
        'stage': 'select', 'run_utc': now_utc(),
        'input_features': {'path': features_path.name, 'sha256': sha256_file(features_path)},
        'param_overrides': overrides, 'params': PARAMS,
        'counts': {'cells': int(len(cells)), 'eligible': int(cells.eligible.sum()),
                   'clusters': int(len(clusters)), 'candidates': int(len(cands))},
        'layer_elimination': elim.to_dict(orient='records'),
        'candidates': cands.to_dict(orient='records'),
        'output_sha256': {p: sha256_file(out / p) for p in outputs},
        'versions': versions(),
    }
    (out / 'gis_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str),
                                          encoding='utf-8')
    print(elim.to_string(index=False))
    if not cands.empty:
        print(cands[['code', 'province', 'lat', 'lon', 'n_cells', 'cluster_eligible_area_km2',
                     'cell_wind_cf_eligible_pct', 'cell_ghi_kwh_m2', 'dist_substation_km']].to_string(index=False))


def parse_overrides(items):
    out = {}
    for item in items or []:
        k, v = item.split('=', 1)
        if k not in PARAMS:
            raise SystemExit(f'Bilinmeyen parametre: {k}')
        out[k] = json.loads(v)
        PARAMS[k] = out[k]
    return out


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='gis_outputs')
    ap.add_argument('--test', action='store_true', help='küçük test alanında çalıştır')
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--from-features', help='A aşamasını atla; bu özellik tablosundan B aşamasını çalıştır')
    ap.add_argument('--set', action='append', metavar='KEY=JSON', help='parametre değiştir (ör. C_wind_cf_variant=0.30)')
    args = ap.parse_args()
    overrides = parse_overrides(args.set)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.from_features:
        features = Path(args.from_features)
    else:
        features = extract(PARAMS['test_bbox'] if args.test else PARAMS['grid_bbox'], out, args.workers, args.test)
    select(features, out, overrides)
    log(f'Bitti ({(time.time() - t0) / 60:.1f} dk). Çıktılar: {out.resolve()}')


if __name__ == '__main__':
    main()
