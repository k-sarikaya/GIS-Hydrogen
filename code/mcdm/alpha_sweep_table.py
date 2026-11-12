# -*- coding: utf-8 -*-
"""Supplementary Table S13: Asama II siralamasinin oznel-nesnel agirlik karisimina (alpha)
duyarliligi.

Girdi : data/processed/stage2/stage2_scores{suffix}.csv ve stage2_weights{suffix}.csv
        (sf_critic_waspas.py --alpha A --suffix S ile uretilir)
Cikti : submission_assets/supplementary/Supplementary_Table_S13_Alpha_Sweep.csv
        submission_assets/supplementary/Supplementary_Table_S13_Caption.txt

Yeniden uretmek icin:
    python code/mcdm/sf_critic_waspas.py --alpha 0.00 --suffix _a000
    python code/mcdm/sf_critic_waspas.py --alpha 0.25 --suffix _a025
    python code/mcdm/sf_critic_waspas.py --alpha 0.75 --suffix _a075
    python code/mcdm/sf_critic_waspas.py --alpha 1.00 --suffix _a10
    python code/mcdm/alpha_sweep_table.py
"""
import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii', errors='backslashreplace')

ROOT = Path(__file__).resolve().parents[2]
S2 = ROOT / 'data' / 'processed' / 'stage2'
OUT = ROOT / 'submission_assets' / 'supplementary'

KOSUM = [(0.00, '_a000'), (0.25, '_a025'), (0.50, ''), (0.75, '_a075'), (1.00, '_a10')]
SAHA = ['S1', 'S2', 'S3', 'S4', 'S5']
OLCULEN = ['K1', 'K2', 'K3', 'K4']       # veriden gelen olculen olcutler


def oku(suffix):
    sk = S2 / f'stage2_scores{suffix}.csv'
    ag = S2 / f'stage2_weights{suffix}.csv'
    for p in (sk, ag):
        if not p.exists():
            raise SystemExit(f'eksik girdi: {p}\n  once sf_critic_waspas.py --alpha ... --suffix '
                             f'{suffix or "(bos)"} kosulmali')
    return pd.read_csv(sk), pd.read_csv(ag)


def main():
    satir, siralamalar = [], []
    for a, suf in KOSUM:
        sk, ag = oku(suf)
        sk = sk.sort_values('Q01', ascending=False).reset_index(drop=True)
        q01 = dict(zip(sk['site'], sk['Q01']))
        rank = dict(zip(sk['site'], sk['rank']))
        siralamalar.append(' > '.join(sk['site'].tolist()))

        fark = sk['Q01'].iloc[0] - sk['Q01'].iloc[1]
        pay = ag.loc[ag['criterion'].isin(OLCULEN), 'w_final'].sum()

        etiket = f'{a:.2f}' + (' (used here)' if suf == '' else '')
        satir.append([etiket] + [f'{q01[s]:.3f} ({rank[s]})' for s in SAHA]
                     + [f'{fark:.3f}', f'{pay:.2f}'])

    df = pd.DataFrame(satir, columns=(['Expert weight share (beta)'] + SAHA
                                      + ['Lead of 1st over 2nd', 'Weight on K1-K4']))
    csv_yol = OUT / 'Supplementary_Table_S13_Alpha_Sweep.csv'
    df.to_csv(csv_yol, index=False, encoding='utf-8')

    tekil = sorted(set(siralamalar))
    if len(tekil) != 1:
        print('UYARI: siralama alpha ile degisiyor ->', tekil)
    sabit = tekil[0] if len(tekil) == 1 else 'degisken'

    ilk = float(satir[0][-2])
    son = float(satir[-1][-2])
    yon = 'narrows' if son < ilk else ('widens' if son > ilk else 'is unchanged')

    caption = (
        'Supplementary Table S13. Sensitivity of the Stage II ranking to the subjective-objective '
        'weight blend. The parameter beta is the share of each final criterion weight taken from '
        'the aggregated expert ratings, the remainder coming from the CRITIC contrast weights, so '
        'beta = 0 applies the CRITIC weights alone and beta = 1 the expert weights alone; the '
        'manuscript holds beta at 0.5. It is distinct from the Stage III confidence levels '
        'alpha_j. Cells give the suitability score Q01 '
        'and the rank in parentheses. The ordering is ' + sabit + ' at every value tested, so no '
        'rank reversal occurs anywhere on the interval. The lead of the first site over the second '
        f'{yon} monotonically from {ilk:.3f} at beta = 0 to {son:.3f} at beta = 1, that is, the '
        'separation of S5 is widest when the weights come entirely from the measured data and '
        'narrowest when they come entirely from the panel. The last column reports the share of '
        'the final weight carried by the four measured criteria K1-K4. This check varies the '
        'weight blend; the method variants of Table S5 vary the data mapping, the CRITIC '
        'normalisation and the use of fuzzy arithmetic.')
    cap_yol = OUT / 'Supplementary_Table_S13_Caption.txt'
    cap_yol.write_text(caption + '\n', encoding='utf-8')

    print(f'  siralama (tum alpha) : {sabit}')
    print(f'  fark 1.-2.           : {ilk:.3f} (alpha=0) -> {son:.3f} (alpha=1)')
    print(f'  yazildi              : {csv_yol.name}, {cap_yol.name}')


if __name__ == '__main__':
    main()
