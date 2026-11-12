"""
Aşama I aday seçiminin eşik duyarlılığı (yalnız B aşaması, ağ gerektirmez).

Dondurulmuş özellik tablosu üzerinde önceden tanımlı senaryoları çalıştırır ve her aday hücrenin
kaç senaryoda seçildiğini raporlar.

Kullanım:  python code/gis/sensitivity_stageB.py
Çıktı:     data/processed/gis_sensitivity/{scenario_candidates.csv, candidate_frequency.csv}
"""
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / 'data/raw/gis/real/grid_cells_features.csv'
OUT = ROOT / 'data/processed/gis_sensitivity'
SCENARIOS = {
    'base': [],
    'wind_cf20': ['C_wind_cf_variant=0.20'],
    'wind_cf30': ['C_wind_cf_variant=0.30'],
    'pv_patch10': ['C_pv_variant="p10"', 'C_pv_area_min_km2=10'],
    'pv_with_cropland': ['C_pv_variant="withcrop"'],
    'ghi1550': ['C_ghi_min_kwh_m2_yr=1550'],
    'water30': ['C_water_max_km=30'],
    'substation30': ['C_substation_max_km=30'],
    'spacing_none': ['min_spacing_km=0'],
    'spacing50': ['min_spacing_km=50'],
    'spacing150': ['min_spacing_km=150'],
    'spacing200': ['min_spacing_km=200'],
}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    rows = []
    for name, sets in SCENARIOS.items():
        out = OUT / name
        cmd = [sys.executable, '-I', str(ROOT / 'code/gis/gis_pipeline_real.py'),
               '--from-features', str(FEATURES), '--out', str(out)]
        for s in sets:
            cmd += ['--set', s]
        subprocess.run(cmd, check=True, capture_output=True)
        summary = json.loads((out / 'gis_summary.json').read_text(encoding='utf-8'))
        for big in ['grid_cells_layers.csv', 'Fig1_GIS_filter_results.png']:   # disk tasarrufu; özet JSON'da SHA-256 kayıtlı
            (out / big).unlink(missing_ok=True)
        for c in summary['candidates']:
            rows.append({'scenario': name, 'eligible_cells': summary['counts']['eligible'],
                         'clusters': summary['counts']['clusters'], **{k: c[k] for k in
                         ['code', 'cell_id', 'province', 'lat', 'lon', 'cluster_eligible_area_km2']}})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / 'scenario_candidates.csv', index=False)

    base = df[df.scenario == 'base']
    cells = pd.read_csv(FEATURES, usecols=['cell_id', 'lon', 'lat'])
    freq = []
    for b in base.itertuples():
        # bir senaryodaki aday, temel adaya ≤ 0.3° (~30 km) uzaklıktaysa aynı bölge sayılır
        near = df[((df.lat - b.lat) ** 2 + (df.lon - b.lon) ** 2) ** 0.5 <= 0.3]
        freq.append({'base_code': b.code, 'province': b.province, 'lat': b.lat, 'lon': b.lon,
                     'scenarios_selected': near.scenario.nunique(), 'n_scenarios': len(SCENARIOS),
                     'scenarios': ', '.join(sorted(near.scenario.unique()))})
    pd.DataFrame(freq).to_csv(OUT / 'candidate_frequency.csv', index=False)
    print(pd.DataFrame(freq)[['base_code', 'province', 'lat', 'lon', 'scenarios_selected', 'n_scenarios']].to_string(index=False))


if __name__ == '__main__':
    main()
