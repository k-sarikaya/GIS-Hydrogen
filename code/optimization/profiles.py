"""
Aşama III girdisi: aday sahalar için saatlik rüzgâr/GES kapasite faktörü profilleri ve mevsimsel
temsilî günler.

- Rüzgâr: ERA5 100 m rüzgâr hızı (Open-Meteo arşiv API'si) → Vestas V126-3.45 MW güç eğrisi
  (windpowerlib/OEDB; Global Wind Atlas IEC2 sınıfının referans türbini, Davis vd. 2023).
  Yıllık brüt KF, sahanın Global Wind Atlas brüt KF'sine rüzgâr hızının çarpımsal ölçeklenmesiyle
  kalibre edilir (yeniden analiz verisinin yanlılık düzeltmesi).
- GES: PVGIS-SARAH3 seriescalc, 1 kWp, sabit montaj, optimum eğim, %14 sistem kaybı.
- Temsilî günler: her mevsim (DJF, MAM, JJA, SON) için k-medoids (PAM, deterministik BUILD +
  SWAP) ile k gün; ağırlık = temsil ettiği gün sayısı.

Yeniden üretilebilirlik: API yanıtları data/raw/profiles/ altına dondurulur ve manifestte SHA-256
ile kaydedilir; dosyalar mevcutsa ağa çıkılmaz (--refresh ile yeniden çekilir).

Kullanım:  python code/optimization/profiles.py [--year 2023] [--k 3] [--refresh]
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
RAW = ROOT / 'data/raw/profiles'
OUT = ROOT / 'data/processed/profiles'
SITES = ROOT / 'data/raw/gis/real/candidate_sites.csv'
UA = {'User-Agent': 'GH2-SCN-research/1.0 (Tokat Gaziosmanpasa Univ.; academic use)'}
ERA5_URL = 'https://archive-api.open-meteo.com/v1/archive'
PVGIS_URL = 'https://re.jrc.ec.europa.eu/api/v5_3/seriescalc'
TURBINE = 'V126/3450'
SEASONS = {'DJF': [12, 1, 2], 'MAM': [3, 4, 5], 'JJA': [6, 7, 8], 'SON': [9, 10, 11]}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def fetch(name, url, params, refresh):
    import requests
    path = RAW / name
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding='utf-8')), sha256_bytes(path.read_bytes()), 'cached'
    r = requests.get(url, params=params, headers=UA, timeout=180)
    r.raise_for_status()
    path.write_bytes(r.content)
    return r.json(), sha256_bytes(r.content), 'downloaded'


def power_curve():
    from windpowerlib import WindTurbine
    t = WindTurbine(turbine_type=TURBINE, hub_height=100)
    pc = t.power_curve.sort_values('wind_speed')
    return pc.wind_speed.values.astype(float), (pc.value.values / t.nominal_power).astype(float)


def wind_cf(ws, curve, scale=1.0):
    v, p = curve
    return np.interp(ws * scale, v, p, left=0.0, right=0.0)


def calibrate(ws, curve, target):
    lo, hi = 0.3, 3.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if wind_cf(ws, curve, mid).mean() < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def pam(X, k):
    """Deterministik k-medoids (BUILD + SWAP), öklid uzaklığı."""
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    med = [int(np.argmin(D.sum(1)))]
    while len(med) < k:
        cur = D[:, med].min(1)
        gains = [(cur - np.minimum(cur, D[:, c])).sum() if c not in med else -1 for c in range(len(X))]
        med.append(int(np.argmax(gains)))
    improved = True
    while improved:
        improved = False
        cost = D[:, med].min(1).sum()
        for mi in range(k):
            for c in range(len(X)):
                if c in med:
                    continue
                trial = med.copy(); trial[mi] = c
                tc = D[:, trial].min(1).sum()
                if tc < cost - 1e-12:
                    med, cost, improved = trial, tc, True
    labels = np.argmin(D[:, med], 1)
    return med, labels


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, default=2023)
    ap.add_argument('--k', type=int, default=6, help='mevsim başına temsilî gün sayısı')
    ap.add_argument('--refresh', action='store_true')
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

    sites = pd.read_csv(SITES)
    curve = power_curve()
    hours = pd.date_range(f'{a.year}-01-01', f'{a.year}-12-31 23:00', freq='h')
    frames, sources = [], {}
    for s in sites.itertuples():
        era, h1, st1 = fetch(f'era5_{s.code}_{a.year}.json', ERA5_URL,
                             {'latitude': s.lat, 'longitude': s.lon, 'start_date': f'{a.year}-01-01',
                              'end_date': f'{a.year}-12-31', 'hourly': 'wind_speed_100m',
                              'wind_speed_unit': 'ms', 'timezone': 'UTC', 'models': 'era5'}, a.refresh)
        pv, h2, st2 = fetch(f'pvgis_{s.code}_{a.year}.json', PVGIS_URL,
                            {'lat': s.lat, 'lon': s.lon, 'startyear': a.year, 'endyear': a.year,
                             'pvcalculation': 1, 'peakpower': 1, 'loss': 14, 'optimalangles': 1,
                             'outputformat': 'json', 'raddatabase': 'PVGIS-SARAH3'}, a.refresh)
        ws = pd.Series(era['hourly']['wind_speed_100m'], index=pd.to_datetime(era['hourly']['time'])).reindex(hours)
        ws = ws.interpolate(limit_direction='both').values
        target = s.cell_wind_cf_eligible_pct / 100.0
        k = calibrate(ws, curve, target)
        cf_w = wind_cf(ws, curve, k)
        ph = pd.DataFrame(pv['outputs']['hourly'])
        t = pd.to_datetime(ph.time, format='%Y%m%d:%H%M').dt.floor('h')
        cf_pv = pd.Series(ph.P.values / 1000.0, index=t).groupby(level=0).mean().reindex(hours).fillna(0).values
        frames.append(pd.DataFrame({'time': hours, 'site': s.code, 'wind_cf': cf_w.round(5), 'pv_cf': cf_pv.round(5)}))
        sources[s.code] = {
            'era5': {'url': ERA5_URL, 'sha256': h1, 'status': st1, 'grid_point': [era.get('latitude'), era.get('longitude')]},
            'pvgis': {'url': PVGIS_URL, 'sha256': h2, 'status': st2,
                      'optimal_slope_deg': pv['inputs']['mounting_system']['fixed']['slope']['value']},
            'gwa_target_gross_cf': target, 'wind_speed_scale': round(k, 4),
            'era5_raw_cf': round(float(wind_cf(ws, curve).mean()), 4),
            'wind_cf_mean': round(float(cf_w.mean()), 4), 'pv_cf_mean': round(float(cf_pv.mean()), 4),
            'wind_pv_hourly_corr': round(float(np.corrcoef(cf_w, cf_pv)[0, 1]), 3),
        }
        print(f'{s.code} {s.province}: ölçek {k:.3f}, rüzgâr KF {cf_w.mean():.3f}, GES KF {cf_pv.mean():.3f}')
    prof = pd.concat(frames, ignore_index=True)
    prof.to_csv(OUT / f'hourly_profiles_{a.year}.csv', index=False)

    # Temsilî günler
    prof['date'] = prof.time.dt.date
    prof['hour'] = prof.time.dt.hour
    wide = prof.pivot_table(index='date', columns=['site', 'hour'], values=['wind_cf', 'pv_cf'])
    wide = wide[[c for c in wide.columns]].dropna()
    months = pd.to_datetime(pd.Series(wide.index)).dt.month.values
    rows, assign = [], []
    for season, ms in SEASONS.items():
        idx = np.where(np.isin(months, ms))[0]
        X = wide.values[idx]
        med, lab = pam(X, a.k)
        for j, m in enumerate(med):
            day = wide.index[idx[m]]
            w = int((lab == j).sum())
            sub = prof[prof.date == day]
            for r in sub.itertuples():
                rows.append({'season': season, 'rep_day': f'{season}{j + 1}', 'date': str(day), 'weight_days': w,
                             'hour': r.hour, 'site': r.site, 'wind_cf': r.wind_cf, 'pv_cf': r.pv_cf})
        assign += [{'date': str(wide.index[i]), 'season': season, 'rep_day': f'{season}{lab[n] + 1}'} for n, i in enumerate(idx)]
    rep = pd.DataFrame(rows)
    # Yıllık enerjiyi koruma: site × teknoloji için ağırlıklı ortalama tam yıl ortalamasına eşitlenir
    # (KF ≤ 1 sınırı nedeniyle ölçek yinelemeli bulunur).
    rep_scale = {}
    for s in sites.code:
        for col in ['wind_cf', 'pv_cf']:
            m = rep.site == s
            target = prof.loc[prof.site == s, col].mean()
            base = rep.loc[m, col].values.copy()
            wts = rep.loc[m, 'weight_days'].values
            f = 1.0
            for _ in range(50):
                cur = (np.minimum(base * f, 1.0) * wts).sum() / wts.sum()
                if cur <= 0:
                    break
                f *= target / cur
            rep.loc[m, col] = np.minimum(base * f, 1.0).round(5)
            rep_scale[f'{s}_{col}'] = round(f, 4)
    rep.to_csv(OUT / f'representative_days_{a.year}_k{a.k}.csv', index=False)
    pd.DataFrame(assign).to_csv(OUT / f'day_assignment_{a.year}_k{a.k}.csv', index=False)

    # Temsil doğruluğu: ağırlıklı temsilî günlerden yıllık ortalama KF vs tam yıl
    check = {}
    for s in sites.code:
        r = rep[rep.site == s]
        wmean = lambda col: float((r[col] * r.weight_days).sum() / (r.weight_days.sum()))
        full = prof[prof.site == s]
        check[s] = {'wind_full': round(full.wind_cf.mean(), 4), 'wind_rep': round(wmean('wind_cf'), 4),
                    'pv_full': round(full.pv_cf.mean(), 4), 'pv_rep': round(wmean('pv_cf'), 4)}
    manifest = {'run_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'year': a.year,
                'k_per_season': a.k, 'turbine': TURBINE, 'hub_height_m': 100, 'pv': '1 kWp fixed, optimal tilt, 14% loss',
                'sources': sources, 'representation_check': check, 'energy_preserving_scale': rep_scale,
                'outputs_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob(f'*{a.year}*.csv'))}}
    (OUT / f'profiles_manifest_{a.year}.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(check, indent=1))


if __name__ == '__main__':
    main()
