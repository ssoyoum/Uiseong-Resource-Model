"""Build a public Pages artifact using only files referenced by the Web GIS.

Uses Python's standard library. Validates saved results; does not collect data.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = 'https://ssoyoum.github.io/Uiseong-Resource-Model/'
SOURCE_FILES = {
    'data/manifests/sgis_sources.csv',
    'data/manifests/vworld_sources.csv',
    'data/manifests/population_sources.csv',
    'data/analysis/validation_report.json',
}
MODULES = ('def-dashboard.mjs', 'quality-dashboard.mjs')
# 링크 공유 미리보기(og:image)는 절대 URL이라 참조 수집에 잡히지 않아 직접 포함한다.
SHARE_FILES = {'assets/og-image.png'}
# 잘못된 주소로 들어온 방문자를 첫 화면으로 돌려보내는 GitHub Pages 404 페이지.
STATIC_PAGES = {'404.html'}
PUBLIC_VENDOR_FILES = {
    'vendor/leaflet/LICENSE',
    'vendor/leaflet/images/layers.png',
    'vendor/leaflet/images/layers-2x.png',
    'vendor/leaflet/images/marker-icon.png',
    'vendor/leaflet/images/marker-icon-2x.png',
    'vendor/leaflet/images/marker-shadow.png',
}


class PageReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.integrities = []
        self.ids = set()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get('id'):
            if attrs['id'] in self.ids:
                raise ValueError(f'Duplicate HTML id: {attrs["id"]}')
            self.ids.add(attrs['id'])
        for attribute in ('src', 'href'):
            if attrs.get(attribute):
                self.references.append(attrs[attribute])
        reference = attrs.get('src') or attrs.get('href')
        if reference and attrs.get('integrity'):
            parsed = urlsplit(reference)
            if not parsed.scheme and not parsed.netloc and parsed.path:
                self.integrities.append((parsed.path, attrs['integrity']))


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))


def read_csv(relative):
    with (ROOT / relative).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def available(value):
    return value not in (None, '', 'DATA_NOT_AVAILABLE')


def check_saved_results():
    summary = read_json('data/analysis/sgis_catchment_analysis.json')
    evidence = read_json('data/analysis/sgis_policy_evidence.json')
    validation = read_json('data/analysis/validation_report.json')
    rows = read_csv('data/analysis/sgis_catchment_analysis.csv')
    policies = read_csv('data/analysis/sgis_policy_evidence.csv')
    ids = {row['pond_id'] for row in rows}
    if len(rows) != 427 or len(ids) != 427 or summary['facility_count'] != len(rows):
        raise ValueError('SGIS facilities must match the 427 distinct source IDs.')
    if len(policies) != len(rows) or {row['pond_id'] for row in policies} != ids:
        raise ValueError('Policy evidence IDs differ from SGIS analysis IDs.')
    eligible = [row for row in rows if row['sgis_analysis_eligible'].lower() == 'true']
    if len(eligible) != 380 or len({row['coordinate_group_id'] for row in eligible}) != len(eligible):
        raise ValueError('Eligible coordinate sample differs from the published 380 points.')
    coverage = {
        'available_5min': sum(available(row['sgis_population_5min']) for row in eligible),
        'available_10min': sum(available(row['sgis_population_10min']) for row in eligible),
        'available_both': sum(available(row['sgis_population_5min']) and available(row['sgis_population_10min']) for row in eligible),
        'none': sum(not available(row['sgis_population_5min']) and not available(row['sgis_population_10min']) for row in eligible),
    }
    if coverage != summary['coverage']:
        raise ValueError('SGIS CSV coverage does not match the JSON summary.')
    if (coverage['available_both'], coverage['available_10min']) != (175, 190):
        raise ValueError('Update the public page sample counts before publishing new SGIS results.')
    counts = dict(Counter(row['policy_review_context'] for row in policies))
    if counts != evidence['policy_review_context_counts']:
        raise ValueError('Policy group counts differ from the saved summary.')
    if summary['status'] != 'PASS' or validation['status'] != 'PASS' or validation['fail_count'] != 0:
        raise ValueError('Saved analysis validation must be PASS with zero failures.')
    audit = read_json('data/analysis/data_quality_audit.json')
    if audit['status'] != 'PASS':
        raise ValueError('Data quality audit must PASS before publishing.')
    if summary['year'] != 2024:
        raise ValueError('Update the public source-year labels before changing the SGIS year.')
    return {
        'status': 'PASS',
        'facility_count': len(rows),
        'eligible_coordinate_points': len(eligible),
        'sgis_year': summary['year'],
        'sgis_coverage': coverage,
        'policy_review_context_counts': counts,
        'pipeline_validation': {key: validation[key] for key in ('status', 'pass_count', 'fail_count')},
        'data_quality_audit': audit['status_counts'],
    }


def site_files():
    parser = PageReferences()
    parser.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
    files = {'index.html', 'app.js', 'styles.css', *MODULES, '.nojekyll', *SOURCE_FILES, *PUBLIC_VENDOR_FILES, *SHARE_FILES, *STATIC_PAGES}
    for reference in parser.references:
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc:
            continue
        if not parsed.path:
            if parsed.fragment and parsed.fragment not in parser.ids:
                raise ValueError(f'Missing public page anchor: {reference}')
            continue
        if parsed.path.startswith('/') or '..' in Path(parsed.path).parts:
            raise ValueError(f'Non-relative public file reference: {reference}')
        files.add(parsed.path)
    for script in ('app.js', *MODULES):
        text = (ROOT / script).read_text(encoding='utf-8')
        files.update(re.findall(r'''(?:loadJson|loadCsv)\(['"]([^'"]+)['"]\)''', text))
        for reference in re.findall(r'''import\(['"]([^'"]+)['"]\)''', text):
            files.add(urlsplit(reference).path.removeprefix('./'))
    for relative in sorted(files):
        parts = Path(relative).parts
        if any(part in {'.git', '.env', 'raw', 'source', 'submission', 'drafts', 'vworld'} for part in parts):
            raise ValueError(f'Unexpected source/private path in public artifact: {relative}')
        if not (ROOT / relative).is_file():
            raise FileNotFoundError(f'Missing public site input: {relative}')
    for relative, expected in parser.integrities:
        digest = base64.b64encode(hashlib.sha256((ROOT / relative).read_bytes()).digest()).decode()
        actual = f'sha256-{digest}'
        if expected != actual:
            raise ValueError(f'Public asset integrity mismatch: {relative}')
    return files


def build(output):
    summary = check_saved_results()
    files = site_files()
    output = output.resolve()
    if output == ROOT or ROOT not in output.parents:
        raise ValueError('Build output must be a subdirectory of the repository.')
    if output.exists():
        unexpected = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()} - files - {'public-site-manifest.json'}
        if unexpected:
            raise ValueError(f'Unexpected existing artifact files: {sorted(unexpected)}')
    hashes = {}
    for relative in sorted(files):
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
        hashes[relative] = hashlib.sha256(destination.read_bytes()).hexdigest()
    manifest = {'site_url': SITE_URL, 'validation': summary, 'files_sha256': hashes}
    (output / 'public-site-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'public site: PASS ({len(files)} files; 427 facilities; SGIS paired=175, 10min=190)')
    print(f'output: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '_site')
    build(parser.parse_args().output)
