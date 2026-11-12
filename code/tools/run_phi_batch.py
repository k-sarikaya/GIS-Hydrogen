# -*- coding: utf-8 -*-
"""phi duyarlilik paketini tamamlar: Pareto cepheleri + Monte Carlo.

Tek objektif phi kosumlari (phi1_0, phi0_5, phi0_0) zaten var. Bu betik
eksik kalanlari kosar ve her adimi loglar; yarida kesilirse tamamlanmis
adimlari atlayarak devam eder.

Kullanim:  python code/tools/run_phi_batch.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S3 = ROOT / 'data/processed/stage3'
S4 = ROOT / 'data/processed/stage4_phi'

PARETO = [('0.5', 'phi0_5_pareto'), ('0.0', 'phi0_0_pareto')]
DESIGNS = 'phi1_0,phi0_5,phi0_0'


def run(cmd, label):
    t0 = time.time()
    print(f'>>> {label}', flush=True)
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout or '').strip().splitlines()[-3:]
    for ln in tail:
        print('    ' + ln, flush=True)
    if r.returncode != 0:
        print(f'!!! BASARISIZ ({label}):', flush=True)
        print((r.stderr or '')[-1200:], flush=True)
        return False
    print(f'<<< {label} tamam ({time.time() - t0:.0f} s)\n', flush=True)
    return True


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ok = True
    for phi, tag in PARETO:
        # TAMAMLANMA ISARETI = manifest.json. rpp_model.py bunu YALNIZ kosum
        # bittikten sonra yazar; pareto.csv ise cozum ilerledikce surekli
        # guncellenir. pareto.csv'ye bakmak, yarida kesilmis bir Pareto'yu
        # tamamlanmis sayip sessizce atlamaya yol acardi.
        if (S3 / tag / 'manifest.json').exists():
            print(f'=== {tag} tamamlanmis, atlaniyor\n', flush=True)
            continue
        if (S3 / tag / 'pareto_state.json').exists():
            print(f'=== {tag} yarida kalmis, kaldigi yerden devam ediyor', flush=True)
        ok &= run([sys.executable, 'code/optimization/rpp_model.py',
                   '--set', f'land.co_use_share={phi}', '--tag', tag], tag)

    if (S4 / 'stage3_mc_summary.csv').exists():
        print('=== Monte Carlo zaten var, atlaniyor', flush=True)
    else:
        ok &= run([sys.executable, 'code/optimization/stage4_monte_carlo.py',
                   '--designs', DESIGNS, '--out', str(S4)], 'monte carlo (phi)')

    print('TUMU TAMAM' if ok else 'EN AZ BIR ADIM BASARISIZ', flush=True)


if __name__ == '__main__':
    main()
