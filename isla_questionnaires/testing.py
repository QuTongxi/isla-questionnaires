"""Local reproducible test helpers. Synthetic responses are never human results."""
import random
from .session import load_questionnaire


def synthetic_answers(questionnaire, *, pattern='middle', seed=0):
    """Produce valid fixture input, not an answer key. CRT answers may be wrong."""
    if pattern not in {'min', 'max', 'middle', 'random'}:
        raise ValueError('pattern must be min, max, middle, or random')
    rng = random.Random(seed)
    answers = {}
    for q in questionnaire.questions():
        if q.type == 'text':
            value = 'SYNTHETIC TEST RESPONSE'
        elif q.type == 'choice':
            values = [o['value'] for o in q.options]
            value = {'min':values[0], 'max':values[-1], 'middle':values[len(values)//2],
                     'random':rng.choice(values)}[pattern]
        else:
            lo, hi = q.min if q.min is not None else 0, q.max if q.max is not None else 100
            value = {'min':lo, 'max':hi, 'middle':(lo+hi)/2, 'random':rng.uniform(lo,hi)}[pattern]
            if questionnaire._items[q.id].get('integer'):
                import math
                if math.ceil(lo)>math.floor(hi):
                    raise ValueError('No integer within numeric bounds')
                value=max(math.ceil(lo),min(math.floor(hi),round(value)))
        answers[q.id]=value
    return answers


def score_answers(identifier, answers, **load_options):
    q=load_questionnaire(identifier, **load_options)
    q.submit_answers(answers)
    return q.judge()


def batch_score(identifier, answer_sets, **load_options):
    """Fresh independent session per response set; stop at the first invalid record."""
    return [score_answers(identifier, answers, **load_options) for answers in answer_sets]
