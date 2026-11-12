"""
Aşama III — iki amaçlı, mevsimsel, Me-ölçülü sağlam olabilirlik programlama (RPP-I) modeli.

Ağ:     5 aday saha (Aşama I) -> 7 talep düğümü (2030 temel) ve Tuz Gölü tuz mağarası deposu.
Zaman:  4 mevsim × 6 temsili gün × 24 saat (profiles.py, k-medoids, enerji korumalı).
Enerji: sahada eş konumlu yeni rüzgâr + PV, PEM elektrolizör; şebekeden çekiş yok (RFNBO),
        fazla elektrik PTF zaman dilimi katsayılarıyla satılır; satış bağlantısı <= elektrolizör gücü.
Taşıma: yeni 20" boru hattı (ikili, sabit maliyetli) veya CGH2 tüp römork (doğrusal, seviyelendirilmiş).
Depo:   Tuz Gölü; günlük enjeksiyon/çekiş sınırları, mevsim sınırlarında envanter dengesi (döngüsel).
Talep:  d̃_j = s̃ · (amaca yönelik H2)_j, s̃ = RED III oranları (params.yaml); fabrika talebi gün içinde sabit.

Belirsizlik (üçgen bulanık; params.yaml):
  - amaç katsayıları: E_Me[c] = ((1−λ)c1 + c2 + λc3)/2 (Xu & Zhou 2013);
    yıllıklandırılmış katsayıların köşeleri, monoton fonksiyonun uç değerleriyle bulunur
    (ör. düşük = CAPEX_l·CRF(r_l, n_h) + O&M_l);
  - talep: Me{d̃_j <= y_j} >= α_j, α_j ∈ [λ, 1] karar değişkeni (RPP; Pishvaee vd. 2012):
    y_j >= d2 + (α_j−λ)/(1−λ)(d3−d2);
  - teknik katsayılar (SEC, sıkıştırma enerjisi) mod değerinde, senaryo/duyarlılıkla.

Amaçlar
  f1 (min) = E_Me[z] + γ (z_max − z_min) + δ Σ_j (1−α_j)/(1−λ)(d3_j − d2_j)        (RPP-I)
  f2 (max) = Σ_i Q_i H_i   (Aşama II uygunluğu ile ağırlıklı yıllık üretim; Q̄ = f2 / Σ H_i)
  Pareto: AUGMECON2 (Mavrotas & Florios 2013).

Kullanım
  python code/optimization/rpp_model.py                     # temel senaryo, Pareto
  python code/optimization/rpp_model.py --scenario island   # fazla elektrik satılamaz
  python code/optimization/rpp_model.py --scenario grid     # yıllık eşleşmeli şebeke çekişi
  python code/optimization/rpp_model.py --set rpp.gamma_opt=0.5 --set electrolyser.sec_kwh_per_kg=48
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyomo.environ as pyo
import yaml

ROOT = Path(__file__).resolve().parents[2]
P_YAML = ROOT / 'data/raw/params/params.yaml'
F_SITES = ROOT / 'data/raw/gis/real/candidate_sites.csv'
F_DEMAND = ROOT / 'data/raw/demand/demand_inventory.csv'
F_DIST = ROOT / 'data/processed/network/distance_matrix_long.csv'
F_DIST_ST = ROOT / 'data/processed/network/distance_matrix_storage_long.csv'
F_STORE = ROOT / 'data/raw/network/storage_nodes.csv'
F_PROF = ROOT / 'data/processed/profiles/representative_days_2023_k6.csv'
F_CLUST = ROOT / 'data/raw/gis/real/clusters.csv'
STAGE2 = ROOT / 'data/processed/stage2'
SEASONS = ['DJF', 'MAM', 'JJA', 'SON']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tfn(x):
    return np.array(x['tfn'] if isinstance(x, dict) else x, dtype=float)


def crf(r, n):
    return r * (1 + r) ** n / ((1 + r) ** n - 1)


def ann_capex(capex, life, wacc, fom_abs=None, fom_pct=None):
    """Yıllıklandırılmış birim maliyetin üçgen köşeleri (düşük, mod, yüksek). Monoton: düşük köşe
    düşük CAPEX, düşük WACC, uzun ömür ve düşük O&M ile oluşur."""
    lo = capex[0] * crf(wacc[0], life[2])
    mo = capex[1] * crf(wacc[1], life[1])
    hi = capex[2] * crf(wacc[2], life[0])
    out = np.array([lo, mo, hi])
    if fom_abs is not None:
        out = out + fom_abs
    if fom_pct is not None:
        out = out + capex * fom_pct / 100.0
    return out


def collapse_to_mode(P):
    def rec(d):
        for k, v in d.items():
            if isinstance(v, dict):
                if 'tfn' in v:
                    v['tfn'] = [v['tfn'][1]] * 3
                else:
                    rec(v)
    rec(P)
    P['rpp']['gamma_opt'] = 0.0


def set_nested(d, key, val):
    ks = key.split('.')
    for k in ks[:-1]:
        d = d[k]
    if isinstance(d[ks[-1]], dict) and 'tfn' in d[ks[-1]] and not isinstance(val, dict):
        d[ks[-1]]['tfn'] = val
    else:
        d[ks[-1]] = val


# ---------------------------------------------------------------- veri
def load_data(P, q_file):
    lam = P['rpp']['lambda_me']
    sites = pd.read_csv(F_SITES).set_index('code')
    I = list(sites.index)
    dem = pd.read_csv(F_DEMAND)
    dem = dem[dem[P['demand']['rule_column']] == 1].set_index('node_id')
    basis = P['demand']['basis_column']
    by_sector = bool(P['demand'].get('sector_basis', False))
    rpp = P['rpp']
    delta_sec = rpp.get('delta_eur_per_kg_by_sector', {}) if rpp.get('delta_by_sector', False) else {}

    def sector_key(s):
        return 'ammonia' if 'ammonia' in str(s).lower() else 'refinery'

    # Bileşen (tesis) düzeyinde talep TFN'si ve ithalat paritesi
    comp_d, comp_delta = {}, {}
    for j in dem.index:
        sk = sector_key(dem.loc[j, 'sector'])
        share = tfn(P['demand']['green_share_by_sector'][sk]) if by_sector else tfn(P['demand']['green_share'])
        comp_d[j] = share * float(dem.loc[j, basis])
        comp_delta[j] = float(delta_sec.get(sk, rpp['delta_pen_eur_per_kg']))
    # Birbirine < 2 km tesisler tek teslim noktasıdır (V4)
    groups = P['demand'].get('merge_groups', {}) if P['demand'].get('merge_nodes', False) else {}
    member_of = {m: g for g, ms in groups.items() for m in ms}
    J = []
    members = {}
    for j in dem.index:
        g = member_of.get(j, j)
        if g not in members:
            members[g] = []
            J.append(g)
        members[g].append(j)
    d_t = {g: sum(comp_d[m] for m in ms) for g, ms in members.items()}                     # t/yr TFN
    # δ ağırlıkları: ceza terimi Σ_m δ_m (d3_m − d2_m); ithalat (tanı) maliyeti mod talebiyle ağırlıklı δ
    pen_w = {g: sum(comp_delta[m] * (comp_d[m][2] - comp_d[m][1]) for m in ms) for g, ms in members.items()}
    delta_node = {g: sum(comp_delta[m] * comp_d[m][1] for m in ms) / sum(comp_d[m][1] for m in ms)
                  for g, ms in members.items()}
    store = pd.read_csv(F_STORE).set_index('node_id')
    G = list(store.index)

    dl = pd.read_csv(F_DIST)
    ds = pd.read_csv(F_DIST_ST)
    L, Lgeo = {}, {}
    acc = {}
    for _, r in dl.iterrows():
        if r.site in I and r.node_id in member_of or r.node_id in members:
            acc.setdefault((r.site, member_of.get(r.node_id, r.node_id)), []).append((float(r.road_km), float(r.haversine_km)))
    for _, r in ds.iterrows():
        if r.origin in I and r.destination in G:
            acc.setdefault((r.origin, r.destination), []).append((float(r.road_km), float(r.haversine_km)))
        elif r.origin in G and (r.destination in member_of or r.destination in members):
            acc.setdefault((r.origin, member_of.get(r.destination, r.destination)), []).append((float(r.road_km), float(r.haversine_km)))
    for a, vals in acc.items():          # birleşik düğüm: üyelere uzaklıkların ortalaması (< 2 km fark)
        if a[0] in I + G and (a[1] in J or a[1] in G):
            L[a] = float(np.mean([v[0] for v in vals]))
            Lgeo[a] = float(np.mean([v[1] for v in vals]))
    route_rule = P['pipeline'].get('route_rule', 'road_proxy')
    if route_rule == 'road_proxy':
        Lpipe = L.copy()
    elif route_rule == 'geodesic_cap':
        tau = float(P['pipeline'].get('distance_tau', 1.2))
        Lpipe = {a: min(L[a], tau * Lgeo[a]) for a in L}
    else:
        raise ValueError(f'Unsupported pipeline route_rule: {route_rule}')
    A = list(L)

    prof = pd.read_csv(F_PROF)
    days = prof.drop_duplicates('rep_day')[['season', 'rep_day', 'weight_days']]
    Dset = list(days.rep_day)
    wd = dict(zip(days.rep_day, days.weight_days.astype(float)))
    season_of = dict(zip(days.rep_day, days.season))
    cfw = {(r.site, r.rep_day, int(r.hour)): float(r.wind_cf) for r in prof.itertuples()}
    cfp = {(r.site, r.rep_day, int(r.hour)): float(r.pv_cf) for r in prof.itertuples()}

    # Arazi sınırı (MW): hücre veya küme alanı × güç yoğunluğu
    if P['land']['area_basis'] == 'cell':
        aw, ap = sites.cell_wind_area_km2, sites.cell_pv_area_km2
        ov_col = 'cell_wind_pv_overlap_km2'
    else:
        aw, ap = sites.cluster_wind_area_km2, sites.cluster_pv_area_km2
        ov_col = 'cluster_wind_pv_overlap_km2'
    Wmax = (aw * P['wind']['density_mw_per_km2']).to_dict()
    Pmax = (ap * P['pv']['density_mw_per_km2']).to_dict()

    # Rüzgâr ve PV maskeleri örtüşür: aynı km²'yi iki kez tahsis etmemek için ortak kullanım
    # kısıtı (bkz. params.yaml land.co_use_share). Örtüşme ölçülmemişse (eski öznitelik tablosu)
    # 0 kabul edilir; birleşim alanı aw+ap olur ve kısıt bağlayıcı olmaz, yani model eski
    # bağımsız üst sınırlara birebir indirgenir.
    ov = sites[ov_col].fillna(0.0) if ov_col in sites.columns else pd.Series(0.0, index=sites.index)
    Acap = ov.to_dict()                       # ölçülen örtüşme (km²)
    Aunion = (aw + ap - ov).to_dict()         # birleşim alanı (km²)
    overlap_measured = bool(ov_col in sites.columns and sites[ov_col].notna().all())

    q = pd.read_csv(q_file).set_index('site')['Q01'].to_dict()
    return dict(I=I, J=J, G=G, A=A, L=L, Lpipe=Lpipe, D=Dset, wd=wd, season_of=season_of, cfw=cfw, cfp=cfp,
                d_t=d_t, Wmax=Wmax, Pmax=Pmax, Acap=Acap, Aunion=Aunion,
                overlap_measured=overlap_measured, Q=q, lam=lam, dem=dem, sites=sites,
                members=members, comp_d=comp_d, comp_delta=comp_delta, pen_w=pen_w, delta_node=delta_node)


def coefficients(P):
    """Amaçtaki birim maliyetlerin üçgen köşeleri (€ / birim)."""
    r = tfn(P['finance']['wacc_real'])
    w, pv, el, cp, cv, pl, tr = (P[k] for k in ['wind', 'pv', 'electrolyser', 'compression', 'cavern', 'pipeline', 'trailer'])
    C = {}
    C['wind_MW'] = 1000 * ann_capex(tfn(w['capex_eur_per_kw']), tfn(w['lifetime_yr']), r, fom_abs=tfn(w['fom_eur_per_kw_yr']))
    C['pv_MW'] = 1000 * ann_capex(tfn(pv['capex_eur_per_kw']), tfn(pv['lifetime_yr']), r, fom_abs=tfn(pv['fom_eur_per_kw_yr']))
    C['ely_MW'] = 1000 * ann_capex(tfn(el['capex_eur_per_kw']), tfn(el['lifetime_yr']), r, fom_pct=tfn(el['fom_pct_capex_yr']))
    cap = tfn(el['capex_eur_per_kw'])
    C['stack_MWh'] = 1000 * np.array([tfn(el['stack_cost_pct_capex'])[0] / 100 * cap[0] / tfn(el['stack_lifetime_h'])[2],
                                      tfn(el['stack_cost_pct_capex'])[1] / 100 * cap[1] / tfn(el['stack_lifetime_h'])[1],
                                      tfn(el['stack_cost_pct_capex'])[2] / 100 * cap[2] / tfn(el['stack_lifetime_h'])[0]])
    C['water_t'] = tfn(P['water']['use_l_per_kg']) * tfn(P['water']['cost_eur_per_m3'])   # L/kg·€/m3 = €/t
    C['comp_MW'] = 1000 * ann_capex(tfn(cp['capex_eur_per_kw']), tfn(cp['lifetime_yr']), r, fom_pct=tfn(cp['fom_pct_capex_yr']))
    C['cavern_t'] = 1000 * ann_capex(tfn(cv['capex_eur_per_kg_wg']), tfn(cv['lifetime_yr']), r, fom_pct=tfn(cv['fom_pct_capex_yr']))
    C['pipe_km'] = 1e6 * ann_capex(tfn(pl['capex_meur_per_km']), tfn(pl['lifetime_yr']), r, fom_pct=tfn(pl['fom_pct_capex_yr']))
    if 'small' in pl:
        C['pipe_km_S'] = 1e6 * ann_capex(tfn(pl['small']['capex_meur_per_km']), tfn(pl['lifetime_yr']), r,
                                         fom_pct=tfn(pl['fom_pct_capex_yr']))
    if 'capex_eur_per_kg_payload' in tr:
        # yıllıklandırılmış römork sermayesi + bakım, € / (kg yük kapasitesi · yıl)
        capt = tfn(tr['capex_eur_per_kg_payload'])
        C['trailer_cap_kgpl'] = ann_capex(capt, tfn(tr['lifetime_yr']), r, fom_pct=np.full(3, tr['om_pct_capex_yr']))
    C['truck_t_fix'] = 1000 * tfn(tr['fix_eur_per_kg'])
    C['truck_t_100km'] = 1000 * tfn(tr['var_eur_per_kg_per_100km'])
    C['ptf_MWh'] = tfn(P['electricity_market']['ptf_eur_per_mwh'])
    return C


def band(h_utc, bf):
    h = (h_utc + 3) % 24          # Türkiye UTC+3
    if h >= 22 or h < 6:
        return bf['night']
    return bf['day'] if h < 17 else bf['peak']


# ---------------------------------------------------------------- model
def build(P, D, scenario, disruption=None):
    lam, gam = D['lam'], P['rpp']['gamma_opt']
    dpen = 1000.0 * P['rpp']['delta_pen_eur_per_kg']
    C = coefficients(P)
    E = {k: ((1 - lam) * v[0] + v[1] + lam * v[2]) / 2 for k, v in C.items()}
    sec = P['electrolyser']['sec_kwh_per_kg']
    e_pipe = tfn(P['compression']['pipeline_kwh_per_kg'])[1]
    e_truck = tfn(P['compression']['trailer_kwh_per_kg'])[1]
    e_cav = tfn(P['compression']['cavern_booster_kwh_per_kg'])[1]
    e_recomp = P['pipeline']['recompression_kwh_per_kg_per_1000km']
    pipe_cap = P['pipeline']['capacity_t_per_day']
    PT = ['L'] + (['S'] if P['pipeline'].get('small_diameter', False) and 'small' in P['pipeline'] else [])
    cap_pt = {'L': pipe_cap, 'S': P['pipeline'].get('small', {}).get('capacity_t_per_day', 0.0)}
    trP = P['trailer']
    fleet = bool(trP.get('fleet_correction', False))
    refill = bool(trP.get('cavern_refill_compression', False))
    mandate = bool(P['rpp'].get('import_mandate', True))

    def extra_trailer_years(Lkm):
        # (1/n(L) − 1/n_ref) yük-kapasitesi·yıl / kg teslim; n(L) = min(n_ref, H / (2L/v + t_lu))
        if not fleet:
            return 0.0
        n_ref = trP['trips_ref_yr']
        n = min(n_ref, trP['hours_available_yr'] / (2 * Lkm / trP['speed_kmh'] + trP['load_unload_h']))
        return max(0.0, 1.0 / n - 1.0 / n_ref)
    cav = P['cavern']
    Vmax, inj_max, wd_max = tfn(cav['working_gas_max_t'])[0], tfn(cav['injection_t_per_day'])[0], tfn(cav['withdrawal_t_per_day'])[0]
    bf = P['electricity_market']['band_factor']
    ratio = P['electricity_market']['export_cap_ratio']
    nday = P['demand']['days_per_year']
    H = range(24)
    I, J, G, A, L = D['I'], D['J'], D['G'], D['A'], D['L']
    g = G[0]
    M = pyo.ConcreteModel()
    M.I, M.J, M.A, M.D, M.H = pyo.Set(initialize=I), pyo.Set(initialize=J), pyo.Set(initialize=A, dimen=2), \
        pyo.Set(initialize=D['D']), pyo.Set(initialize=list(H))
    M.MODE = pyo.Set(initialize=['pipe', 'truck'])
    M.PT = pyo.Set(initialize=PT)
    M.S = pyo.Set(initialize=SEASONS)

    # kapasite değişkenleri
    M.W = pyo.Var(M.I, bounds=lambda m, i: (0, D['Wmax'][i]))
    M.PV = pyo.Var(M.I, bounds=lambda m, i: (0, D['Pmax'][i]))
    M.E = pyo.Var(M.I, within=pyo.NonNegativeReals)
    M.K = pyo.Var(M.I, within=pyo.NonNegativeReals)
    M.o = pyo.Var(M.I, within=pyo.Binary)
    M.y = pyo.Var(M.A, M.PT, within=pyo.Binary)            # boru hattı (çap türü)
    M.c_one_pt = pyo.Constraint(M.A, rule=lambda m, a0, a1: sum(m.y[(a0, a1), pt] for pt in m.PT) <= 1)
    M.Kg = pyo.Var(within=pyo.NonNegativeReals)              # MW, depoda römork dolum kompresörü
    M.imp = pyo.Var(M.J, within=pyo.NonNegativeReals)        # t/yıl, ithalat (yalnız import_mandate: false)
    M.V = pyo.Var(bounds=(0, Vmax))
    # işletme
    M.e = pyo.Var(M.I, M.D, M.H, within=pyo.NonNegativeReals)        # MW elektrolizör tüketimi
    M.x = pyo.Var(M.I, M.D, M.H, within=pyo.NonNegativeReals)        # MW satış
    M.cu = pyo.Var(M.I, M.D, M.H, within=pyo.NonNegativeReals)       # MW kısıntı
    M.im = pyo.Var(M.I, M.D, M.H, within=pyo.NonNegativeReals)       # MW şebeke çekişi (yalnız grid)
    M.f = pyo.Var(M.A, M.MODE, M.D, within=pyo.NonNegativeReals)     # t/gün
    M.inv = pyo.Var(M.S, bounds=(0, Vmax))
    M.yd = pyo.Var(M.J, within=pyo.NonNegativeReals)                  # t/yıl teslim
    M.alpha = pyo.Var(M.J, bounds=(lam, 1.0))
    M.shortfall = pyo.Var(M.J, within=pyo.NonNegativeReals)

    # Ortak arazi kullanımı: rüzgâr ve PV maskeleri örtüşür, bu yüzden iki teknolojinin ayak izi
    # toplamı birleşim alanını aşamaz. s[i] = aynı anda her iki teknolojiyi taşıyan alan;
    # üst sınırı, ölçülen örtüşmenin phi payı. phi=1 ve PV maskesi rüzgârın içindeyse kısıt
    # bağımsız Wmax/Pmax sınırlarına birebir indirgenir; phi=0 münhasır arazi demektir.
    densW = P['wind']['density_mw_per_km2']
    densP = P['pv']['density_mw_per_km2']
    phi = float(P['land'].get('co_use_share', 1.0))
    M.s = pyo.Var(M.I, within=pyo.NonNegativeReals)   # km², ortak kullanılan alan
    M.c_land_union = pyo.Constraint(M.I, rule=lambda m, i:
                                    m.W[i] / densW + m.PV[i] / densP - m.s[i] <= D['Aunion'][i])
    M.c_land_sw = pyo.Constraint(M.I, rule=lambda m, i: m.s[i] <= m.W[i] / densW)
    M.c_land_sp = pyo.Constraint(M.I, rule=lambda m, i: m.s[i] <= m.PV[i] / densP)
    M.c_land_cap = pyo.Constraint(M.I, rule=lambda m, i: m.s[i] <= phi * D['Acap'][i])

    # Büyük-M: elektrolizör, sahada kurulabilecek yenilenebilir kapasiteyi aşamaz (optimumu değiştirmez,
    # LP gevşetmesini sıkılaştırır)
    Emax = {i: D['Wmax'][i] + D['Pmax'][i] for i in I}
    M.c_open_hi = pyo.Constraint(M.I, rule=lambda m, i: m.E[i] <= Emax[i] * m.o[i])
    M.c_open_lo = pyo.Constraint(M.I, rule=lambda m, i: m.E[i] >= P['electrolyser']['min_size_mw_if_open'] * m.o[i])

    out_arcs = {i: [a for a in A if a[0] == i] for i in I}
    in_arcs = {j: [a for a in A if a[1] == j] for j in J}
    g_in, g_out = [a for a in A if a[1] == g], [a for a in A if a[0] == g]

    if disruption == 'cavern':
        for arc in g_in + g_out:
            for pt in PT:
                M.y[arc, pt].fix(0)
            for mode in ['pipe', 'truck']:
                for d in D['D']:
                    M.f[arc, mode, d].fix(0)
        M.V.fix(0)
        for season in SEASONS:
            M.inv[season].fix(0)
    elif disruption == 'pipeline':
        failed_arc = tuple(D.get('fail_arc') or ())
        if failed_arc not in A:
            raise ValueError(f'Pipeline disruption arc is absent from the network: {failed_arc}')
        for pt in PT:
            M.y[failed_arc, pt].fix(0)

    # Saatlik üretim, boru hattı ve römork akışlarına ayrılır; sıkıştırıcı elektrolizörle birlikte çalışır
    # (gün içi fark yerel tampon/römork stoğu ile karşılanır). Sıkıştırma yükü (MW) = t/saat × kWh/kg.
    M.pp = pyo.Var(M.I, M.D, M.H, within=pyo.NonNegativeReals)       # t/saat, boru hattına
    M.pt = pyo.Var(M.I, M.D, M.H, within=pyo.NonNegativeReals)       # t/saat, römorka
    M.c_split = pyo.Constraint(M.I, M.D, M.H, rule=lambda m, i, d, h: m.pp[i, d, h] + m.pt[i, d, h] == m.e[i, d, h] / sec)
    M.c_dpipe = pyo.Constraint(M.I, M.D, rule=lambda m, i, d:
                               sum(m.pp[i, d, h] for h in H) == sum(m.f[a, 'pipe', d] for a in out_arcs[i]))
    M.c_dtruck = pyo.Constraint(M.I, M.D, rule=lambda m, i, d:
                                sum(m.pt[i, d, h] for h in H) == sum(m.f[a, 'truck', d] for a in out_arcs[i]))

    def comp_load(m, i, d, h):    # MW
        return e_pipe * m.pp[i, d, h] + e_truck * m.pt[i, d, h]

    def elec_bal(m, i, d, h):
        gen = D['cfw'][(i, d, h)] * m.W[i] + D['cfp'][(i, d, h)] * m.PV[i] + m.im[i, d, h]
        return gen == m.e[i, d, h] + m.x[i, d, h] + m.cu[i, d, h] + comp_load(m, i, d, h)
    M.c_elec = pyo.Constraint(M.I, M.D, M.H, rule=elec_bal)
    M.c_ely = pyo.Constraint(M.I, M.D, M.H, rule=lambda m, i, d, h: m.e[i, d, h] <= m.E[i])
    M.c_exp = pyo.Constraint(M.I, M.D, M.H, rule=lambda m, i, d, h: m.x[i, d, h] <= ratio * m.E[i])
    M.c_comp = pyo.Constraint(M.I, M.D, M.H, rule=lambda m, i, d, h: comp_load(m, i, d, h) <= m.K[i])
    if scenario == 'island':
        for v in M.x.values():
            v.fix(0)
    if scenario != 'grid':
        for v in M.im.values():
            v.fix(0)
    else:   # yıllık eşleşme: çekilen enerji <= satılan enerji
        M.c_match = pyo.Constraint(expr=sum(D['wd'][d] * (M.im[i, d, h] - M.x[i, d, h]) for i in I for d in D['D'] for h in H) <= 0)

    # H2 dengeleri (günlük): c_split + c_dpipe + c_dtruck üretimi çıkış akışlarına bağlar
    M.c_dem = pyo.Constraint(M.J, M.D, rule=lambda m, j, d:
                             sum(m.f[a, md, d] for a in in_arcs[j] for md in m.MODE) == m.yd[j] / nday)
    M.c_pipe = pyo.Constraint(M.A, M.D, rule=lambda m, a0, a1, d:
                              m.f[(a0, a1), 'pipe', d] <= sum(cap_pt[pt] * m.y[(a0, a1), pt] for pt in PT))
    # Depodan çıkan römorklar 500 bara yeniden doldurulur (V4): kompresör gücü günlük ortalama yükü karşılar
    if refill:
        M.c_kg = pyo.Constraint(M.D, rule=lambda m, d: m.Kg >= e_truck * sum(m.f[a, 'truck', d] for a in g_out) / 24)
    else:
        M.Kg.fix(0)
    M.c_inj = pyo.Constraint(M.D, rule=lambda m, d: sum(m.f[a, md, d] for a in g_in for md in m.MODE) <= inj_max)
    M.c_wdr = pyo.Constraint(M.D, rule=lambda m, d: sum(m.f[a, md, d] for a in g_out for md in m.MODE) <= wd_max)

    def inv_rule(m, s):
        nxt = SEASONS[(SEASONS.index(s) + 1) % 4]
        net = sum(D['wd'][d] * (sum(m.f[a, md, d] for a in g_in for md in m.MODE)
                                - sum(m.f[a, md, d] for a in g_out for md in m.MODE))
                  for d in D['D'] if D['season_of'][d] == s)
        return m.inv[nxt] == m.inv[s] + net
    M.c_inv = pyo.Constraint(M.S, rule=inv_rule)
    M.c_invV = pyo.Constraint(M.S, rule=lambda m, s: m.inv[s] <= m.V)

    # Me talep kısıtı (α_j >= λ dalı)
    dd = D['d_t']
    M.c_me = pyo.Constraint(M.J, rule=lambda m, j: m.yd[j] + m.imp[j] >= dd[j][1] + (m.alpha[j] - lam) / (1 - lam) * (dd[j][2] - dd[j][1]))
    if mandate:
        for j in J:
            M.imp[j].fix(0)
    if disruption != 'none':
        M.c_me.deactivate()
        M.c_disruption_demand = pyo.Constraint(M.J, rule=lambda m, j: m.yd[j] + m.shortfall[j] == dd[j][1])
        for j in J:
            M.imp[j].fix(0)
        for j in J:
            M.alpha[j].fix(lam)
    else:
        for j in J:
            M.shortfall[j].fix(0)

    # ------------------------------------------------ maliyet ifadeleri (üçgen köşe k = 0,1,2 ve E_Me)
    # Tüm miktarlar {değişken: katsayı} sözlükleri olarak kurulur ve tek düz doğrusal ifadeye çevrilir.
    # İç içe çarpım-toplam ifadeleri Pyomo'nun çözücüye aktarımını dakikalarca yavaşlatıyordu.
    from pyomo.common.collections import ComponentMap as CM

    def add(dst, src, k=1.0):
        for var, c in (src.items() if hasattr(src, 'items') else src):
            dst[var] = dst.get(var, 0.0) + k * c
        return dst

    def lin(d):
        it = d.items() if hasattr(d, 'items') else d
        return pyo.quicksum(c * var for var, c in it if c != 0.0)

    Dd, wd = D['D'], D['wd']
    q = {k: CM() for k in ['wind_MW', 'pv_MW', 'ely_MW', 'stack_MWh', 'water_t', 'comp_MW', 'pipe_km', 'pipe_km_S',
                         'truck_t_fix', 'truck_t_100km', 'trailer_cap_kgpl', 'cavern_t', 'ptf_MWh_cost', 'ptf_MWh_rev']}
    H2d = {i: CM() for i in I}
    for i in I:
        q['wind_MW'][M.W[i]] = 1.0; q['pv_MW'][M.PV[i]] = 1.0
        q['ely_MW'][M.E[i]] = 1.0; q['comp_MW'][M.K[i]] = 1.0
        for d in Dd:
            for h in H:
                q['stack_MWh'][M.e[i, d, h]] = wd[d]
                H2d[i][M.e[i, d, h]] = wd[d] / sec
                q['ptf_MWh_rev'][M.x[i, d, h]] = wd[d] * band(h, bf)
                q['ptf_MWh_cost'][M.im[i, d, h]] = wd[d] * band(h, bf)
    for i in I:
        add(q['water_t'], H2d[i])
    q['comp_MW'][M.Kg] = 1.0
    for a in A:
        q['pipe_km'][M.y[a, 'L']] = D['Lpipe'][a]
        if 'S' in PT:
            q['pipe_km_S'][M.y[a, 'S']] = D['Lpipe'][a]
        xt = extra_trailer_years(L[a])
        for d in Dd:
            q['truck_t_fix'][M.f[a, 'truck', d]] = wd[d]
            q['truck_t_100km'][M.f[a, 'truck', d]] = wd[d] * L[a] / 100
            if xt > 0:
                q['trailer_cap_kgpl'][M.f[a, 'truck', d]] = wd[d] * 1000 * xt     # kg-yük·yıl
            if refill and a in g_out:
                add(q['ptf_MWh_cost'], [(M.f[a, 'truck', d], wd[d] * e_truck)])      # MWh (t·kWh/kg)
            add(q['ptf_MWh_cost'], [(M.f[a, 'pipe', d], wd[d] * e_recomp * D['Lpipe'][a] / 1000)])   # MWh (t·kWh/kg)
            if a in g_in:
                add(q['ptf_MWh_cost'], [(M.f[a, md, d], wd[d] * e_cav) for md in ['pipe', 'truck']])
    q['cavern_t'][M.V] = 1.0
    flow_yr = {(a, md): [(M.f[a, md, d], wd[d]) for d in Dd] for a in A for md in ['pipe', 'truck']}

    part_of = {'wind': ['wind_MW'], 'pv': ['pv_MW'], 'electrolyser': ['ely_MW'], 'stack': ['stack_MWh'],
               'water': ['water_t'], 'compressor': ['comp_MW'], 'pipeline': ['pipe_km'],
               'truck': ['truck_t_fix', 'truck_t_100km', 'trailer_cap_kgpl'], 'cavern': ['cavern_t'],
               'grid_energy': ['ptf_MWh_cost']}
    if 'S' in PT:
        part_of['pipeline'] = ['pipe_km', 'pipe_km_S']
    for k in ('pipe_km_S', 'trailer_cap_kgpl'):        # katsayısı tanımsız olan miktarlar maliyete girmez
        if k not in C:
            C[k] = np.zeros(3)

    def zdict(c, ptf_rev):
        """Toplam maliyet sözlüğü; c = birim maliyet köşesi, ptf_rev = satış geliri fiyatı."""
        z = CM()
        for keys in part_of.values():
            for k in keys:
                add(z, q[k], c['ptf_MWh'] if k == 'ptf_MWh_cost' else c[k])
        return add(z, q['ptf_MWh_rev'], -ptf_rev)

    E = {k: ((1 - lam) * v[0] + v[1] + lam * v[2]) / 2 for k, v in C.items()}
    vert = [{k: v[n] for k, v in C.items()} for n in range(3)]
    zE_d = zdict(E, E['ptf_MWh'])
    zhi_d = zdict(vert[2], C['ptf_MWh'][0])     # z_max: maliyetler yüksek, satış düşük fiyatla
    zlo_d = zdict(vert[0], C['ptf_MWh'][2])     # z_min: tersi
    f1_d = add(add(add(CM(), zE_d), zhi_d, gam), zlo_d, -gam)
    # Ceza katsayısı düğüm başına Σ_m δ_m (d3_m − d2_m) (V4: sektöre göre ithalat paritesi); v3'te tek δ
    pw = {j: (1000.0 * D['pen_w'][j] if P['rpp'].get('delta_by_sector', False) else dpen * (dd[j][2] - dd[j][1])) for j in J}
    pen_const = sum(pw[j] / (1 - lam) for j in J)
    for j in J:
        add(f1_d, [(M.alpha[j], -pw[j] / (1 - lam))])
    imp_cost = {j: 1000.0 * D['delta_node'][j] for j in J}
    f2_d = CM()
    for i in I:
        add(f2_d, H2d[i], D['Q'][i])

    M.zE = pyo.Expression(expr=lin(zE_d))
    M.zmax = pyo.Expression(expr=lin(zhi_d))
    M.zmin = pyo.Expression(expr=lin(zlo_d))
    M.pen = pyo.Expression(expr=pen_const - pyo.quicksum(pw[j] / (1 - lam) * M.alpha[j] for j in J))
    M.import_cost = pyo.Expression(expr=pyo.quicksum(imp_cost[j] * M.imp[j] for j in J))
    M.f1 = pyo.Expression(expr=lin(f1_d) + pen_const + M.import_cost
                          + pyo.quicksum(imp_cost[j] * M.shortfall[j] for j in J))
    M.H2 = pyo.Expression(I, initialize={i: lin(H2d[i]) for i in I})
    M.f2 = pyo.Expression(expr=lin(f2_d))
    M.parts = {name: sum(lin(q[k]) * (E['ptf_MWh'] if k == 'ptf_MWh_cost' else E[k]) for k in keys)
               for name, keys in part_of.items()}
    M.parts['export_revenue'] = -E['ptf_MWh'] * lin(q['ptf_MWh_rev'])
    # Maliyet = katsayı × miktar; Monte Carlo (Aşama IV) bu miktarları sabit tasarım için kullanır
    M.qty = {k: lin(d) for k, d in q.items()}
    flow_yr = {key: lin(d) for key, d in flow_yr.items()}
    M.flow_yr = flow_yr
    M._PT = PT
    return M


def solve(M, time_limit=600, gap=1e-3):
    opt = pyo.SolverFactory('appsi_highs')
    opt.config.time_limit = time_limit
    opt.config.mip_gap = gap
    opt.config.stream_solver = bool(__import__("os").environ.get("RPP_STREAM"))
    # Süre sınırı doğrudan HiGHS seçeneği olarak verilir (appsi config.time_limit HiGHS'a ulaşmıyordu).
    # Not: user_objective_scale denendi; appsi üzerinden erken ve yanlış "optimal" sonlanmaya yol açtı.
    opt.highs_options = {'time_limit': float(time_limit), 'mip_rel_gap': gap}
    t0 = time.time()
    res = opt.solve(M, load_solutions=False)
    tc = res.solver.termination_condition
    ok = tc == pyo.TerminationCondition.optimal or (tc == pyo.TerminationCondition.maxTimeLimit and len(res.solution) > 0)
    if ok:
        M.solutions.load_from(res)
        lb, ub = res.problem.lower_bound, res.problem.upper_bound
        try:
            M._gap = abs(ub - lb) / max(abs(ub), 1e-9)
        except TypeError:
            M._gap = float('nan')
        M._status = str(tc)
    else:
        print('Çözücü durumu:', tc, flush=True)
    return ok, res, time.time() - t0


def report(M, D):
    v = pyo.value
    sec = D['sec']
    I, J = D['I'], D['J']
    tot_del = sum(v(M.yd[j]) for j in J)
    H = {i: v(M.H2[i]) for i in I}
    row = {'f1': v(M.f1), 'f2': v(M.f2), 'E_z': v(M.zE), 'z_max': v(M.zmax), 'z_min': v(M.zmin), 'penalty': v(M.pen),
           'disruption_shortfall_t': sum(v(M.shortfall[j]) for j in J),
           'delivered_t': tot_del, 'produced_t': sum(H.values()),
           'Q_bar': v(M.f2) / max(sum(H.values()), 1e-9),
           'LCOH_E_eur_kg': v(M.zE) / max(tot_del, 1e-9) / 1000,
           'cavern_t': v(M.V), 'open_sites': ','.join(i for i in I if v(M.o[i]) > 0.5),
           'pipelines': ','.join(f'{a[0]}>{a[1]}' + ('' if pt == 'L' else '[12in]')
                                 for a in D['A'] for pt in M._PT if v(M.y[a, pt]) > 0.5),
           'import_t': sum(v(M.imp[j]) for j in J), 'import_cost_MEUR': v(M.import_cost) / 1e6,
           'cavern_refill_MW': v(M.Kg),
           'demand_mode_t': sum(D['d_t'][j][1] for j in J),
           'demand_me_expected_t': sum(((1 - D['lam']) * D['d_t'][j][0] + D['d_t'][j][1] + D['lam'] * D['d_t'][j][2]) / 2
                                       for j in J)}
    for k, e in M.parts.items():
        row[f'cost_{k}_MEUR'] = v(e) / 1e6
    for i in I:
        row[f'{i}_W_MW'], row[f'{i}_PV_MW'], row[f'{i}_E_MW'], row[f'{i}_H2_t'] = v(M.W[i]), v(M.PV[i]), v(M.E[i]), H[i]
        row[f'{i}_FLH_h'] = H[i] * sec / max(v(M.E[i]), 1e-9) if v(M.E[i]) > 1e-6 else 0.0
    for j in J:
        row[f'alpha_{j}'] = v(M.alpha[j])
        row[f'y_{j}_t'] = v(M.yd[j])
        row[f'imp_{j}_t'] = v(M.imp[j])
    for k, e in M.qty.items():
        row[f'q_{k}'] = v(e)
    row['mip_gap'] = getattr(M, '_gap', float('nan'))
    row['solver_status'] = getattr(M, '_status', '')
    return row


def flows_table(M, D):
    v = pyo.value
    rows = []
    for (a, md), e in M.flow_yr.items():
        t = v(e)
        if t > 1e-3:
            ptype = ','.join(pt for pt in M._PT if pyo.value(M.y[a, pt]) > 0.5) if md == 'pipe' else ''
            rows.append({'origin': a[0], 'destination': a[1], 'mode': md, 'pipe_type': ptype, 'road_km': D['L'][a],
                         'pipeline_km': D['Lpipe'][a], 't_per_yr': t})
    return pd.DataFrame(rows)


def augmecon2(M, D, npts, tl, out):
    """İki amaç: f1 (en küçük) ve üretimle ağırlıklı ortalama uygunluk Q̄ = Σ Q_i H_i / Σ H_i (en büyük).
    Q̄ oranlı bir amaçtır; ε-kısıtı doğrusal biçimde yazılır: Σ_i (Q_i − ε) H_i − S = 0, S >= 0
    (AUGMECON2'deki artırma terimi S ile; Mavrotas & Florios 2013).
    1) min f1 -> Q̄_0;  2) ulaşılabilir en yüksek Q̄, ε üzerinde ikiye bölmeyle bulunur (her uygun çözüm bir
    Pareto noktasıdır);  3) [Q̄_0, Q̄_max] aralığı npts eşit adımla taranır.
    Her nokta bulunduğu anda diske yazılır; süreç kesilirse kaldığı yerden devam eder."""
    v = pyo.value
    f_par, f_flw, f_st = out / 'pareto.csv', out / 'pareto_flows.csv', out / 'pareto_state.json'
    log = lambda msg: print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)
    st = json.loads(f_st.read_text(encoding='utf-8')) if f_st.exists() else {'done_eps': []}
    Q = D['Q']
    Hsum = sum(M.H2[i] for i in D['I'])
    M.S2 = pyo.Var(within=pyo.NonNegativeReals)
    M.e2 = pyo.Param(mutable=True, initialize=0.0)
    M.c_eps = pyo.Constraint(expr=sum((Q[i] - M.e2) * M.H2[i] for i in D['I']) - M.S2 == 0)
    M.c_eps.deactivate()

    def record(tag):
        row = report(M, D); row.update({'step': tag, 'eps_Qbar': v(M.e2) if M.c_eps.active else float('nan')})
        pd.DataFrame([row]).to_csv(f_par, mode='a', header=not f_par.exists(), index=False)
        flows_table(M, D).assign(step=tag).to_csv(f_flw, mode='a', header=not f_flw.exists(), index=False)
        return row

    def save():
        f_st.write_text(json.dumps(st, indent=2), encoding='utf-8')

    # 1) f1 en küçük
    if 'Q0' not in st:
        M.obj = pyo.Objective(expr=M.f1, sense=pyo.minimize)
        ok, _, t = solve(M, tl); assert ok, 'f1 çözülemedi'
        row = record('f1_min'); st.update({'f1_min': row['f1'], 'Q0': row['Q_bar']}); save()
        log(f'f1_min = {row["f1"]:.4e}, Q̄_0 = {row["Q_bar"]:.4f} ({t:.0f} s)')
        M.obj.deactivate()
    # V4: S'nin ölçeği ikinci amacın aralığıdır, (max Q − min Q) × mod talep (t/yıl). v3'teki 1e5 t ölçeği
    # artırma terimini MIP boşluğunun altına düşürüyordu (hakem R1-M5).
    Hnorm = max((max(Q.values()) - min(Q.values())) * sum(D['d_t'][j][1] for j in D['J']), 1.0)
    st['Hnorm_t'] = Hnorm
    M.obj_aug = pyo.Objective(expr=M.f1 - 1e-3 * abs(st['f1_min']) * M.S2 / Hnorm, sense=pyo.minimize)
    M.c_eps.activate()

    def run_eps(e, tag):
        M.e2 = e
        ok, _, t = solve(M, tl)
        if ok:
            row = record(tag)
            log(f'{tag}: ε = {e:.4f} -> f1 = {row["f1"]:.4e}, Q̄ = {row["Q_bar"]:.4f}, siteler {row["open_sites"]} ({t:.0f} s)')
        else:
            log(f'{tag}: ε = {e:.4f} -> uygun çözüm yok ({t:.0f} s)')
        st['done_eps'].append([tag, e, bool(ok)]); save()
        return ok

    # 2) ulaşılabilir en yüksek Q̄: ikiye bölme
    if 'Qmax' not in st:
        lo, hi = st.get('bis_lo', st['Q0']), st.get('bis_hi', max(Q.values()))
        for it in range(st.get('bis_it', 0), 6):
            mid = 0.5 * (lo + hi)
            if run_eps(mid, f'bisect{it}'):
                lo = mid
            else:
                hi = mid
            st.update({'bis_lo': lo, 'bis_hi': hi, 'bis_it': it + 1}); save()
        st['Qmax'] = lo; save()
        log(f'ulaşılabilir en yüksek Q̄ ≈ {lo:.4f} (üst sınır {hi:.4f})')

    # 3) eşit adımlı tarama
    for k in range(st.get('grid_k', 1), npts + 1):
        e = st['Q0'] + k * (st['Qmax'] - st['Q0']) / npts
        run_eps(e, f'grid{k}')
        st['grid_k'] = k + 1; save()
    payoff = {k: st[k] for k in ('f1_min', 'Q0', 'Qmax')}
    return payoff, pd.read_csv(f_par)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', default='base', choices=['base', 'island', 'grid'])
    ap.add_argument('--disruption', default='none', choices=['none', 'cavern', 'pipeline'],
                    help='full-year cavern closure or loss of the S5-to-Gemlik pipeline asset')
    ap.add_argument('--pipeline-distance-rule', choices=['road_proxy', 'geodesic_cap'], default=None,
                    help='override the pipeline route-length assumption for sensitivity analysis')
    ap.add_argument('--pipeline-distance-tau', type=float, default=None,
                    help='geodesic multiplier used by geodesic_cap; defaults to params.yaml')
    ap.add_argument('--set', action='append', default=[], help='KEY=JSON, ör. rpp.gamma_opt=0.5')
    default_q = STAGE2 / 'stage2_scores.csv' if (STAGE2 / 'stage2_scores.csv').exists() else STAGE2 / 'stage2_scores_provisional.csv'
    ap.add_argument('--q', default=str(default_q), help='Aşama II skorları (Q01)')
    ap.add_argument('--single', action='store_true', help='yalnız f1 minimumu (Pareto yok)')
    ap.add_argument('--eps-qbar', type=float, default=None,
                    help='tek ε-kısıtlı çözüm: Q̄ >= ε altında f1 (AUGMECON2 artırmalı); Pareto noktasını yeniden çözmek için')
    ap.add_argument('--f1-ref', type=float, default=None, help='artırma teriminin ölçeği (Pareto f1_min)')
    ap.add_argument('--deterministic', action='store_true',
                    help='tüm üçgen sayılar mod değerine indirgenir, γ = 0 (karşılaştırma tasarımı)')
    ap.add_argument('--fail-arc', default=None, help='kesinti testi için boru hattı yayı, ör. S5>TR_NH3_GEMLIK')
    ap.add_argument('--sites', default=None, help='yalnız bu adaylar (virgülle), sıralı karşı-olgusal tasarım için')
    ap.add_argument('--tag', default=None)
    ap.add_argument('--time-limit', type=float, default=1800)
    a = ap.parse_args()

    P = yaml.safe_load(P_YAML.read_text(encoding='utf-8'))
    for kv in a.set:
        k, val = kv.split('=', 1)
        set_nested(P, k, json.loads(val))
    if a.pipeline_distance_rule is not None:
        P['pipeline']['route_rule'] = a.pipeline_distance_rule
    if a.pipeline_distance_tau is not None:
        P['pipeline']['distance_tau'] = a.pipeline_distance_tau
    if a.deterministic:
        collapse_to_mode(P)
    D = load_data(P, a.q)
    D['sec'] = P['electrolyser']['sec_kwh_per_kg']
    D['fail_arc'] = tuple(a.fail_arc.split('>')) if a.fail_arc else None
    tag = a.tag or (a.scenario + ('_det' if a.deterministic else '')
                    + (f'_outage_{a.disruption}' if a.disruption != 'none' else '')
                    + (f'_pipe_{a.pipeline_distance_rule}' if a.pipeline_distance_rule else '')
                    + ('_' + '_'.join(s.replace('=', '-').replace('.', '-') for s in a.set) if a.set else ''))
    out = ROOT / 'data/processed/stage3' / tag
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    M = build(P, D, a.scenario, a.disruption)
    if a.sites:
        keep = set(a.sites.split(','))
        for i in D['I']:
            if i not in keep:
                M.o[i].fix(0); M.W[i].fix(0); M.PV[i].fix(0); M.K[i].fix(0)
    print(f'Model: {M.nvariables()} değişken, {M.nconstraints()} kısıt ({time.time() - t0:.1f} s)')
    if a.eps_qbar is not None:
        Q = D['Q']
        M.S2 = pyo.Var(within=pyo.NonNegativeReals)
        M.c_eps = pyo.Constraint(expr=sum((Q[i] - a.eps_qbar) * M.H2[i] for i in D['I']) - M.S2 == 0)
        Hn = max((max(Q.values()) - min(Q.values())) * sum(D['d_t'][j][1] for j in D['J']), 1.0)
        M.obj = pyo.Objective(expr=M.f1 - 1e-3 * abs(a.f1_ref or 2.5e9) * M.S2 / Hn, sense=pyo.minimize)
        ok, res, t = solve(M, a.time_limit)
        assert ok, 'çözüm yok'
        row = report(M, D); row.update({'solve_s': round(t, 1), 'eps_Qbar': a.eps_qbar})
        pd.DataFrame([row]).to_csv(out / 'solution.csv', index=False)
        flows_table(M, D).to_csv(out / 'flows.csv', index=False)
        payoff, pts = None, [(row, None)]
    elif a.single:
        if a.disruption != 'none':
            M.obj = pyo.Objective(expr=sum(M.yd[j] for j in D['J']), sense=pyo.maximize)
            ok, _, t_max = solve(M, a.time_limit)
            assert ok, 'kesinti altında azami teslimat çözülemedi'
            max_delivered = sum(pyo.value(M.yd[j]) for j in D['J'])
            M.c_max_delivery = pyo.Constraint(expr=sum(M.yd[j] for j in D['J']) >= max_delivered - 0.1)
            M.obj.deactivate()
            M.obj_cost = pyo.Objective(expr=M.f1, sense=pyo.minimize)
            ok, res, t_cost = solve(M, a.time_limit)
            assert ok, 'azami teslimat korunurken en düşük maliyet çözülemedi'
            row = report(M, D)
            row['max_deliverable_t'] = max_delivered
            row['max_delivery_solve_s'] = round(t_max, 1)
            t = t_max + t_cost
        else:
            M.obj = pyo.Objective(expr=M.f1, sense=pyo.minimize)
            ok, res, t = solve(M, a.time_limit)
            assert ok, 'çözüm yok'
            row = report(M, D)
        row['solve_s'] = round(t, 1)
        pd.DataFrame([row]).to_csv(out / 'solution.csv', index=False)
        flows_table(M, D).to_csv(out / 'flows.csv', index=False)
        payoff, pts = None, [(row, None)]
    else:
        payoff, par = augmecon2(M, D, P['rpp']['pareto_points'], a.time_limit, out)
        pts = [(r, None) for r in par.to_dict('records')]

    C = coefficients(P)
    man = {'run_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'scenario': a.scenario,
           'overrides': a.set, 'disruption': a.disruption, 'payoff': payoff,
           'demand_tfn_t': {j: list(map(float, v)) for j, v in D['d_t'].items()},
           'coefficients_tfn': {k: list(map(float, v)) for k, v in C.items()},
           'Q': D['Q'], 'Wmax_MW': D['Wmax'], 'Pmax_MW': D['Pmax'],
           'land_co_use_share': float(P['land'].get('co_use_share', 1.0)),
           'land_overlap_km2': D['Acap'], 'land_union_km2': D['Aunion'],
           'land_overlap_measured': D['overlap_measured'],
           'pipeline_route_rule': P['pipeline'].get('route_rule', 'road_proxy'),
           'demand_nodes_members': D['members'], 'delta_node_eur_per_kg': D['delta_node'],
           'sites_restricted_to': a.sites, 'fail_arc': a.fail_arc,
           'pipeline_distance_tau': P['pipeline'].get('distance_tau', None),
           'inputs_sha256': {p.name: sha(p) for p in [P_YAML, F_SITES, F_DEMAND, F_DIST, F_DIST_ST, F_STORE, F_PROF, Path(a.q)]},
           'solver': 'HiGHS via pyomo appsi', 'pyomo': __import__('pyomo').version.version, 'highspy': __import__('highspy').__version__ if hasattr(__import__('highspy'), '__version__') else 'n/a'}
    (out / 'manifest.json').write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding='utf-8')
    show = ['step', 'grid_k', 'f1', 'f2', 'Q_bar', 'LCOH_E_eur_kg', 'delivered_t', 'cavern_t', 'open_sites', 'pipelines']
    print(pd.DataFrame([p[0] for p in pts])[[c for c in show if c in pts[0][0]]].round(3).to_string(index=False))
    print(f'Toplam süre {time.time() - t0:.0f} s -> {out}')


if __name__ == '__main__':
    main()
