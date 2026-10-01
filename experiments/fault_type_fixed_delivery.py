"""Verify explicit archive SHA/CRC/every member; never extract or delete data."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from core.fault_type_provenance import save_json
from core.logger import setup_run
from experiments.fault_type_archive import _sha


def verify_archive(item):
    path=Path(item['path'])
    if path.stat().st_size!=item['bytes'] or _sha(path)!=item['sha256']:
        raise ValueError('archive whole SHA/length mismatch')
    with zipfile.ZipFile(path) as bundle:
        if bundle.testzip(): raise ValueError('archive CRC mismatch')
        index=json.loads(bundle.read('BUNDLE_INDEX.json'))
        expected={e['path'] for e in index['files']}|{'BUNDLE_INDEX.json'}
        if set(bundle.namelist())!=expected or len(bundle.namelist())!=len(expected):
            raise ValueError('archive member inventory mismatch')
        if len(index['files'])!=item['source_files']: raise ValueError('archive member count mismatch')
        for entry in index['files']:
            digest=hashlib.sha256(); size=0
            with bundle.open(entry['path']) as source:
                for chunk in iter(lambda:source.read(1024*1024),b''):
                    size+=len(chunk); digest.update(chunk)
            if size!=entry['bytes'] or digest.hexdigest()!=entry['sha256']:
                raise ValueError('archive member SHA/length mismatch')
    return dict(item,member_sha_status='PASS',crc_status='PASS',whole_sha_status='PASS')


def run(pools, *, indices):
    archives=[]
    for path in indices:
        index=json.loads(Path(path).read_text(encoding='utf-8'))
        archives.extend(verify_archive(item) for item in index['archives'])
    return {'status':'PASS','archives':archives,'archive_count':len(archives),
            'verified_members':sum(a['source_files'] for a in archives),'source_files_removed':False,
            'backup_scope':'single D volume; not offsite backup; indices retain original source paths'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',action='append',type=Path,required=True)
    args=parser.parse_args(); log,paths=setup_run('fault_type_fixed_delivery')
    result=run(None,indices=args.index)
    save_json(paths.output_dir/'member_verification.json',result)
    log.info('{} archives / {} members SHA/CRC PASS; no deletion',result['archive_count'],result['verified_members'])


if __name__=='__main__': main()
