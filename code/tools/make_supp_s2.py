# -*- coding: utf-8 -*-
"""params_sources.md -> Supplementary Table S2 (caption + CSV + source notes).

Kullanim: python code/tools/make_supp_s2.py
"""
import csv
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data' / 'raw' / 'params' / 'params_sources.md'
OUT = ROOT / 'submission_assets' / 'supplementary'
OUT.mkdir(parents=True, exist_ok=True)

satir = SRC.read_text(encoding='utf-8').splitlines()


def bolum(baslik_re):
    """Bir '## N. ...' basligindan bir sonrakine kadar olan satirlar."""
    bas = son = None
    for i, s in enumerate(satir):
        if re.match(r'^## ', s):
            if bas is not None and son is None:
                son = i
            if re.search(baslik_re, s):
                bas = i
                son = None
    return satir[bas:son] if bas is not None else []


def md_hucre(s):
    """| a | b | -> ['a','b']; kalin/italik ve kacis isaretleri temizlenir."""
    h = [x.strip() for x in s.strip().strip('|').split('|')]
    return [re.sub(r'\*\*|\*|`', '', x) for x in h]


# --- 1. Parametre tablosu -> CSV ---
s1 = bolum(r'1\. Parameter table')
rows = [md_hucre(s) for s in s1 if s.strip().startswith('|')]
rows = [r for r in rows if not all(set(x) <= set('-: ') for x in r)]   # ayrac satiri at

csv_yol = OUT / 'Supplementary_Table_S2_Parameter_Sources.csv'
with csv_yol.open('w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    for r in rows:
        w.writerow(r)
print(f'CSV   : {csv_yol.name}  ({len(rows)} satir, {len(rows[0])} sutun)')

# --- 2+3+5 -> kaynak notlari ---
parcalar = [satir[:15]]                                   # kurallar/konvansiyonlar
for re_b in (r'2\. Tuz G', r'3\. Notes on conversions', r'5\. Additional inputs', r'6\. V4 additions'):
    parcalar.append([''] + bolum(re_b))
notlar = '\n'.join('\n'.join(p).rstrip() for p in parcalar)
notlar = notlar.replace('# Techno-economic parameter set',
                        'Supplementary Table S2 - source notes\n\nTechno-economic parameter set')
not_yol = OUT / 'Supplementary_Table_S2_Source_Notes.txt'
not_yol.write_text(notlar + '\n', encoding='utf-8')
print(f'Notlar: {not_yol.name}  ({len(notlar.splitlines())} satir)')

# --- Caption ---
cap = (
    "Supplementary Table S2. Techno-economic parameter set for Stage III, with sources "
    "and evidence levels. The CSV gives, for each parameter, the triangular fuzzy "
    "low/mode/high values, the unit, the price basis year and currency, the full source "
    "reference, and an evidence level recording how far each source was read: FT = full "
    "text or full relevant section, FT-sec = full text of a secondary compilation, "
    "Ex = excerpt or search highlight, Abs = abstract only. Values marked (D) were derived "
    "by the author. Derivations for all values marked (D), the deterministic Tuz Golu "
    "facility data used in the model, and additional model inputs are documented in the "
    "Notes to Table S2 section; the underlying source notes are also available in the "
    "project GitHub repository.\n"
)
cap_yol = OUT / 'Supplementary_Table_S2_Caption.txt'
cap_yol.write_text(cap, encoding='utf-8')
print(f'Caption: {cap_yol.name}')

print('\n=== CSV ilk 3 satir ===')
for r in rows[:3]:
    print('   ', ' | '.join(x[:40] for x in r[:6]))
