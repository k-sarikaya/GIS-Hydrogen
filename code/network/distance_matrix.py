"""
Aday sahalar × talep düğümleri mesafe matrisi.

- haversine_km : büyük daire mesafesi (R = 6371.0088 km, IUGG ortalama yarıçap)
- road_km      : OSRM karayolu mesafesi (OpenStreetMap; table servisi, tek istek)
- snap_*_m     : noktanın en yakın yola oturtulma mesafesi (OSRM); büyükse yol mesafesi şüphelidir

Yeniden üretilebilirlik: OSRM yanıtı ham haliyle osrm_response.json'a dondurulur. Girdi dosyalarının
SHA-256 değerleri manifest ile aynıysa ağa çıkılmaz; --refresh ile yeniden sorgulanır.

Kullanım:
  python code/network/distance_matrix.py \
      --sites data/raw/gis/real/candidate_sites.csv \
      --demand data/raw/demand/demand_inventory.csv --rule rule_2040
"""
import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OSRM_URL = 'https://router.project-osrm.org/table/v1/driving/'
R_EARTH_KM = 6371.0088
UA = {'User-Agent': 'GH2-SCN-research/1.0 (Tokat Gaziosmanpasa Univ.; academic use)'}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dlmb = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * R_EARTH_KM * np.arcsin(np.sqrt(a))


def osrm_table(sites, nodes):
    import requests
    pts = list(zip(sites.lon, sites.lat)) + list(zip(nodes.lon, nodes.lat))
    coords = ';'.join(f'{lon:.6f},{lat:.6f}' for lon, lat in pts)
    params = {'sources': ';'.join(map(str, range(len(sites)))),
              'destinations': ';'.join(map(str, range(len(sites), len(pts)))),
              'annotations': 'distance,duration'}
    r = requests.get(OSRM_URL + coords, params=params, headers=UA, timeout=120)
    r.raise_for_status()
    data = r.json()
    if data.get('code') != 'Ok':
        raise RuntimeError(f'OSRM hatası: {data.get("code")} {data.get("message")}')
    return data, r.url


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--sites', default=str(ROOT / 'data/raw/gis/real/candidate_sites.csv'))
    ap.add_argument('--demand', default=str(ROOT / 'data/raw/demand/demand_inventory.csv'))
    ap.add_argument('--storage', default=str(ROOT / 'data/raw/network/storage_nodes.csv'),
                    help='depolama düğümleri; hem kaynak hem hedef olarak eklenir ("none" = yok)')
    ap.add_argument('--rule', default='rule_2040', help='talep envanterindeki seçim sütunu; "all" = koordinatı olan tümü')
    ap.add_argument('--out', default=str(ROOT / 'data/processed/network'))
    ap.add_argument('--refresh', action='store_true', help='dondurulmuş OSRM yanıtını yok say, yeniden sorgula')
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    sites = pd.read_csv(args.sites)[['code', 'province', 'lat', 'lon']].rename(columns={'code': 'site'})
    demand = pd.read_csv(args.demand)
    demand = demand[demand.lat.notna() & demand.lon.notna()]
    if args.rule != 'all':
        demand = demand[demand[args.rule] == 1]
    nodes = demand[['node_id', 'name', 'lat', 'lon']].reset_index(drop=True)
    n_sites, n_nodes = len(sites), len(nodes)

    inputs = {'sites': {'path': Path(args.sites).name, 'sha256': sha256_file(args.sites)},
              'demand': {'path': Path(args.demand).name, 'sha256': sha256_file(args.demand), 'rule': args.rule}}
    # Depolama düğümleri kaynaklara (depo -> talep) ve hedeflere (saha -> depo) eklenir
    store = pd.DataFrame(columns=['node_id', 'name', 'lat', 'lon'])
    if args.storage != 'none' and Path(args.storage).exists():
        store = pd.read_csv(args.storage)[['node_id', 'name', 'lat', 'lon']]
        inputs['storage'] = {'path': Path(args.storage).name, 'sha256': sha256_file(args.storage)}
    src = pd.concat([sites.rename(columns={'site': 'id'})[['id', 'lat', 'lon']],
                     store.rename(columns={'node_id': 'id'})[['id', 'lat', 'lon']]], ignore_index=True)
    dst = pd.concat([nodes, store], ignore_index=True)
    manifest_path, frozen = out / 'distance_manifest.json', out / 'osrm_response.json'
    old = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    if frozen.exists() and not args.refresh and old.get('inputs') == inputs:
        data = json.loads(frozen.read_text(encoding='utf-8'))
        request_url, retrieved = old['osrm']['request_url'], old['osrm']['retrieved_utc']
        print('OSRM: dondurulmuş yanıt kullanılıyor (girdiler değişmedi).')
    else:
        data, request_url = osrm_table(src, dst)
        retrieved = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
        frozen.write_text(json.dumps(data, indent=1), encoding='utf-8')
        print('OSRM: yeni sorgu yapıldı ve donduruldu.')

    rows = []
    for i, s in sites.iterrows():
        for j, n in nodes.iterrows():
            d_road, t_road = data['distances'][i][j], data['durations'][i][j]
            rows.append({
                'site': s.site, 'site_province': s.province, 'node_id': n.node_id, 'node_name': n['name'],
                'haversine_km': round(float(haversine_km(s.lat, s.lon, n.lat, n.lon)), 2),
                'road_km': round(d_road / 1000, 2) if d_road is not None else np.nan,
                'road_duration_h': round(t_road / 3600, 2) if t_road is not None else np.nan,
                'snap_site_m': round(data['sources'][i]['distance'], 0),
                'snap_node_m': round(data['destinations'][j]['distance'], 0),
            })
    long = pd.DataFrame(rows)
    long['road_to_haversine'] = (long.road_km / long.haversine_km).round(3)
    long.to_csv(out / 'distance_matrix_long.csv', index=False)
    for col in ['haversine_km', 'road_km']:
        long.pivot(index='site', columns='node_id', values=col).to_csv(out / f'distance_matrix_{col}.csv')

    # Depolama yayları: saha -> depo ve depo -> talep
    srows = []
    for k, g in store.reset_index(drop=True).iterrows():
        pairs = [(i, n_nodes + k, sites.site[i], g.node_id) for i in range(n_sites)]
        pairs += [(n_sites + k, j, g.node_id, nodes.node_id[j]) for j in range(n_nodes)]
        for si, dj, o, d in pairs:
            d_road, t_road = data['distances'][si][dj], data['durations'][si][dj]
            srows.append({
                'origin': o, 'destination': d,
                'haversine_km': round(float(haversine_km(src.lat[si], src.lon[si], dst.lat[dj], dst.lon[dj])), 2),
                'road_km': round(d_road / 1000, 2) if d_road is not None else np.nan,
                'road_duration_h': round(t_road / 3600, 2) if t_road is not None else np.nan,
                'snap_origin_m': round(data['sources'][si]['distance'], 0),
                'snap_dest_m': round(data['destinations'][dj]['distance'], 0),
            })
    if srows:
        slong = pd.DataFrame(srows)
        slong['road_to_haversine'] = (slong.road_km / slong.haversine_km).round(3)
        slong.to_csv(out / 'distance_matrix_storage_long.csv', index=False)
        print(slong[['origin', 'destination', 'haversine_km', 'road_km']].to_string(index=False))

    manifest = {
        'run_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'inputs': inputs,
        'osrm': {'service': OSRM_URL, 'request_url': request_url, 'retrieved_utc': retrieved,
                 'profile': 'driving', 'note': 'OSRM demo server, OpenStreetMap data at retrieval time'},
        'earth_radius_km': R_EARTH_KM,
        'outputs_sha256': {p.name: sha256_file(p) for p in sorted(out.glob('distance_matrix_*.csv'))},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(long.pivot(index='site', columns='node_id', values='road_km').to_string())
    big_snap = long[(long.snap_site_m > 2000) | (long.snap_node_m > 2000)]
    if not big_snap.empty:
        print(f'UYARI: {len(big_snap)} çiftte yol oturtma mesafesi > 2 km (snap_*_m sütunlarına bakın).')


if __name__ == '__main__':
    main()
