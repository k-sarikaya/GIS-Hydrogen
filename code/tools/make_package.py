# -*- coding: utf-8 -*-
"""Dergiye gonderilecek duz LaTeX paketini package/ altinda kurar.

manuscript.tex ile cagrilan figurler kaynakla ayni klasore kopyalanir;
boylece paket kendi basina derlenir (graphicspath'e gerek kalmaz).

Kullanim: python code/tools/make_package.py
"""
import os
import re
import shutil
import stat
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'package'
TEX = ROOT / 'manuscript' / 'manuscript.tex'


def _force_rw(func, path, exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


if OUT.exists():
    for _ in range(4):
        try:
            shutil.rmtree(OUT, onexc=_force_rw)
            break
        except PermissionError:
            time.sleep(1.5)
OUT.mkdir(parents=True, exist_ok=True)

tex = TEX.read_text(encoding='utf-8')
# V5: Asama III modeli Ek Not S7'ye tasindi. Include hala varsa satir ici alinir;
# yoksa model ek materyalde oldugu icin bu adim atlanir.
model_include = r'\input{../submission_assets/supplementary/Stage_III_Mathematical_Model.tex}'
model_source = ROOT / 'submission_assets' / 'supplementary' / 'Stage_III_Mathematical_Model.tex'
if model_include in tex:
    if not model_source.exists():
        raise SystemExit('Stage III mathematical model include is missing.')
    tex = tex.replace(model_include, model_source.read_text(encoding='utf-8').strip())
elif not model_source.exists():
    raise SystemExit('Stage III model source is missing from submission_assets/supplementary.')
figs = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex)
# V4: dosya adları makaledeki şekil numarasıyla eşleşir (Fig1_..., Fig2_...); sıra = metindeki geçiş sırası
rename = {}
for n, f in enumerate(dict.fromkeys(figs), start=1):
    stem = re.sub(r'^Fig\d+_', '', f)
    rename[f] = f'Fig{n}_{stem}'
    tex = tex.replace('{' + f + '}', '{' + rename[f] + '}')
# derleme kontrolü: tablo bloklarının işaretleri pakete gitmez
tex = re.sub(r'^%<<(GEN:[a-z_]+|END)>>\n', '', tex, flags=re.M)

(OUT / 'manuscript.tex').write_text(tex, encoding='utf-8')
if TEX.with_suffix('.pdf').exists():
    shutil.copy2(TEX.with_suffix('.pdf'), OUT / 'manuscript.pdf')

eksik = []
for f in dict.fromkeys(figs):
    src = ROOT / 'figures' / f
    shutil.copy2(src, OUT / rename[f]) if src.exists() else eksik.append(f)

ga = ROOT / 'figures' / 'Graphical_Abstract.png'
if ga.exists():
    shutil.copy2(ga, OUT / ga.name)
for name in ('highlights.txt', 'graphical_abstract_caption.txt', 'cover_letter.txt'):
    p = ROOT / 'submission_assets' / name
    shutil.copy2(p, OUT / name) if p.exists() else eksik.append(name)
# Ek materyal tek dosya olarak gider: kaynak + derlenmis PDF.
# Alttaki CSV/TXT'ler girdi dosyalaridir, pakete girmez.
for name in ('supplementary.tex', 'supplementary.pdf'):
    p = ROOT / 'manuscript' / name
    shutil.copy2(p, OUT / name) if p.exists() else eksik.append(name)

print(f'paket      : {OUT}')
print(f'figur      : {len(figs)} -> {", ".join(figs)}')
if eksik:
    print(f'EKSIK      : {eksik}')
    sys.exit(1)
n = sum(1 for _ in OUT.rglob('*') if _.is_file())
mb = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file()) / 1024 / 1024
print(f'dosya      : {n}   ({mb:.1f} MB)')
print('\nDerleme testi icin:  cd package && pdflatex manuscript.tex  (uc gecis)')
