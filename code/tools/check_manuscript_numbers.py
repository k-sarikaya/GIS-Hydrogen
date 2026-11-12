"""Makaledeki turetilmis sayilarin son kosumun ciktisiyla uyustugunu denetler.

manuscript_numbers.py sayilari URETIR; bu betik makaleye DOGRU gecip gecmediklerini
denetler. Her yeniden kosumdan sonra calistirin: 'MISSING' kalan her satir, makalenin
o sayi icin guncellenmedigi anlamina gelir.

Kullanim:
    python code/tools/check_manuscript_numbers.py
    python code/tools/check_manuscript_numbers.py --tex manuscript/manuscript.tex
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUMBERS = ROOT / 'data/processed/manuscript_numbers.json'
TEX = ROOT / 'manuscript/manuscript.tex'

# (JSON yolu, bicim, aciklama). Yol '/' ile gezinir; liste icin '#<indeks>'.
CHECKS = [
    ('base_LCOH_E',                 '{:.2f}',  'baz teslim maliyeti'),
    ('base_production_eur_kg',      '{:.2f}',  'uretim payi'),
    ('base_logistics_eur_kg',       '{:.2f}',  'lojistik payi'),
    ('base_delivered_kt',           '{:.1f}',  'teslim edilen'),
    ('det_LCOH',                    '{:.2f}',  'deterministik maliyet'),
    ('base_cost_eur_per_kg/wind',   '{:.2f}',  'ruzgar'),
    ('base_cost_eur_per_kg/pv',     '{:.2f}',  'PV'),
    ('base_cost_eur_per_kg/electrolyser', '{:.2f}', 'elektrolizor'),
    ('base_cost_eur_per_kg/stack',  '{:.2f}',  'yigin degisimi'),
    ('base_cost_eur_per_kg/pipeline', '{:.2f}', 'boru hatti'),
    ('base_cost_eur_per_kg/truck',  '{:.2f}',  'tir'),
    ('base_cost_eur_per_kg/cavern', '{:.2f}',  'kavern'),
    ('base_cost_eur_per_kg/compressor', '{:.2f}', 'kompresor'),
    ('base_mean_FLH',               '{:,.0f}', 'ortalama tam yuk saati'),
    ('base_export_TWh',             '{:.2f}',  'sebekeye satis'),
    ('base_cavern_kt',              '{:.1f}',  'kavern stogu'),
    ('base_flows_kt/truck',         '{:.1f}',  'tir akisi'),
    ('base_flows_kt/via_tuzgolu',   '{:.1f}',  'Tuz Golu uzerinden'),
    ('base_mean_truck_haul_km',     '{:,.0f}', 'ortalama tir mesafesi'),
    ('base_max_truck_haul_km',      '{:,.0f}', 'en uzun tir bacagi'),
    ('pareto/n_points',             '{:.0f}',  'Pareto nokta sayisi'),
    ('pareto/Qknee',                '{:.3f}',  'diz noktasi Qbar'),
    ('pareto/Qmax',                 '{:.3f}',  'azami Qbar'),
    ('pareto/LCOHknee',             '{:.2f}',  'diz noktasi maliyeti'),
    ('pareto/knee_dQ_pct',          '{:.1f}',  'diz uygunluk kazanci %'),
    ('pareto/knee_df1_pct',         '{:.1f}',  'diz maliyet artisi %'),
    ('mc/base/cost_mean',           '{:,.0f}', 'MC baz ortalama'),
    ('mc/base/cost_p95',            '{:,.0f}', 'MC baz P95'),
    ('mc/base/short_kt',            '{:.1f}',  'MC ortalama acik'),
    ('mc/delta20/cost_mean',        '{:,.0f}', 'MC delta20 ortalama'),
    ('stage2_Q01/S5',               '{:.3f}',  'S5 Q01'),
    ('stage2_Q01/S3',               '{:.3f}',  'S3 Q01'),
    ('stage2_w/K2',                 '{:.3f}',  'K2 agirligi'),
    ('stage2_w/K4',                 '{:.3f}',  'K4 agirligi'),
    ('emissions/base|1000/total',   '{:.2f}',  'baz emisyon (1000 kg)'),
    ('emissions/base|300/total',    '{:.2f}',  'baz emisyon (300 kg)'),
    ('emissions/delta20|1000/total', '{:.2f}', 'delta20 emisyon'),
    ('scenarios/grid/LCOH',         '{:.2f}',  'S-grid maliyeti'),
    ('scenarios/island/LCOH',       '{:.2f}',  'S-island maliyeti'),
    ('scenarios/land_cluster/LCOH', '{:.2f}',  'kume arazi maliyeti'),
    ('grid_import_export_TWh#0',    '{:.2f}',  'sebeke alimi'),
]


def dig(obj, path):
    cur = obj
    for part in path.split('/'):
        if '#' in part:
            key, idx = part.split('#')
            if key:
                cur = cur[key]
            cur = cur[int(idx)]
        else:
            cur = cur[part]
    return cur


def variants(text):
    """Makalede gecebilecek yazimlar: 1,234 ve 1234 ayni sayidir."""
    out = {text}
    if ',' in text:
        out.add(text.replace(',', ''))
        out.add(text.replace(',', '{,}'))
    return out


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--numbers', default=str(NUMBERS))
    ap.add_argument('--tex', default=str(TEX))
    ap.add_argument('--quiet', action='store_true', help='yalniz eksikleri yaz')
    a = ap.parse_args()

    N = json.loads(Path(a.numbers).read_text(encoding='utf-8'))
    tex = Path(a.tex).read_text(encoding='utf-8')
    body = tex.split(r'\begin{thebibliography}')[0]   # kaynakcadaki sayilar sayilmaz

    missing, ok = [], 0
    for path, fmt, label in CHECKS:
        try:
            val = dig(N, path)
        except (KeyError, IndexError, TypeError):
            missing.append((path, '(JSON yolu yok)', label, 0))
            continue
        want = fmt.format(val)
        hits = sum(len(re.findall(re.escape(v), body)) for v in variants(want))
        if hits:
            ok += 1
            if not a.quiet:
                print(f'OK       {path:34s} {want:>12s}  ({hits}x)  {label}')
        else:
            missing.append((path, want, label, hits))

    for path, want, label, _ in missing:
        print(f'MISSING  {path:34s} {want:>12s}        {label}')

    print(f'\n{ok}/{len(CHECKS)} sayi makalede bulundu.')
    if missing:
        print(f'{len(missing)} sayi eksik veya guncel degil -> makaleyi guncelleyin.')
        sys.exit(1)
    print('Tum denetlenen sayilar son kosumla uyusuyor.')


if __name__ == '__main__':
    main()
