"""Method overview figure (figures/Fig0_method_overview.png). Usage: python code/tools/make_method_figure.py"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'figures' / 'Fig0_method_overview.png'
GA_OUT = ROOT / 'figures' / 'Graphical_Abstract.png'

STAGES = [
    ('Stage I  GIS screening', 'code/gis/gis_pipeline_real.py', '#dbe9f6',
     'Open data: DEM,\nWorldCover, Global Wind\nAtlas, PVGIS, OSM,\nHydroRIVERS',
     'Pixel-level exclusion X1-X7 (90 m)\nWind / PV masks, patch sizes\nCell constraints C1-C5 (0.1 deg)\nDBSCAN clusters, 100 km spacing',
     '333 eligible cells\n29 clusters\n5 candidate sites'),
    ('Stage II  Spherical fuzzy ranking', 'code/mcdm/sf_critic_waspas.py', '#e3f1df',
     'K1-K4 from data\n(fixed anchors)\nK5-K7 from 4 experts\n(9-term scale)',
     'Hybrid spherical fuzzy matrix\nCRITIC + expert weights (α = 0.5)\nSF-WASPAS (λ = 0.5)',
     'Suitability\nscores Q_i'),
    ('Stage III  RPP-Me network model', 'code/optimization/rpp_model.py', '#fdf0d5',
     '5 delivery nodes (2030)\n4 seasons x 6 days\nhourly wind / PV (2023)\nTriangular fuzzy inputs',
     'MILP (Pyomo, HiGHS)\nWind + PV, electrolysers,\n20" and 12" pipelines, trailers,\nsalt cavern; AUGMECON2',
     'Network design\nPareto front\nCounterfactuals and\noutage runs'),
    ('Stage IV  Robustness evaluation', 'code/optimization/stage4_monte_carlo.py', '#f4e1e6',
     'Fixed Stage III\ndesigns, Stage II\nweights, survey\nresponses',
     'Weight noise, leave-one-out,\nmethod comparison\nCost draws on RPP coefficients\nRFNBO emission check',
     'Ranking stability\nCost distributions\nBreak-even prices\nEmission intensity'),
]

LINKS = ['5 candidates', 'Q_i in objective 2', 'fixed designs']
FS = 7.0


def box(ax, x, y, w, h, text, fc, code=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3,rounding_size=1.2',
                                fc=fc, ec='#444444', lw=0.8))
    ax.text(x + w / 2, y + h / 2 + (1.8 if code else 0), text, ha='center', va='center',
            fontsize=FS, linespacing=1.35)
    if code:
        ax.text(x + w / 2, y + 1.6, code, ha='center', va='center', fontsize=5.6,
                family='monospace', color='#555555')


def arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=9, lw=1.0, color='#333333'))


def graphical_abstract():
    """V4: sol yarıda ağ haritası (Fig3), sağda aşama bulguları; her bulgu doğru aşamaya etiketli."""
    import matplotlib.image as mpimg
    fig = plt.figure(figsize=(13.28, 5.31))
    fig.text(0.5, 0.95, 'When do siting preferences and hedging change a green hydrogen network? T\u00fcrkiye 2030',
             ha='center', va='center', fontsize=14, fontweight='bold', color='#20364b')
    axm = fig.add_axes([0.005, 0.02, 0.50, 0.86])
    axm.imshow(mpimg.imread(str(ROOT / 'figures' / 'Fig3_network_base.png')))
    axm.axis('off')
    ax = fig.add_axes([0.52, 0.02, 0.47, 0.86])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    cards = [
        ('I  GIS SCREENING', '333 eligible 0.1\u00b0 cells \u2192 5 candidate sites', '#dbe9f6'),
        ('II  SPHERICAL-FUZZY RANKING', 'K\u0131rklareli first; data and expert criteria kept apart', '#e3f1df'),
        ('III  ROBUST NETWORK DESIGN', '105.2 kt/yr at \u20ac9.96/kg; 12-inch pipelines make 86% of deliveries\n'
         'Ranking as pre-filter: +11% cost; front knee: 60% of gain for 22% of cost', '#fdf0d5'),
        ('IV  ROBUSTNESS EVALUATION', 'RPP = deterministic design; hedging pays above \u20ac32/kg\n'
         'Imports cheaper below \u20ac10\u201312.5/kg; RFNBO met without grid', '#f4e1e6'),
    ]
    y, h = 97, 22
    for head, body, col in cards:
        ax.add_patch(FancyBboxPatch((1, y - h), 97, h - 2, boxstyle='round,pad=0.4,rounding_size=1.5',
                                    fc=col, ec='#53616d', lw=0.9))
        ax.text(3, y - 5, head, fontsize=9.5, fontweight='bold', color='#263746', va='center')
        ax.text(3, y - 13, body, fontsize=8.4, color='#20364b', va='center', linespacing=1.4)
        y -= h + 2.5
    fig.savefig(GA_OUT, dpi=100, bbox_inches=None, pad_inches=0.02)
    print(f'wrote {GA_OUT}')


def main():
    fig, ax = plt.subplots(figsize=(7.4, 8.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(-8, 112)
    ax.axis('off')
    row_h, gap, top = 19.0, 11.0, 108.0
    tops, bottoms = [], []
    # Script paths are kept in STAGES as the source for the Reproducibility appendix,
    # but are deliberately not drawn in the figure.
    for i, (title, _code, color, inp, proc, out) in enumerate(STAGES):
        y_top = top - i * (row_h + gap)
        y0 = y_top - row_h - 3.5
        ax.text(1, y_top, title, fontsize=9, fontweight='bold', ha='left', va='center')
        box(ax, 1, y0, 26, row_h, inp, 'white')
        box(ax, 32, y0, 38, row_h, proc, color)
        box(ax, 75, y0, 24, row_h, out, 'white')
        ymid = y0 + row_h / 2
        arrow(ax, (27.6, ymid), (31.4, ymid))
        arrow(ax, (70.6, ymid), (74.4, ymid))
        tops.append(y0 + row_h)
        bottoms.append(y0)
    for i, label in enumerate(LINKS):
        y_from, y_to = bottoms[i] - 0.8, tops[i + 1] + 0.8
        arrow(ax, (87, y_from), (87, y_to))
        ax.text(85.8, (y_from + y_to) / 2, label, fontsize=6.6, style='italic', ha='right', va='center',
                color='#333333')
    fig.savefig(OUT, dpi=300, bbox_inches='tight', pad_inches=0.05)
    print(f'wrote {OUT}')
    graphical_abstract()


if __name__ == '__main__':
    main()
