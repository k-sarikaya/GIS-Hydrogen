# -*- coding: utf-8 -*-
"""Kaynakca alfabetik sirasini denetler.

Siralama anahtari Ingilizce alfabelemeye gore kurulur: Turkce ve Almanca
harfler ASCII karsiliklarina indirilir (c->c, g->g, i->i, o->o, s->s, u->u,
ss->ss). Aksi halde dogru siradaki kayitlar sahte uyari uretir.
"""
import io
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii', errors='backslashreplace')
MAN = Path(r'C:\Users\Lenova\Desktop\GIS_Hydrojen\v5\manuscript\manuscript.tex')

LATEX = [(r'\\ss\b', 'ss'), (r'\\["\'`^~=.]\s*\{?([a-zA-Z])\}?', r'\1'),
         (r'\\[ucvHkrdb]\s*\{([a-zA-Z]+)\}', r'\1'), (r'\\i\b', 'i'), (r'\\j\b', 'j')]


def anahtar(e):
    for d, k in LATEX:
        e = re.sub(d, k, e)
    e = re.sub(r'\\[a-zA-Z]+\s*', ' ', e)
    e = re.sub(r'[{}~]', '', e)          # parantez bosluk birakmadan atilir:
    #                                      G{\"u}l -> Gul olmali, "G u l" degil
    e = re.sub(r'\(\d{4}[a-z]?\)', '', e)
    for a, b in (('ı', 'i'), ('İ', 'i'), ('ß', 'ss'), ('ø', 'o'), ('ł', 'l')):
        e = e.replace(a, b)
    e = unicodedata.normalize('NFKD', e)
    e = ''.join(c for c in e if not unicodedata.combining(c))
    return re.sub(r'[^a-z ]', '', e.lower()).strip()


et = re.findall(r'\\bibitem\[([^\]]*)\]\{([^}]*)\}', MAN.read_text(encoding='utf-8'))
bozuk = [(et[i - 1], et[i]) for i in range(1, len(et))
         if anahtar(et[i][0]) < anahtar(et[i - 1][0])]

print(f'  bibitem: {len(et)}  | sira bozulmasi: {len(bozuk)}')
for onc, son in bozuk:
    print(f'    {onc[1]:<30} "{anahtar(onc[0])}"  ->  {son[1]:<30} "{anahtar(son[0])}"')
sys.exit(1 if bozuk else 0)
