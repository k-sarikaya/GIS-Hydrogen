# -*- coding: utf-8 -*-
"""Kaynakca capraz dogrulama: manuscript.tex bibitem'lerini Crossref'e karsi denetler.

Cikti: docs/reviews/ref_verify_report.csv  (her kayit icin alan bazli karsilastirma)
       konsola ozet

Kullanim:  python code/tools/verify_references.py [--limit N] [--only-doi]
"""
import argparse
import csv
import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii', errors='backslashreplace')

ROOT = Path(__file__).resolve().parents[2]
MAN = ROOT / 'manuscript' / 'manuscript.tex'
OUT = ROOT / 'docs' / 'reviews' / 'ref_verify_report.csv'
UA = 'GIS-Hydrogen-refcheck/1.0 (mailto:kadir.sarikaya@gop.edu.tr)'


# ------------------------------------------------------------------ ayristirma
LATEX_AKSAN = [
    # once coklu-karakter karsiliklar
    (r'\\ss\b', 'ss'), (r'\\ae\b', 'ae'), (r'\\oe\b', 'oe'),
    # \"o  \'e  \`a  \^i  \~n  \=o  \.z   (suslu parantezli ve parantezsiz)
    (r'\\["\'`^~=.]\s*\{?([a-zA-Z])\}?', r'\1'),
    # \u{g}  \c{c}  \v{s}  \H{o}  \k{a}  \r{a}  \d{s}  \b{o}  \t{oo}
    (r'\\[ucvHkrdbt]\s*\{([a-zA-Z]+)\}', r'\1'),
    (r'\\[ucvHkrdbt]\s+([a-zA-Z])', r'\1'),
    # noktasiz i ve j
    (r'\\i\b', 'i'), (r'\\j\b', 'j'),
    (r'\\[lLoO]\b', lambda m: m.group(0)[1]),
]


def sadelestir(s):
    """LaTeX kacislarini ve aksanlari temizler, karsilastirma icin normalize eder.

    Aksan komutlari SILINMEZ, tasidiklari harfe indirgenir: \\u{g} -> g, \\i -> i,
    \\ss -> ss. Aksi halde Turkce ve Almanca soyadlari parcalanip sahte uyusmazlik
    uretir (Dagistanli -> 'Da g stanl').
    """
    for desen, karsilik in LATEX_AKSAN:
        s = re.sub(desen, karsilik, s)
    s = re.sub(r'\\[a-zA-Z]+\s*', ' ', s)
    s = s.replace('~', ' ').replace('{', '').replace('}', '')
    s = s.replace('--', '-').replace('\\&', '&')
    # NFKD bunlari ayristirmaz: ayri harf sayilirlar
    for a, b in (('ı', 'i'), ('İ', 'I'), ('ß', 'ss'), ('ø', 'o'), ('Ø', 'O'),
                 ('đ', 'd'), ('ð', 'd'), ('þ', 'th'), ('ł', 'l'), ('Ł', 'L')):
        s = s.replace(a, b)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', s).strip()


def anahtar(s):
    s = sadelestir(s).lower()
    return re.sub(r'[^a-z0-9 ]', '', s)


def bibitemleri_oku():
    t = MAN.read_text(encoding='utf-8')
    kayitlar = []
    parcalar = re.split(r'\\bibitem\[', t)[1:]
    for p in parcalar:
        m = re.match(r'(.*?)\]\{(.*?)\}(.*?)(?=\n\s*\n|\Z)', p, re.S)
        if not m:
            continue
        etiket, key, govde = m.group(1), m.group(2), m.group(3).strip()
        govde = re.sub(r'\s+', ' ', govde)

        doi = None
        d = re.search(r'(?:doi\.org/|\\doi\{)(10\.[^\s},]+)', govde)
        if d:
            doi = d.group(1).rstrip('.').replace('\\', '')

        yil = None
        y = re.search(r',\s*((?:19|20)\d{2})[a-z]?\.', govde)
        if y:
            yil = y.group(1)
        elif (ye := re.search(r'\((\d{4})', etiket)):
            yil = ye.group(1)

        # yazarlar: ilk "YYYY." oncesi ('a'/'b' ekli yillar dahil)
        yzr = ''
        if yil:
            ym = re.search(r'(.*?),\s*' + re.escape(yil) + r'[a-z]?\.', govde)
            yzr = ym.group(1) if ym else ''
        ilk_soyad = sadelestir(yzr.split(',')[0]).strip() if yzr else ''

        # baslik: "YYYY. " sonrasi ilk cumle
        baslik = ''
        if yil:
            # yil 'a'/'b' ekiyle gelebilir (2019a, 2019b); eksi halde baslik ve cilt ayristirilamaz
            b = re.search(re.escape(yil) + r'[a-z]?\.\s*(.+?)\.\s', govde)
            if b:
                baslik = b.group(1)

        cilt = None
        if baslik:
            kalan = govde.split(baslik, 1)[-1]
            c = re.search(r'\s(\d+)\s*(?:~?\(\d+\))?,', kalan)
            if c:
                cilt = c.group(1)

        kayitlar.append({'key': key, 'etiket': sadelestir(etiket), 'doi': doi, 'yil': yil,
                         'ilk_soyad': ilk_soyad, 'baslik': sadelestir(baslik), 'cilt': cilt,
                         'govde': govde})
    return kayitlar


# ------------------------------------------------------------------ crossref
def crossref(doi):
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='/().;-_')
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode('utf-8'))['message'], None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return datacite(doi)
        return None, f'HTTP {e.code}'
    except Exception as e:                                    # aglayan her sey
        return None, type(e).__name__


def datacite(doi):
    """Crossref 404 -> DataCite dene. Zenodo, Copernicus ve cogu veri seti orada kayitli;
    Crossref'te bulunmamalari DOI'nin yanlis oldugu anlamina gelmez."""
    url = 'https://api.datacite.org/dois/' + urllib.parse.quote(doi, safe='/().;-_')
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode('utf-8'))['data']['attributes']
        return {'title': [(d.get('titles') or [{}])[0].get('title', '')],
                'author': [{'family': (a.get('familyName') or a.get('name') or '')}
                           for a in (d.get('creators') or [])],
                'issued': {'date-parts': [[d.get('publicationYear')]]},
                'volume': None, 'update-to': [], '_kaynak': 'DataCite'}, None
    except urllib.error.HTTPError as e:
        return None, f'HTTP {e.code} (Crossref ve DataCite)'
    except Exception as e:
        return None, type(e).__name__


def karsilastir(k, cr):
    """Alan bazli karsilastirma -> (durum, notlar)."""
    notlar = []
    agir = False

    cr_baslik = (cr.get('title') or [''])[0]
    cr_baslik = re.sub(r'<[^>]+>', '', cr_baslik)        # Crossref basliklarinda MathML olur
    cr_baslik = sadelestir(cr_baslik)
    if k['baslik'] and cr_baslik:
        # "[dataset]", "[dataset; GLO-90 instance]" gibi bizim ekledigimiz nitelemeleri at
        k = {**k, 'baslik': re.sub(r'\s*\[[^\]]*\]', '', k['baslik']).strip()}
        oran = SequenceMatcher(None, anahtar(k['baslik']), anahtar(cr_baslik)).ratio()
        if oran < 0.90:
            notlar.append(f'BASLIK farkli (benzerlik {oran:.2f}) | CR: {cr_baslik[:90]}')
            agir = True

    yazarlar = cr.get('author') or []
    if yazarlar and k['ilk_soyad']:
        cr_soyad = sadelestir(yazarlar[0].get('family', ''))
        # tire/bosluk farki yalnizca bicimdir (Turkali-Ozbek ~ Turkali Ozbek)
        a_biz = anahtar(k['ilk_soyad']).replace(' ', '')
        a_cr = anahtar(cr_soyad).replace(' ', '')
        if a_cr and a_biz and a_cr not in a_biz and a_biz not in a_cr:
            # DataCite creator listeleri cogu zaman eksik ve sirasiz gelir; baslik birebir
            # tutuyorsa yazar uyusmazligini kaydin kendi eksikligi say, hata degil.
            baslik_tam = (k['baslik'] and cr_baslik
                          and SequenceMatcher(None, anahtar(k['baslik']),
                                              anahtar(cr_baslik)).ratio() >= 0.95)
            if cr.get('_kaynak') == 'DataCite' and baslik_tam:
                notlar.append(f'bilgi: DataCite yazar listesi eksik | CR ilk: {cr_soyad}')
            else:
                notlar.append(f'ILK YAZAR farkli | bizde {k["ilk_soyad"]} | CR: {cr_soyad}')
                agir = True

    dp = (cr.get('issued') or {}).get('date-parts') or [[None]]
    cr_yil = str(dp[0][0]) if dp and dp[0] and dp[0][0] else None
    cr_cilt = str(cr.get('volume') or '')
    cilt_tutuyor = bool(k['cilt'] and cr_cilt and k['cilt'] == cr_cilt)
    if k['cilt'] and cr_cilt and k['cilt'] != cr_cilt:
        notlar.append(f'CILT farkli | bizde {k["cilt"]} | CR: {cr_cilt}')
        agir = True

    if k['yil'] and cr_yil and k['yil'] != cr_yil:
        fark = abs(int(k['yil']) - int(cr_yil))
        # Crossref 'issued' online-first tarihini tasir; cilt yili bir sonraki yil olabilir.
        # Cilt ayni ve fark 1 yil ise bu bir hata degil, yayin akisinin normali: Info.
        if fark == 1 and cilt_tutuyor:
            notlar.append(f'bilgi: online-first kaymasi | cilt yili {k["yil"]} | CR issued {cr_yil}')
        else:
            notlar.append(f'YIL farkli | bizde {k["yil"]} | CR: {cr_yil}')
            if fark > 1:
                agir = True

    for u in (cr.get('update-to') or []):
        notlar.append(f'BILDIRIM: {u.get("type")} -> {u.get("DOI")}')
        agir = True
    if (cr.get('update-policy') or '') and cr.get('type') == 'retraction':
        notlar.append('BILDIRIM: kayit turu retraction')
        agir = True

    if agir:
        return 'Needs fix', notlar
    if any(not n.startswith('bilgi:') for n in notlar):
        return 'Check suggested', notlar
    return 'Verified', notlar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--only-doi', action='store_true')
    a = ap.parse_args()

    kayitlar = bibitemleri_oku()
    print(f'  ayristirilan bibitem : {len(kayitlar)}')
    print(f'  DOI tasiyan          : {sum(1 for k in kayitlar if k["doi"])}')
    if a.limit:
        kayitlar = kayitlar[:a.limit]

    satirlar, sayim = [], {}
    for i, k in enumerate(kayitlar, 1):
        if not k['doi']:
            if a.only_doi:
                continue
            durum, notlar = 'Unverifiable', ['DOI yok - Adim 2 gerekiyor']
        else:
            cr, hata = crossref(k['doi'])
            if hata == 'HTTP 404':
                durum, notlar = 'Needs fix', ['DOI COZULMUYOR (Crossref 404)']
            elif hata:
                durum, notlar = 'Unverifiable', [f'sorgu basarisiz: {hata}']
            else:
                durum, notlar = karsilastir(k, cr)
            time.sleep(0.35)

        sayim[durum] = sayim.get(durum, 0) + 1
        satirlar.append({'key': k['key'], 'durum': durum, 'doi': k['doi'] or '',
                         'yil': k['yil'] or '', 'ilk_soyad': k['ilk_soyad'],
                         'baslik': k['baslik'][:120], 'notlar': ' ;; '.join(notlar)})
        if durum != 'Verified':
            print(f'  [{i:3}] {durum:<16} {k["key"]:<32} {" ;; ".join(notlar)[:110]}')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)

    print('\n  --- ozet ---')
    for d in ('Verified', 'Check suggested', 'Needs fix', 'Unverifiable'):
        print(f'  {d:<17}: {sayim.get(d, 0)}')
    print(f'  rapor: {OUT}')


if __name__ == '__main__':
    main()
