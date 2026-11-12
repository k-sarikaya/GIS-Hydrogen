"""Regenerates the deterministic parts of the pipeline and compares them with the stored results.

Checks: (1) Stage I selection step from the frozen feature table, (2) Stage II scores from the survey export,
(3) the baseline Stage III solution (a MIP, so compared with a relative tolerance, not bit-exactly).
Usage: python code/tools/verify_reproduction.py [--skip-stage3]  (survey export must be present for check 2)
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / 'data/raw/gis/real'
STAGE2 = ROOT / 'data/processed/stage2'
S3 = ROOT / 'data/processed/stage3'
sys.path.insert(0, str(ROOT / 'code/mcdm'))


def run(cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def check_stage1():
    out = Path(tempfile.mkdtemp(prefix='gh2_stage1_'))
    run([sys.executable, 'code/gis/gis_pipeline_real.py', '--from-features',
         str(REAL / 'grid_cells_features.csv'), '--out', str(out)])
    stored = json.loads((REAL / 'gis_summary.json').read_text(encoding='utf-8'))['output_sha256']
    fresh = json.loads((out / 'gis_summary.json').read_text(encoding='utf-8'))['output_sha256']
    same = {name: stored[name] == fresh[name] for name in stored}
    cand_a = pd.read_csv(REAL / 'candidate_sites.csv')
    cand_b = pd.read_csv(out / 'candidate_sites.csv')
    # Yeni tanisal sutunlar (ornegin wind_pv_overlap_km2) eklendiginde dosya sağlaması
    # degisir ama RAPORLANAN sonuclar degismemelidir. Bu yuzden iki karsilastirma yapilir:
    # (a) ortak sutunlarda birebir esitlik, (b) sonradan eklenen sutunlarin listesi.
    shared = [c for c in cand_a.columns if c in cand_b.columns]
    added = [c for c in cand_b.columns if c not in cand_a.columns]
    removed = [c for c in cand_a.columns if c not in cand_b.columns]
    return {'sha256_identical': same,
            'candidate_table_equal': bool(cand_a.equals(cand_b)),
            'candidate_shared_columns_equal': bool(cand_a[shared].equals(cand_b[shared])),
            'candidate_columns_added': added,
            'candidate_columns_removed': removed}


def check_stage2():
    import sf_critic_waspas as sf
    survey = ROOT / 'data/survey/expert_responses.csv'
    if not survey.exists():
        return {'skipped': 'survey export not present'}
    res = sf.run('survey', 0.5, 0.5, survey_path=str(survey))[0].set_index('site')
    stored = pd.read_csv(STAGE2 / 'stage2_scores.csv').set_index('site')
    diff = float(np.max(np.abs(res.loc[stored.index, 'Q01'] - stored.Q01)))
    return {'max_abs_diff_Q01': diff, 'ranking_equal': list(res.sort_values('Q', ascending=False).index)
            == list(stored.sort_values('Q', ascending=False).index), 'ok': diff < 1e-5}


def check_stage3():
    tag = 'verify_base'
    run([sys.executable, 'code/optimization/rpp_model.py', '--scenario', 'base', '--single', '--tag', tag])
    new = pd.read_csv(S3 / tag / 'solution.csv').iloc[0]
    old = pd.read_csv(S3 / 'base' / 'solution.csv').iloc[0]
    rel = abs(new.f1 - old.f1) / abs(old.f1)
    return {'f1_stored': float(old.f1), 'f1_rerun': float(new.f1), 'rel_diff': float(rel),
            'sites_equal': new.open_sites == old.open_sites, 'ok': bool(rel < 2e-3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-stage3', action='store_true')
    args = ap.parse_args()
    report = {'stage1': check_stage1(), 'stage2': check_stage2()}
    if not args.skip_stage3:
        report['stage3_base'] = check_stage3()
    (ROOT / 'data/processed/reproduction_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
