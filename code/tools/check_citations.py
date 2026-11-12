# -*- coding: utf-8 -*-
"""Atif ve kaynakca butunlugunu denetler (gonderim oncesi kontrol).

Denetlenenler:
  1. Metinde atif yapilip kaynakcada bulunmayan anahtarlar
  2. Kaynakcada olup hic atif yapilmayan anahtarlar
  3. Tekrarlanan \\bibitem anahtarlari
  4. Dergi makalesi gorunumlu ama DOI tasimayan kayitlar (rapor/kitap/mevzuat haric)
  5. Elsevier tam yazar listesi kurali: govdesinde 'et al.' gecen kayitlar

Kullanim:  python code/tools/check_citations.py
"""
import re
import sys
from pathlib import Path

TEX = Path(__file__).resolve().parents[2] / 'manuscript' / 'manuscript.tex'

# DOI beklenmeyen kayit turleri (rapor, mevzuat, kitap, tez, veri sayfasi)
NO_DOI_OK = re.compile(
    r'(Technical Report|Report|Directive|Regulation|Strategy|Roadmap|Review 20|Thesis|thesis|'
    r'Presentation|Project Document|Annual Report|Fact sheet|Plenum Press|Agency|Information|'
    r'Conversion Factors|Cost Report|Vision|Landscape|Programme|Program Record|COM/|Paper No|'
    r'Clean Air Task Force|Hintco|auction|Bilgi Formu|Ankara|Washington|Boston|Brussels|Abu Dhabi)')


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    text = TEX.read_text(encoding='utf-8')

    cited = set()
    for m in re.findall(r'\\cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\{([^}]*)\}', text):
        cited.update(k.strip() for k in m.split(',') if k.strip())

    body = text.split(r'\begin{thebibliography}')[1]
    keys = re.findall(r'\\bibitem\[[^\]]*\]\{([^}]+)\}', body)
    entries = {}
    for part in re.split(r'\n\n(?=\\bibitem\[)', body.strip()):
        m = re.match(r'\\bibitem\[[^\]]*\]\{([^}]+)\}\n(.*)', part, re.S)
        if m:
            entries[m.group(1)] = ' '.join(m.group(2).split())

    dup = sorted({k for k in keys if keys.count(k) > 1})
    missing = sorted(cited - set(keys))
    unused = sorted(set(keys) - cited)
    no_doi = sorted(k for k, v in entries.items()
                    if 'doi.org/' not in v and not NO_DOI_OK.search(v))
    etal = sorted(k for k, v in entries.items() if re.search(r'et~?\s?al\.', v))

    print(f'atif yapilan anahtar : {len(cited)}')
    print(f'kaynakca kaydi       : {len(keys)}')
    print()
    checks = [
        ('Kaynakcada olmayan atif', missing),
        ('Hic atif yapilmayan kayit', unused),
        ('Tekrarlanan anahtar', dup),
        ('DOI tasimayan dergi kaydi', no_doi),
        ("Govdesinde 'et al.' gecen kayit", etal),
    ]
    bad = 0
    for name, items in checks:
        mark = 'OK  ' if not items else 'DIKKAT'
        print(f'{mark} {name}: {len(items)}')
        for k in items:
            print(f'        {k}')
        bad += len(items)

    print()
    if bad:
        print(f'{bad} madde incelenmeli.')
        sys.exit(1)
    print('Kaynakca butunlugu temiz.')


if __name__ == '__main__':
    main()
