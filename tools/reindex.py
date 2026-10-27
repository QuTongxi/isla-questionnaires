"""Validate authored data and update its catalog checksums after a reviewed change.

Does not rewrite source evidence or loosen a review_required gate.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from isla_questionnaires.validation import validate_definition


def main():
    root=ROOT/'isla_questionnaires/data';entries=[]
    for path in sorted(root.glob('*/questionnaire.json')):
        parent=path.parent;raw={k:(parent/f'{k}.json').read_bytes() for k in ['questionnaire','scoring','provenance']}
        d,s,p=(json.loads(raw[k]) for k in ['questionnaire','scoring','provenance'])
        if d['id'] != parent.name:raise ValueError('Directory/ID mismatch')
        validate_definition(d,s)
        for evidence in p['files']:
            file=(root/evidence['path']).resolve()
            if not file.is_relative_to(root.resolve()):raise ValueError('Source path escapes data directory')
            if hashlib.sha256(file.read_bytes()).hexdigest()!=evidence['sha256']:raise ValueError(f'Source changed: {file}')
        entries.append({'id':d['id'],'name':d['name'],'version':d['version'],'status':d['status'],'mode':s['mode'],
                        'items':len(d['items']),'languages':d['languages'],'review_notes':d.get('review_notes',[]),
                        'sha256':{k:hashlib.sha256(v).hexdigest() for k,v in raw.items()}})
    (root/'catalog.json').write_text(json.dumps({'schema_version':1,'questionnaires':entries},ensure_ascii=False,indent=2)+'\n')
    print(f'Indexed {len(entries)} forms.')


if __name__=='__main__':main()
