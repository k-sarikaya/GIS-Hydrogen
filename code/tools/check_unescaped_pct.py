# -*- coding: utf-8 -*-
"""manuscript.tex icinde kacissiz % arar.

LaTeX'te kacissiz % yorum baslatir: satirin geri kalani HATA VERMEDEN kaybolur.
Satir sonundaki % (bosluk bastirma) kasitlidir ve raporlanmaz.

Kullanim: python code/tools/check_unescaped_pct.py
Cikis kodu 1 ise supheli kullanim var.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
TEX = Path(__file__).resolve().parents[2] / 'manuscript' / 'manuscript.tex'

bulgu = []
for i, l in enumerate(TEX.read_text(encoding='utf-8').splitlines(), 1):
    if l.lstrip().startswith('%'):     # bastan sona yorum satiri -> kasitli
        continue
    for m in re.finditer('%', l):
        j = m.start()
        k = 0
        while j - 1 - k >= 0 and l[j - 1 - k] == '\\':
            k += 1
        if k % 2:                      # tek sayida ters egik cizgi -> kacisli
            continue
        if not l[j + 1:].strip():      # satir sonu % -> kasitli
            continue
        bulgu.append((i, j, l[max(0, j - 60):j + 50]))

for i, j, c in bulgu:
    print(f'  satir {i}, sutun {j}: ...{c}...')
print(f'\nSupheli kacissiz %: {len(bulgu)}')
sys.exit(1 if bulgu else 0)
