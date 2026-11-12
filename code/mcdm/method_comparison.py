"""
Aşama II yöntem karşılaştırması (V4, hakem yanıtı).

Aynı karar matrisi ve aynı uzman yargılarıyla şu okumalar yan yana raporlanır:
  - SF-WASPAS, v3 kurgusu      : veri SFN'si (0.1+0.8r, 0.9−0.8r, 0), CRITIC p üzerinde doğrudan
  - SF-WASPAS, ölçek eşlemeli  : veri SFN'si (0.18+0.64r, 0.82−0.64r, 0), CRITIC doğrudan
  - SF-WASPAS, CRITIC min–max  : v3 veri eşlemesi, CRITIC kriter başına min–max ölçekli
  - SF-WASPAS, V4 kurgusu      : ölçek eşlemeli + CRITIC min–max
  - Kesin WSM ve kesin WASPAS  : V4 kesin matrisi p ve V4 ağırlıklarıyla (bulanık aritmetik yok)
Ek kontrol: skor fonksiyonunun birleştirilmiş SFN'lerde tutarlılığı (μ < ν iken Skor > 0 olan hücre var mı).

Çıktılar: data/processed/stage2/method_comparison.csv, score_monotonicity_check.csv
Kullanım: python code/mcdm/method_comparison.py --survey data/survey/expert_responses.csv
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/mcdm'))
import sf_critic_waspas as sf   # noqa: E402

VARIANTS = {
    'SF-WASPAS wide-range mapping, CRITIC unnormalised': ('v3', 'none'),
    'SF-WASPAS matched data scale': ('matched', 'none'),
    'SF-WASPAS wide-range mapping, CRITIC min-max': ('v3', 'minmax'),
    'SF-WASPAS scale-matched mapping, CRITIC min-max': ('matched', 'minmax'),
}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--survey', required=True)
    a = ap.parse_args()
    rows, wrows = [], []
    for name, (dm, cn) in VARIANTS.items():
        res, wt, p, *_ , matrix = sf.run('survey', 0.5, 0.5, a.survey, data_map=dm, critic_norm=cn)
        for _, r in res.iterrows():
            rows.append({'method': name, 'site': r.site, 'Q01': r.Q01, 'rank': int(r['rank'])})
        for k, r in wt.iterrows():
            wrows.append({'method': name, 'criterion': k, 'w_CRITIC': r.w_CRITIC, 'w_expert': r.w_expert, 'w_final': r.w_final})
        if name == 'SF-WASPAS scale-matched mapping, CRITIC min-max':
            w = wt.w_final.values
            pm = p.values
            wsm = pm @ w
            wpm = np.prod(np.clip(pm, 1e-9, None) ** w, axis=1)
            for lab, val in [('Crisp WSM (defuzzified matrix and weights used here)', wsm), ('Crisp WASPAS (defuzzified matrix and weights used here)', 0.5 * wsm + 0.5 * wpm)]:
                rk = pd.Series(val, index=p.index).rank(ascending=False, method='min').astype(int)
                for s in p.index:
                    rows.append({'method': lab, 'site': s, 'Q01': float(pd.Series(val, index=p.index)[s]), 'rank': int(rk[s])})
            chk = []
            for k in sf.EXPERT_CRIT:
                for s in sf.SITES:
                    mu, nu, pi = matrix[k][s]
                    sc = sf.score((mu, nu, pi))
                    chk.append({'criterion': k, 'site': s, 'mu': mu, 'nu': nu, 'pi': pi, 'score': sc,
                                'inconsistent_sign': (mu < nu and sc > 0) or (mu > nu and sc < 0)})
            pd.DataFrame(chk).round(5).to_csv(sf.STAGE2 / 'score_monotonicity_check.csv', index=False)
    df = pd.DataFrame(rows)
    df.round(6).to_csv(sf.STAGE2 / 'method_comparison.csv', index=False)
    pd.DataFrame(wrows).round(6).to_csv(sf.STAGE2 / 'method_comparison_weights.csv', index=False)
    print(df.pivot(index='site', columns='method', values='rank').to_string())
    print(pd.DataFrame(wrows).pivot(index='criterion', columns='method', values='w_final').round(3).to_string())


if __name__ == '__main__':
    main()
