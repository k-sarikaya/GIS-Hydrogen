# -*- coding: utf-8 -*-
"""Bayat \bibitem anahtarlarini girdinin gercek ilk yazariyla uyumlu hale getirir.

Anahtar adi basilan metni DEGISTIRMEZ (LaTeX \bibitem[...] etiketini yazdirir);
amac capraz kontrolu guvenilir kilmak ve yanlis makaleyi tarif etme hatasinin
tekrarini onlemek.

Kullanim: python code/tools/rename_bibkeys.py [--apply]
--apply verilmezse yalnizca rapor basar, dosyaya dokunmaz.
"""
import re
import sys
from pathlib import Path

TEX = Path(__file__).resolve().parents[2] / 'manuscript' / 'manuscript.tex'

RENAME = {
    'schulte2023green':      'muller2023green',
    'gassert2025gis':        'gargi2026gis',
    'wang2025designing':     'jin2025designing',
    'li2023hydrogen':        'monteiro2023hydrogen',
    'han2023challenges':     'gorji2023challenges',
    'zhou2025optimization':  'yu2025optimization',
    'qadrdan2024great':      'dergunova2024great',
    'zhao2026robust':        'shao2026robust',
    'solomon2024techno':     'kim2024techno',
    'haase2025techno':       'scheffler2025techno',
    'fan2024large':          'ma2024large',
    'janzen2025quantifying': 'frischmuth2024quantifying',
    'akhlaghi2020design':    'fazlikhalaf2020design',
    'pishvaee2016multi':     'bairamzadeh2016multi',
}

t = TEX.read_text(encoding='utf-8')

# mevcut tum anahtarlar (carpisma kontrolu)
mevcut = set(re.findall(r'\\bibitem\[[^\]]*\]\{([^}]+)\}', t))
carpisma = [v for v in RENAME.values() if v in mevcut]
if carpisma:
    print('DURDU - yeni anahtar zaten var:', carpisma)
    sys.exit(1)

eksik = [k for k in RENAME if k not in mevcut]
if eksik:
    print('DURDU - eski anahtar kaynakcada yok:', eksik)
    sys.exit(1)

print(f'{"eski":26s} {"yeni":28s} degisen gecis')
toplam = 0
yeni = t
for eski, yeniad in RENAME.items():
    pat = re.compile(r'(?<![A-Za-z0-9_])' + re.escape(eski) + r'(?![A-Za-z0-9_])')
    yeni, n = pat.subn(yeniad, yeni)
    toplam += n
    print(f'{eski:26s} {yeniad:28s} {n}')

print(f'\ntoplam {toplam} gecis degisti')

# dogrulama: eski anahtarlardan hicbiri kalmamali
kalan = [k for k in RENAME if re.search(r'(?<![A-Za-z0-9_])' + re.escape(k) + r'(?![A-Za-z0-9_])', yeni)]
print('kalan eski anahtar:', kalan or 'yok')

# dogrulama: atif sayisi = kaynakca sayisi
bibs = re.findall(r'\\bibitem\[[^\]]*\]\{([^}]+)\}', yeni)
cites = set()
for g in re.findall(r'\\cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\{([^}]*)\}', yeni):
    cites.update(x.strip() for x in g.split(',') if x.strip())
print(f'kaynakca {len(bibs)} / atif {len(cites)} / yetim {len(set(bibs)-cites)} / eksik {len(cites-set(bibs))}')

if '--apply' in sys.argv:
    TEX.write_text(yeni, encoding='utf-8')
    print('\nUYGULANDI')
else:
    print('\nKURU KOSUM - dosyaya dokunulmadi (--apply ile uygulayin)')
