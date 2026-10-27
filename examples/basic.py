"""Run from the installed package: python examples/basic.py."""
from isla_questionnaires import load_questionnaire
from isla_questionnaires.testing import synthetic_answers

questionnaire=load_questionnaire('gse')
print(questionnaire.describe()['instructions'])
answers=synthetic_answers(questionnaire,pattern='max')
while (question:=questionnaire.next_question()) is not None:
    print(question.number,question.text)
    questionnaire.submit_answer(question.id,answers[question.id])
print('Synthetic example:',questionnaire.judge().to_dict())
assert questionnaire.judge().scores['self_efficacy']['value']==40
