"""Rebuild normalized JSON using ONLY the source snapshots in this project.

No imports from InCharacter, no network, no inferred psychometric cutoffs.
Run extract_sources.mjs first only when updating the vendored TS snapshots.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from isla_questionnaires.validation import validate_definition

DATA = ROOT / 'isla_questionnaires/data'
SRC = DATA / 'sources'
INDEX = json.loads((SRC / 'index.json').read_text())
EX = json.loads((SRC / 'extracted.json').read_text())
CATALOG = []
VERSION = '1.0.0'


def read(p):
    return json.loads((SRC / p).read_text())


def clean(s):
    import html
    return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', s or '')).split())


def slug(s):
    return re.sub('[^a-z0-9]+', '-', s.lower()).strip('-')


def choices(lo, hi, labels=None):
    return [{'value': n, 'label': (labels or {}).get(n, str(n)) if isinstance(labels, dict)
             else labels[n-lo] if labels else str(n)} for n in range(lo, hi+1)]


def item(i, text, opts, help=''):
    return {'id': str(i), 'text': text, 'type': 'choice', 'options': opts, 'help': help}


def dim(id, name, terms, op='mean', description=None, **extra):
    return {'id': id, 'name': name, 'operation': op, 'terms': terms,
            'description': description or f'{name}: {op} of the keyed responses. No population cutoff is applied.', **extra}


def terms(ids, reverse=()):
    return [{'item': str(i), 'reverse': i in reverse} for i in ids]


def emit(id, name, items, dims, source, paths, *, instructions, notes=(), blockers=(),
         mode='automatic', parameters=None, evidence=(), verification='source_key_checked', language='en'):
    status = 'review_required' if blockers else 'available'
    d = {'schema_version': 1, 'id': id, 'version': VERSION, 'name': name,
         'languages': [language], 'default_language': language, 'status': status,
         'instructions': instructions, 'expected_items': len(items), 'items': items,
         'parameters': parameters or {}, 'review_notes': list(blockers), 'notes': list(notes)}
    s = {'schema_version': 1, 'questionnaire_id': id, 'mode': mode,
         'missing_policy': 'require_complete', 'dimensions': dims}
    upstream = copy.deepcopy(INDEX.get(source, {'repository': 'primary-author-material', 'url': source}))
    files = [f'sources/{source}/{p}' for p in paths] if source in INDEX else list(paths)
    files += [f'sources/{source}/{p}' for p in upstream.get('license_files', [])]
    files += [p for p in evidence if (DATA / p).is_file()]
    p = {'source': upstream, 'files': [{'path': f, 'sha256': hashlib.sha256((DATA / f).read_bytes()).hexdigest()}
                                    for f in dict.fromkeys(files)],
         'verification': {'level': 'pending' if blockers else verification,
                          'scope': 'Versioned item text, response coding and declarative score rules; not a validation study or diagnostic approval.',
                          'blockers': list(blockers)},
         'transformations': list(notes), 'license_notice': 'Original questionnaire rights and source licenses remain applicable. See source files and THIRD_PARTY_NOTICES.md.'}
    validate_definition(d, s)
    target = DATA / id
    target.mkdir(exist_ok=True)
    hashes = {}
    for key, data in [('questionnaire', d), ('scoring', s), ('provenance', p)]:
        raw = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
        (target / f'{key}.json').write_bytes(raw)
        hashes[key] = hashlib.sha256(raw).hexdigest()
    CATALOG.append({'id': id, 'name': name, 'version': VERSION, 'status': status,
                    'mode': mode, 'items': len(items), 'languages': [language],
                    'review_notes': list(blockers), 'sha256': hashes})


AGREE5 = ['Strongly disagree', 'Disagree', 'Neither agree nor disagree', 'Agree', 'Strongly agree']
AGREE7 = ['Strongly disagree', 'Disagree', 'Slightly disagree', 'Neither agree nor disagree', 'Slightly agree', 'Agree', 'Strongly agree']


def incharacter():
    for code, id in [('BFI','bfi-44'),('EPQ-R','epq-r'),('ECR-R','ecr-r'),('LOT-R','lot-r'),('WLEIS','wleis'),('EIS','eis'),('CABIN','cabin')]:
        path = f'data/questionnaires/{code}.json'
        src = read('incharacter/' + path)
        lo, hi = src['range']
        labels = AGREE5 if hi-lo == 4 else AGREE7 if hi-lo == 6 else ['No','Yes']
        if code == 'CABIN': labels = ['Strongly dislike','Dislike','Neither like nor dislike','Like','Strongly like']
        if code == 'BFI': labels = ['Disagree strongly','Disagree a little','Neither agree nor disagree','Agree a little','Agree strongly']
        rows = [(i, q['origin_en']) for i,q in src['questions'].items()]
        notes = ['Use origin_en only; omit all role-play rewrites, character prompts, crowd norms and InCharacter assessment code.',
                 'English form only; upstream Chinese translations are retained in the source snapshot, not silently certified.']
        ev = []
        instruction = 'Please indicate how much you agree or disagree with each statement.'
        if code == 'BFI': instruction = 'I see myself as someone who…'
        if code == 'CABIN': instruction = 'Indicate how much you would like or dislike performing each activity.'
        if code == 'EPQ-R': instruction = 'Answer each question Yes or No, according to your usual way of acting or feeling.'
        if code == 'ECR-R':
            txt = (SRC/'primary/ecrr-items.txt').read_text()
            matches = re.findall(r'(?:^|\n)\s*(\d{1,2})\.\s*(.*?)(?=\n\s*\d{1,2}\.\s|\Z)',txt,re.S)
            rows = [(i, clean(t)) for i,t in matches if 1 <= int(i) <= 36]
            assert len(rows) == 36
            # The last item is followed only by whitespace in the author's page.
            assert rows[-1][1] == 'My partner really understands me and my needs.'
            instruction = 'The statements below concern how you feel in emotionally intimate relationships. We are interested in how you generally experience relationships, not just in what is happening in a current relationship. Respond to each statement to indicate how much you agree or disagree with the statement.'
            ev = ['sources/primary/ecrr-items.html','sources/primary/ecrr-items.txt']
            notes.append('Replace upstream transcription errors with the author’s English item text; use anxiety and avoidance means, never inferred four-type attachment labels.')
        its = [item(i,t,choices(lo,hi,labels)) for i,t in rows]
        if code == 'ECR-R':
            for q in its:q['options']=choices(1,7,{1:'Strongly disagree',7:'Strongly agree'})
            notes.append('The author page specifies endpoint anchors only; middle response points remain numeric.')
        dims = [dim(slug(c['cat_name']), c['cat_name'], terms(c['cat_questions'],src['reverse']),
                    'sum' if src['compute_mode']=='SUM' else 'mean') for c in src['categories']]
        if code == 'LOT-R': notes.append('Present all ten items; filler items 2, 5, 6, 8 do not enter the six-item 0–24 total.')
        emit(id,src['full_name'],its,dims,'incharacter',[path],instructions=instruction,notes=notes,evidence=ev,
             verification='primary_key_checked' if code == 'ECR-R' else 'source_key_checked')


def openscales():
    codes = {'GSE':'gse','RSES':'rses','SWLS':'swls','ERQ':'erq','DOSPERT':'dospert-rt-30',
             'IE-4':'ie-4','ESS-BSTS':'ess-social-trust','ESS-ITS':'ess-institutional-trust',
             'ESS-PE':'ess-political-efficacy','SECS':'secs','ESS-PVQ21':'pvq-21'}
    for code,id in codes.items():
        path=f'scales/openscales/{code}/{code}.osd'
        raw=read('openscales/'+path); src=raw['definition']; tr=raw['translations']['en']
        its=[]; prompts=[]; notes=[]; ev=[]; blockers=[]
        for row in src['items']:
            if row['type']=='inst': prompts.append(clean(tr[row['text_key']]))
            if row['type'] not in ('likert','vas'): continue
            if code=='DOSPERT' and not re.fullmatch(r'rt\d+',row['id']):continue
            if code=='ESS-PVQ21' and row['id'].endswith('_f'):continue
            opts={**src.get('likert_options',{}),**row.get('likert_options',{})}
            head=clean(tr.get(row.get('question_head',opts.get('question_head')),''))
            if row['type']=='vas':
                its.append({'id':row['id'],'text':clean(tr[row['text_key']]),'type':'number',
                            'min':row['min'],'max':row['max'],'help':head})
            else:
                lo=opts.get('min',1); hi=opts.get('max',lo+opts['points']-1)
                labels=[clean(tr.get(k,'')) or str(lo+n) for n,k in enumerate(opts.get('labels',[None]*(hi-lo+1)))]
                its.append(item(row['id'],clean(tr[row['text_key']]),choices(lo,hi,labels),head))
        ids={q['id'] for q in its}; names={d['id']:d['name'] for d in src['dimensions']}
        dims=[]
        for k,rule in src['scoring'].items():
            if not isinstance(rule,dict) or not rule.get('items'):continue
            keys=rule['items']; keys=keys if isinstance(keys,dict) else dict.fromkeys(keys,1)
            selected=[{'item':i,'reverse':v<0} for i,v in keys.items() if i in ids and v]
            if not selected:continue
            op={'sum_coded':'sum','mean_coded':'mean'}[rule['method']]
            desc=rule.get('description', f'{names.get(k,k)}: {op} of keyed responses.')
            if code=='RSES':desc='Global self-esteem, sum 0–30; higher means greater self-esteem. No universal high/normal/low thresholds are applied.'
            dims.append(dim(k,names.get(k,k),selected,op,desc))
        instruction='\n\n'.join(prompts) or clean(tr.get(src.get('likert_options',{}).get('question_head'),'')) or 'Answer each item using the displayed response scale.'
        if code=='GSE':
            txt=(SRC/'primary/gse-english.txt').read_text()
            matches=re.findall(r'(?:^|\n)\s*(10|[1-9])\s*\n(.*?)(?=\n\s*(?:10|[1-9])\s*\n|Response Format)',txt,re.S)
            pairs={int(n):clean(t) for n,t in matches};assert len(pairs)==10
            for n,q in enumerate(its,1):
                q['text']=pairs[n]
                q['options']=choices(1,4,['Not at all true','Hardly true','Moderately true','Exactly true'])
            notes.append('Use original author’s English items, replacing paraphrases in the OpenScales English table. Sum all ten 1–4 responses.')
            ev=['sources/primary/gse-english.html','sources/primary/gse-english.txt','sources/primary/gse-scoring.html']
        if code=='SWLS':
            for q in its:q['options']=choices(1,7,AGREE7)
            notes.append('Correct upstream reversed option labels against the author’s form: 1=strongly disagree, 7=strongly agree. Sum 5–35; interpretation intervals copied explicitly from the author’s English form, not generated by the runtime.')
            dims[0]['interpretation']={'source':'https://labs.psychology.illinois.edu/~ediener/Documents/SWLS_English.doc',
                'bands':[{'min':lo,'max':hi,'label':label} for lo,hi,label in [
                    (5,9,'Extremely dissatisfied'),(10,14,'Dissatisfied'),(15,19,'Slightly dissatisfied'),
                    (20,20,'Neutral'),(21,25,'Slightly satisfied'),(26,30,'Satisfied'),(31,35,'Extremely satisfied')]]}
            ev=['sources/primary/swls.html','sources/primary/swls-english.doc','sources/primary/swls-english.txt']
        if code=='ERQ':notes.append('Full 10-item ERQ only; omit short-form branching; preserve two separate dimension means.')
        if code=='DOSPERT':
            instruction=tr['rt_head'];notes.append('Risk-taking form only: 30 activity ratings, 5 means. Risk-perception and expected-benefit batteries are separate forms and are not included.')
        if code=='SECS':
            blockers.append('Upstream supplies only a composite; original social/economic subscale keys and exact aggregation need primary-source verification before release.')
        if code in ['ESS-ITS','ESS-PE']:
            # ESS supplies items, not diagnostic thresholds or an official universal aggregate.
            dims=[dim(q['id'],q['text'],terms([q['id']]),'sum',
                      'Original ESS item score. Higher means greater reported trust/efficacy; no unofficial composite or cutoff.') for q in its]
            notes.append('Return each original ESS item score; omit repository-created composite/group means because they are not an ESS classification standard.')
        if code=='ESS-BSTS':notes.append('Three-item mean is a descriptive index; it is not an official ESS diagnostic classification.')
        if code=='ESS-PVQ21':
            notes.append('ESS male-portrait form; preserve 1=very much like me to 6=not like me at all. Lower raw AND lower centered score indicate stronger endorsement. Fix contradictory upstream interpretation of centered-score sign.')
            for d in list(dims):
                if d['id']=='grand_mean': continue
                dims.append(dim(d['id']+'-centered',d['name']+' (centered)',copy.deepcopy(d['terms']),'centered_mean',
                                'Raw dimension mean minus mean of all 21 responses. Lower = relatively stronger value endorsement.',reference_items=[q['id'] for q in its]))
        notes.append('No missing-value imputation. Source report templates, guessed norm thresholds and generated text are not used.')
        emit(id,src['scale_info']['name'],its,dims,'openscales',[path],instructions=instruction,
             notes=notes,blockers=blockers,evidence=ev,verification='primary_key_checked' if code in ['GSE','SWLS'] else 'source_key_checked')


def bench():
    for file,id in [('ipip50','ipip-50'),('ncs18','ncs-18'),('mfq30','mfq-30'),('locus_levenson','levenson-ipc-24')]:
        path=f'instruments/{file}.json';src=read('personality-bench/'+path)
        its=[item(q['position'],q['text'],choices(src['scaleMin'],src['scaleMax'],src['scaleLabels'])) for q in src['items']]
        ds=[dim(d['id'],d['label'],[{'item':str(q['position']),'reverse':q.get('reverseKeyed',False)}
             for q in src['items'] if q['dimension']==d['id']], 'sum') for d in src['dimensions']]
        notes=['Preserve source item order and text. Source implementation percentile/0–100 normalization is not used.'];blockers=[]
        if id=='mfq-30':
            for n,q in enumerate(its):q['options']=choices(0,5,[s.split(' / ')[0 if n<15 else 1] for s in src['scaleLabels']])
            blockers=['This source omits two unscored attention items and changes some wording. Full original administration form must be verified before automatic release.']
        if id=='ncs-18':blockers=['Source uses a 1–5 agreement response form; original extremely uncharacteristic/characteristic anchors and version-specific coding must be checked.']
        if id=='levenson-ipc-24':blockers=['Duplicate/mismatched item wording and 1–6 versus -3,-2,-1,+1,+2,+3 response coding require original-form verification. Do not apply an assumed +24 conversion.']
        emit(id,src['name'],its,ds,'personality-bench',[path],instructions='Indicate how accurately each statement describes you.' if id=='ipip-50' else 'Respond to each statement using the displayed scale.',
             notes=notes,blockers=blockers,evidence=['sources/primary/ipip50.html'] if id=='ipip-50' else [])


def psyche():
    for id in ['iri-28','grit-s','grit-o','ius-12','mfq-2','self-monitoring-18','crt-7']:
        src=EX[id];its=[]
        for q in src['items']:
            r=q['response'];t=r['type']
            if t=='likert':it=item(q['id'],q['text'],choices(r['min'],r['max'],r['labels']))
            elif t=='binary':it=item(q['id'],q['text'],choices(0,1,['False','True']))
            else:it={'id':q['id'],'text':q['text'],'type':'number' if t=='numeric' else 'text'}
            its.append(it)
        ds=[]
        for d in src['scales']:
            qs=[q for q in src['items'] if q['scaleId']==d['id'] or d['id']=='overall']
            if not qs:continue
            ds.append(dim(d['id'],d['name'],[{'item':q['id'],'reverse':q.get('reversed',False)} for q in qs],
                          'sum' if id in ['ius-12','self-monitoring-18','iri-28'] else 'mean',d.get('description')))
        notes=['Only source data and explicit dimension keys are used; no generic scoreLikert normalization or personality labels.'];blockers=[]
        if id=='crt-7':
            answers=[5,5,47,4,29,20,'c']
            ds=[dim('correct','Correct answers',[{'item':q['id'],'accepted':[a]} for q,a in zip(its,answers)],'correct_count',
                    'Number of correct answers out of 7. Numeric answers use the units stated in each item; last answer accepts c (case-insensitive).')]
        if id in ['ius-12','grit-s']:
            ds.append(dim('total','Total', [{'item':q['id'],'reverse':q.get('reversed',False)} for q in src['items']], 'sum' if id=='ius-12' else 'mean'))
        if id=='iri-28':blockers=['Source reorders items by factor and uses 1–5 rather than original 0–4 anchors. Verify the original form, order, and scoring before release.']
        if id=='ius-12':blockers=['Source changes original item wording, including the last item; recover the original IUS-12 administration form before release.']
        if id=='mfq-2':blockers=['Source contains reworded items and 5 response options; verify the original MFQ-2 form and 6-point response anchors before release.']
        if id=='grit-o':blockers=['Source reorders and rephrases some 12-item Grit items; original administration form must be restored before release.']
        if id=='self-monitoring-18':notes.append('Explicit binary input: 0=False, 1=True. Reverse-keyed items score 1 for False. Sum 0–18; no inferred high/low cutoff.')
        emit(id,src['name'],its,ds,'psyche',[f'web/src/instruments/{id}.ts'],instructions='Answer each question in the stated units.' if id=='crt-7' else 'Indicate how well each statement describes you.',notes=notes,blockers=blockers,
             evidence=['sources/extracted.json'])


def others():
    rows=EX['bigfive'];labels=['Very Inaccurate','Moderately Inaccurate','Neither Accurate Nor Inaccurate','Moderately Accurate','Very Accurate']
    its=[item(q['id'],q['text'],choices(1,5,labels)) for q in rows]
    ds=[]
    for code,name in {'N':'Neuroticism','E':'Extraversion','O':'Openness','A':'Agreeableness','C':'Conscientiousness'}.items():
        ds.append(dim(code,name,[{'item':q['id'],'reverse':q['keyed']=='minus'} for q in rows if q['domain']==code],'sum'))
        for f in range(1,7):ds.append(dim(f'{code}{f}',f'{name} facet {f}',[{'item':q['id'],'reverse':q['keyed']=='minus'} for q in rows if q['domain']==code and q['facet']==f],'sum'))
    emit('ipip-neo-120','IPIP-NEO-120',its,ds,'bigfive-web',['packages/questions/src/data/en/questions.ts','packages/questions/src/data/en/choices.ts'],instructions='Describe yourself as you generally are now. Indicate how accurately each statement describes you.',notes=['Keep the 120 original source UUIDs, order, domain/facet mapping and key direction. Report raw sums, without invented population percentiles.'],evidence=['sources/extracted.json'])
    src=EX['scc'];its=[item(i+1,t,choices(1,5,['非常不同意','比较不同意','不确定','比较同意','非常同意'])) for i,t in enumerate(src['items'])]
    emit('scc','自我概念清晰性量表（来源译本待核）',its,[dim('clarity','自我概念清晰性',[{'item':str(i+1),'reverse':v} for i,v in enumerate(src['reverse'])],'mean','待核实的译本；不输出正式分数。')],'psv',['04_code_and_reproducibility/procedure/day1/surveys/selfclarity.js'],instructions=clean(src['instructions']),language='zh',blockers=['第一题译文将“自己的信念相互冲突”改成与其他人的看法冲突；不能将这个译本作为原标准量表自动评分。'],evidence=['sources/extracted.json'])
    raw=read('holi/data/official_item/Schwartz/PVQ-40_they.json')
    its=[item(i+1,t,choices(1,6,['Very much like me','Like me','Somewhat like me','A little like me','Not like me','Not like me at all'])) for i,t in enumerate(raw)]
    ds=[dim(slug(k),k,terms([i+1 for i,v in enumerate(raw.values()) if v['trait']==k]),'mean') for k in dict.fromkeys(v['trait'] for v in raw.values())]
    emit('pvq-40','PVQ-40 (source neutral-portrait form)',its,ds,'holi',['data/official_item/Schwartz/PVQ-40_they.json'],instructions='How much like you is this person?',blockers=['Source groups items by value and uses a neutral-pronoun adaptation; restore original administration order and verify response anchors before release.'])
    src=EX['pvqrr'];its=[]
    for i,t in enumerate(src['baseItems'],1):
        for k,v in src['pronounMaps']['male'].items():t=t.replace('{'+k+'}',v)
        its.append(item(i,t,choices(1,6,src['labels1to6'])))
    ds=[]
    for k,v in src['valueMeta'].items():
        ds.append(dim(k,v['name'],terms(v['items']),'mean',v['desc']))
        ds.append(dim(k+'-centered',v['name']+' (centered)',terms(v['items']),'centered_mean','Source response direction: higher = stronger relative endorsement.',reference_items=[q['id'] for q in its]))
    emit('pvq-rr','PVQ-RR (source 57-item form)',its,ds,'pvq-rr',['index.html'],instructions='How much like you is this person?',blockers=['Verify original item wording, value key and response coding: this source reverses the common 1=very much like me orientation.'],evidence=['sources/extracted.json'])
    its=[item(q['id'],q['en'],choices(1,7,{1:'Strongly disagree',7:'Strongly agree'}),'{{behavior}} is something…') for q in EX['srhi']]
    emit('srhi','Self-Report Habit Index (source form)',its,[dim('habit','Habit strength',terms([q['id'] for q in its]),'mean')],'health-habit-hub',['app/utils/srhi.js'],instructions='Rate the following statements about {{behavior}}.',parameters={'behavior':{'required':True}},blockers=['Source expands the daily-routine item to daily/weekly/monthly; verify the original item wording and aggregation rule before release.'],evidence=['sources/extracted.json'])
    its=[{'id':'context','text':'Describe the situation you want to reflect on.','type':'text'},
         {'id':'response','text':'Describe your thoughts, feelings, and actions in that situation.','type':'text'},
         {'id':'reflection','text':'What would you like a human reviewer to consider?','type':'text'}]
    emit('reflection-demo','Qualitative reflection — API demonstration',its,[],'project-authored',[],instructions='Write freely. This is an API demonstration, not a validated questionnaire.',mode='manual',notes=['Project-authored example, excluded from the 36-instrument inventory. A human supplies any interpretation.'],verification='demo')


def primary():
    txt=(SRC/'primary/hexaco-self60.txt').read_text()
    rows=re.findall(r'(?:^|\n)\s*(\d{1,2})\s*\n(.*?)(?=\n\s*\d{1,2}\s*\n|\Z)',txt,re.S)
    assert len(rows)==60
    its=[item(n,clean(t.replace('Continued…','').split('1 = strongly disagree')[0]),choices(1,5,['Strongly disagree','Disagree','Neutral (neither agree nor disagree)','Agree','Strongly agree'])) for n,t in rows]
    # Extract factor/facet keys from the author's two-page scoring document.
    key=(SRC/'primary/hexaco-keys.txt').read_text().split('Notes')[0];factor=None;facets={};ds=[]
    for line in key.splitlines():
        match=re.match(r'\s*([A-Za-z -]+?)\s+(\d.*)',line)
        if match and factor:
            name,codes=match.groups();ts=[{'item':m.group(1),'reverse':bool(m.group(2))} for m in re.finditer(r'(\d+)(R?)',codes)]
            ds.append(dim(slug(name.strip()),name.strip(),ts));facets.setdefault(factor,[]).extend(ts)
        elif line.strip() in ['Honesty-Humility','Emotionality','Extraversion','Agreeableness','Conscientiousness','Openness to Experience']:factor=line.strip()
    assert len(ds)==24 and all(len(v)==10 for v in facets.values())
    ds=[dim(slug(k),k,v) for k,v in facets.items()]+ds
    emit('hexaco-60','HEXACO-PI-R 60-item English self-report',its,ds,'https://hexaco.org/hexaco-inventory',
         ['sources/primary/hexaco-self60.doc','sources/primary/hexaco-self60.txt','sources/primary/hexaco-keys.pdf','sources/primary/hexaco-keys.txt','sources/primary/hexaco-terms.html'],
         instructions='Indicate how much you agree or disagree with each statement about yourself.',verification='primary_key_checked',
         notes=['Replace the mislabeled IPIP-like repository form with the authors’ actual English HEXACO-60. Factor means use all 10 keyed items, not an unweighted mean of unequal-length facets.',
                'Author terms restrict use to non-profit academic research; public survey/app access restrictions apply. This bundled source does not grant unrestricted redistribution.'])
    txt=(SRC/'primary/onet-mini-ip.txt').read_text();section=txt[txt.index('Realistic Items'):txt.index('Appendix B',txt.index('Realistic Items'))]
    groups={};current=None
    for line in section.splitlines():
        if re.fullmatch(r'(Realistic|Investigative|Artistic|Social|Enterprising|Conventional) Items\s*',line):current=line.split()[0]
        m=re.match(r'\s*(\d{1,2})\s+([A-Za-z].+)',line)
        if m and current:groups[int(m[1])]=(current,m[2].strip())
    # The PDF wraps item 19 across three lines; preserve its original wording.
    groups[19]=('Realistic','Drive a truck to deliver packages to offices and homes')
    assert len(groups)==30
    its=[item(n,groups[n][1],choices(0,4,['Strongly dislike','Dislike','Unsure','Like','Strongly like'])) for n in range(1,31)]
    ds=[dim(k[0],k,terms([n for n,(g,t) in groups.items() if g==k]),'sum',f'{k} interest: sum of five responses, range 0–20. Higher scores indicate stronger interest.') for k in ['Realistic','Investigative','Artistic','Social','Enterprising','Conventional']]
    emit('riasec-mini-ip','O*NET Mini Interest Profiler (2016 computerized form)',its,ds,'https://www.onetcenter.org/reports/Mini-IP.html',['sources/primary/onet-mini-ip.pdf','sources/primary/onet-mini-ip.txt'],instructions='Indicate how much you would like or dislike doing each work activity.',verification='primary_key_checked',notes=['Use Appendix A original suggested order and report page 13 computerized coding 0–4, sum 0–20. Do not substitute the repository’s altered 1–5 item bank. No occupation recommendation database is bundled.'])


if __name__=='__main__':
    incharacter();openscales();bench();psyche();others();primary()
    CATALOG.sort(key=lambda e:e['id'])
    (DATA/'catalog.json').write_text(json.dumps({'schema_version':1,'questionnaires':CATALOG},ensure_ascii=False,indent=2)+'\n')
    print(f'{len(CATALOG)} forms; {sum(e["status"]=="available" for e in CATALOG)} available (including one demonstration).')
