"""Trace high population values to saved responses without deleting observations."""
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def run():
    source = ROOT / 'data/analysis/sgis_catchment_analysis.csv'
    raw_path = ROOT / 'data/processed/population/sgis_drive_population.csv'
    frame = pd.read_csv(source, dtype={'pond_id': str})
    raw = pd.read_csv(raw_path, dtype={'pond_id': str})
    eligible = frame[frame.sgis_analysis_eligible.astype(str).str.lower().eq('true')]
    paired = eligible.drop_duplicates('coordinate_group_id').dropna(subset=['sgis_population_5min', 'sgis_population_10min'])
    top = paired.loc[paired.sgis_population_5min.idxmax()]
    responses = raw[raw.pond_id.eq(top.pond_id)]
    for minutes in [5, 10]:
        assert responses.loc[responses.drive_time_min.eq(minutes), 'sgis_population'].item() == top[f'sgis_population_{minutes}min']
    rest = paired[~paired.pond_id.eq(top.pond_id)]
    keys = ['pond_id', 'address', 'coordinate_group_size', 'coordinate_validation', 'sgis_population_5min', 'sgis_population_10min', 'sgis_area_5min_m2', 'sgis_area_10min_m2']
    result = {
        'status': 'PASS', 'paired_count': len(paired), 'extreme_value': json.loads(top[keys].to_json(force_ascii=False)),
        'raw_response_match': True, 'excluded_due_to_magnitude': 0,
        'decision': 'Retain the maximum; x-axis log scale; annotate ID. No evidence of transcription error or duplicate coordinate.',
        'causal_limit': 'The saved area and population confirm the high statistic, but do not identify which residential area caused it. No causal spatial explanation is asserted.',
        'mean_5min_all': float(paired.sgis_population_5min.mean()),
        'mean_5min_without_max_sensitivity_only': float(rest.sgis_population_5min.mean()),
        'median_5min_all': float(paired.sgis_population_5min.median()),
        'source_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [source, raw_path]},
    }
    (ROOT / 'data/analysis/sgis_extreme_value_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))

if __name__ == '__main__':
    run()
