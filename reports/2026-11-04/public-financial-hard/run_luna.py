"""One attempt per question, fresh sessions; no answer key given to solver."""
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
MODEL = 'gpt-6-luna'
TIMEOUT = 240


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')


def run(q):
    output = ROOT/'runs'/q['id']
    output.mkdir(parents=True, exist_ok=True)
    if (output/'result.json').exists():
        return json.loads((output/'result.json').read_text())
    prompt = (ROOT/q['directory']/'prompt.txt').read_bytes()
    assert hashlib.sha256(prompt).hexdigest() == q['prompt_sha256']
    args = [os.environ.get('CODEX_BIN', 'codex'),'exec','--ignore-user-config','--ephemeral',
            '--skip-git-repo-check','--model',MODEL,'--sandbox','read-only',
            '--cd',str(ROOT/q['directory']),'-c','model_reasoning_effort="medium"',
            '-c','web_search="disabled"','-c','features.shell_tool=false',
            '-c','features.shell_snapshot=false','-c','features.view_image=false',
            '-c','features.multi_agent=false','-c','history.persistence="none"',
            '-c','log_dir='+json.dumps(str(output/'logs')),
            '-c','sqlite_home='+json.dumps(str(output/'state')),
            '--color','never','--json','--output-schema',str(ROOT/q['schema']),
            '--output-last-message',str(output/'answer.txt')]
    for image in q['images']:
        path = ROOT/image['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == image['sha256']
        args.extend(['--image',str(path)])
    args.append('-')
    save(output/'request_manifest.json', {'id': q['id'],'model': MODEL,'effort':'medium',
         'cli_version': '0.166.0', 'prompt_sha256': q['prompt_sha256'], 'images': q['images'],
         'timeout_seconds': TIMEOUT,'attempt':1,'args_without_prompt':args,
         'no_answer_key_supplied': True,'session':'fresh ephemeral',
         'declared_disabled_tools':['shell','web_search','view_image','multi_agent'],
         'response_bound':'JSON schema: max 5 evidence items or 16 changes; no CLI hard output-token cap'})
    start = time.monotonic()
    with (output/'events.jsonl').open('wb') as stdout, (output/'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,
                                   env=os.environ.copy(),start_new_session=True)
        try:
            process.communicate(prompt,timeout=TIMEOUT)
            status = 'completed' if process.returncode == 0 else 'process_error'
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL); process.wait()
            status = 'timeout'
    events, invalid_lines = [], 0
    for line in (output/'events.jsonl').read_text(errors='replace').splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: invalid_lines += 1
    answer = None
    if (output/'answer.txt').exists():
        try: answer = json.loads((output/'answer.txt').read_text())
        except json.JSONDecodeError:
            if status == 'completed': status = 'malformed_answer'
    elif status == 'completed': status = 'missing_answer'
    usages = [e.get('usage',{}) for e in events if e.get('type')=='turn.completed']
    items = [e.get('item',{}) for e in events if e.get('type')=='item.completed']
    tools = [i for i in items if i.get('type') in ('command_execution','mcp_tool_call','web_search','image_view','tool_call','collab_tool_call')]
    result = {'id': q['id'],'kind': q['kind'],'model': MODEL,'effort':'medium','status': status,
              'exit_code':process.returncode,'elapsed_seconds':round(time.monotonic()-start,3),
              'answer': answer,'usage_per_turn': usages,'tool_events':tools,
              'turn_started_count':sum(e.get('type')=='turn.started' for e in events),
              'turn_completed_count':len(usages),'agent_message_count':sum(i.get('type')=='agent_message' for i in items),
              'unparsed_event_lines':invalid_lines,
              'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(output/'result.json',result)
    print(json.dumps({k:result[k] for k in ('id','status','elapsed_seconds','usage_per_turn','turn_completed_count')},ensure_ascii=False),flush=True)
    return result


questions = json.loads((ROOT/'questions_manifest.json').read_text())['questions']
if sys.argv[1] == 'canary':
    run(questions[0])
elif sys.argv[1] == 'remaining':
    first = json.loads((ROOT/'runs/H01/result.json').read_text())
    assert first['status']=='completed' and isinstance(first['answer'],dict), 'Canary failed; do not expand.'
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(run,questions[1:]))
else:
    raise SystemExit('Use canary or remaining')
