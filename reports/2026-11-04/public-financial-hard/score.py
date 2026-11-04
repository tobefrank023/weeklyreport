"""Check manual semantic adjudication, then compute diagnostic completion metrics."""
from decimal import Decimal
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
tp=ROOT/'private/ground_truth.json';gp=ROOT/'manual_grading.json'
truth={t['id']:t for t in json.loads(tp.read_text())}
manual=json.loads(gp.read_text())
assert len(manual['items'])==10


def amount(value):
    text=value.replace(',','').replace(' ','').strip()
    if text.startswith('(') and text.endswith(')'):text='-'+text[1:-1]
    return Decimal(text)


def equivalent(pred,expected,kind):
    if kind=='amount':return amount(pred)==amount(expected)
    if kind=='unit':
        token='billions' if 'billions' in expected else 'millions'
        return token in pred.casefold() and ('millions' if token=='billions' else 'billions') not in pred.casefold()
    if kind=='year':
        year=re.findall(r'20\d\d',expected)
        return len(year)==1 and re.findall(r'20\d\d',pred).count(year[0])==1
    return pred.strip()==expected.strip()


items=[];results=[]
for grade in manual['items']:
    qid=grade['id'];t=truth[qid];rp=ROOT/'runs'/qid/'result.json';result=json.loads(rp.read_text())
    assert result['status']=='completed' and result['turn_completed_count']==1
    assert result['tool_events']==[]
    answer=result['answer'];matched=expected=extras=0
    if t['kind']=='single':
        full=(answer['decision']=='suspicious' and grade['single_supported']) if t['introduced_content_edit'] else (answer['decision']=='no_clear_evidence' and grade['control_correct'])
        score=10.0 if full else 0.0
    elif t['introduced_content_edit']:
        bykey={x['key']:x for x in t['expected_changes']};used=set();seen=set()
        for match in grade['matches']:
            index,key=match['prediction_index'],match['truth_field']
            assert index not in used and key not in seen
            pred,gold=answer['changes'][index],bykey[key]
            assert equivalent(pred['before'],gold['before'],gold['kind']),(qid,index,'before',pred,gold)
            assert equivalent(pred['after'],gold['after'],gold['kind']),(qid,index,'after',pred,gold)
            if gold['kind']=='year':
                # A model may quote the full statement date, including an unchanged comparative year.
                before_years=Counter(re.findall(r'20\d\d',pred['before']))
                after_years=Counter(re.findall(r'20\d\d',pred['after']))
                before_years.subtract(re.findall(r'20\d\d',gold['before']))
                before_years.update(re.findall(r'20\d\d',gold['after']))
                assert +before_years==+after_years,(qid,index,'year context')
            assert pred['page_a']==gold['page_a'] and pred['page_b']==gold['page_b'],(qid,index,'page')
            # Semantic row, column and repeated-position binding is independently documented by the manual adjudication.
            used.add(index);seen.add(key)
        matched,expected=len(seen),len(bykey);extras=len(answer['changes'])-len(used)
        assert extras==grade['extra_claims']
        score=10*matched/expected;full=matched==expected and extras==0
    else:
        extras=len(answer['changes']);full=extras==0 and grade['control_correct'];score=10.0 if full else 0.0
    items.append({'id':qid,'kind':t['kind'],'introduced_content_edit':t['introduced_content_edit'],
          'score':score,'maximum':10,'fully_completed':full,'verdict':grade['verdict'],'reason':grade['reason'],
          'paired_matched_fields':matched,'paired_expected_fields':expected,'paired_extra_claims':extras,
          'wrong_binding_predictions':grade.get('wrong_binding_predictions',0),
          'result_sha256':hashlib.sha256(rp.read_bytes()).hexdigest()})
    results.append(result)

single=[x for x in items if x['kind']=='single'];paired=[x for x in items if x['kind']=='paired']
matched=sum(x['paired_matched_fields'] for x in paired);expected=sum(x['paired_expected_fields'] for x in paired)
extra=sum(x['paired_extra_claims'] for x in paired)
usage={}
for r in results:
    for u in r['usage_per_turn']:
        for k,v in u.items():
            if isinstance(v,(int,float)):usage[k]=usage.get(k,0)+v
summary={'questions':10,'completed_valid_answers':10,'content_completion_score':round(sum(x['score'] for x in items),2),
  'fully_completed_questions':sum(x['fully_completed'] for x in items),
  'single_edited_supported':sum(x['fully_completed'] for x in single if x['introduced_content_edit']),
  'single_controls_correct':sum(x['fully_completed'] for x in single if not x['introduced_content_edit']),
  'single_control_false_alarms':sum(r['answer'].get('decision')=='suspicious' for r in results if r['id'] in ('H05','H06')),
  'single_abstentions':sum(r['answer'].get('decision')=='insufficient' for r in results),
  'paired_correct_fields':matched,'paired_expected_fields':expected,'paired_field_recall':matched/expected,
  'paired_extra_claims':extra,'paired_wrong_binding_predictions':sum(x['wrong_binding_predictions'] for x in paired),
  'paired_field_precision':matched/(matched+extra) if matched+extra else 0,
  'paired_control_correct':next(x['fully_completed'] for x in items if x['id']=='H08'),
  'single_content_completion_percent':sum(x['score'] for x in single)*2,
  'paired_content_completion_percent':sum(x['score'] for x in paired)*2,
  'tool_event_count':sum(len(r['tool_events']) for r in results),
  'turn_completed_count':sum(r['turn_completed_count'] for r in results),
  'agent_message_count':sum(r['agent_message_count'] for r in results),
  'reported_usage':usage,'model':'gpt-6-luna','effort':'medium','cli_version':'0.166.0',
  'source_documents':2,'source_publishers':1,'base_pages':7,
  'score_scope':'frozen adaptive development difficulty experiment; no independent expert gold, box score or held-out claim',
  'previous_public_pilot_score':95.0,'causal_comparison_established':False}
evaluation={'summary':summary,'items':items,'protocol':'grading_protocol.json',
            'truth_sha256':hashlib.sha256(tp.read_bytes()).hexdigest(),'manual_grading_sha256':hashlib.sha256(gp.read_bytes()).hexdigest()}
(ROOT/'evaluation.json').write_text(json.dumps(evaluation,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
