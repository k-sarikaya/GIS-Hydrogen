import pandas as pd
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
survey_path = ROOT / 'data/survey/expert_responses.csv'
if not survey_path.exists():
    raise FileNotFoundError(f'Expert survey export not found: {survey_path}')

df = pd.read_csv(survey_path)
consent_column = next((column for column in df if column == 'Onam'), None)
consented = int(df[consent_column].notna().sum()) if consent_column else 0
print(f'Responses: {len(df)}')
print(f'Consent responses present: {consented}')
print('Direct identifiers, demographics, timestamps, and free text are intentionally not displayed.')
