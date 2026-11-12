# -*- coding: utf-8 -*-
"""soft_criteria_literature_review.md -> Supplementary Table S3.

Kodlanan calismalar (3.1), olcut-frekans matrisi (3.3) ve notlar (3.3 anahtar,
3.4 ozet, 5.3 elenen olcutler).

Kullanim: python code/tools/make_supp_s3.py
"""
import csv
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'docs' / 'reviews' / 'soft_criteria_literature_review.md'
OUT = ROOT / 'submission_assets' / 'supplementary'
OUT.mkdir(parents=True, exist_ok=True)
satir = SRC.read_text(encoding='utf-8').splitlines()


def bolum(baslik_re):
    """Bir '### N.N ...' basligindan bir sonraki ## veya ### basligina kadar."""
    bas = None
    for i, s in enumerate(satir):
        if re.match(r'^#{2,3} ', s):
            if bas is not None:
                return satir[bas:i]
            if re.search(baslik_re, s):
                bas = i
    return satir[bas:] if bas is not None else []


def hucre(s):
    h = [x.strip() for x in s.strip().strip('|').split('|')]
    return [re.sub(r'\*\*|\\\*|`', '', x) for x in h]


def tablo(blok):
    r = [hucre(s) for s in blok if s.strip().startswith('|')]
    return [x for x in r if not all(set(c) <= set('-: ') for c in x)]


def yaz_csv(ad, rows):
    p = OUT / ad
    with p.open('w', newline='', encoding='utf-8-sig') as f:
        csv.writer(f).writerows(rows)
    print(f'  {ad}  ({len(rows)} satir x {len(rows[0])} sutun)')


print('CSV:')
yaz_csv('Supplementary_Table_S3_Coded_Studies.csv', tablo(bolum(r'3\.1 Coded studies')))
yaz_csv('Supplementary_Table_S3_Criterion_Frequency.csv', tablo(bolum(r'3\.3 Criterion-frequency')))

# --- Notlar ---
parcalar = []
for baslik, re_b in [('Mode codes and criterion key', r'3\.3 Criterion-frequency'),
                     ('Frequency summary', r'3\.4 Frequency summary'),
                     ('Criteria considered and not retained', r'5\.3 Candidate criteria'),
                     ('References for the coded studies', r'^## 8\. References')]:
    blok = bolum(re_b)
    blok = [s for s in blok if not re.match(r'^#{2,3} ', s)]          # markdown basliklari
    if re_b.startswith(r'3\.3'):                                      # matris govdesi + ayraci
        blok = [s for s in blok
                if not re.match(r'^\|\s*(S\d\d|ID)\s*\|', s.strip())
                and not re.match(r'^\|[\s\-:|]+\|$', s.strip())]
    parcalar.append(f'--- {baslik} ---\n' + '\n'.join(blok).strip())

notlar = ('Supplementary Table S3 - notes\n\n'
          'Coding of the siting studies reviewed for Stage II criterion selection.\n\n'
          + '\n\n'.join(parcalar) + '\n')
(OUT / 'Supplementary_Table_S3_Notes.txt').write_text(notlar, encoding='utf-8')
print(f"Notlar: Supplementary_Table_S3_Notes.txt  ({len(notlar.splitlines())} satir)")

cap = (
    "Supplementary Table S3. Literature coding underpinning Stage II criterion selection. "
    "Table S3a summarizes the 22 coded studies, including country or study context, "
    "weighting and ranking methods, and evidence levels. Table S3b presents the criterion-by-study matrix "
    "used for frequency screening, with each criterion coded according to its mode of "
    "treatment in the study. The accompanying notes define the coding modes and criterion "
    "key, summarize criterion frequencies, and explain the criteria considered but not "
    "retained. The supplementary data and supporting notes are also available in the "
    "project GitHub repository.\n"
)
(OUT / 'Supplementary_Table_S3_Caption.txt').write_text(cap, encoding='utf-8')
print('Caption: Supplementary_Table_S3_Caption.txt')
