"""Acquire seven pinned public consumer implementation files; no inference or traces."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Explicit directory for the pinned source files')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'consumer_reuse/source_manifest.json').read_text())
    verified = []
    for item in manifest['source_files']:
        relative = item['url'].split(manifest['consumer_source_revision']+'/')[1]
        destination = args.out/relative
        if destination.exists():
            data = destination.read_bytes()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Existing source differs from pin: '+relative)
        else:
            with urllib.request.urlopen(item['url'], timeout=30) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Downloaded source differs from pin: '+relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        verified.append(relative)
    print(json.dumps({'pinned_revision':manifest['consumer_source_revision'], 'verified_source_files':verified}, indent=2))

if __name__ == '__main__':
    main()
