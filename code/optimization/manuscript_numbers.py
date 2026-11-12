"""
Makalede geçen türetilmiş sayıların tek kaynağı (yüzdeler, kg başına kırılımlar, farklar).
Girdi: data/processed/stage2, stage3, stage4 çıktıları. Çıktı: data/processed/manuscript_numbers.json
Kullanım: python code/optimization/manuscript_numbers.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PR = ROOT / 'data/processed'
S3 = PR / 'stage3'
SITES = ['S1', 'S2', 'S3', 'S4', 'S5']


def sol(tag):
    return pd.read_csv(S3 / tag / 'solution.csv').iloc[0]


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    N = {}
    b = sol('base')
    kg = b.delivered_t * 1000
    parts = {c[5:-5]: b[c] for c in b.index if c.startswith('cost_')}
    N['base_cost_eur_per_kg'] = {k: round(v * 1e6 / kg, 3) for k, v in parts.items()}
    prod = sum(parts[k] for k in ['wind', 'pv', 'electrolyser', 'stack', 'water', 'export_revenue'])
    logi = sum(parts[k] for k in ['compressor', 'pipeline', 'truck', 'cavern', 'grid_energy'])
    N['base_production_eur_kg'] = round(prod * 1e6 / kg, 2)
    N['base_logistics_eur_kg'] = round(logi * 1e6 / kg, 2)
    N['base_truck_share_of_logistics'] = round(parts['truck'] / logi, 3)
    N['base_LCOH_E'] = round(b.LCOH_E_eur_kg, 2)
    N['base_f1_MEUR'] = round(b.f1 / 1e6, 1)
    N['base_Ez_MEUR'] = round(b.E_z / 1e6, 1)
    N['base_zmin_zmax_MEUR'] = [round(b.z_min / 1e6, 1), round(b.z_max / 1e6, 1)]
    N['base_delivered_kt'] = round(b.delivered_t / 1e3, 1)
    N['base_capacity_MW'] = {'wind': round(b.q_wind_MW), 'pv': round(b.q_pv_MW), 'ely': round(b.q_ely_MW)}
    N['base_sites'] = {i: {'W': round(b[f'{i}_W_MW']), 'PV': round(b[f'{i}_PV_MW']), 'E': round(b[f'{i}_E_MW']),
                           'H2_kt': round(b[f'{i}_H2_t'] / 1e3, 1), 'FLH': round(b[f'{i}_FLH_h'])} for i in SITES}
    N['base_mean_FLH'] = round(b.produced_t * 55.0 / b.q_ely_MW)
    N['base_export_TWh'] = round(b.q_ptf_MWh_rev / 1e6, 2)
    N['base_cavern_kt'] = round(b.cavern_t / 1e3, 1)
    man = json.loads((S3 / 'base' / 'manifest.json').read_text(encoding='utf-8'))
    N['land_limit_MW'] = {i: {'W': round(man['Wmax_MW'][i]), 'PV': round(man['Pmax_MW'][i])} for i in SITES}
    fl = pd.read_csv(S3 / 'base' / 'flows.csv')
    tr = fl[fl['mode'] == 'truck']
    N['base_flows_kt'] = {'pipe': round(fl[fl['mode'] == 'pipe'].t_per_yr.sum() / 1e3, 1), 'truck': round(tr.t_per_yr.sum() / 1e3, 1),
                          'via_tuzgolu': round(fl[fl.destination == 'TR_UGS_TUZGOLU'].t_per_yr.sum() / 1e3, 1)}
    N['base_mean_truck_haul_km'] = round((tr.t_per_yr * tr.road_km).sum() / tr.t_per_yr.sum())
    N['base_max_truck_haul_km'] = round(tr.road_km.max())
    dt = sol('deterministic')
    N['det_LCOH'] = round(dt.LCOH_E_eur_kg, 2)

    sc = pd.read_csv(S3 / 'summary_scenarios.csv').set_index('scenario')
    N['scenarios'] = {s: {'LCOH': round(r.LCOH_E_eur_kg, 2), 'delivered_kt': round(r.delivered_kt, 1), 'alpha': round(r.alpha_mean, 2),
                          'Qbar': round(r.Q_bar, 6), 'ely_MW': round(r.ely_MW), 'wind_MW': round(r.wind_MW), 'pv_MW': round(r.pv_MW),
                          'cavern_kt': round(r.cavern_kt, 1), 'sites': r.open_sites, 'pipelines': r.pipelines}
                      for s, r in sc.iterrows()}
    for t in ['grid', 'delta12_5', 'delta15']:          # özet tablosundan önce çözülenler
        if t not in N['scenarios']:
            r = sol(t)
            al = [r[c] for c in r.index if c.startswith('alpha_')]
            N['scenarios'][t] = {'LCOH': round(r.LCOH_E_eur_kg, 2), 'delivered_kt': round(r.delivered_t / 1e3, 1),
                                 'alpha': round(sum(al) / len(al), 2), 'Qbar': round(r.Q_bar, 6), 'ely_MW': round(r.q_ely_MW),
                                 'wind_MW': round(r.q_wind_MW), 'pv_MW': round(r.q_pv_MW), 'cavern_kt': round(r.cavern_t / 1e3, 1),
                                 'sites': r.open_sites, 'pipelines': r.pipelines}
    g = sol('grid')
    N['grid_import_export_TWh'] = [round(g.q_ptf_MWh_cost / 1e6, 2), round(g.q_ptf_MWh_rev / 1e6, 2)]
    N['grid_mip_gap'] = round(float(g.mip_gap), 4)

    em = pd.read_csv(S3 / 'emissions_rfnbo.csv')
    N['emissions'] = {f'{r.case}|{r.payload_kg}': {'total': r.total_kg_per_kg, 'truck': r.truck_kg_per_kg, 'grid': r.grid_kg_per_kg,
                                                   'max_leg': r.max_truck_leg_kg_per_kg}
                      for r in em.itertuples() if not r.case.startswith('pareto')}
    pf = pd.read_csv(S3 / 'base_pareto' / 'pareto_front_final.csv')
    lo, hi, kn = pf.iloc[0], pf.iloc[-1], pf[pf.is_knee].iloc[0]
    N['pareto'] = {'n_points': len(pf), 'Q0': round(lo.Q_bar, 3), 'Qmax': round(hi.Q_bar, 3), 'Qknee': round(kn.Q_bar, 3),
                   'LCOH0': round(lo.LCOH_E_eur_kg, 2), 'LCOHknee': round(kn.LCOH_E_eur_kg, 2), 'LCOHmax': round(hi.LCOH_E_eur_kg, 2),
                   'f1_0': round(lo.f1 / 1e6, 1), 'f1_knee': round(kn.f1 / 1e6, 1), 'f1_max': round(hi.f1 / 1e6, 1),
                   'knee_dQ_pct': round(100 * (kn.Q_bar / lo.Q_bar - 1), 1), 'knee_df1_pct': round(100 * (kn.f1 / lo.f1 - 1), 1),
                   'max_dQ_pct': round(100 * (hi.Q_bar / lo.Q_bar - 1), 1), 'max_df1_pct': round(100 * (hi.f1 / lo.f1 - 1), 1),
                   'knee_to_max_dQ_pct': round(100 * (hi.Q_bar / kn.Q_bar - 1), 1),
                   'knee_to_max_df1_pct': round(100 * (hi.f1 / kn.f1 - 1), 1),
                   'sites_max': hi.open_sites, 'max_gap': round(float(pf.mip_gap.max()), 4)}

    # V4: φ duyarlılığı tek amaçlı çözümlerle raporlanır (ayrı Pareto cepheleri yok)
    N['land_co_use_single_objective'] = {}
    for phi, tag in [('1.0', 'base'), ('0.5', 'phi0_5'), ('0.0', 'phi0_0')]:
        m = sol(tag)
        N['land_co_use_single_objective'][phi] = {'LCOH': round(float(m.LCOH_E_eur_kg), 2), 'sites': m.open_sites,
                                                  'pipelines': m.pipelines, 'mip_gap': round(float(m.mip_gap), 6)}
    lam = {t: sol(t) for t in ['base', 'lambda0_25', 'lambda0_75']}
    N['lambda_capacity_range_pct'] = {k: round(100 * (max(r[f'q_{k}'] for r in lam.values()) - min(r[f'q_{k}'] for r in lam.values()))
                                               / lam['base'][f'q_{k}'], 1) for k in ['wind_MW', 'pv_MW', 'ely_MW']}
    N['n_pipelines'] = {t: len(str(sol(t).pipelines).split(',')) for t in ['base', 'delta20', 'gamma0', 'gamma0_5', 'lambda0_75', 'land_cluster', 'demand_upper']}
    mc = pd.read_csv(PR / 'stage4' / 'stage3_mc_summary.csv').set_index('design')
    N['mc'] = {d: {'cost_mean': round(r.cost_mean), 'cost_p05': round(r.cost_p05), 'cost_p95': round(r.cost_p95),
                   'p_short_system': round(r.p_shortfall_system, 3), 'p_short_any_node': round(r.p_shortfall_any_node, 3), 'short_kt': round(r.shortfall_mean_t / 1e3, 1)} for d, r in mc.iterrows()}
    be = PR / 'stage4' / 'stage3_mc_breakeven.csv'
    if be.exists():
        N['mc_breakeven_eur_kg'] = pd.read_csv(be).set_index('design').breakeven_import_eur_kg.round(1).to_dict()
    ev = pd.read_csv(PR / 'stage4' / 'stage3_mc_delta_eval.csv')
    N['mc_delta_eval'] = {f'{r.design}|{r.delta_eval_eur_kg}': [round(r.total_mean_MEUR), round(r.total_p95_MEUR)] for r in ev.itertuples()}
    st = json.loads((PR / 'stage4' / 'stage2_stability.json').read_text(encoding='utf-8'))
    N['stage2_stability'] = {'ranking': st['baseline_ranking'],
                             'by_sigma': {str(r['sigma_rel']): {'SI': r['SI_top'], 'RPR': r['RPR']} for r in st['results']}}
    q_path = PR / 'stage2' / 'stage2_scores.csv' if (PR / 'stage2' / 'stage2_scores.csv').exists() else PR / 'stage2' / 'stage2_scores_provisional.csv'
    q = pd.read_csv(q_path)
    N['stage2_Q01'] = {r.site: round(r.Q01, 3) for r in q.itertuples()}
    w_path = PR / 'stage2' / 'stage2_weights.csv' if (PR / 'stage2' / 'stage2_weights.csv').exists() else PR / 'stage2' / 'stage2_weights_provisional.csv'
    w = pd.read_csv(w_path)
    N['stage2_w'] = {r.criterion: round(r.w_final, 3) for r in w.itertuples()}
    (PR / 'manuscript_numbers.json').write_text(json.dumps(N, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(N, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
