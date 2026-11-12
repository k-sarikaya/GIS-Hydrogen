# -*- coding: utf-8 -*-
"""IJHE sinir denetimi: ozet, govde, float, anahtar kelime, highlights.
Kalici arac - gonderim oncesi her derlemeden sonra kosturulabilir."""
import io, sys, re, subprocess, tempfile, os
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii', errors='backslashreplace')

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / 'manuscript' / 'manuscript.tex'
L = TEX.read_text(encoding='utf-8').splitlines()
src = '\n'.join(L)

def say(a, b):
    f = tempfile.NamedTemporaryFile('w', suffix='.tex', delete=False, encoding='utf-8')
    f.write('\n'.join(L[a-1:b])); f.close()
    out = subprocess.run(['texcount', '-1', f.name], capture_output=True, text=True).stdout
    os.unlink(f.name)
    try:
        return int(out.split('+')[0].strip())
    except Exception:
        return -1

def ln(onek):
    return next(k for k, s in enumerate(L, 1) if s.strip().startswith(onek))

sonuc = []
n = say(ln(r'\begin{abstract}'), ln(r'\end{abstract}'))
sonuc.append(('Ozet', n, 150))
n = say(ln(r'\section{Introduction}'), ln(r'\section*{CRediT') - 1)
sonuc.append(('Govde 1-6', n, 8000))
n = (len(re.findall(r'^\\begin\{table', src, re.M)) +
     len(re.findall(r'^\\begin\{figure', src, re.M)))
sonuc.append(('Float', n, 12))
kw = src.split(r'\begin{keyword}')[1].split(r'\end{keyword}')[0]
sonuc.append(('Anahtar kelime', len([k for k in kw.split(r'\sep') if k.strip()]), 6))

hl = ROOT / 'submission_assets' / 'highlights.txt'
if not hl.exists():
    hl = ROOT / 'package' / 'highlights.txt'
if hl.exists():
    ms = [l.strip().lstrip('-').strip() for l in hl.read_text(encoding='utf-8').splitlines()
          if l.strip()]
    sonuc.append(('Highlights madde', len(ms), 5))
    sonuc.append(('Highlights en uzun', max((len(m) for m in ms), default=0), 85))

kotu = 0
for ad, deger, sinir in sonuc:
    ok = deger <= sinir
    kotu += 0 if ok else 1
    print('{:22} {:6}  / {:5}   {}'.format(ad, deger, sinir, 'OK' if ok else 'ASIM'))

print('\n' + ('TUM SINIRLAR KARSILANDI' if not kotu else f'{kotu} SINIR ASILDI'))
sys.exit(1 if kotu else 0)
