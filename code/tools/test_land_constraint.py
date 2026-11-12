"""Ortak arazi kullanimi kisitinin birim testi (ag gerektirmez, cozucu calistirmaz).

Kisit ailesi (rpp_model.build):
    W/dW + PV/dP - s <= Aunion
    s <= W/dW,  s <= PV/dP,  s <= phi * Acap

Dogrulanan uc ozellik:
  1. phi=1 ve PV maskesi ruzgar maskesinin icindeyse (Acap = PV alani) kisit,
     bagimsiz Wmax/Pmax ust sinirlarina birebir indirgenir -> her iki teknoloji
     ayni anda tavanda kurulabilir.
  2. phi=0 (munhasir arazi) iki teknolojinin ayni anda tavanda kurulmasini engeller.
  3. Ortusme olculmemisse (Acap=0, Aunion=aw+ap) kisit hicbir phi degerinde
     baglamaz; model eski davranisina doner.

Kullanim:  python code/tools/test_land_constraint.py
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'optimization'))
import rpp_model as R  # noqa: E402


def feasible(aw_i, ap_i, Acap, Aunion, phi, w_frac, p_frac, tol=1e-9):
    """w_frac/p_frac kadar doluluk icin kisit ailesinin uygun olup olmadigi."""
    aW, aP = aw_i * w_frac, ap_i * p_frac
    s = min(aW, aP, phi * Acap)          # s en buyuk degerini alir (kisiti gevsetir)
    return aW + aP - s <= Aunion + tol


def main():
    P = yaml.safe_load(open(R.P_YAML, encoding='utf-8'))
    dW = P['wind']['density_mw_per_km2']
    dP = P['pv']['density_mw_per_km2']
    q_file = R.STAGE2 / 'stage2_scores.csv'
    if not q_file.exists():
        q_file = R.STAGE2 / 'stage2_scores_provisional.csv'
    D = R.load_data(P, q_file)

    sites = list(D['I'])
    aw = {i: D['Wmax'][i] / dW for i in sites}
    ap = {i: D['Pmax'][i] / dP for i in sites}

    failures = []

    # --- 1 + 2: PV maskesi ruzgarin icinde (Acap = ap) -----------------------
    for i in sites:
        Acap = ap[i]
        Aunion = aw[i] + ap[i] - Acap          # = aw[i]
        if not feasible(aw[i], ap[i], Acap, Aunion, 1.0, 1.0, 1.0):
            failures.append(f'[1] {i}: phi=1 iken iki tavan birlikte kurulamadi')
        if feasible(aw[i], ap[i], Acap, Aunion, 0.0, 1.0, 1.0) and ap[i] > 1e-9:
            failures.append(f'[2] {i}: phi=0 iken iki tavan birlikte kuruldu')
        if not feasible(aw[i], ap[i], Acap, Aunion, 0.0, 1.0, 0.0):
            failures.append(f'[2] {i}: phi=0 iken yalniz ruzgar tavani kurulamadi')

    # --- 3: ortusme olculmemis (Acap = 0, Aunion = aw + ap) ------------------
    for i in sites:
        for phi in (0.0, 0.5, 1.0):
            if not feasible(aw[i], ap[i], 0.0, aw[i] + ap[i], phi, 1.0, 1.0):
                failures.append(f'[3] {i}: olculmemis ortusmede phi={phi} kisiti bagladi')

    width = max(len(i) for i in sites)
    print(f'{"saha":<{width}}  {"aw":>7}  {"ap":>7}  {"aw+ap":>8}  '
          f'{"birlesim (PV ic icinde)":>24}')
    for i in sites:
        print(f'{i:<{width}}  {aw[i]:7.1f}  {ap[i]:7.1f}  {aw[i] + ap[i]:8.1f}  {aw[i]:24.1f}')

    print()
    if failures:
        for f in failures:
            print('BASARISIZ', f)
        sys.exit(1)
    print(f'Tum kontroller gecti ({len(sites)} saha).')
    print('Not: ortusme sutunu olculene kadar kisit baglamaz; model eski davranisini korur.')
    print(f'Ortusme olculdu mu: {D["overlap_measured"]}')


if __name__ == '__main__':
    main()
