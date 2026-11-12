"""Anket bilgi kartı için konum haritası: beş aday saha, aynı ölçek ve stil, performans değeri içermez.

Kullanım:  python survey/make_site_map.py   →  survey/assets/site_map.png
"""
import gzip
import io
from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sites = pd.read_csv(ROOT / 'data/raw/gis/real/candidate_sites.csv')
adm1 = gpd.read_file(io.BytesIO(gzip.decompress((ROOT / 'data/raw/gis/real/snapshot_adm1_simplified.geojson.gz').read_bytes())))

fig, ax = plt.subplots(figsize=(11, 5.2))
adm1.plot(ax=ax, color='#f2f2f2', edgecolor='#9e9e9e', linewidth=0.4)
ax.scatter(sites.lon, sites.lat, s=180, marker='o', color='#1f4e79', edgecolor='white', linewidth=1.5, zorder=5)
for r in sites.itertuples():
    ax.annotate(r.code, (r.lon, r.lat), xytext=(8, 6), textcoords='offset points', fontsize=13, weight='bold', color='#1f4e79')
ax.set_axis_off()
ax.set_aspect(1.27)
ax.set_title('Aday sahaların konumu / Location of candidate sites (S1–S5)', fontsize=12)
fig.tight_layout()
out = ROOT / 'survey/assets/site_map.png'
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200, metadata={'Software': None})
print(out)
