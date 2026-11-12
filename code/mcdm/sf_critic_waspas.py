"""
Aşama II — hibrit küresel bulanık (SF) karar matrisi, CRITIC + uzman birleşik ağırlıkları ve SF-WASPAS.

Girdiler
  data/processed/stage2/data_criteria.csv          K1–K4 (stage2_data_criteria.py)
  data/processed/stage2/normalisation_anchors.json  sabit çapalar (adaylardan bağımsız)
  --survey <csv>                                    Google Forms dışa aktarımı (C, D1–D3 ızgaraları)

Kipler
  provisional : anket yok; yalnızca K1–K4, yalnızca CRITIC ağırlıkları (Aşama III ön çalıştırması)
  survey      : gerçek anket; K1–K7, w = α·w_S + (1−α)·w_C
  synthetic   : yalnız kod testi için tohumlu yapay panel; çıktılar *_SYNTHETIC adını taşır

Yöntem (makale, Bölüm Stage II)
  - Dilsel ölçek: Kutlu Gündoğdu & Kahraman (2019), 9 terim, birebir.
  - "Bilgim yok" eksik veri sayılır; uzman SFN'leri SWAM ile eşit ağırlıkla birleştirilir.
  - Veri kriterleri: r = (x−L)/(U−L) (fayda) veya (U−x)/(U−L) (maliyet), [0,1]'e kırpılır;
    SFN = (0.1+0.8r, 0.9−0.8r, 0), yani ölçeğin uç terimlerinin üyelik aralığı.
  - Skor = (μ−π)² − (ν−π)²; kesin değer p = (1+Skor)/2 ∈ [0,1].
  - CRITIC: p matrisi üzerinde (Diakoulaki vd. 1995).
  - Uzman önem ağırlığı: w_S ∝ (1+Skor) (skor negatif olabildiği için kaydırılır).
  - SF-WASPAS: WSM = SWAM_j(x̃_ij; w), WPM = SWGM_j(x̃_ij; w); Q_i = λ·Skor(WSM) + (1−λ)·Skor(WPM).

Kullanım
  python code/mcdm/sf_critic_waspas.py                       # provisional
  python code/mcdm/sf_critic_waspas.py --survey data/survey/expert_responses.csv
  python code/mcdm/sf_critic_waspas.py --synthetic           # yalnız test
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STAGE2 = ROOT / 'data/processed/stage2'

# Kutlu Gündoğdu & Kahraman (2019), Informatica 30(2), Tablo 2 — birebir
SCALE = {1: (0.1, 0.9, 0.1), 2: (0.2, 0.8, 0.2), 3: (0.3, 0.7, 0.3), 4: (0.4, 0.6, 0.4), 5: (0.5, 0.5, 0.5),
         6: (0.6, 0.4, 0.4), 7: (0.7, 0.3, 0.3), 8: (0.8, 0.2, 0.2), 9: (0.9, 0.1, 0.1)}
SITES = ['S1', 'S2', 'S3', 'S4', 'S5']
DATA_CRIT = ['K1', 'K2', 'K3', 'K4']
EXPERT_CRIT = ['K5', 'K6', 'K7']
DATA_COLS = {'K1': 'K1_substation_km', 'K2': 'K2_water_stress_score', 'K3': 'K3_protected_km', 'K4': 'K4_pga_g'}
GRID_OF = {'K5': 'D1', 'K6': 'D2', 'K7': 'D3'}


# ------------------------------------------------------------------ SF işlemleri
def score(s):
    mu, nu, pi = s
    return (mu - pi) ** 2 - (nu - pi) ** 2


def swam(sfns, w):
    """Spherical weighted arithmetic mean (Kutlu Gündoğdu & Kahraman 2019)."""
    a = np.asarray(sfns, float); w = np.asarray(w, float) / np.sum(w)
    mu, nu, pi = a[:, 0], a[:, 1], a[:, 2]
    p1 = np.prod((1 - mu ** 2) ** w)
    p2 = np.prod(np.clip(1 - mu ** 2 - pi ** 2, 0, None) ** w)
    return (np.sqrt(max(1 - p1, 0)), float(np.prod(nu ** w)), np.sqrt(max(p1 - p2, 0)))


def swgm(sfns, w):
    """Spherical weighted geometric mean (Kutlu Gündoğdu & Kahraman 2019)."""
    a = np.asarray(sfns, float); w = np.asarray(w, float) / np.sum(w)
    mu, nu, pi = a[:, 0], a[:, 1], a[:, 2]
    q1 = np.prod(np.clip(1 - nu ** 2, 0, None) ** w)
    q2 = np.prod(np.clip(1 - nu ** 2 - pi ** 2, 0, None) ** w)
    return (float(np.prod(mu ** w)), np.sqrt(max(1 - q1, 0)), np.sqrt(max(q1 - q2, 0)))


def critic(p, norm='none'):
    """CRITIC (Diakoulaki vd. 1995); p: alternatif × kriter, [0,1].
    norm='minmax': özgün yöntemdeki gibi her kriter kendi aralığına göre [0,1]'e ölçeklenir (V4 temel);
    norm='none': v3 okuması, p doğrudan kullanılır (kriter ölçeklerinin farklı yayılımı ağırlığa yansır)."""
    p = np.asarray(p, float)
    if norm == 'minmax':
        rng_ = p.max(axis=0) - p.min(axis=0)
        p = np.where(rng_ > 0, (p - p.min(axis=0)) / np.where(rng_ > 0, rng_, 1), 0.0)
    sd = p.std(axis=0, ddof=1)
    with np.errstate(invalid='ignore', divide='ignore'):
        r = np.corrcoef(p, rowvar=False)
    r = np.nan_to_num(r, nan=0.0)
    np.fill_diagonal(r, 1.0)
    c = sd * (1 - r).sum(axis=0)
    return c / c.sum()


# ------------------------------------------------------------------ girdiler
DATA_MAP = {'mode': 'v3'}   # 'v3': (0.1+0.8r, 0.9−0.8r, 0) -> Skor ±0.80; 'matched': (0.18+0.64r, 0.82−0.64r, 0) -> ±0.64


def data_sfns():
    d = pd.read_csv(STAGE2 / 'data_criteria.csv').set_index('code').loc[SITES]
    anc = json.loads((STAGE2 / 'normalisation_anchors.json').read_text(encoding='utf-8'))
    out, rr = {}, {}
    for k in DATA_CRIT:
        a = anc[DATA_COLS[k]]
        x = d[DATA_COLS[k]].astype(float)
        r = (x - a['L']) / (a['U'] - a['L']) if a['direction'] == 'benefit' else (a['U'] - x) / (a['U'] - a['L'])
        r = r.clip(0, 1)
        rr[k] = r
        out[k] = {s: data_sfn(float(r[s])) for s in SITES}
    return out, pd.DataFrame(rr), anc


def data_sfn(r):
    if DATA_MAP['mode'] == 'matched':
        # V4: μ+ν = 1, π = 0 korunur; Skor = μ−ν = 1.28r − 0.64, yani dilsel ölçeğin ±0.64 aralığıyla aynı
        return (0.18 + 0.64 * r, 0.82 - 0.64 * r, 0.0)
    return _data_sfn_v3(r)


def _data_sfn_v3(r):
    """Ölçülen veri: üyelik, ölçeğin uç terimlerinin (ALI 0.1 / AMI 0.9) aralığına eşlenir; π = 0.
    Böylece veri, en uç uzman yargısından daha uç olamaz ve r = 0 iken WPM'de sıfır üyelik
    (veto etkisi) oluşmaz. Skor = (0.1+0.8r)² − (0.9−0.8r)² = 1.6r − 0.8 (doğrusal, artan)."""
    return (0.1 + 0.8 * r, 0.9 - 0.8 * r, 0.0)


def term(v):
    v = str(v).strip()
    m = re.match(r'^(\d)', v)
    return int(m.group(1)) if m and 1 <= int(m.group(1)) <= 9 else None   # "Bilgim yok"/boş -> None


def parse_survey(df):
    """Google Forms ızgara sütunları: 'C. ... [K1 — ...]' ve 'D1. ... [S1]'."""
    imp = {k: [] for k in DATA_CRIT + EXPERT_CRIT}
    rat = {k: {s: [] for s in SITES} for k in EXPERT_CRIT}
    for col in df.columns:
        mc = re.match(r'^\s*C\.\s.*\[(K[1-7])\b', col)
        if mc:
            imp[mc.group(1)] += [t for t in map(term, df[col]) if t]
            continue
        md = re.match(r'^\s*(D[1-3])\.\s.*\[(S[1-5])\b', col)
        if md:
            k = {v: k for k, v in GRID_OF.items()}[md.group(1)]
            rat[k][md.group(2)] += [t for t in map(term, df[col]) if t]
    return imp, rat


def synthetic_panel(n=15, seed=20261018, p_missing=0.15):
    """YALNIZ TEST: rastgele uzman yanıtları. Sonuçları raporlanmaz."""
    rng = np.random.default_rng(seed)
    imp = {k: list(rng.integers(4, 10, n)) for k in DATA_CRIT + EXPERT_CRIT}
    rat = {k: {s: [int(t) for t in rng.integers(2, 10, n) if rng.random() > p_missing] for s in SITES}
           for k in EXPERT_CRIT}
    return imp, rat


# ------------------------------------------------------------------ ana akış
def run(mode, alpha, lam, survey_path=None, survey_frame=None, drop=None, data_map='matched', critic_norm='minmax'):
    """drop: tek bir kriteri (ör. 'K2') analiz dışı bırakır. Kriter, CRITIC ve uzman
    ağırlıkları hesaplanmadan ÖNCE düşürülür, böylece kalan ağırlıklar yeniden
    hesaplanır — sabit ağırlıkları normalize etmek yanlış sonuç verir."""
    DATA_MAP['mode'] = data_map
    dsfn, r_data, anc = data_sfns()
    matrix = {k: dsfn[k] for k in DATA_CRIT}
    n_resp, imp = {}, None
    if mode in ('survey', 'synthetic'):
        if mode == 'synthetic':
            imp, rat = synthetic_panel()
        else:
            frame = survey_frame if survey_frame is not None else pd.read_csv(survey_path)
            imp, rat = parse_survey(frame)
        for k in EXPERT_CRIT:
            matrix[k] = {}
            for s in SITES:
                ts = rat[k][s]
                n_resp[f'{k}_{s}'] = len(ts)
                if not ts:
                    raise ValueError(f'{k}/{s}: hiç geçerli yanıt yok')
                matrix[k][s] = swam([SCALE[t] for t in ts], np.ones(len(ts)))
    if drop is not None:
        if drop not in matrix:
            raise ValueError(f'bilinmeyen kriter: {drop}')
        matrix = {k: v for k, v in matrix.items() if k != drop}
    crit = list(matrix)

    p = pd.DataFrame({k: [(1 + score(matrix[k][s])) / 2 for s in SITES] for k in crit}, index=SITES)
    w_c = pd.Series(critic(p.values, critic_norm), index=crit)
    if imp is not None:
        agg = {k: swam([SCALE[t] for t in imp[k]], np.ones(len(imp[k]))) for k in crit}
        sraw = pd.Series({k: 1 + score(agg[k]) for k in crit})
        w_s = sraw / sraw.sum()
        w = alpha * w_s + (1 - alpha) * w_c
    else:
        w_s, w = pd.Series(np.nan, index=crit), w_c.copy()

    rows = []
    for s in SITES:
        x = [matrix[k][s] for k in crit]
        wsm, wpm = swam(x, w.values), swgm(x, w.values)
        q = lam * score(wsm) + (1 - lam) * score(wpm)
        rows.append({'site': s, 'WSM_mu': wsm[0], 'WSM_nu': wsm[1], 'WSM_pi': wsm[2], 'score_WSM': score(wsm),
                     'WPM_mu': wpm[0], 'WPM_nu': wpm[1], 'WPM_pi': wpm[2], 'score_WPM': score(wpm),
                     'Q': q, 'Q01': (1 + q) / 2})
    res = pd.DataFrame(rows)
    res['rank'] = res.Q.rank(ascending=False, method='min').astype(int)
    wt = pd.DataFrame({'w_CRITIC': w_c, 'w_expert': w_s, 'w_final': w})
    return res, wt, p, r_data, n_resp, anc, matrix


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--survey', default=None)
    ap.add_argument('--synthetic', action='store_true')
    ap.add_argument('--alpha', type=float, default=0.5, help='uzman ağırlığı payı')
    ap.add_argument('--lam', type=float, default=0.5, help='WASPAS λ')
    ap.add_argument('--data-map', default='matched', choices=['v3', 'matched'])
    ap.add_argument('--critic-norm', default='minmax', choices=['none', 'minmax'])
    ap.add_argument('--suffix', default='', help='çıktı adlarına ek (ör. _v3construction)')
    a = ap.parse_args()
    mode = 'synthetic' if a.synthetic else ('survey' if a.survey else 'provisional')
    res, wt, p, r_data, n_resp, anc, *rest = run(mode, a.alpha, a.lam, a.survey, data_map=a.data_map,
                                                critic_norm=a.critic_norm)

    tag = {'provisional': '_provisional', 'survey': '', 'synthetic': '_SYNTHETIC'}[mode] + a.suffix
    res.round(6).to_csv(STAGE2 / f'stage2_scores{tag}.csv', index=False)
    wt.round(6).to_csv(STAGE2 / f'stage2_weights{tag}.csv', index_label='criterion')
    p.round(6).to_csv(STAGE2 / f'stage2_crisp_matrix{tag}.csv', index_label='site')
    man = {'run_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'mode': mode,
           'alpha': a.alpha, 'lambda_waspas': a.lam, 'data_map': a.data_map, 'critic_norm': a.critic_norm,
           'inputs_sha256': {f: hashlib.sha256((STAGE2 / f).read_bytes()).hexdigest()
                             for f in ['data_criteria.csv', 'normalisation_anchors.json']},
           'survey_sha256': hashlib.sha256(Path(a.survey).read_bytes()).hexdigest() if a.survey else None,
           'n_valid_ratings': n_resp}
    (STAGE2 / f'stage2_manifest{tag}.json').write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding='utf-8')

    if mode == 'synthetic':
        print('*** SYNTHETIC PANEL — CODE TEST ONLY, NOT A RESULT ***')
    print('Normalised data criteria r_ij:\n', r_data.round(3).to_string())
    print('\nWeights:\n', wt.round(4).to_string())
    print('\nScores:\n', res[['site', 'score_WSM', 'score_WPM', 'Q', 'Q01', 'rank']].round(4).to_string(index=False))


if __name__ == '__main__':
    main()
