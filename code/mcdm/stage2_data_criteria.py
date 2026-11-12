"""
Aşama II — veriden türetilen kriterler (K1–K4), aday sahaların temsil hücreleri için.

K1  En yakın ≥154 kV trafo merkezine uzaklık (km)            — Aşama I çıktısı (OSM anlık kopyası)
K2  Temel yıllık su stresi skoru (0–5), WRI Aqueduct 4.0      — Kuzma vd. (2023)
K3  En yakın koruma alanına uzaklık (km)                       — Aşama I OSM koruma alanı anlık kopyası
K4  PGA, %10 / 50 yıl (475 yıl), kaya zemin (g), GEM GSHM v2023.1 — Johnson vd. (2023), doi:10.5281/zenodo.8409647

Büyük kaynaklar (Aqueduct 262 MB, GEM 35 MB) bellekte işlenir; yalnız çıkarılan değerler ve kaynak
SHA-256 değerleri diske yazılır. Çıktı mevcutsa yeniden indirilmez (--refresh ile yenilenir).

Kullanım:  python code/mcdm/stage2_data_criteria.py [--refresh]
"""
import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SITES = ROOT / 'data/raw/gis/real/candidate_sites.csv'
GIS = ROOT / 'data/raw/gis/real'
OUT = ROOT / 'data/processed/stage2'
AQUEDUCT_URL = 'https://files.wri.org/aqueduct/aqueduct-4-0-water-risk-data.zip'
GEM_URL = 'https://zenodo.org/records/8409647/files/GEM-GSHM_PGA-475y-rock_v2023.zip?download=1'
METRIC_CRS = '+proj=laea +lat_0=39 +lon_0=35 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs'
UA = {'User-Agent': 'GH2-SCN-research/1.0 (Tokat Gaziosmanpasa Univ.; academic use)'}


def get(url):
    import requests
    r = requests.get(url, headers=UA, timeout=1800)
    r.raise_for_status()
    return r.content


def aqueduct_bws(points):
    import geopandas as gpd
    import pyogrio
    content = get(AQUEDUCT_URL)
    sha = hashlib.sha256(content).hexdigest()
    import shutil
    import tempfile
    zin = zipfile.ZipFile(io.BytesIO(content))
    gdb = [n for n in zin.namelist() if '.gdb/' in n and not n.endswith('/')]
    root = gdb[0].split('.gdb/')[0] + '.gdb/'
    # OpenFileGDB bellekteki zip'in alt klasöründen okunamadığı için GDB geçici klasöre açılır ve
    # okunduktan hemen sonra silinir (kalıcı disk kullanımı yok).
    tmp = Path(tempfile.mkdtemp(prefix='aqueduct_'))
    try:
        for n in gdb:
            p = tmp / 'aq.gdb' / n[len(root):]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(zin.read(n))
        del content, zin
        layers = [l[0] for l in pyogrio.list_layers(tmp / 'aq.gdb')]
        layer = [n for n in layers if 'baseline' in n.lower() and 'annual' in n.lower()][0]
        df = pyogrio.read_dataframe(tmp / 'aq.gdb', layer=layer, bbox=(25, 35, 46, 43),
                                    columns=['pfaf_id', 'name_0', 'bws_raw', 'bws_score', 'bws_cat', 'bws_label'])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    g = gpd.GeoDataFrame(df, geometry='geometry', crs=df.crs or 'EPSG:4326').to_crs('EPSG:4326')
    j = gpd.sjoin(points, g, how='left', predicate='within')
    j = j[~j.index.duplicated()]
    return j[['pfaf_id', 'bws_raw', 'bws_score', 'bws_cat', 'bws_label']], {'url': AQUEDUCT_URL, 'sha256': sha, 'layer': layer}


def gem_pga(points):
    import rasterio
    from rasterio.io import MemoryFile
    content = get(GEM_URL)
    sha = hashlib.sha256(content).hexdigest()
    zin = zipfile.ZipFile(io.BytesIO(content))
    tif = [n for n in zin.namelist() if n.lower().endswith('.tif')][0]
    # Aday koordinatları 0.05° piksel sınırlarına denk gelebildiği için tek piksel yerine noktayı
    # çevreleyen 3×3 pencerenin (~15 km) ortalaması alınır.
    with MemoryFile(zin.read(tif)) as mf, mf.open() as src:
        arr = src.read(1)
        vals = []
        for p in points.geometry:
            r, c = src.index(p.x, p.y)
            win = arr[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2]
            vals.append(float(np.mean(win[win < 1e300])))
        meta = {'crs': str(src.crs), 'res': list(src.res), 'aggregation': '3x3 window mean'}
    return np.array(vals, dtype=float), {'url': GEM_URL, 'sha256': sha, 'file': tif, **meta}


def protected_km(pts, prot):
    import geopandas as gpd
    d = gpd.sjoin_nearest(pts.to_crs(METRIC_CRS), prot.to_crs(METRIC_CRS)[['geometry']], distance_col='_d')
    return d.groupby(level=0)['_d'].min() / 1000.0


def anchors(prot):
    """Normalizasyon çapaları, beş adaydan bağımsız tanımlanır (adaylara bakılmadan sabitlenen kural):
    yayımlanmış ölçek veya Aşama I eşiği varsa o kullanılır (K1: 0–50 km, Aşama I trafo eşiği;
    K2: Aqueduct skor ölçeği 0–5); yoksa Aşama I'de uygun bulunan tüm hücrelerin 5. ve 95. yüzdelikleri
    (K3, K4)."""
    import geopandas as gpd
    cells = pd.read_csv(GIS / 'grid_cells_layers.csv')
    cells = cells[cells.eligible == 1].reset_index(drop=True)
    pts = gpd.GeoDataFrame(cells[['cell_id']], crs='EPSG:4326', geometry=gpd.points_from_xy(cells.lon, cells.lat))
    k3 = protected_km(pts, prot).values
    k4, src_gem = gem_pga(pts)
    pd.DataFrame({'cell_id': cells.cell_id, 'K1_substation_km': cells.dist_substation_km.round(2),
                  'K3_protected_km': np.round(k3, 2), 'K4_pga_g': np.round(k4, 4)}) \
        .to_csv(OUT / 'eligible_cells_criteria.csv', index=False)
    q = lambda v, p: round(float(np.percentile(v, p)), 4)
    return {
        'rule': 'published scale or Stage I threshold where available; otherwise P5/P95 over Stage I-eligible cells',
        'n_eligible_cells': int(len(cells)),
        'K1_substation_km': {'L': 0.0, 'U': 50.0, 'direction': 'cost', 'basis': 'Stage I threshold C_substation_max_km'},
        'K2_water_stress_score': {'L': 0.0, 'U': 5.0, 'direction': 'cost', 'basis': 'Aqueduct 4.0 score scale'},
        'K3_protected_km': {'L': q(k3, 5), 'U': q(k3, 95), 'direction': 'benefit', 'basis': 'P5/P95 eligible cells'},
        'K4_pga_g': {'L': q(k4, 5), 'U': q(k4, 95), 'direction': 'cost', 'basis': 'P5/P95 eligible cells'},
    }, src_gem


def main():
    import geopandas as gpd
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true')
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    out_csv, man = OUT / 'data_criteria.csv', OUT / 'data_criteria_manifest.json'
    anc_path = OUT / 'normalisation_anchors.json'
    sites = pd.read_csv(SITES)
    pts = gpd.GeoDataFrame(sites[['code', 'province', 'cell_id']], crs='EPSG:4326',
                           geometry=gpd.points_from_xy(sites.lon, sites.lat))
    prot = gpd.read_file(io.BytesIO(gzip.decompress((GIS / 'snapshot_osm_protected.geojson.gz').read_bytes())))
    if not anc_path.exists() or a.refresh:
        anc, src_gem = anchors(prot)
        anc['gem_sha256'] = src_gem['sha256']
        anc_path.write_text(json.dumps(anc, indent=2, ensure_ascii=False), encoding='utf-8')
    print(anc_path.read_text(encoding='utf-8'))
    if out_csv.exists() and not a.refresh and json.loads(man.read_text(encoding='utf-8'))['sites_sha256'] == \
            hashlib.sha256(SITES.read_bytes()).hexdigest():
        print(pd.read_csv(out_csv).to_string(index=False)); return

    k3 = protected_km(pts, prot)

    bws, src_aq = aqueduct_bws(pts)
    pga, src_gem = gem_pga(pts)
    res = pd.DataFrame({
        'code': sites.code, 'province': sites.province,
        'K1_substation_km': sites.dist_substation_km.round(2),
        'K2_water_stress_score': bws.bws_score.round(3).values, 'K2_bws_raw': bws.bws_raw.round(4).values,
        'K2_bws_label': bws.bws_label.values, 'K2_pfaf_id': bws.pfaf_id.values,
        'K3_protected_km': k3.round(2).values,
        'K4_pga_g': np.round(pga, 4),
    })
    res.to_csv(out_csv, index=False)
    man.write_text(json.dumps({
        'run_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'sites_sha256': hashlib.sha256(SITES.read_bytes()).hexdigest(),
        'sources': {'aqueduct40': src_aq, 'gem_gshm_v2023_1': src_gem,
                    'protected_snapshot': 'data/raw/gis/real/snapshot_osm_protected.geojson.gz'},
        'output_sha256': hashlib.sha256(out_csv.read_bytes()).hexdigest()}, indent=2, ensure_ascii=False), encoding='utf-8')
    print(res.to_string(index=False))


if __name__ == '__main__':
    main()
