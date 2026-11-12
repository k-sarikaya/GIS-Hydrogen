"""
V4 makale tabloları: Aşama III duyarlılık tablosu, karşı-olgusal karşılaştırma ve Monte Carlo tablosu
doğrudan çözüm dosyalarından LaTeX satırı olarak üretilir (elle sayı yazılmaz).

Çıktılar: manuscript/generated/tab_sensitivity.tex, tab_counterfactual.tex, tab_mc.tex, numbers_v4.json
          submission_assets/supplementary/Supplementary_Table_S6_Run_Register.csv
Kullanım: python code/tools/v4_tables.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
S3 = ROOT / 'data/processed/stage3'
S4 = ROOT / 'data/processed/stage4'
GEN = ROOT / 'manuscript/generated'
SUP = ROOT / 'submission_assets/supplementary'
SITES = ['S1', 'S2', 'S3', 'S4', 'S5']
Q = pd.read_csv(ROOT / 'data/processed/stage2/stage2_scores.csv').set_index('site').Q01.to_dict()

SENS = [
    ('base', r'Baseline (cell land, $\phi=1$)'),
    ('deterministic', r'Deterministic (modal values, $\gamma = 0$)'),
    ('land_cluster', 'Cluster-level land (second baseline)'),
    ('phi0_5', r'Co-use $\phi=0.5$'),
    ('phi0_0', r'Exclusive land $\phi=0$'),
    ('island', 'S-island (no surplus sales)'),
    ('grid', 'S-grid (annual matching)'),
    ('sec48', r'$\eta = 48$\,kWh/kg'),
    ('sec57_5', r'$\eta = 57.5$\,kWh/kg'),
    ('trailer_h4400', 'Trailer hours 4,400\\,h/yr'),
    ('trailer_h8000', 'Trailer hours 8,000\\,h/yr'),
    ('pipe_geo_cap', r'Pipeline length $\le 1.2\times$ geodesic'),
    ('pipe12_cap311', '12-inch capacity 311\\,t/d'),
    ('pipe12_dea', '12-inch cost and capacity, DEA (2025)'),
    ('pipe_capex135', 'Pipeline CAPEX $+35\\%$ (DEA owner\'s costs)'),
    ('demand_upper', 'Upper-bound demand (42\\% for all)'),
    ('gamma0', r'$\gamma = 0$'),
    ('gamma0_25', r'$\gamma = 0.25$'),
    ('lambda0_25', r'$\lambda = 0.25$'),
    ('lambda0_75', r'$\lambda = 0.75$'),
    ('delta10', r'$\delta = 10$'),
    ('delta12_5', r'$\delta = 12.5$'),
    ('delta15', r'$\delta = 15$'),
    ('delta20', r'$\delta = 20$'),
]


def sol(tag):
    f = S3 / tag / 'solution.csv'
    return pd.read_csv(f).iloc[0] if f.exists() else None


def qbar(s):
    prod = sum(s[f'{i}_H2_t'] for i in SITES)
    return sum(Q[i] * s[f'{i}_H2_t'] for i in SITES) / max(prod, 1e-9)


def npipes(s):
    p = str(s.pipelines) if isinstance(s.pipelines, str) else ''
    if not p:
        return '0'
    items = p.split(',')
    small = sum('[12in]' in x for x in items)
    large = len(items) - small
    parts = ([f'{large}$\\times$20$^{{\\prime\\prime}}$'] if large else []) + ([f'{small}$\\times$12$^{{\\prime\\prime}}$'] if small else [])
    return ' + '.join(parts)


def trailer_final_share(tag, s):
    f = pd.read_csv(S3 / tag / 'flows.csv')
    fin = f[(f.destination != 'TR_UGS_TUZGOLU') & (f['mode'] == 'truck')]
    return fin.t_per_yr.sum() / max(s.delivered_t, 1e-9)


def sens_table(N):
    rows, reg = [], []
    for tag, lab in SENS:
        s = sol(tag)
        if s is None:
            continue
        a = np.mean([s[c] for c in s.index if c.startswith('alpha_')])
        tsh = trailer_final_share(tag, s)
        rows.append(f"{lab} & {s.LCOH_E_eur_kg:.2f} & {s.delivered_t / 1e3:.1f} & {a:.2f} & {s.q_wind_MW / 1e3:.2f} & "
                    f"{s.q_pv_MW / 1e3:.2f} & {s.q_ely_MW / 1e3:.2f} & {abs(s.cavern_t) / 1e3:.1f} & {s.open_sites.replace(',', ', ')} & "
                    f"{npipes(s)} & {tsh:.2f} & {qbar(s):.3f} \\\\")
        reg.append({'Run': tag, 'Description': lab.replace('$', '').replace('\\', ''), 'Delivered cost (EUR/kg)': round(s.LCOH_E_eur_kg, 3),
                    'Delivered (kt/yr)': round(s.delivered_t / 1e3, 1), 'Open sites': s.open_sites, 'Pipelines': s.pipelines,
                    'MIP gap': round(float(s.mip_gap), 5), 'Status': s.solver_status})
        N[f'lcoh_{tag}'] = round(float(s.LCOH_E_eur_kg), 2)
    (GEN / 'tab_sensitivity.tex').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    for tag in ['abl0_v3equiv', 'abl1_demand', 'abl2_merge', 'abl3_small', 'import_free', 'import_free_d10',
                'import_free_d12_5', 'import_free_d15', 'outage_cavern', 'outage_pipeline', 'cf_top3_det', 'cf_top3_rpp']:
        s = sol(tag)
        if s is not None:
            reg.append({'Run': tag, 'Description': tag, 'Delivered cost (EUR/kg)': round(s.LCOH_E_eur_kg, 3),
                        'Delivered (kt/yr)': round(s.delivered_t / 1e3, 1), 'Open sites': s.open_sites, 'Pipelines': s.pipelines,
                        'MIP gap': round(float(s.mip_gap), 5), 'Status': s.solver_status})
    pd.DataFrame(reg).to_csv(SUP / 'Supplementary_Table_S6_Run_Register.csv', index=False, encoding='utf-8-sig')
    N['max_mip_gap_singles'] = float(max(r['MIP gap'] for r in reg if r['MIP gap'] == r['MIP gap']))


def cf_table(N):
    rows = []
    spec = [('base', 'Integrated RPP (all candidates, suitability objective at cost optimum)'),
            ('deterministic', 'Deterministic (all candidates)'),
            ('cf_top3_rpp', 'Sequential: top-3 by ranking, then RPP'),
            ('cf_top3_det', 'Sequential: top-3 by ranking, then deterministic')]
    for tag, lab in spec:
        s = sol(tag)
        if s is None:
            continue
        modal = None
        rows.append(f"{lab} & {s.LCOH_E_eur_kg:.2f} & {s.f1 / 1e6:,.0f} & {qbar(s):.3f} & {s.open_sites.replace(',', ', ')} & {npipes(s)} \\\\")
        N[f'cf_{tag}'] = {'lcoh': round(float(s.LCOH_E_eur_kg), 2), 'qbar': round(qbar(s), 4), 'f1_MEUR': round(float(s.f1) / 1e6, 1)}
    (GEN / 'tab_counterfactual.tex').write_text('\n'.join(rows) + '\n', encoding='utf-8')


def mc_table(N):
    f = S4 / 'stage3_mc_summary.csv'
    if not f.exists():
        return
    m = pd.read_csv(f).set_index('design')
    ev = pd.read_csv(S4 / 'stage3_mc_delta_eval.csv')
    lab = {'deterministic': 'Deterministic', 'base': 'Baseline RPP', 'delta12_5': r'RPP, $\delta = 12.5$',
           'delta15': r'RPP, $\delta = 15$', 'delta20': r'RPP, $\delta = 20$', 'phi0_5': r'Co-use $\phi = 0.5$',
           'phi0_0': r'Exclusive land $\phi = 0$', 'cf_top3_det': 'Sequential top-3 (deterministic)'}
    rows = []
    for d in ['deterministic', 'base', 'delta12_5', 'delta15', 'delta20', 'cf_top3_det', 'phi0_5', 'phi0_0']:
        if d not in m.index:
            continue
        r = m.loc[d]
        cells = []
        for de in [7.30, 20, 30]:
            e = ev[(ev.design == d) & (np.isclose(ev.delta_eval_eur_kg, de))].iloc[0]
            cells.append(f"{e.total_mean_MEUR:,.0f} / {e.total_p95_MEUR:,.0f}")
        rows.append(f"{lab[d]} & {r.cost_mean:,.0f} & {r.cost_p95:,.0f} & {r.p_shortfall_system:.2f} & {r.shortfall_mean_t / 1e3:.1f} & "
                    + ' & '.join(cells) + ' \\\\')
        N[f'mc_{d}'] = {k: float(r[k]) for k in ['cost_mean', 'cost_p95', 'p_shortfall_system', 'p_shortfall_any_node',
                                                  'shortfall_mean_t', 'lcoh_mean_eur_kg', 'mean_triangular_MEUR', 'E_Me_MEUR']}
    (GEN / 'tab_mc.tex').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    be = S4 / 'stage3_mc_breakeven.csv'
    if be.exists():
        N['mc_breakeven'] = pd.read_csv(be).set_index('design').breakeven_import_eur_kg.round(1).to_dict()


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    GEN.mkdir(parents=True, exist_ok=True)
    N = {}
    sens_table(N)
    cf_table(N)
    mc_table(N)
    (GEN / 'numbers_v4.json').write_text(json.dumps(N, indent=2, ensure_ascii=False), encoding='utf-8')
    for f in ['tab_sensitivity.tex', 'tab_counterfactual.tex', 'tab_mc.tex']:
        if (GEN / f).exists():
            print('==', f); print((GEN / f).read_text(encoding='utf-8'))
    print(json.dumps(N, indent=1))


if __name__ == '__main__':
    main()
