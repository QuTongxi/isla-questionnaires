import argparse
import json
import sys
from pathlib import Path
from .catalog import list_questionnaires
from .session import load_questionnaire, restore_session
from .errors import QuestionnaireError, ReviewRequired
from .testing import synthetic_answers


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))


def main(argv=None):
    parser=argparse.ArgumentParser(description='Offline questionnaires; explicit response coding and auditable native scores.')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('list');p.add_argument('--all',action='store_true',help='Include forms blocked for source review')
    sub.add_parser('validate',help='Validate every definition, rule and source hash')
    for cmd in ['show','audit','run','score','generate-answers']:
        p=sub.add_parser(cmd)
        p.add_argument('id');p.add_argument('--language');p.add_argument('--allow-review',action='store_true')
        p.add_argument('--parameter',action='append',default=[],metavar='NAME=TEXT')
        if cmd=='run':
            p.add_argument('--save',type=Path,required=True,help='Save after every valid answer')
            p.add_argument('--resume',type=Path)
            p.add_argument('--sheet',type=Path,help='Write printable complete answer sheet')
        if cmd=='score':
            p.add_argument('answers',help='JSON object keyed by item ID, or - for stdin')
            p.add_argument('--trace',action='store_true')
        if cmd=='generate-answers':
            p.add_argument('--pattern',choices=['min','max','middle','random'],default='middle')
            p.add_argument('--seed',type=int,default=0)
    args=parser.parse_args(argv)
    try:
        if args.command=='list':
            output(list_questionnaires(include_review=args.all));return 0
        if args.command=='validate':
            results=[]
            for entry in list_questionnaires(include_review=True):
                q=load_questionnaire(entry['id'],allow_review=True,parameters={'behavior':'validation placeholder'} if entry['id']=='srhi' else None)
                results.append({'id':q.id,**q.audit_definition()['validation']})
            output(results);return 0
        parameters={}
        for pair in args.parameter:
            key,sep,val=pair.partition('=')
            if not sep or not key or key in parameters:raise QuestionnaireError('Parameters must be unique NAME=TEXT pairs')
            parameters[key]=val
        if args.command=='run' and args.resume:
            q=restore_session(args.resume,allow_review=args.allow_review)
            if q.id != args.id:raise QuestionnaireError('Resume file belongs to a different questionnaire')
            if args.language is not None and q.language != args.language:raise QuestionnaireError('Resume language differs')
            if parameters and q._parameters != parameters:raise QuestionnaireError('Resume parameters differ')
        else:
            q=load_questionnaire(args.id,language=args.language,parameters=parameters,allow_review=args.allow_review)
        if args.command=='show':output(q.describe())
        elif args.command=='audit':output(q.audit_definition())
        elif args.command=='generate-answers':output(synthetic_answers(q,pattern=args.pattern,seed=args.seed))
        elif args.command=='score':
            answers=json.loads(sys.stdin.read() if args.answers=='-' else Path(args.answers).read_text(encoding='utf8'))
            q.submit_answers(answers);output(q.audit_score() if args.trace else q.judge().to_dict())
        elif args.command=='run':
            print(q.describe()['name']);print(q.describe()['instructions'])
            if q.capabilities['status']=='review_required':
                print('REVIEW REQUIRED: answer collection/export only; automatic scoring is blocked.')
                for note in q.describe()['review_notes']:print(note)
            q.export_session(args.save)
            try:
                while (item:=q.next_question()) is not None:
                    print(f'\n{item.number}/{item.total} [{item.id}] {item.text}')
                    if item.help:print(item.help)
                    for opt in item.options:print(f"  {opt['value']}: {opt['label']}")
                    if item.type=='number':print(f'Numeric answer; min={item.min}, max={item.max}')
                    raw=input('Answer (:quit saves and exits): ')
                    if raw.strip()==':quit':return 0
                    try:
                        value=raw if item.type=='text' else json.loads(raw)
                        q.submit_answer(item.id,value)
                    except (QuestionnaireError,json.JSONDecodeError) as error:
                        print(f'Invalid answer: {error}',file=sys.stderr);continue
                    q.export_session(args.save)
            except (EOFError,KeyboardInterrupt):
                print('\nSaved. Resume with --resume.',file=sys.stderr);return 0
            if args.sheet:
                with args.sheet.open('w',encoding='utf8') as stream:q.print(file=stream)
            if q.capabilities['status']=='review_required':return 0
            result=q.judge()
            if result.status=='needs_human_review' and not args.sheet:q.print()
            output(result.to_dict())
        return 0
    except (QuestionnaireError,OSError,json.JSONDecodeError) as error:
        print(f'Error: {error}',file=sys.stderr);return 2


if __name__=='__main__':
    raise SystemExit(main())
