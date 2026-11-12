"""
gis_pipeline_real.py ve requirements-gis.txt dosyalarını tek bir Colab notebook'una gömer.
Kodun tek kaynağı .py dosyasıdır; notebook her değişiklikten sonra bu betikle yeniden üretilir.

Kullanım:  python code/gis/build_colab_notebook.py
Çıktı:     code/gis/GH2_GIS_Real_Colab.ipynb
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'gis_pipeline_real.py'
REQS = HERE / 'requirements-gis.txt'
OUT = HERE / 'GH2_GIS_Real_Colab.ipynb'


def md(text):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': text.splitlines(keepends=True)}


def code(text):
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [],
            'source': text.splitlines(keepends=True)}


def main():
    script = SCRIPT.read_text(encoding='utf-8')
    reqs = [l for l in REQS.read_text(encoding='utf-8').splitlines() if l and not l.startswith('#')]
    # %%writefile sondaki satır sonunu kırpabildiği için karşılaştırma tek satır sonuna normalize edilir;
    # repo dosyası tek satır sonuyla bittiğinde bu değer dosyanın kendi SHA-256 değerine eşittir.
    sha = hashlib.sha256((script.rstrip('\n') + '\n').encode('utf-8')).hexdigest()

    cells = [
        md(f"""# GH₂ — Aşama I GIS (gerçek veri)

Bu notebook `code/gis/build_colab_notebook.py` ile **otomatik üretilmiştir; elle düzenlemeyin.**
Gömülü betik: `gis_pipeline_real.py`, SHA-256 `{sha}`

**Ne yapar:** Global Wind Atlas, PVGIS-SARAH3, Copernicus GLO-90, OSM ve HydroRIVERS verilerinden
Türkiye için 0.1° ızgarada 6 katmanı hesaplar, özellik tablosunu dondurur, filtre + DBSCAN ile aday
sahaları seçer.

**Süre:** yaklaşık 30–60 dk (en uzun adım ~8.000 PVGIS sorgusu). Ara sonuçlar önbelleğe yazılır;
oturum koparsa aynı hücreleri yeniden çalıştırın, kaldığı yerden devam eder.

**Sonunda:** `gis_outputs.zip` indirilir (birkaç MB). Repoda `data/raw/gis/real/` altına açın.

Adımlar: 1 → 2 → 3 → 4 → 5 sırasıyla çalıştırın."""),
        md('## 1. Ayarlar\nGoogle Drive kullanılırsa önbellek oturum kopsa da korunur (önerilir).'),
        code("""USE_DRIVE = True   # False: çıktılar yalnız /content altında tutulur
TEST_MODE = False  # True: yalnız küçük test alanı (~5 dk)

import os
if USE_DRIVE:
    from google.colab import drive
    drive.mount('/content/drive')
    OUT = '/content/drive/MyDrive/GH2_GIS/gis_outputs' + ('_test' if TEST_MODE else '')
else:
    OUT = '/content/gis_outputs' + ('_test' if TEST_MODE else '')
os.makedirs(OUT, exist_ok=True)
print('Çıktı klasörü:', OUT)"""),
        md('## 2. Paketler\nTest edilmiş sürümler kurulur. Kurulamazsa uyarı verilir ve güncel sürümler kurulur; '
           'kullanılan sürümler her durumda `features_manifest.json` içine kaydedilir.'),
        code(f"""import subprocess, sys
PINNED = {json.dumps(reqs)}
r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', *PINNED], capture_output=True, text=True)
if r.returncode != 0:
    print('UYARI: sabit sürümler kurulamadı, güncel sürümler kuruluyor.\\n', r.stderr[-1500:])
    names = [p.split('==')[0] for p in PINNED]
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', *names], check=True)
print(subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True).stdout)"""),
        md('## 3. Betiği yaz'),
        code('%%writefile gis_pipeline_real.py\n' + script),
        code(f"""import hashlib
txt = open('gis_pipeline_real.py', encoding='utf-8').read()
sha = hashlib.sha256((txt.rstrip('\\n') + '\\n').encode('utf-8')).hexdigest()
print(sha)
assert sha == '{sha}', 'Betik repodaki sürümle aynı değil!'"""),
        md('## 4. Çalıştır\nA (veri çıkarma) + B (seçim) aşamaları. Kesilirse bu hücreyi yeniden çalıştırın.'),
        code("""args = ['--out', OUT] + (['--test'] if TEST_MODE else [])
!python gis_pipeline_real.py {' '.join(args)}"""),
        md('## 5. Sonuçları indir'),
        code("""import shutil
from google.colab import files
zip_path = shutil.make_archive('/content/gis_outputs', 'zip', OUT)
files.download(zip_path)"""),
    ]
    nb = {'cells': cells, 'metadata': {'colab': {'provenance': []},
                                       'kernelspec': {'display_name': 'Python 3', 'name': 'python3'},
                                       'language_info': {'name': 'python'}},
          'nbformat': 4, 'nbformat_minor': 5}
    OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'Yazıldı: {OUT}  (betik sha256 {sha[:12]}…)')


if __name__ == '__main__':
    main()
