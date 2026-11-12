"""
Aşama IV — Monte Carlo sağlamlık değerlendirmesi (Aşama II ve III ile tutarlı).

(a) Aşama II sıralama kararlılığı. Ağırlıklar w'_j = w_j(1 + σ ε_j), ε ~ N(0,1), kırpılır ve
    normalize edilir; α sabit (0.5) tutulur. SI = ilk sıradaki sahanın korunma oranı,
    RPR = tüm sıralamanın korunma oranı.
(b) Aşama III tasarımlarının değerlendirilmesi (V4). Tasarım ve işletme miktarları (rpp_model.py çıktısındaki
    q_* sütunları) sabit tutulur; yeniden dağıtım (recourse) yoktur. İki örnekleme okuması:
      - 'coefficient' (temel, RPP ile tutarlı): RPP amacındaki yıllıklandırılmış birim maliyet TFN'lerinin
        (rpp_model.coefficients) her biri kendi üçgen dağılımından bağımsız örneklenir; RPP'nin kullandığı
        belirsizlik nesnesi budur.
      - 'component' (v3 okuması, ikincil): CAPEX, WACC, ömür vb. ayrı ayrı örneklenir, sonra yıllıklandırılır.
    Talep: tek ortak U(0,1) çekilişi her sektörün TFN'sine ters dağılım fonksiyonuyla eşlenir (komonoton);
    düğüm talebi bileşen tesislerin toplamıdır. Karşılanamayan talep düğümün ithalat paritesiyle (sektöre göre δ)
    fiyatlanır. P(eksik) sistem düzeyinde (toplam talep > toplam teslim) ve düğüm düzeyinde (herhangi bir düğüm) verilir.
    Not: üçgen dağılım, olabilirlik dağılımının olasılıksal bir yorumudur; sonuçlar bu varsayım altında okunmalıdır.

Kullanım: python code/optimization/stage4_monte_carlo.py [--n 10000] [--designs base,deterministic,delta12_5,delta15,delta20]
"""
import argparse
import copy
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/optimization'))
sys.path.insert(0, str(ROOT / 'code/mcdm'))
import rpp_model as rm                     # noqa: E402
import sf_critic_waspas as sf              # noqa: E402

OUT = ROOT / 'data/processed/stage4'
SEED = 20261018


def sample_params(P, rng):
    Ps = copy.deepcopy(P)

    def rec(d):
        for k, v in d.items():
            if isinstance(v, dict):
                if 'tfn' in v:
                    lo, mo, hi = v['tfn']
                    x = lo if hi == lo else rng.triangular(lo, mo, hi)
                    v['tfn'] = [x, x, x]
                else:
                    rec(v)
    rec(Ps)
    return Ps


def stage2_stability(n, sigmas, rng):
    cand = ROOT / 'data/survey/expert_responses.csv'
    survey_path = str(cand) if cand.exists() else None
    mode = 'survey' if survey_path else 'provisional'
    out_sf = sf.run(mode, 0.5, 0.5, survey_path=survey_path)
    res, wt = out_sf[0], out_sf[1]
    matrix = out_sf[6] if len(out_sf) > 6 else out_sf[0]
    crit = list(wt.index)
    w0 = wt.w_final.values
    base_rank = list(res.sort_values('Q', ascending=False).site)
    top = base_rank[0]
    results = []
    for sigma in sigmas:
        keep_top = keep_all = 0
        first = {s: 0 for s in sf.SITES}
        for _ in range(n):
            w = np.clip(w0 * (1 + sigma * rng.standard_normal(len(w0))), 1e-6, None)
            w = w / w.sum()
            q = {}
            for s in sf.SITES:
                x = [matrix[k][s] for k in crit]
                q[s] = 0.5 * sf.score(sf.swam(x, w)) + 0.5 * sf.score(sf.swgm(x, w))
            rank = sorted(q, key=q.get, reverse=True)
            first[rank[0]] += 1
            keep_top += rank[0] == top
            keep_all += rank == base_rank
        results.append({'sigma_rel': sigma, 'SI_top': keep_top / n, 'RPR': keep_all / n,
                        'share_first': {s: v / n for s, v in first.items()}})
    return {'mode': f'{mode} ({len(crit)} criteria)', 'n': n, 'baseline_ranking': base_rank, 'results': results}


def tri_inv(v, u):
    """Üçgen dağılımın ters CDF'si; v = (a, m, b)."""
    a, m, b = map(float, v)
    if b <= a:
        return a
    fc = (m - a) / (b - a)
    return a + np.sqrt(u * (b - a) * (m - a)) if u < fc else b - np.sqrt((1 - u) * (b - a) * (b - m))


def stage3_mc(P, designs, n, rng, sampling='coefficient'):
    D = rm.load_data(P, rm.STAGE2 / 'stage2_scores.csv')
    members, comp_d, comp_delta = D['members'], D['comp_d'], D['comp_delta']
    C0 = rm.coefficients(P)
    sol = {d: pd.read_csv(ROOT / 'data/processed/stage3' / d / 'solution.csv').iloc[0] for d in designs}
    cost_keys = [k for k in C0 if k != 'ptf_MWh']
    rows = []
    for k in range(n):
        if sampling == 'coefficient':
            C = {key: (v[0] if v[2] <= v[0] else rng.triangular(v[0], v[1], v[2])) for key, v in C0.items()}
        else:
            Ps = sample_params(P, rng)
            C = {key: v[1] for key, v in rm.coefficients(Ps).items()}
        u = rng.random()
        dem_c = {m: tri_inv(comp_d[m], u) for m in comp_d}
        for d, s in sol.items():
            cost = sum(C[c] * s.get(f'q_{c}', 0.0) for c in cost_keys)
            cost += C['ptf_MWh'] * (s['q_ptf_MWh_cost'] - s['q_ptf_MWh_rev'])
            short_node, imp_val = {}, 0.0
            for j, ms in members.items():
                dj = sum(dem_c[m] for m in ms)
                sh = max(0.0, dj - s[f'y_{j}_t'])
                short_node[j] = sh
                # bileşenlere oransal dağıtılır, her biri kendi sektörünün δ'sıyla fiyatlanır
                imp_val += sum(1000 * comp_delta[m] * sh * dem_c[m] / dj for m in ms) if dj > 0 else 0.0
            tot_dem = sum(dem_c.values())
            deliv = sum(s[f'y_{j}_t'] for j in members)
            rows.append({'draw': k, 'design': d, 'cost_MEUR': cost / 1e6, 'shortfall_t': sum(short_node.values()),
                         'sys_short': tot_dem > deliv + 1e-6, 'any_short': any(v > 1e-6 for v in short_node.values()),
                         'import_MEUR': imp_val / 1e6, 'total_MEUR': (cost + imp_val) / 1e6, 'delivered_t': deliv})
    df = pd.DataFrame(rows)
    summ = df.groupby('design').agg(
        cost_mean=('cost_MEUR', 'mean'), cost_p05=('cost_MEUR', lambda x: x.quantile(.05)),
        cost_p95=('cost_MEUR', lambda x: x.quantile(.95)), cost_sd=('cost_MEUR', 'std'),
        p_shortfall_system=('sys_short', 'mean'), p_shortfall_any_node=('any_short', 'mean'),
        shortfall_mean_t=('shortfall_t', 'mean'),
        total_mean=('total_MEUR', 'mean'), total_p95=('total_MEUR', lambda x: x.quantile(.95)),
        delivered_t=('delivered_t', 'first'))
    summ['lcoh_mean_eur_kg'] = summ.cost_mean * 1e6 / summ.delivered_t / 1000
    # RPP Me beklenen maliyetiyle uzlaştırma: doğrusal maliyet için katsayı okumasında ortalama ≈ Σ q (c1+c2+c3)/3
    rec = {}
    for d, s in sol.items():
        z = [sum(C0[c][v] * s.get(f'q_{c}', 0.0) for c in cost_keys)
             + C0['ptf_MWh'][v] * s['q_ptf_MWh_cost'] - C0['ptf_MWh'][2 - v] * s['q_ptf_MWh_rev'] for v in range(3)]
        rec[d] = {'z_low_MEUR': z[0] / 1e6, 'z_mode_MEUR': z[1] / 1e6, 'z_high_MEUR': z[2] / 1e6,
                  'mean_triangular_MEUR': sum(z) / 3 / 1e6, 'E_Me_MEUR': s['E_z'] / 1e6}
    summ = summ.join(pd.DataFrame(rec).T)
    return df, summ


def break_even(summ, base='base'):
    """Karşılanamayan talep fiyatı p için ortalama toplam maliyet eşitliği: c_h + p s_h = c_b + p s_b."""
    out = []
    b = summ.loc[base]
    for d, r in summ.iterrows():
        if d == base or r.shortfall_mean_t >= b.shortfall_mean_t - 1e-9:
            continue
        p = (r.cost_mean - b.cost_mean) * 1e6 / ((b.shortfall_mean_t - r.shortfall_mean_t) * 1000)
        out.append({'design': d, 'breakeven_import_eur_kg': p})
    return pd.DataFrame(out)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=10000)
    ap.add_argument('--sigmas', default='0.05,0.10,0.15,0.20')
    ap.add_argument('--designs', default='base,deterministic,delta12_5,delta15,delta20,phi0_5,phi0_0,cf_top3_det')
    ap.add_argument('--sampling', default='coefficient', choices=['coefficient', 'component'])
    ap.add_argument('--skip-stage2', action='store_true')
    ap.add_argument('--out', default=str(OUT), help='output directory; use a new directory to preserve earlier runs')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    sigmas = [float(value) for value in a.sigmas.split(',')]
    if not a.skip_stage2:
        st2 = stage2_stability(a.n, sigmas, rng)
        (out / 'stage2_stability.json').write_text(json.dumps(st2, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(st2, indent=1, ensure_ascii=False))
    rng3 = np.random.default_rng(SEED + 1)
    P = yaml.safe_load(rm.P_YAML.read_text(encoding='utf-8'))
    designs = a.designs.split(',')
    df, summ = stage3_mc(P, designs, a.n, rng3, a.sampling)
    df.to_csv(out / 'stage3_mc_draws.csv.gz', index=False, compression='gzip')
    summ.round(4).to_csv(out / 'stage3_mc_summary.csv')
    be = break_even(summ)
    be.round(2).to_csv(out / 'stage3_mc_breakeven.csv', index=False)
    # Karşılanamayan talebin tek tip ithalat fiyatlarıyla değerlendirilmesi (sigorta etkisi: ortalama ve P95)
    ev = []
    for de in [5.63, 7.30, 10, 15, 20, 30, 40, 50]:
        tot = df.cost_MEUR + de * df.shortfall_t / 1000
        g = tot.groupby(df.design)
        for d in g.mean().index:
            ev.append({'delta_eval_eur_kg': de, 'design': d, 'total_mean_MEUR': g.mean()[d], 'total_p95_MEUR': g.quantile(.95)[d]})
    pd.DataFrame(ev).round(2).to_csv(out / 'stage3_mc_delta_eval.csv', index=False)
    (out / 'manifest.json').write_text(json.dumps({
        'run_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'seed': SEED, 'n': a.n,
        'sigma_rel': sigmas, 'designs': designs, 'sampling': a.sampling,
        'params_sha256': rm.sha(rm.P_YAML)}, indent=2), encoding='utf-8')
    print(summ.round(3).T.to_string())
    print(be.round(2).to_string(index=False))


if __name__ == '__main__':
    main()
