"""
RFNBO emisyon kontrolü (son işlem). Elektroliz elektriği eş konumlu yeni yenilenebilir kaynaktan geldiği için
sıfır kabul edilir (Delegated Regulation (EU) 2023/1185). Sayılan kalemler:
  - şebeke elektriği: depo enjeksiyon sıkıştırması, boru hattı ara sıkıştırması ve (S-grid'de) şebeke çekişi;
  - tüp römork taşımacılığı: dizel, kuyudan tekerleğe, boş dönüş dahil.
Sonuç: kg CO2e / kg teslim edilen H2, eşik 3.38 ile karşılaştırılır. Römork yükü (300 / 1000 / 1300 kg)
duyarlılık olarak verilir.

Çıktı: data/processed/stage3/emissions_rfnbo.csv
Kullanım: python code/optimization/emissions.py
"""
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
S3 = ROOT / 'data/processed/stage3'


def intensity(sol, flows, E, payload):
    kg_del = sol.delivered_t * 1000
    grid_t = sol.q_ptf_MWh_cost * E['grid_ef_t_per_mwh']
    trips = 2 if E['empty_return'] else 1
    l_per_km = E['truck_fuel_l_per_100km'] / 100
    tr = flows[flows['mode'] == 'truck']
    # t CO2e = (t H2 * 1000 / yük kg) sefer x mesafe x L/km x kg/L / 1000
    truck_t = (tr.t_per_yr * 1000 / payload * trips * tr.road_km * l_per_km * E['diesel_wtw_kg_per_l'] / 1000).sum()
    leg = trips * tr.road_km * l_per_km * E['diesel_wtw_kg_per_l'] / payload        # kg CO2e / kg H2, bacak
    return {'grid_kg_per_kg': grid_t * 1000 / kg_del, 'truck_kg_per_kg': truck_t * 1000 / kg_del,
            'total_kg_per_kg': (grid_t + truck_t) * 1000 / kg_del,
            'max_truck_leg_kg_per_kg': float(leg.max()) if len(leg) else 0.0,
            'truck_share_of_deliveries': tr.t_per_yr.sum() / sol.delivered_t}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    P = yaml.safe_load((ROOT / 'data/raw/params/params.yaml').read_text(encoding='utf-8'))
    E = P['emissions']
    rows = []
    cases = [(d.name, d / 'solution.csv', d / 'flows.csv', None) for d in sorted(S3.iterdir())
             if d.is_dir() and (d / 'solution.csv').exists() and (d / 'flows.csv').stat().st_size > 10]
    par = S3 / 'base_pareto'
    if (par / 'pareto.csv').exists():
        pp, pf = pd.read_csv(par / 'pareto.csv'), pd.read_csv(par / 'pareto_flows.csv')
        for _, r in pp.drop_duplicates('step').iterrows():
            cases.append((f'pareto:{r.step}', r, pf[pf.step == r.step], 'row'))
    for name, sol, fl, kind in cases:
        if kind is None:
            sol, fl = pd.read_csv(sol).iloc[0], pd.read_csv(fl)
        for pl in E['trailer_payload_kg']:
            r = intensity(sol, fl, E, pl)
            rows.append({'case': name, 'payload_kg': pl, **{k: round(v, 4) for k, v in r.items()},
                         'rfnbo_ok': r['total_kg_per_kg'] <= E['rfnbo_threshold_kg_per_kg'],
                         'LCOH_E_eur_kg': round(sol.LCOH_E_eur_kg, 3), 'Q_bar': round(sol.Q_bar, 4)})
    df = pd.DataFrame(rows)
    df.to_csv(S3 / 'emissions_rfnbo.csv', index=False)
    print(df[df.payload_kg == 1000].drop(columns='payload_kg').to_string(index=False))
    print('\nRömork yükü duyarlılığı (temel):')
    print(df[df.case == 'base'][['payload_kg', 'truck_kg_per_kg', 'total_kg_per_kg', 'max_truck_leg_kg_per_kg', 'rfnbo_ok']].to_string(index=False))


if __name__ == '__main__':
    main()
