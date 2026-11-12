"""manuscript.tex içindeki üretilmiş tablo satırlarını günceller.

Blok biçimi:  %<<GEN:tab_sensitivity>> ... %<<END>>   (ya da ilk kez \\input{generated/tab_x.tex})
Kullanım: python code/tools/inline_generated.py   (v4_tables.py'den sonra)
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / 'manuscript/manuscript.tex'
GEN = ROOT / 'manuscript/generated'

t = TEX.read_text(encoding='utf-8')
t = re.sub(r'\\input\{generated/(tab_[a-z_]+)\.tex\}', r'%<<GEN:\1>>\n%<<END>>', t)


def fill(m):
    name = m.group(1)
    body = (GEN / f'{name}.tex').read_text(encoding='utf-8').rstrip('\n')
    return f'%<<GEN:{name}>>\n{body}\n%<<END>>'


t = re.sub(r'%<<GEN:(tab_[a-z_]+)>>\n.*?%<<END>>', fill, t, flags=re.S)
TEX.write_text(t, encoding='utf-8')
print('inlined:', re.findall(r'%<<GEN:(tab_[a-z_]+)>>', t))
