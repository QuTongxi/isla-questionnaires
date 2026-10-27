import copy
import io
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from isla_questionnaires import load_questionnaire, list_questionnaires, restore_session
from isla_questionnaires.catalog import data_directory, digest
from isla_questionnaires.errors import AnswerError, DefinitionError, IncompleteQuestionnaire, IntegrityError, ReviewRequired
from isla_questionnaires.session import Questionnaire
from isla_questionnaires.testing import synthetic_answers, batch_score
from isla_questionnaires.validation import validate_definition


def filled(id, value):
    q=load_questionnaire(id)
    q.submit_answers({i.id:value for i in q.questions()})
    return q


class StandardScores(unittest.TestCase):
    def test_gse_author_wording_and_total(self):
        q=filled('gse',4)
        self.assertEqual(q.judge().scores['self_efficacy']['value'],40)
        self.assertEqual(q._d['items'][2]['text'],'It is easy for me to stick to my aims and accomplish my goals.')
        self.assertEqual(filled('gse',1).judge().scores['self_efficacy']['value'],10)

    def test_swls_anchor_direction(self):
        q=load_questionnaire('swls');opts=q.next_question().options
        self.assertEqual(opts[0],{'value':1,'label':'Strongly disagree'})
        self.assertEqual(opts[-1],{'value':7,'label':'Strongly agree'})
        self.assertEqual(filled('swls',7).judge().scores['swlsscore']['value'],35)

    def test_swls_author_interpretation_boundaries(self):
        for total,label in [(5,'Extremely dissatisfied'),(9,'Extremely dissatisfied'),(10,'Dissatisfied'),
                            (14,'Dissatisfied'),(15,'Slightly dissatisfied'),(19,'Slightly dissatisfied'),
                            (20,'Neutral'),(21,'Slightly satisfied'),(25,'Slightly satisfied'),
                            (26,'Satisfied'),(30,'Satisfied'),(31,'Extremely satisfied'),(35,'Extremely satisfied')]:
            with self.subTest(total=total):
                q=load_questionnaire('swls');extra=total-5
                for item in q.questions():
                    step=min(extra,6);q.submit_answer(item.id,1+step);extra-=step
                score=q.judge().scores['swlsscore']
                self.assertEqual(score['value'],total)
                self.assertEqual(score['interpretation']['label'],label)

    def test_ecrr_separate_dimensions(self):
        s=filled('ecr-r',1).judge().scores
        self.assertAlmostEqual(s['attachment-related-anxiety']['value'],30/18)
        self.assertEqual(s['attachment-related-avoidance']['value'],5)
        self.assertEqual(len(s),2)

    def test_rses_reversal(self):
        q=load_questionnaire('rses')
        q.submit_answers({f'rses{i}':0 if i in {3,5,8,9,10} else 3 for i in range(1,11)})
        self.assertEqual(q.judge().scores['self_esteem']['value'],30)
        self.assertEqual(filled('rses',3).judge().scores['self_esteem']['value'],15)

    def test_lotr_fillers_do_not_change_total(self):
        q=filled('lot-r',0)
        self.assertEqual(q.judge().scores['optimistic']['value'],12)
        q.submit_answers({str(i):4 for i in [2,5,6,8]},replace=True)
        self.assertEqual(q.judge().scores['optimistic']['value'],12)
        self.assertEqual(set(q.audit_definition()['unscored_items']),{'2','5','6','8'})

    def test_erq_two_means_no_reverse(self):
        q=load_questionnaire('erq')
        q.submit_answers({f'erq{i}':7 if i in [1,3,5,7,8,10] else 1 for i in range(1,11)})
        s=q.judge().scores
        self.assertEqual(s['reappraisal']['value'],7)
        self.assertEqual(s['suppression']['value'],1)

    def test_hexaco_official_keys_and_no_footer(self):
        q=filled('hexaco-60',1);s=q.judge().scores
        for key,value in [('honesty-humility',3.4),('emotionality',2.6),('extraversion',2.6),
                          ('agreeableness',2.6),('conscientiousness',3.4),('openness-to-experience',3)]:
            self.assertAlmostEqual(s[key]['value'],value)
        self.assertEqual(len(s),30)
        self.assertEqual(q._d['items'][0]['text'],'I would be quite bored by a visit to an art gallery.')
        self.assertEqual(q._d['items'][-1]['text'],'I’d be tempted to use counterfeit money, if I were sure I could get away with it.')

    def test_crt_units_and_text(self):
        q=load_questionnaire('crt-7')
        q.submit_answers(dict(zip([f'crt-{i}' for i in range(1,8)],[5,5,47,4,29,20,' C '])))
        self.assertEqual(q.judge().scores['correct']['value'],7)
        q.submit_answer('crt-1',0.05,replace=True) # question explicitly asks cents
        self.assertEqual(q.judge().scores['correct']['value'],6)
        q.submit_answer('crt-7','a',replace=True)
        self.assertEqual(q.judge().scores['correct']['value'],5)

    def test_onet_2016_coding_and_order(self):
        q=filled('riasec-mini-ip',4)
        self.assertEqual([x['value'] for x in q.judge().scores.values()],[20]*6)
        texts=[x.text for x in q.questions()]
        self.assertEqual(texts[6],'Repair household appliances')
        self.assertEqual(texts[18],'Drive a truck to deliver packages to offices and homes')
        q=filled('riasec-mini-ip',0);q.submit_answer('1',4,replace=True)
        self.assertEqual(q.judge().scores['R']['value'],4)
        self.assertEqual(q.judge().scores['I']['value'],0)

    def test_pvq_centering_direction(self):
        q=filled('pvq-21',3)
        q.submit_answers({'ipcrtiv':1,'impfree':1},replace=True)
        s=q.judge().scores
        self.assertEqual(s['self_direction']['value'],1)
        self.assertAlmostEqual(s['self_direction-centered']['value'],1-59/21)
        self.assertIsNone(s['self_direction-centered']['range'])

    def test_ess_no_unsupported_composite(self):
        q=filled('ess-institutional-trust',8)
        self.assertEqual(len(q.judge().scores),7)
        self.assertNotIn('total',q.judge().scores)

    def test_other_native_score_baselines(self):
        expected={
            'bfi-44':(1,{'extraversion':2.5,'agreeableness':25/9,'conscientiousness':25/9,'neuroticism':2.5,'openness':1.8}),
            'epq-r':(0,{'extraversion':3,'psychoticism':19,'neuroticism':0,'lying':15}),
            'eis':(1,{'emotionally-intelligent':45}),
            'wleis':(1,{'sea':1,'oea':1,'uoe':1,'roe':1}),
            'ipip-50':(1,{'extraversion':30,'agreeableness':26,'conscientiousness':26,'neuroticism':18,'openness':22}),
            'grit-s':(1,{'perseverance':1,'interest_consistency':5,'total':3}),
            'ie-4':(1,{'internal':1,'external':1}),
        }
        for id,(answer,values) in expected.items():
            with self.subTest(id=id):
                actual=filled(id,answer).judge().scores
                self.assertEqual(set(actual),set(values))
                for key,value in values.items():self.assertAlmostEqual(actual[key]['value'],value)


class SessionBehavior(unittest.TestCase):
    def test_peek_submit_and_resume(self):
        q=load_questionnaire('gse');first=q.next_question()
        self.assertEqual(first,q.next_question())
        q.submit_answer(first.id,3)
        restored=restore_session(q.export_session())
        self.assertEqual(restored.next_question().id,'gse2')
        self.assertEqual(restored.answers,q.answers)

    def test_incomplete_and_invalid_answers(self):
        q=load_questionnaire('gse')
        with self.assertRaises(IncompleteQuestionnaire):q.judge()
        for value in [True,False,'3',0,5,1.5,float('nan'),float('inf'),None]:
            with self.subTest(value=value),self.assertRaises(AnswerError):q.submit_answer('gse1',value)
        with self.assertRaises(AnswerError):q.submit_answer('not-an-item',2)
        self.assertEqual(q.answers,{})

    def test_atomic_bulk_and_audited_revision(self):
        q=load_questionnaire('gse')
        with self.assertRaises(AnswerError):q.submit_answers({'gse1':3,'gse2':100})
        self.assertEqual(q.answers,{})
        q.submit_answer('gse1',3)
        with self.assertRaises(AnswerError):q.submit_answer('gse1',2)
        q.submit_answer('gse1',2,replace=True)
        self.assertEqual(len(q.export_session()['events']),2)
        self.assertEqual(restore_session(q.export_session()).answers,{'gse1':2})

    def test_input_and_output_isolation(self):
        q=load_questionnaire('gse');q.submit_answer('gse1',3)
        answers=q.answers;answers['gse1']=1
        self.assertEqual(q.answers['gse1'],3)
        question=q.next_question();question.options[0]['value']=999
        self.assertEqual(q.next_question().options[0]['value'],1)
        self.assertEqual(load_questionnaire('gse').answers,{})

    def test_no_silent_translation(self):
        with self.assertRaises(DefinitionError):load_questionnaire('gse',language='zh')

    def test_tampering(self):
        q=filled('gse',3);data=q.export_session();data['answers']['gse1']=4
        with self.assertRaises(IntegrityError):restore_session(data)

    def test_malformed_session(self):
        q=filled('gse',3)
        with self.assertRaises(IntegrityError):restore_session({})
        data=filled('gse',2).export_session();data['events'][0].pop('replace')
        data['session_hash']=digest({k:v for k,v in data.items() if k!='session_hash'})
        with self.assertRaises(IntegrityError):restore_session(data)
        # Even updating the outer checksum cannot conceal a broken event chain.
        data=q.export_session();data['events'][0]['value']=4
        data['session_hash']=digest({k:v for k,v in data.items() if k!='session_hash'})
        with self.assertRaises(IntegrityError):restore_session(data)
        data=q.export_session();data['content_hash']='wrong'
        data['session_hash']=digest({k:v for k,v in data.items() if k!='session_hash'})
        with self.assertRaises(IntegrityError):restore_session(data)

    def test_review_gate_and_printable_form(self):
        with self.assertRaises(ReviewRequired):load_questionnaire('scc')
        q=load_questionnaire('scc',allow_review=True);q.submit_answers(synthetic_answers(q))
        with self.assertRaises(ReviewRequired):q.judge()
        self.assertFalse(q.capabilities['local_judge'])
        self.assertEqual(q.audit_definition()['validation']['status'],'review_required')
        stream=io.StringIO();text=q.print(file=stream)
        self.assertIn('Answer: 3',text)
        self.assertIn('自我概念',text)
        self.assertEqual(stream.getvalue(),text+'\n')

    def test_human_review_has_no_invented_verdict(self):
        q=load_questionnaire('reflection-demo');q.submit_answers(synthetic_answers(q))
        self.assertEqual(q.judge().status,'needs_human_review')
        self.assertEqual(q.judge().scores,{})
        self.assertIn('SYNTHETIC',q.print(file=io.StringIO()))

    def test_parameters_required_and_persisted(self):
        with self.assertRaises(DefinitionError):load_questionnaire('srhi',allow_review=True)
        q=load_questionnaire('srhi',allow_review=True,parameters={'behavior':'Walking'})
        self.assertIn('Walking',q.next_question().help)
        restored=restore_session(q.export_session(),allow_review=True)
        self.assertEqual(restored.next_question().help,q.next_question().help)

    def test_reproducible_batch_helpers(self):
        q=load_questionnaire('gse')
        self.assertEqual(synthetic_answers(q,pattern='random',seed=42),synthetic_answers(q,pattern='random',seed=42))
        result=batch_score('gse',[synthetic_answers(q,pattern='min'),synthetic_answers(q,pattern='max')])
        self.assertEqual([r.scores['self_efficacy']['value'] for r in result],[10,40])


class CatalogAndCLI(unittest.TestCase):
    def test_all_bundles_and_score_ranges(self):
        entries=list_questionnaires(include_review=True)
        self.assertEqual(len(entries),37)
        self.assertEqual(sum(e['status']=='available' and e['mode']=='automatic' for e in entries),24)
        for entry in entries:
            with self.subTest(id=entry['id']):
                q=load_questionnaire(entry['id'],allow_review=True,parameters={'behavior':'Walking'} if entry['id']=='srhi' else None)
                self.assertEqual(q.audit_definition()['validation']['items'],entry['items'])
                if q.capabilities['local_judge']:
                    q.submit_answers(synthetic_answers(q,pattern='random',seed=44))
                    for score in q.judge().scores.values():
                        self.assertTrue(math.isfinite(score['value']))
                        if score['range']:self.assertTrue(score['range'][0]<=score['value']<=score['range'][1])
                    self.assertEqual(restore_session(q.export_session()).judge(),q.judge())

    def test_invalid_rule_is_rejected(self):
        q=load_questionnaire('gse');d=copy.deepcopy(q._d);s=copy.deepcopy(q._rules)
        s['dimensions'][0]['terms'][0]['item']='missing'
        with self.assertRaises(DefinitionError):validate_definition(d,s)
        d['items'].append(d['items'][0])
        with self.assertRaises(DefinitionError):validate_definition(d,q._rules)

    def test_modified_definition_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'gse').mkdir()
            (root/'catalog.json').write_bytes((data_directory()/'catalog.json').read_bytes())
            (root/'gse/questionnaire.json').write_text('{}')
            with self.assertRaises(IntegrityError):load_questionnaire('gse',data_root=root)

    def cli(self,*args,input=None):
        return subprocess.run([sys.executable,'-m','isla_questionnaires',*args],input=input,text=True,capture_output=True)

    def test_cli_score_and_errors(self):
        answers=json.dumps(synthetic_answers(load_questionnaire('gse'),pattern='max'))
        r=self.cli('score','gse','-',input=answers)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['scores']['self_efficacy']['value'],40)
        r=self.cli('score','gse','-',input='{}')
        self.assertEqual(r.returncode,2)
        self.assertIn('Unanswered',r.stderr)
        self.assertNotIn('Traceback',r.stderr)

    def test_interactive_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'answers.json')
            r=self.cli('run','gse','--save',path,input='4\n:quit\n')
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(restore_session(path).next_question().id,'gse2')
            r=self.cli('run','gse','--save',path,'--resume',path,input='4\n'*9)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(restore_session(path).judge().scores['self_efficacy']['value'],40)

    def test_resume_restores_required_parameter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'answers.json')
            q=load_questionnaire('srhi',allow_review=True,parameters={'behavior':'Walking'})
            q.export_session(path)
            r=self.cli('run','srhi','--allow-review','--save',path,'--resume',path,input=':quit\n')
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('Walking',r.stdout)


if __name__=='__main__':unittest.main()
