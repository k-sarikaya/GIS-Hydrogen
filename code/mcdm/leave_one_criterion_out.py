"""Asama II kriter cikarma analizi (leave-one-criterion-out).

Her kriteri sirayla disarida birakir ve CRITIC ile uzman agirliklarini kalan
kriterler uzerinde YENIDEN hesaplar. Sabit agirliklari normalize etmek yanlistir:
CRITIC agirligi matrisin kontrast ve catisma yapisindan gelir, bu yuzden bir
kriter dustugunde kalanlarin agirliklari da degisir.

Raporlanan: siralama, birincinin Q01 degeri ve birinci ile ikinci arasindaki fark.

Kullanim:
    python code/mcdm/leave_one_criterion_out.py
    python code/mcdm/leave_one_criterion_out.py --survey data/survey/expert_responses.csv
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sf_critic_waspas as sf  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / 'data/survey/expert_responses.csv'
OUT = ROOT / 'data/processed/stage2/leave_one_criterion_out.csv'


def summarise(res, wt, dropped):
    r = res.sort_values('Q01', ascending=False).reset_index(drop=True)
    gap = float(r.Q01.iloc[0] - r.Q01.iloc[1])
    return {
        'dropped': dropped,
        'ranking': ' > '.join(r.site),
        'top': r.site.iloc[0],
        'top_Q01': round(float(r.Q01.iloc[0]), 5),
        'second': r.site.iloc[1],
        'second_Q01': round(float(r.Q01.iloc[1]), 5),
        'gap_top_second': round(gap, 5),
        'w_final_max_crit': wt.w_final.idxmax(),
        'w_final_max': round(float(wt.w_final.max()), 4),
    }


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--survey', default=str(SURVEY))
    ap.add_argument('--alpha', type=float, default=0.5)
    ap.add_argument('--lam', type=float, default=0.5)
    a = ap.parse_args()

    path = Path(a.survey)
    if not path.exists():
        raise FileNotFoundError(
            f'Anket disa aktarimi bulunamadi: {path}\n'
            'Bu analiz gercek uzman yanitlarini gerektirir; sentetik panel raporlanmaz.')
    frame = pd.read_csv(path)

    criteria = sf.DATA_CRIT + sf.EXPERT_CRIT
    rows = []
    res, wt, *_ = sf.run('survey', a.alpha, a.lam, survey_frame=frame)
    rows.append(summarise(res, wt, '-'))
    for k in criteria:
        res, wt, *_ = sf.run('survey', a.alpha, a.lam, survey_frame=frame, drop=k)
        rows.append(summarise(res, wt, k))

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    base = df.iloc[0]
    print(df[['dropped', 'ranking', 'top_Q01', 'gap_top_second',
              'w_final_max_crit', 'w_final_max']].to_string(index=False))
    print()
    print(f'Taban siralama      : {base.ranking}')
    print(f'Taban fark (1.-2.)  : {base.gap_top_second}')
    worst = df.iloc[1:].sort_values('gap_top_second').iloc[0]
    print(f'Farki en cok daraltan: {worst.dropped} -> {worst.gap_top_second} '
          f'(siralama: {worst.ranking})')
    flips = df.iloc[1:][df.iloc[1:].top != base.top]
    if len(flips):
        print('Birinciyi degistiren kriterler: ' + ', '.join(flips.dropped))
    else:
        print('Hicbir kriter cikarildiginda birinci degismiyor.')
    print(f'\nYazildi: {OUT}')


if __name__ == '__main__':
    main()
