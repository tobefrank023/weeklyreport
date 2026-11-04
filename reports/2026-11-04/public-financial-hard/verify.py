import hashlib
import json
from pathlib import Path
import pymupdf as fitz

ROOT=Path(__file__).resolve().parent
assets=json.loads((ROOT/'private/assets.json').read_text())
questions=json.loads((ROOT/'questions_manifest.json').read_text())['questions']
truth={t['id']:t for t in json.loads((ROOT/'private/ground_truth.json').read_text())}
freeze=json.loads((ROOT/'freeze_manifest.json').read_text())
publication_path=ROOT/'publication_manifest.json'
publication=json.loads(publication_path.read_text()) if publication_path.exists() else {}
overrides=publication.get('published_file_sha256',{})
assert set(overrides) <= {'run_luna.py'}, 'Publication override cannot change question or answer hashes'
for rel,value in publication.get('original_recorded_sha256',{}).items():
    assert freeze['files'][rel]==value
for rel,expected in freeze['files'].items():
    assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==overrides.get(rel,expected),rel
assert freeze['frozen_before_solver_calls']
assert len(questions)==10 and sum(len(q['images']) for q in questions)==46
assert sum(len(t['expected_changes']) for t in truth.values() if t['kind']=='paired')==37
assert max(len(t['expected_changes']) for t in truth.values())==11
checks=[]
for key,asset in assets.items():
    if not asset['changes']:continue
    control=assets[asset['page_id']+'__control']
    a,b=fitz.Pixmap(ROOT/control['image']),fitz.Pixmap(ROOT/asset['image'])
    assert a.width==b.width and a.height==b.height and a.n==b.n==3
    regions=[]
    for change in asset['changes']:
        x,y=change['bbox_a'],change['bbox_b']
        regions.append((min(x[0],y[0])*a.width-4,min(x[1],y[1])*a.height-4,
                        max(x[2],y[2])*a.width+4,max(x[3],y[3])*a.height+4))
    first,second=a.samples,b.samples; changed,outside=0,0
    for row in range(a.height):
        begin=row*a.width*3;end=begin+a.width*3
        if first[begin:end]==second[begin:end]:continue
        for col in range(a.width):
            i=begin+col*3
            if first[i:i+3]!=second[i:i+3]:
                changed+=1
                if not any(x0<=col<=x1 and y0<=row<=y1 for x0,y0,x1,y1 in regions):outside+=1
    assert changed>0 and outside==0,(key,changed,outside)
    checks.append({'asset':key,'edited_fields':len(asset['changes']),'changed_pixels':changed,
                   'outside_annotated_union_with_4px_margin':outside})
for q in questions:
    assert hashlib.sha256((ROOT/q['directory']/'prompt.txt').read_bytes()).hexdigest()==q['prompt_sha256']
    for im in q['images']:
        assert hashlib.sha256((ROOT/im['path']).read_bytes()).hexdigest()==im['sha256']
    assert not any(p.name.endswith('.json') for p in (ROOT/q['directory']).iterdir())
    assert len(truth[q['id']]['expected_changes'])<=16
result={'questions_verified':len(questions),'image_attachments_verified':46,'assets_verified':len(assets),
        'edited_asset_pixel_checks':checks,'freeze_integrity':True,
        'native_text_and_field_readback':'all 21 assets checked during generation',
        'scope':'source values, text preservation, intended raster regions and input hashes; no independent authenticity or realism certification'}
(ROOT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'questions':len(questions),'edited_asset_pages':len(checks),'off_target_pixels':sum(c['outside_annotated_union_with_4px_margin'] for c in checks),'freeze_integrity':True}))
