"""
Aşama III/IV çıktılarının özeti: senaryo tablosu, Pareto cephesi ve ağ haritası.

Çıktılar
  data/processed/stage3/summary_scenarios.csv
  figures/Fig3_network_base.png
  figures/Fig4_pareto_base.png
Kullanım: python code/optimization/summarise_stage3.py
"""
import gzip
import io
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402
import pandas as pd               # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
S3 = ROOT / 'data/processed/stage3'
FIG = ROOT / 'figures'
STAGE2 = ROOT / 'data/processed/stage2'
SITES = ['S1', 'S2', 'S3', 'S4', 'S5']
ORDER = ['base', 'deterministic', 'island', 'grid', 'sec48', 'sec57_5', 'land_cluster', 'phi0_5', 'phi0_0',
         'gamma0', 'gamma0_5', 'lambda0_25', 'lambda0_75', 'delta10', 'delta12_5', 'delta15', 'delta20',
         'import_free', 'trailer_h4400', 'trailer_h8000', 'pipe_geo_cap', 'pipe12_cap311', 'pipe12_dea', 'pipe_capex135', 'demand_upper', 'outage_cavern',
         'outage_pipeline', 'cf_top3_det', 'cf_top3_rpp', 'abl0_v3equiv', 'abl1_demand', 'abl2_merge', 'abl3_small']


def scenario_table():
    q_file = STAGE2 / 'stage2_scores.csv'
    q_scores = pd.read_csv(q_file).set_index('site').Q01.to_dict()
    rows = []
    for tag in ORDER:
        f = S3 / tag / 'solution.csv'
        if not f.exists():
            continue
        r = pd.read_csv(f).iloc[0]
        q_bar = sum(q_scores[i] * r[f'{i}_H2_t'] for i in SITES) / max(r.produced_t, 1e-9)
        alpha = [r[c] for c in r.index if c.startswith('alpha_')]
        rows.append({
            'scenario': tag, 'f1_MEUR': r.f1 / 1e6, 'E_z_MEUR': r.E_z / 1e6, 'z_min_MEUR': r.z_min / 1e6,
            'z_max_MEUR': r.z_max / 1e6, 'penalty_MEUR': r.penalty / 1e6, 'delivered_kt': r.delivered_t / 1e3,
            'LCOH_E_eur_kg': r.LCOH_E_eur_kg, 'Q_bar': q_bar, 'alpha_mean': float(np.mean(alpha)),
            'wind_MW': sum(r[f'{i}_W_MW'] for i in SITES), 'pv_MW': sum(r[f'{i}_PV_MW'] for i in SITES),
            'ely_MW': sum(r[f'{i}_E_MW'] for i in SITES), 'cavern_kt': r.cavern_t / 1e3,
            'export_rev_MEUR': -r.cost_export_revenue_MEUR, 'truck_MEUR': r.cost_truck_MEUR,
            'pipeline_MEUR': r.cost_pipeline_MEUR, 'open_sites': r.open_sites, 'pipelines': r.pipelines,
            'import_kt': r.get('import_t', 0.0) / 1e3, 'mip_gap': r.get('mip_gap', np.nan),
            **{f'{i}_E_MW': r[f'{i}_E_MW'] for i in SITES}, **{f'{i}_H2_kt': r[f'{i}_H2_t'] / 1e3 for i in SITES},
            **{f'{i}_FLH_h': r[f'{i}_FLH_h'] for i in SITES}})
    df = pd.DataFrame(rows)
    # Tam hassasiyetle yazilir: bir sayi zincir boyunca YALNIZ BIR KEZ yuvarlanmalidir.
    # Burada 4 ondaliga yuvarlamak, manuscript_numbers.py'nin 3 ondaliga indirgemesiyle
    # birlesince Q_bar gibi dar araliklarda yanlis degerler uretiyordu.
    df.to_csv(S3 / 'summary_scenarios.csv', index=False)
    return df


def network_map(tag='base'):
    import geopandas as gpd
    adm = gpd.read_file(io.BytesIO(gzip.decompress((ROOT / 'data/raw/gis/real/snapshot_adm1_simplified.geojson.gz').read_bytes())))
    sites = pd.read_csv(ROOT / 'data/raw/gis/real/candidate_sites.csv').set_index('code')
    dem = pd.read_csv(ROOT / 'data/raw/demand/demand_inventory.csv').set_index('node_id')
    st = pd.read_csv(ROOT / 'data/raw/network/storage_nodes.csv').set_index('node_id')
    xy = {**{i: (sites.lon[i], sites.lat[i]) for i in sites.index},
          **{j: (dem.lon[j], dem.lat[j]) for j in dem.index if pd.notna(dem.lon[j])},
          **{g: (st.lon[g], st.lat[g]) for g in st.index}}
    man = json.loads((S3 / tag / 'manifest.json').read_text(encoding='utf-8'))
    for j, ms in man.get('demand_nodes_members', {}).items():     # birleşik teslim noktaları
        if j not in xy:
            xy[j] = (float(np.mean([dem.lon[m] for m in ms])), float(np.mean([dem.lat[m] for m in ms])))
    fl = pd.read_csv(S3 / tag / 'flows.csv')
    sol = pd.read_csv(S3 / tag / 'solution.csv').iloc[0]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    adm.boundary.plot(ax=ax, color='0.75', lw=0.4)
    tmax = fl.t_per_yr.max()
    for r in fl.itertuples():
        (x0, y0), (x1, y1) = xy[r.origin], xy[r.destination]
        small = r.mode == 'pipe' and str(getattr(r, 'pipe_type', 'L')) == 'S'
        ax.plot([x0, x1], [y0, y1], color=('tab:cyan' if small else 'tab:blue') if r.mode == 'pipe' else 'tab:orange',
                ls='-' if r.mode == 'pipe' else '--', lw=0.4 + 4.0 * r.t_per_yr / tmax, alpha=0.8, zorder=2)
    for i in SITES:
        e = sol[f'{i}_E_MW']
        if e < 1:          # açılmayan aday: içi boş işaret
            ax.scatter(*xy[i], s=30, marker='^', facecolors='none', edgecolors='0.4', zorder=4)
            ax.annotate(f'{i}\nnot opened', xy[i], xytext=(5, 4), textcoords='offset points', fontsize=7, color='0.4')
            continue
        ax.scatter(*xy[i], s=20 + e / 6, marker='^', color='tab:green', edgecolor='k', zorder=4)
        ax.annotate(f'{i}\n{e:,.0f} MW', xy[i], xytext=(5, 4), textcoords='offset points', fontsize=7)
    for j in [c[2:-2] for c in sol.index if c.startswith('y_') and c.endswith('_t')]:
        ax.scatter(*xy[j], s=25, marker='s', color='tab:red', edgecolor='k', zorder=4)
    for g in st.index:
        ax.scatter(*xy[g], s=70, marker='D', color='tab:purple', edgecolor='k', zorder=5)
        ax.annotate(f'Tuz Gölü\n{sol.cavern_t / 1e3:,.1f} kt', xy[g], xytext=(5, -16), textcoords='offset points', fontsize=7)
    from matplotlib.lines import Line2D
    types = set(fl.loc[fl['mode'] == 'pipe', 'pipe_type'].astype(str)) if 'pipe_type' in fl else {'L'}
    h = ([Line2D([], [], color='tab:blue', lw=2, label='Pipeline (20")')] if 'L' in types else []) + \
        ([Line2D([], [], color='tab:cyan', lw=2, label='Pipeline (12")')] if 'S' in types else [])
    ax.legend(handles=h + [
                       Line2D([], [], color='tab:orange', lw=2, ls='--', label='Tube trailer'),
                       Line2D([], [], marker='^', ls='', color='tab:green', mec='k', label='Production site (electrolyser MW)'),
                       Line2D([], [], marker='s', ls='', color='tab:red', mec='k', label='Demand node'),
                       Line2D([], [], marker='D', ls='', color='tab:purple', mec='k', label='Salt-cavern storage')],
              loc='lower left', fontsize=7, frameon=True)
    ax.set_xlim(25.5, 45); ax.set_ylim(35.7, 42.3); ax.set_aspect(1.25)
    ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
    fig.tight_layout()
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f'Fig3_network_{tag}.png', dpi=300)
    plt.close(fig)


def pareto_front(tag='base_pareto'):
    """Pareto noktaları; süre sınırına takılıp ayrıca (pareto_fix_<adım>) yeniden çözülen noktalar onların
    yerine konur; yalnız aynı Q skorları ve aynı ε ile çözülmüş düzeltmeler kabul edilir.
    Diz noktası: uçları birleştiren doğruya normalize uzayda en uzak nokta."""
    f = S3 / tag / 'pareto.csv'
    if not f.exists():
        return None
    front_q = json.loads((S3 / tag / 'manifest.json').read_text(encoding='utf-8'))['Q']
    p = pd.read_csv(f).drop_duplicates('Q_bar', keep='first')
    for d in S3.glob('pareto_fix_*'):
        step = d.name.replace('pareto_fix_', '')
        if (d / 'solution.csv').exists() and step in set(p.step):
            fix_q = json.loads((d / 'manifest.json').read_text(encoding='utf-8'))['Q']
            fix = pd.read_csv(d / 'solution.csv').iloc[0]
            old = p.loc[p.step == step].iloc[0]
            if fix_q != front_q or abs(fix.eps_Qbar - old.eps_Qbar) > 1e-9:
                print(f'Skipping {d.name}: solved with different Q scores or epsilon')
                continue
            if fix.f1 <= old.f1:          # yalnız iyileşme varsa değiştir
                row = {c: fix[c] for c in p.columns if c in fix.index}
                row['step'] = step + '_resolved'
                p = pd.concat([p[p.step != step], pd.DataFrame([row])], ignore_index=True)
    p = p.sort_values('Q_bar').reset_index(drop=True)
    x = (p.Q_bar - p.Q_bar.min()) / (p.Q_bar.max() - p.Q_bar.min())
    y = (p.f1 - p.f1.min()) / (p.f1.max() - p.f1.min())
    p['knee_dist'] = (x - y) / np.sqrt(2)          # doğru y = x'e uzaklık (dışbükey cephe için pozitif)
    p['is_knee'] = p.knee_dist == p.knee_dist.max()
    p.to_csv(S3 / tag / 'pareto_front_final.csv', index=False)
    return p


def pareto_plot(tag='base_pareto'):
    p = pareto_front(tag)
    if p is None:
        return None
    fig, ax = plt.subplots(figsize=(5.5, 4))
    # V4: eksen teslim edilen €/kg (E_Me) ve mutlak Q̄; yüzde değişim ölçeğe bağlı olduğundan kullanılmaz
    p['f1_per_kg'] = p.f1 / p.delivered_t / 1000
    ax.plot(p.Q_bar, p.f1_per_kg, 'o-', color='tab:blue')
    k = p[p.is_knee].iloc[0]
    ax.scatter([k.Q_bar], [k.f1_per_kg], s=120, facecolors='none', edgecolors='tab:red', zorder=5, label='Knee point')
    ax.legend(fontsize=7, loc='upper left')
    ax.margins(x=0.08, y=0.12)                    # etiketler icin bosluk
    prev = None
    for r in p.itertuples():                      # etiket yalnız açık saha kümesi değiştiğinde
        if r.open_sites != prev:
            first = prev is None
            # Her iki etiket de noktanin ALTINA konur. Yukari kaydirmak sonuncuyu
            # eksenin disina tasiriyor (en ust nokta), ilkini de egrinin uzerine
            # bindiriyordu; altta her iki tarafta da bos alan var.
            ax.annotate('open: ' + r.open_sites.replace(',', ', '), (r.Q_bar, r.f1 / r.delivered_t / 1000),
                        xytext=(6, -10) if first else (-8, -10), textcoords='offset points',
                        fontsize=7, ha='left' if first else 'right', va='top')
            prev = r.open_sites
    ax.set_xlabel(r'Production-weighted suitability $\bar{Q}$')
    ax.set_ylabel(r'Robust objective $f_1$ per kg delivered (€/kg)')
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / 'Fig4_pareto_base.png', dpi=300)
    plt.close(fig)
    return p


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    df = scenario_table()
    cols = ['scenario', 'f1_MEUR', 'E_z_MEUR', 'LCOH_E_eur_kg', 'delivered_kt', 'alpha_mean', 'Q_bar', 'wind_MW', 'pv_MW',
            'ely_MW', 'cavern_kt', 'export_rev_MEUR', 'open_sites', 'pipelines']
    print(df[cols].round(3).to_string(index=False))
    network_map('base')
    p = pareto_plot('base_pareto')
    if p is not None:
        print(p[['step', 'f1', 'Q_bar', 'LCOH_E_eur_kg', 'mip_gap', 'knee_dist', 'is_knee', 'open_sites']].round(3).to_string(index=False))


if __name__ == '__main__':
    main()
