"""Anonymous leave-one-respondent-out sensitivity for the Stage II ranking."""
import json
import sys
from pathlib import Path

import pandas as pd

import sf_critic_waspas as sf

ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / 'data/survey/expert_responses.csv'
OUT = ROOT / 'data/processed/stage2/stage2_leave_one_out.json'


def summarize(frame, label, alpha, lam):
    result, *_ = sf.run('survey', alpha, lam, survey_frame=frame)
    ranking = result.sort_values(['Q', 'site'], ascending=[False, True]).site.tolist()
    return {
        'case': label,
        'ranking': ranking,
        'top_site': ranking[0],
    }


def main():
    if not SURVEY.exists():
        raise FileNotFoundError(f'Real survey export not found: {SURVEY}')
    frame = pd.read_csv(SURVEY)
    if len(frame) < 3:
        raise ValueError('At least three respondents are required for leave-one-out analysis.')

    alpha, lam = 0.5, 0.5
    cases = [summarize(frame, 'full_panel', alpha, lam)]
    for index in range(len(frame)):
        reduced = frame.drop(frame.index[index]).reset_index(drop=True)
        cases.append(summarize(reduced, f'one_respondent_omitted_{index + 1}', alpha, lam))

    loo = cases[1:]
    baseline = cases[0]
    report = {
        'method': 'leave-one-respondent-out; respondent-level scores and identifiers are not retained',
        'alpha_expert': alpha,
        'lambda_waspas': lam,
        'n_respondents': len(frame),
        'full_panel': baseline,
        'leave_one_out_rankings': [case['ranking'] for case in loo],
        'top_site_preserved_count': sum(case['top_site'] == baseline['top_site'] for case in loo),
        'top_site_preserved_fraction': sum(case['top_site'] == baseline['top_site'] for case in loo) / len(loo),
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({
        'n_respondents': report['n_respondents'],
        'baseline_ranking': baseline['ranking'],
        'leave_one_out_rankings': [case['ranking'] for case in loo],
        'top_site_preserved_fraction': report['top_site_preserved_fraction'],
        'output': str(OUT),
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()