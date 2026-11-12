# -*- coding: utf-8 -*-
"""Ruzgar/PV maske ortusmesini (wind_pv_overlap_km2) guvenli sekilde olcer.

NEDEN BIR YORDAM GEREKIYOR
--------------------------
1. layer_tiles() onbellekli calisir: adi cache_tiles_tallies.csv'de bulunan karo
   YENIDEN ISLENMEZ. Bu yuzden cikarma adimini oldugu gibi yeniden kosmak
   hicbir karoyu hesaplamaz ve ortusme sutunu NaN kalir.
2. OSM katmanlari cikti klasorundeki snapshot_osm_*.geojson.gz dosyalari varsa
   DONDURULMUS halleriyle okunur; yoksa Overpass'tan GUNCEL veri cekilir ve
   uygun hucre kumesi degisebilir. Bu, makalenin butun sayilarini gecersiz kilar.

YORDAM
------
  --prepare : ayri bir calisma klasoru kurar (dondurulmus OSM anlik kopyalari,
              PVGIS onbellegi, ve ilgili 13 karosu cikarilmis karo onbellekleri).
              Donmus temel klasorune DOKUNMAZ.
  (sonra)   : cikarma adimini o klasore kosarsiniz; sadece eksik karolar islenir.
  --verify  : (a) yeniden indirilen DEM karolarinin sha256'si orijinal kosumdakiyle
              ayni mi, (b) yeniden hesaplanan hucrelerin ESKI sutunlari degismis mi.
              Ikisi de temizse ortusme olcumu guvenle devralinabilir.
  --promote : dogrulanmis ciktilari data/raw/gis/real'e kopyalar (--verify sart).

Kullanim:
    python code/gis/measure_overlap.py --prepare
    python code/gis/gis_pipeline_real.py --out data/processed/overlap_run --workers 4
    python code/gis/measure_overlap.py --verify
    python code/gis/measure_overlap.py --promote
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / 'data/raw/gis/real'
WORK = ROOT / 'data/processed/overlap_run'

REUSE = ['snapshot_osm_protected.geojson.gz', 'snapshot_osm_military.geojson.gz',
         'snapshot_osm_airports.geojson.gz', 'snapshot_osm_substations.geojson.gz',
         'snapshot_osm_power_lines.geojson.gz', 'snapshot_adm1_simplified.geojson.gz',
         'cache_pvgis_ghi.csv', 'cache_tiles_cells.csv', 'cache_tiles_tallies.csv']


def target_tiles():
    """Secilen bes kumenin TUM hucrelerini kapsayan karolar."""
    sys.path.insert(0, str(ROOT / 'code/gis'))
    import gis_pipeline_real as G
    cells = pd.read_csv(REAL / 'grid_cells_layers.csv')
    el, _cl, cand = G.cluster_and_select(cells)
    sub = el[el.cluster.isin(set(cand.cluster))]
    return sorted({f'N{int(np.floor(r.lat)):02d}E{int(np.floor(r.lon)):03d}' for r in sub.itertuples()})


def prepare():
    tiles = target_tiles()
    WORK.mkdir(parents=True, exist_ok=True)
    for name in REUSE:
        src = REAL / name
        if not src.exists():
            print(f'EKSIK girdi: {src}')
            sys.exit(1)
        shutil.copy2(src, WORK / name)

    tal = pd.read_csv(WORK / 'cache_tiles_tallies.csv')
    cac = pd.read_csv(WORK / 'cache_tiles_cells.csv')
    cells = pd.read_csv(REAL / 'grid_cells_layers.csv')
    cells = cells.assign(tile=['N%02dE%03d' % (np.floor(r.lat), np.floor(r.lon)) for r in cells.itertuples()])
    drop_ids = set(cells[cells.tile.isin(tiles)].cell_id)

    tal[~tal.tile.isin(tiles)].to_csv(WORK / 'cache_tiles_tallies.csv', index=False)
    cac[~cac.cell_id.isin(drop_ids)].to_csv(WORK / 'cache_tiles_cells.csv', index=False)

    (WORK / 'OVERLAP_RUN_TILES.json').write_text(
        json.dumps({'tiles': tiles, 'n_cells_invalidated': len(drop_ids)}, indent=2), encoding='utf-8')

    print(f'Calisma klasoru : {WORK}')
    print(f'Yeniden islenecek karo: {len(tiles)} / {len(tal)} ({", ".join(tiles)})')
    print(f'Onbellekten dusurulen hucre: {len(drop_ids)}')
    print('\nOSM anlik kopyalari kopyalandi -> Overpass SORGULANMAYACAK.')
    print('\nSimdi su komutu calistirin (saatler surebilir):')
    print('  python code/gis/gis_pipeline_real.py --out data/processed/overlap_run --workers 4')
    print('\nArdindan: python code/gis/measure_overlap.py --verify')


def verify():
    man_old = json.loads((REAL / 'features_manifest.json').read_text(encoding='utf-8'))
    man_new = json.loads((WORK / 'features_manifest.json').read_text(encoding='utf-8'))
    s_old = man_old.get('sources', man_old)
    s_new = man_new.get('sources', man_new)
    tiles = json.loads((WORK / 'OVERLAP_RUN_TILES.json').read_text(encoding='utf-8'))['tiles']

    h_old = s_old.get('copernicus_glo90', {}).get('tile_sha256_this_run', {})
    h_new = s_new.get('copernicus_glo90', {}).get('tile_sha256_this_run', {})
    dem_bad = [t for t in tiles if t in h_old and t in h_new and h_old[t] != h_new[t]]
    dem_seen = [t for t in tiles if t in h_new]

    a = pd.read_csv(REAL / 'grid_cells_layers.csv').set_index('cell_id')
    b = pd.read_csv(WORK / 'grid_cells_layers.csv').set_index('cell_id')
    common_rows = a.index.intersection(b.index)
    common_cols = [c for c in a.columns if c in b.columns and c != 'wind_pv_overlap_km2']
    num = [c for c in common_cols
           if pd.api.types.is_numeric_dtype(a[c]) and not pd.api.types.is_bool_dtype(a[c])
           and pd.api.types.is_numeric_dtype(b[c]) and not pd.api.types.is_bool_dtype(b[c])]
    other = [c for c in common_cols if c not in num]
    diff = (a.loc[common_rows, num] - b.loc[common_rows, num]).abs().max()
    changed = diff[diff > 1e-9]
    # sayisal olmayan / boolean sutunlar: dogrudan esitlik
    for c in other:
        ne = int((a.loc[common_rows, c].fillna('~') != b.loc[common_rows, c].fillna('~')).sum())
        if ne:
            changed = pd.concat([changed, pd.Series({c: float(ne)})])

    ov = b['wind_pv_overlap_km2'] if 'wind_pv_overlap_km2' in b.columns else pd.Series(dtype=float)
    measured = int(ov.notna().sum())

    print(f'Yeniden indirilen DEM karosu : {len(dem_seen)} / {len(tiles)}')
    print(f'DEM sha256 UYUSMAYAN karo    : {len(dem_bad)} {dem_bad if dem_bad else ""}')
    print(f'Degeri degisen eski sutun    : {len(changed)}')
    if len(changed):
        print(changed.to_string())
    print(f'Ortusme olculen hucre        : {measured}')
    ok = not dem_bad and changed.empty and measured > 0
    print('\n' + ('DOGRULAMA GECTI -> --promote calistirilabilir'
                  if ok else 'DOGRULAMA GECMEDI -> devralmayin, farki inceleyin'))
    return ok


def promote():
    if not verify():
        sys.exit(1)
    # Donmus girdi tablosu + onbellekler + manifest. Secim adimi ciktilari
    # (candidate_sites.csv, clusters.csv, ...) asagida yeniden uretilir, cunku
    # Asama III bunlari okur ve ortusme sutunlarini tasimalari gerekir.
    for name in ['grid_cells_features.csv', 'cache_tiles_cells.csv', 'cache_tiles_tallies.csv',
                 'features_manifest.json']:
        src = WORK / name
        if src.exists():
            shutil.copy2(src, REAL / name)
            print(f'devralindi: {name}')

    print('\nSecim adimi yeniden kosuluyor (aday kumesi degismemeli)...')
    import subprocess
    tmp = WORK.parent / '_promote_select'
    if tmp.exists():
        shutil.rmtree(tmp)
    r = subprocess.run([sys.executable, 'code/gis/gis_pipeline_real.py', '--from-features',
                        str(REAL / 'grid_cells_features.csv'), '--out', str(tmp)],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print('secim adimi BASARISIZ:\n', r.stdout[-1500:], r.stderr[-1500:])
        sys.exit(1)
    old = pd.read_csv(REAL / 'candidate_sites.csv')
    new = pd.read_csv(tmp / 'candidate_sites.csv')
    # Ortusme/birlesim sutunlarinin DEGISMESI beklenir (NaN -> olculen deger);
    # degismemesi gereken, raporlanan aday kumesi ve alanlaridir.
    expected = {'cell_wind_pv_overlap_km2', 'cluster_wind_pv_overlap_km2',
                'cell_union_area_km2', 'cluster_union_area_km2'}
    same = [c for c in old.columns if c in new.columns and c not in expected]
    if not old[same].equals(new[same]):
        print('UYARI: aday tablosu degisti -- DEVRALINMADI. Farki inceleyin:')
        print(tmp)
        sys.exit(1)
    for name in ['grid_cells_layers.csv', 'candidate_sites.csv', 'clusters.csv',
                 'layer_elimination.csv', 'gis_summary.json', 'Fig1_GIS_filter_results.png']:
        if (tmp / name).exists():
            shutil.copy2(tmp / name, REAL / name)
            print(f'devralindi: {name}')
    shutil.rmtree(tmp)
    print('\nAday kumesi degismedi. Simdi asagi akisi dogrulayin:')
    print('  python code/tools/verify_reproduction.py')


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare', action='store_true')
    g.add_argument('--verify', action='store_true')
    g.add_argument('--promote', action='store_true')
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if a.prepare:
        prepare()
    elif a.verify:
        verify()
    else:
        promote()


if __name__ == '__main__':
    main()
