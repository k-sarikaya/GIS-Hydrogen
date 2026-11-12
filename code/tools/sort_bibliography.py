# -*- coding: utf-8 -*-
"""thebibliography girdilerini yazar-yil duzenine gore alfabetik siralar.

Kaynak kunyeleri duzeltilince bazi girdilerin yazari degisti (ornegin
'Liu et al.' -> 'Ma et al.'), bu yuzden liste alfabetik olmaktan cikti.
Elsevier author-year stilinde kaynakca alfabetik olmalidir.

Siralama anahtari: \\bibitem[ETIKET] icindeki soyadi + yil. LaTeX aksanlari
sadelestirilir, 'de/El/van/von' onekleri korunur (yayincinin yaptigi gibi).

Kullanim:  python code/tools/sort_bibliography.py [--dry-run]
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

TEX = Path(__file__).resolve().parents[2] / 'manuscript' / 'manuscript.tex'

ACCENT = {r'{\"u}': 'u', r'{\"o}': 'o', r'{\"a}': 'a', r'{\c{s}}': 's', r'{\c{S}}': 'S',
          r'{\c{c}}': 'c', r'{\c{C}}': 'C', r'{\u{g}}': 'g', r'{\u{G}}': 'G',
          r'{\i}': 'i', r'{\.I}': 'I', r"{\'a}": 'a', r"{\'e}": 'e', r"{\'\i}": 'i',
          r'{\~n}': 'n', r'{\ss}': 'ss', r'~': ' '}


def plain(s):
    for k, v in ACCENT.items():
        s = s.replace(k, v)
    s = re.sub(r'\\[a-zA-Z]+', '', s).replace('{', '').replace('}', '')
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()


def sort_key(label, body=None):
    """Alfabetik anahtar: alinti etiketindeki ilk soyadi (veya kurum kisaltmasi) + yil.

    Etiket esas alinir, govde degil: makalenin mevcut duzeni kurumsal yazarlari
    kisaltmalariyla siraliyor (AIIB 'A'da, DOE 'D'de, ICCT 'I'de). Govdeye gore
    siralamak bu kayitlari yerinden oynatirdi; amac yalniz kunyesi duzeltilen
    girdileri dogru yere tasimak.

    Ayni ilk yazarda tek yazarli kayit, cok yazarliyi onceler (Elsevier duzeni):
    bunu 'et al./and' yerine ayrilan sirali alan saglar.
    """
    s = plain(label)
    m = re.match(r'(.*?)\((\d{4})([a-z]?)\)', s)
    name, year, suf = (m.group(1), m.group(2), m.group(3)) if m else (s, '9999', '')
    # Elsevier duzeni: ayni ilk yazarda once tek yazarli, sonra iki yazarli,
    # sonra uc ve uzeri ('et al.'). Anahtar yalniz ILK soyadi kullanir.
    if re.search(r'\bet al\.?', name):
        multi = 2
    elif re.search(r'\band\b', name):
        multi = 1
    else:
        multi = 0
    name = re.split(r'\bet al\.?|\band\b', name)[0]
    name = re.sub(r'[^A-Za-z ]', ' ', name)
    name = ' '.join(name.split()).lower()
    return (name, multi, year, suf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    text = TEX.read_text(encoding='utf-8')
    head, rest = text.split('\\begin{thebibliography}{99}\n', 1)
    body, tail = rest.split('\\end{thebibliography}', 1)

    parts = re.split(r'\n\n(?=\\bibitem\[)', body.strip('\n'))
    entries = []
    for p in parts:
        m = re.match(r'\\bibitem\[([^\]]*)\]', p)
        if not m:
            print('AYRISTIRILAMADI:', p[:80])
            sys.exit(1)
        body = p.split(']', 1)[1].split('}', 1)[1].strip()
        entries.append((sort_key(m.group(1), body), m.group(1), p))

    viol = [(entries[i][1], entries[i + 1][1])
            for i in range(len(entries) - 1) if entries[i][0] > entries[i + 1][0]]
    print(f'{len(entries)} kayit; mevcut dosyada {len(viol)} sira ihlali.')
    for x, y in viol:
        print(f'   {x}  >  {y}')

    ordered = sorted(entries, key=lambda e: e[0])
    if not viol:
        print('\nListe zaten alfabetik; degisiklik gerekmiyor.')
        return

    new = (head + '\\begin{thebibliography}{99}\n'
           + '\n\n'.join(p for _k, _l, p in ordered) + '\n\n'
           + '\\end{thebibliography}' + tail)

    if a.dry_run:
        print('\n(dry-run: dosya yazilmadi)')
        return
    TEX.write_text(new, encoding='utf-8')
    print(f'\nyazildi: {TEX}')


if __name__ == '__main__':
    main()
