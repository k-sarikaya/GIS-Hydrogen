# -*- coding: utf-8 -*-
"""DOI'siz kayitlarin URL'lerini yoklar. Cozulmeyenler elle arastirilir."""
import io
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_references import bibitemleri_oku, sadelestir  # noqa: E402

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/124.0 Safari/537.36')


def yokla(url):
    for yontem in ('HEAD', 'GET'):
        req = urllib.request.Request(url, method=yontem,
                                     headers={'User-Agent': UA, 'Accept': '*/*'})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status, r.url
        except urllib.error.HTTPError as e:
            if yontem == 'HEAD' and e.code in (403, 405, 501):
                continue                       # bazi sunucular HEAD kabul etmiyor
            return e.code, None
        except Exception as e:
            if yontem == 'HEAD':
                continue
            return type(e).__name__, None
    return 'bilinmiyor', None


def main():
    kayitlar = [k for k in bibitemleri_oku() if not k['doi']]
    print(f'  DOI tasimayan kayit: {len(kayitlar)}\n')
    iyi = kotu = urlsuz = 0
    for k in kayitlar:
        u = re.search(r'(https?://[^\s,}]+)', k['govde'])
        if not u:
            print(f'  URLSIZ   {k["key"]:<26} {sadelestir(k["baslik"])[:66]}')
            urlsuz += 1
            continue
        url = u.group(1).replace('\\_', '_').replace('\\&', '&').rstrip('.')
        durum, son = yokla(url)
        ok = durum == 200
        iyi, kotu = (iyi + 1, kotu) if ok else (iyi, kotu + 1)
        if not ok:
            print(f'  {str(durum):<8} {k["key"]:<26} {url[:88]}')
        time.sleep(0.3)

    print(f'\n  --- ozet ---\n  URL cozuldu (200): {iyi}\n  URL cozulmedi    : {kotu}'
          f'\n  URL yok          : {urlsuz}')


if __name__ == '__main__':
    main()
