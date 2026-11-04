import datetime
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
for sub in ('downloads', 'vendor', 'sources', 'tmp', 'cache'):
    (ROOT / sub).mkdir(exist_ok=True)

def fetch(url, destination, limit):
    if destination.exists():
        raw = destination.read_bytes()
        assert len(raw) <= limit
        return raw, {'url': url, 'cached': True}
    request = urllib.request.Request(url, headers={'User-Agent': 'PublicFinancialDocumentResearch/0.1'})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('Download exceeded byte limit')
        metadata = {'url': url, 'resolved_url': response.url,
                    'content_type': response.headers.get_content_type(),
                    'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    destination.write_bytes(raw)
    return raw, metadata

wheel_url = 'https://files.pythonhosted.org/packages/4f/bf/6e02e3d84b32c137c71a0a3dcdba8f2f6e9950619a3bc272245c7c06a051/pymupdf-1.26.6-cp310-abi3-manylinux_2_28_x86_64.whl'
wheel, _ = fetch(wheel_url, ROOT / 'downloads/pymupdf-1.26.6.whl', 25_000_000)
assert hashlib.sha256(wheel).hexdigest() == '7777d0b7124c2ebc94849536b6a1fb85d158df3b9d873935e63036559391534c'
with zipfile.ZipFile(io.BytesIO(wheel)) as archive:
    size = sum(f.file_size for f in archive.infolist())
    print(json.dumps({'wheel_bytes': len(wheel), 'unpacked_bytes': size}), flush=True)
    assert size < 100_000_000
    for member in archive.infolist():
        assert (ROOT / 'vendor' / member.filename).resolve().is_relative_to((ROOT / 'vendor').resolve())
    if not (ROOT / 'vendor/pymupdf/__init__.py').exists():
        archive.extractall(ROOT / 'vendor')

sources = [
    ('TREASURY2024', 'https://fiscal.treasury.gov/system/files/files/reports-statements/financial-report/2024/financial-statements-2024.pdf'),
    ('TREASURY2025', 'https://fiscal.treasury.gov/system/files/2026-03/financial-statements-2025.pdf'),
]
manifest = []
for sid, url in sources:
    destination = ROOT / 'sources' / (sid + '.pdf')
    try:
        raw, meta = fetch(url, destination, 12_000_000)
        if not raw.startswith(b'%PDF-'):
            raise ValueError('Source is not PDF')
        meta.update({'source_id': sid, 'path': str(destination.relative_to(ROOT)),
                     'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                     'source_kind': 'US Treasury official public financial statements',
                     'rights_basis': 'US federal-government authored financial tables; no third-party photos selected',
                     'rights_reference': 'https://www.loc.gov/legal/security-copyright-and-privacy/understanding-copyright/'})
        manifest.append(meta)
        print(json.dumps({'source': sid, 'bytes': len(raw), 'status': 'downloaded'}), flush=True)
    except Exception as error:
        print(json.dumps({'source': sid, 'status': 'error', 'error': str(error)}), flush=True)
(ROOT / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
