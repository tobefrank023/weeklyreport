import hashlib
import json
from pathlib import Path
from decimal import Decimal

ROOT = Path(__file__).resolve().parent
truth_path = ROOT/'private/ground_truth.json'
grading_path = ROOT/'manual_grading.json'
truth = {x['id']:x for x in json.loads(truth_path.read_text())}
manual = json.loads(grading_path.read_text())
items, results = [], []


def number(value):
    return Decimal(value.replace(',','').strip())


for grade in manual['items']:
    qid = grade['id']
    t = truth[qid]
    result_path = ROOT/'runs'/qid/'result.json'
    result = json.loads(result_path.read_text())
    assert result['status']=='completed' and result['turn_completed_count']==1
    assert not result['tool_events']
    answer = result['answer']
    if t['kind']=='single':
        if t['introduced_content_edit']:
            full = answer['decision']=='suspicious' and grade['single_supported']
        else:
            full = answer['decision']=='no_clear_evidence' and grade['control_correct']
        score = 10.0 if full else 0.0
        matched, expected, extras = 0, 0, 0
    elif t['introduced_content_edit']:
        matched_ids, used = set(), set()
        by_field = {x['id']:x for x in t['expected_changes']}
        for match in grade['matches']:
            index, field = match['prediction_index'], match['truth_field']
            assert index not in used and field not in matched_ids
            pred, gold = answer['changes'][index], by_field[field]
            assert number(pred['before'])==number(gold['before'])
            assert number(pred['after'])==number(gold['after'])
            # Row/column semantics are documented in manual_grading.json, not inferred from numbers alone.
            used.add(index); matched_ids.add(field)
        matched, expected = len(matched_ids), len(t['expected_changes'])
        extras = len(answer['changes'])-len(used)
        assert extras==grade['extra_claims']
        score = 10.0*matched/expected
        full = matched==expected and extras==0
    else:
        full = not answer['changes'] and grade['control_correct']
        score = 10.0 if full else 0.0
        matched, expected, extras = 0, 0, len(answer['changes'])
    item = {'id': qid,'kind': t['kind'],'introduced_content_edit': t['introduced_content_edit'],
            'score':score,'maximum':10,'verdict':grade['verdict'],
            'fully_completed':full,'paired_matched_fields':matched,'paired_expected_fields':expected,
            'paired_extra_claims':extras,'reason':grade['reason'],
            'answer_result_sha256':hashlib.sha256(result_path.read_bytes()).hexdigest()}
    items.append(item);results.append(result)

single = [x for x in items if x['kind']=='single']
paired = [x for x in items if x['kind']=='paired']
correct_fields = sum(x['paired_matched_fields'] for x in paired)
expected_fields = sum(x['paired_expected_fields'] for x in paired)
extra = sum(x['paired_extra_claims'] for x in paired)
usage = {}
for r in results:
    for u in r['usage_per_turn']:
        for k,v in u.items():
            if isinstance(v,(int,float)):usage[k]=usage.get(k,0)+v
summary = {
    'questions':len(items),'completed_valid_answers':len(results),
    'content_completion_score':round(sum(x['score'] for x in items),2),
    'fully_completed_questions':sum(x['fully_completed'] for x in items),
    'single_edited_supported':sum(x['fully_completed'] for x in single if x['introduced_content_edit']),
    'single_controls_correct':sum(x['fully_completed'] for x in single if not x['introduced_content_edit']),
    'single_control_false_alarms':sum(r['answer']['decision']=='suspicious' for r in results if r['id'] in ('P02','P07')),
    'single_abstentions':sum(r['answer'].get('decision')=='insufficient' for r in results),
    'paired_correct_fields':correct_fields,'paired_expected_fields':expected_fields,
    'paired_field_recall':round(correct_fields/expected_fields,6),
    'paired_extra_claims':extra,'paired_field_precision':round(correct_fields/(correct_fields+extra),6),
    'paired_control_correct':next(x['fully_completed'] for x in items if x['id']=='P10'),
    'tool_event_count':sum(len(r['tool_events']) for r in results),
    'turn_completed_count':sum(r['turn_completed_count'] for r in results),
    'agent_message_count':sum(r['agent_message_count'] for r in results),
    'reported_usage':usage,'model':'gpt-6-luna','effort':'medium','cli_version':'0.166.0',
    'source_documents':2,'source_publishers':1,'base_pages':4,
    'score_scope':'fixed diagnostic content completion; no box score; not independent expert review or formal held-out benchmark',
}
evaluation = {'summary':summary,'items':items,
              'truth_sha256':hashlib.sha256(truth_path.read_bytes()).hexdigest(),
              'manual_grading_sha256':hashlib.sha256(grading_path.read_bytes()).hexdigest(),
              'protocol':'grading_protocol.json'}
(ROOT/'evaluation.json').write_text(json.dumps(evaluation,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
