import hashlib
from collections import Counter
import json
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parent
variants = json.loads((ROOT/'private/variants.json').read_text())
questions = json.loads((ROOT/'questions_manifest.json').read_text())['questions']
truth = json.loads((ROOT/'private/ground_truth.json').read_text())
assert len(questions) == len(truth) == 10
assert len({q['id'] for q in questions}) == 10
checks = []
text_checks = []
for vid, variant in variants.items():
    source = fitz.open(ROOT/'sources'/(variant['source_id']+'.pdf'))
    source_words = Counter(w[4] for w in source[variant['physical_page']-1].get_text('words'))
    native = fitz.open(ROOT/'assets'/vid/'page.pdf')
    expected_words = source_words.copy()
    for change in variant['changes']:
        expected_words[change['before']] -= 1
        expected_words[change['after']] += 1
    actual_words = Counter(w[4] for w in native[0].get_text('words'))
    assert +expected_words == +actual_words, (vid, expected_words-actual_words, actual_words-expected_words)
    text_checks.append({'variant': vid, 'native_text_multiset_matches_only_intended_replacements': True})
    source.close(); native.close()
    image = fitz.Pixmap(ROOT/variant['image'])
    assert image.width == variant['width'] and image.height == variant['height']
    baseline = variants[variant['base_id']+'_control']
    if vid.endswith('_control') or variant['benign_processing']:
        continue
    control = fitz.Pixmap(ROOT/baseline['image'])
    assert image.n == control.n == 3
    first, second = control.samples, image.samples
    changed, outside = 0, 0
    regions = []
    for change in variant['changes']:
        a, b = change['bbox_a'], change['bbox_b']
        regions.append((min(a[0],b[0])*image.width-4, min(a[1],b[1])*image.height-4,
                        max(a[2],b[2])*image.width+4, max(a[3],b[3])*image.height+4))
    for y in range(image.height):
        begin = y*image.width*3
        end = begin+image.width*3
        if first[begin:end] == second[begin:end]:
            continue
        for x in range(image.width):
            offset = begin+x*3
            if first[offset:offset+3] != second[offset:offset+3]:
                changed += 1
                if not any(x0 <= x <= x1 and y0 <= y <= y1 for x0,y0,x1,y1 in regions):
                    outside += 1
    assert changed > 0, vid
    assert outside == 0, (vid, changed, outside)
    checks.append({'variant': vid, 'changed_pixels': changed,
                   'changed_pixels_outside_annotated_regions_with_4px_margin': outside})
for q in questions:
    prompt = ROOT/q['directory']/'prompt.txt'
    assert hashlib.sha256(prompt.read_bytes()).hexdigest() == q['prompt_sha256']
    for image in q['images']:
        assert hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest() == image['sha256']
    assert {x.name for x in (ROOT/q['directory']).iterdir()} <= {'AGENTS.md','prompt.txt','page.png','page_a.png','page_b.png'}
result = {'questions_checked': len(questions), 'edited_variants_checked': len(checks),
          'checks': checks, 'native_text_checks': text_checks,
          'source_value_readback': 'all native PDF replacement values checked by prepare.py',
          'arithmetic_checks': 'private/arithmetic_checks.json',
          'limitations': 'Pixel localization proves intended raster changes only; it does not certify visual realism or original business authenticity.'}
(ROOT/'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False))
