# -*- coding: utf-8 -*-
"""Gonderim paketini (sanitize edilmis) yeni bir surum klasorunde olusturur.

Mevcut paketleri ASLA degistirmez; submissions/ altina yeni bir surum yazar.
Yalnizca acikca istendiginde calistirilir.

Butun kaynaklar CALISMA REPOSUNDAN okunur, onceki paketten degil. Boylece
yeni pakete eski surum kalintisi tasinmaz.

Disarida birakilanlar:
  - .git gecmisi, __pycache__, .ipynb_checkpoints
  - data/survey (bireysel uzman yanitlari: ad, zaman damgasi, serbest metin)
  - survey/ klasorunun yuklenen yanitlari
  - data/processed/overlap_run (yarim kalan calisma klasoru)
  - docs/ (ic degerlendirme notlari)
  - submissions/ (paketin paket icine yuvalanmamasi icin)
  - manuscript/archive ve code/archive (eski surum taslaklari ve betikleri)
  - LaTeX derleme artiklari (.aux, .log, .fls, .fdb_latexmk, .out, .spl ...)
  - .bak ve .pyc dosyalari
  - makalede \\includegraphics ile cagrilmayan figurler

Kullanim:
    python code/tools/build_submission.py --tag 20261104_v6
    python code/tools/build_submission.py --tag 20261104_v6 --zip
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'submission_assets'
# Tum surumler proje icinde, submissions/ altinda tutulur; masaustune yazilmaz.
OUT_BASE = ROOT / 'submissions'
PREV = OUT_BASE / 'GIS_Hydrojen_Submission_20261030'
HOLD = ROOT / 'PRE_SUBMISSION_HOLD.txt'

SNAP_DIRS = ['code', 'data', 'figures', 'manuscript']
SNAP_FILES = ['README.md', '.gitignore']

# 'submissions': paketlerin paket icine yuvalanmasini onler.
# 'archive'    : manuscript/archive ve code/archive eski surum taslaklari ve
#                eski betikleri tutar; bunlar yeni pakete GIRMEZ. Asillari
#                calisma reposunda kalir.
EXCLUDE_DIRS = {'.git', '__pycache__', '.ipynb_checkpoints', 'survey',
                'overlap_run', 'docs', 'submissions', 'archive'}
# .bak/.pyc disinda LaTeX derleme artiklari da anlik goruntuye girmez; bunlar
# her derlemede yeniden uretilir ve depoda gurultu olusturur.
EXCLUDE_SUFFIX = {'.pyc', '.bak',
                  '.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.spl',
                  '.synctex.gz', '.blg', '.toc'}


def ignore(dirpath, names):
    out = []
    for n in names:
        p = Path(dirpath) / n
        if p.is_dir() and n in EXCLUDE_DIRS:
            out.append(n)
        elif p.is_file() and p.suffix in EXCLUDE_SUFFIX:
            out.append(n)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True, help='orn. 20261031_v2')
    ap.add_argument('--zip', action='store_true')
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    OUT_BASE.mkdir(exist_ok=True)
    out = OUT_BASE / f'GIS_Hydrojen_Submission_{a.tag}'
    if out.exists():
        print(f'ZATEN VAR: {out}\nFarkli --tag verin veya klasoru silin.')
        sys.exit(1)
    sub = out / 'submission'
    snap = out / 'repository_snapshot'
    (sub / 'manuscript').mkdir(parents=True)
    (sub / 'figures').mkdir(parents=True)
    (sub / 'supplementary').mkdir(parents=True)
    snap.mkdir(parents=True)

    # --- gonderim dosyalari -------------------------------------------------
    tex = (ROOT / 'manuscript/manuscript.tex').read_text(encoding='utf-8')
    model_include = r'\input{../submission_assets/supplementary/Stage_III_Mathematical_Model.tex}'
    model_source = ASSETS / 'supplementary' / 'Stage_III_Mathematical_Model.tex'
    if model_include not in tex or not model_source.exists():
        print('HATA: Stage III mathematical model source is missing.')
        shutil.rmtree(out)
        sys.exit(1)
    tex = tex.replace(model_include, model_source.read_text(encoding='utf-8').strip())
    (sub / 'manuscript/manuscript.tex').write_text(tex, encoding='utf-8')
    shutil.copy2(ROOT / 'manuscript/manuscript.pdf', sub / 'manuscript/manuscript.pdf')
    shutil.copy2(ROOT / 'manuscript/manuscript.pdf', sub / 'manuscript.pdf')
    # Yalnizca makalede gercekten \includegraphics ile cagrilan figurler paketlenir;
    # ayrica grafiksel ozet. Kullanilmayan figurler pakete girmez ve raporlanir.
    used = set(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex))
    used.add('Graphical_Abstract.png')
    present = {f.name for f in (ROOT / 'figures').glob('*.png')}
    missing = sorted(n for n in used if n not in present)
    if missing:
        print(f'HATA: makalede cagrilan figur yok: {", ".join(missing)}')
        shutil.rmtree(out)
        sys.exit(1)
    for name in sorted(used):
        shutil.copy2(ROOT / 'figures' / name, sub / 'figures' / name)
    unused = sorted(present - used)
    shutil.copy2(ROOT / 'figures/Graphical_Abstract.png', sub / 'graphical_abstract.png')

    # Gonderim metin dosyalari REPODAN alinir (submission_assets/). Daha once bunlar
    # sabit kodlanmis eski bir paketten devralindigi icin her kurulumda sessizce v1
    # metnine geri doner, elle yapilan guncellemeler kaybolurdu. PREV yalnizca geriye
    # donuk yedek olarak kullanilir ve kullanildiginda uyarilir.
    carried, fallback = [], []
    for name in ['highlights.txt', 'graphical_abstract_caption.txt']:
        src = ASSETS / name
        if not src.exists():
            src = PREV / 'submission' / name
            fallback.append(name)
        if src.exists():
            shutil.copy2(src, sub / name)
            carried.append(name)
        else:
            print(f'HATA: gonderim metni bulunamadi: {name}')
            shutil.rmtree(out)
            sys.exit(1)
    supp_src = ASSETS / 'supplementary'
    if not any(supp_src.glob('*')):
        supp_src = PREV / 'submission' / 'supplementary'
        fallback.append('supplementary/')
    for f in sorted(supp_src.glob('*')):
        shutil.copy2(f, sub / 'supplementary' / f.name)
        carried.append(f'supplementary/{f.name}')

    # Bekleme listesi repodan alinir, onceki paketten DEGIL: boylece her
    # surum kendi kaynagindan beslenir ve eski paket kalintisi tasinmaz.
    if HOLD.exists():
        shutil.copy2(HOLD, out / HOLD.name)
        carried.append(HOLD.name)
    else:
        print(f'UYARI: {HOLD.name} repoda yok, pakete eklenmedi.')

    # --- repo anlik goruntusu ----------------------------------------------
    for d in SNAP_DIRS:
        shutil.copytree(ROOT / d, snap / d, ignore=ignore)
    for f in SNAP_FILES:
        if (ROOT / f).exists():
            shutil.copy2(ROOT / f, snap / f)
    for req in ['requirements.txt', 'code/requirements.txt']:
        if (ROOT / req).exists():
            shutil.copy2(ROOT / req, snap / 'requirements.txt')
            break

    n_files = sum(1 for _ in out.rglob('*') if _.is_file())
    size = sum(f.stat().st_size for f in out.rglob('*') if f.is_file()) / 1e6
    print(f'olusturuldu: {out}')
    print(f'  dosya: {n_files}, boyut: {size:.1f} MB')
    print(f'  gonderim metni: {len(carried)} dosya (kaynak: submission_assets/)')
    if fallback:
        print(f'  UYARI: repoda yok, eski paketten alindi: {", ".join(fallback)}')
    print(f'  paketlenen figur: {len(used)} ({", ".join(sorted(used))})')
    if unused:
        print(f'  DISARIDA BIRAKILAN figur (makalede cagrilmiyor): {", ".join(unused)}')

    if a.zip:
        zp = out.parent / f'{out.name}.zip'
        with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.rglob('*')):
                if f.is_file():
                    z.write(f, f.relative_to(out.parent))
        print(f'  zip: {zp} ({zp.stat().st_size/1e6:.1f} MB)')

    # sanitizasyon dogrulamasi
    leaks = [str(p.relative_to(out)) for p in out.rglob('*')
             if p.is_file() and ('survey' in p.parts or p.suffix in EXCLUDE_SUFFIX
                                 or '__pycache__' in p.parts or 'overlap_run' in p.parts)]
    print(f'  sanitizasyon: {"TEMIZ" if not leaks else "SIZINTI: " + ", ".join(leaks[:5])}')


if __name__ == '__main__':
    main()
