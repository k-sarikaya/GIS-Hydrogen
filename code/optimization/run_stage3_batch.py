"""
Aşama III senaryo grubu (V4): temel çözüm, duyarlılıklar, ayrıştırma (ablation), karşı-olgusal ve kesinti testleri.
Her çözüm data/processed/stage3/<etiket>/ altına yazılır (rpp_model.py). En çok N_PAR süreç paralel çalışır.
Pareto cephesi ayrı çalıştırılır:  python code/optimization/rpp_model.py --scenario base --tag base_pareto

Kullanım:  python code/optimization/run_stage3_batch.py [--only etiket1,etiket2] [--group main|ablation|all]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'code/optimization/rpp_model.py'
N_PAR = int(os.environ.get('N_PAR', 2))


def dsec(x):
    return ['--set', 'rpp.delta_eur_per_kg_by_sector=' + json.dumps({'ammonia': x, 'refinery': x})]


V3_OFF = ['--set', 'demand.sector_basis=false', '--set', 'demand.merge_nodes=false', '--set', 'pipeline.small_diameter=false',
          '--set', 'trailer.fleet_correction=false', '--set', 'trailer.cavern_refill_compression=false',
          '--set', 'rpp.delta_by_sector=false']

MAIN = {
    'base':          ['--single'],
    'deterministic': ['--single', '--deterministic'],
    'island':        ['--scenario', 'island', '--single'],
    'grid':          ['--scenario', 'grid', '--single', '--time-limit', '7200'],
    'sec48':         ['--single', '--set', 'electrolyser.sec_kwh_per_kg=48'],
    'sec57_5':       ['--single', '--set', 'electrolyser.sec_kwh_per_kg=57.5'],
    'land_cluster':  ['--single', '--set', 'land.area_basis="cluster"'],
    'phi0_5':        ['--single', '--set', 'land.co_use_share=0.5'],
    'phi0_0':        ['--single', '--set', 'land.co_use_share=0.0'],
    'gamma0':        ['--single', '--set', 'rpp.gamma_opt=0'],
    'gamma0_25':     ['--single', '--set', 'rpp.gamma_opt=0.25'],
    'gamma0_5':      ['--single', '--set', 'rpp.gamma_opt=0.5'],
    'lambda0_25':    ['--single', '--set', 'rpp.lambda_me=0.25'],
    'lambda0_75':    ['--single', '--set', 'rpp.lambda_me=0.75'],
    'delta10':       ['--single', *dsec(10)],
    'delta12_5':     ['--single', *dsec(12.5)],
    'delta15':       ['--single', *dsec(15)],
    'delta20':       ['--single', *dsec(20)],
    'import_free':   ['--single', '--set', 'rpp.import_mandate=false'],
    'import_free_d10': ['--single', '--set', 'rpp.import_mandate=false', *dsec(10)],
    'import_free_d12_5': ['--single', '--set', 'rpp.import_mandate=false', *dsec(12.5)],
    'import_free_d15': ['--single', '--set', 'rpp.import_mandate=false', *dsec(15)],
    'trailer_h4400': ['--single', '--set', 'trailer.hours_available_yr=4400'],
    'trailer_h8000': ['--single', '--set', 'trailer.hours_available_yr=8000'],
    'pipe_geo_cap':  ['--single', '--pipeline-distance-rule', 'geodesic_cap', '--pipeline-distance-tau', '1.2'],
    # 12" sınıfı kontrolleri (N12): DEA 2025 hız sınırlı kapasite; DEA datasheet 12" maliyet üçgeni + 40 barg kapasitesi;
    # DEA not G'deki %35 ek maliyetin (inşaat yönetimi, sahip maliyetleri) her iki çapa eklenmesi
    'pipe12_cap311': ['--single', '--set', 'pipeline.small.capacity_t_per_day=311'],
    'pipe12_dea':    ['--single', '--set', 'pipeline.small.capex_meur_per_km={"tfn":[0.798,1.14,1.71],"src":"DEA 2025 sheet 4.1"}',
                      '--set', 'pipeline.small.capacity_t_per_day=432'],
    'pipe_capex135': ['--single', '--set', 'pipeline.capex_meur_per_km={"tfn":[1.89,2.025,2.43],"src":"6.1 x1.35"}',
                      '--set', 'pipeline.small.capex_meur_per_km={"tfn":[1.411,1.512,1.814],"src":"6.1s x1.35"}'],
    'demand_upper':  ['--single', '--set', 'demand.sector_basis=false'],
    'outage_cavern': ['--single', '--disruption', 'cavern'],
    'outage_pipeline': ['--single', '--disruption', 'pipeline', '--fail-arc', 'TR_UGS_TUZGOLU>TR_HUB_KORFEZ'],
    'cf_top3_det':   ['--single', '--deterministic', '--sites', 'S5,S4,S2'],
    'cf_top3_rpp':   ['--single', '--sites', 'S5,S4,S2'],
}
# Ayrıştırma: v3 kurgusundan V4'e adım adım (her adım bir öncekine bir değişiklik ekler)
ABLATION = {
    'abl0_v3equiv':  ['--single', *V3_OFF],
    'abl1_demand':   ['--single', *[x for x in V3_OFF if x not in ('demand.sector_basis=false', 'rpp.delta_by_sector=false')]],
    'abl2_merge':    ['--single', '--set', 'pipeline.small_diameter=false', '--set', 'trailer.fleet_correction=false',
                      '--set', 'trailer.cavern_refill_compression=false'],
    'abl3_small':    ['--single', '--set', 'trailer.fleet_correction=false', '--set', 'trailer.cavern_refill_compression=false'],
}
RUNS = {**MAIN, **ABLATION}


def clean(args):
    """V3_OFF süzülürken artakalan tekil '--set' bayraklarını ayıklar."""
    out = []
    for x in args:
        if out and out[-1] == '--set' and x == '--set':
            continue
        out.append(x)
    return [x for k, x in enumerate(out) if not (x == '--set' and (k + 1 == len(out) or out[k + 1].startswith('--')))]


def run(tag):
    log = ROOT / 'data/processed/stage3' / f'{tag}.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(log, 'w', encoding='utf-8') as fh:
        rc = subprocess.call([sys.executable, str(MODEL), *clean(RUNS[tag]), '--tag', tag], stdout=fh, stderr=subprocess.STDOUT,
                             cwd=ROOT, env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1'})
    print(f'{tag:16s} rc={rc} {time.time() - t0:6.0f} s', flush=True)
    return tag, rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None)
    ap.add_argument('--group', default='all', choices=['main', 'ablation', 'all'])
    a = ap.parse_args()
    pool = {'main': MAIN, 'ablation': ABLATION, 'all': RUNS}[a.group]
    tags = a.only.split(',') if a.only else list(pool)
    with ThreadPoolExecutor(N_PAR) as ex:
        res = list(ex.map(run, tags))
    bad = [t for t, rc in res if rc != 0]
    print('başarısız:', bad if bad else 'yok')


if __name__ == '__main__':
    main()
