from pathlib import Path
import argparse
import hashlib
import json
import random
import subprocess
import time
from datetime import datetime, timezone
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'pilot20_results.json'
FILES = {
    'cases': ROOT / 'prompt_comparison_pilot20_reviewed.json',
    'protocol': ROOT / 'prompt_comparison_pilot20_protocol.md',
    'original': ROOT / 'end_to_end_q02_no_evidence58.json',
    'focused': ROOT / 'end_to_end_q02_no_evidence58_prompt_v2.json',
}
MODEL = 'qwen3:4b'
OPTIONS = {'temperature': 0, 'seed': 42}
SCHEDULE_SEED = 20261003

def digest(b):
    return hashlib.sha256(b).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def now():
    return datetime.now(timezone.utc).isoformat()

def context(chunks):
    return '\n\n'.join(f"[Page {c['page']}, Chunk {c['chunk_id']}]\n{c['text']}" for c in chunks)

def render(source, case):
    old = context(source['retrieved_chunks'])
    prompt = source['prompt']
    if prompt.count(old) != 1 or prompt.count(source['question_ar']) != 1:
        raise ValueError('Source prompt cannot be replaced unambiguously.')
    prompt = prompt.replace(old, context(case['context']), 1)
    return prompt.replace(source['question_ar'], case['question_ar'], 1)

def save(result):
    temp = OUT.with_suffix('.json.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(OUT)

def git_commit():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()

def metadata():
    # Ollama must use its default local endpoint for this experiment.
    with urlopen('http://127.0.0.1:11434/api/version', timeout=10) as response:
        version = json.load(response)
    with urlopen('http://127.0.0.1:11434/api/tags', timeout=10) as response:
        tags = json.load(response)
    item = next((m for m in tags['models'] if m.get('name') == MODEL or m.get('model') == MODEL), None)
    if item is None:
        raise RuntimeError(f'{MODEL} is not installed locally.')
    return {'ollama_version': version['version'], 'model_digest': item['digest']}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    for p in FILES.values():
        if not p.is_file():
            raise FileNotFoundError(p)
    data = read(FILES['cases'])
    cases = data['cases']
    if len(cases) != 20 or len({c['id'] for c in cases}) != 20:
        raise ValueError('Expected 20 unique cases.')
    sources = {v: read(FILES[v]) for v in ('original', 'focused')}
    rng = random.Random(SCHEDULE_SEED)
    schedule = []
    for case in cases:
        variants = ['original', 'focused']
        rng.shuffle(variants)
        for variant in variants:
            prompt = render(sources[variant], case)
            schedule.append({'case_id': case['id'], 'variant': variant,
                             'prompt': prompt, 'prompt_sha256': digest(prompt.encode())})
    inputs = {name: digest(path.read_bytes()) for name, path in FILES.items()}
    if args.dry_run:
        print('Validated 20 cases and 40 prompts. No generation performed.')
        for condition in ('full', 'partial', 'none'):
            print(condition, sum(c['context_condition'] == condition for c in cases))
        return
    import ollama
    client = ollama.Client(host='http://127.0.0.1:11434')
    meta = metadata()
    show = client.show(MODEL).model_dump(mode='json')
    frozen = {'input_sha256': inputs, 'model': MODEL, 'options': OPTIONS,
              'schedule_seed': SCHEDULE_SEED, 'runtime': meta,
              'model_show_sha256': digest(json.dumps(show, sort_keys=True).encode())}
    if OUT.exists():
        result = read(OUT)
        if result['frozen_configuration'] != frozen:
            raise RuntimeError('Inputs, model or runtime changed. Existing experiment cannot be resumed.')
    else:
        result = {'created_at': now(), 'git_commit_at_start': git_commit(),
                  'frozen_configuration': frozen, 'model_show': show,
                  'scope': 'Controlled-context prompt comparison; human scoring pending.',
                  'schedule': schedule, 'answers': [], 'errors': []}
        save(result)
    completed = {(a['case_id'], a['variant']) for a in result['answers']}
    by_id = {c['id']: c for c in cases}
    try:
        for job in schedule:
            key = (job['case_id'], job['variant'])
            if key in completed:
                continue
            print(f"[{len(completed)+1}/40] {key[0]} {key[1]}", flush=True)
            start = time.monotonic()
            response = client.chat(model=MODEL, messages=[{'role': 'user', 'content': job['prompt']}], options=OPTIONS)
            raw = response.model_dump(mode='json')
            case = by_id[job['case_id']]
            result['answers'].append({**job, 'context_condition': case['context_condition'],
                                      'question_ar': case['question_ar'], 'context': case['context'],
                                      'answer': response.message.content, 'raw_response': raw,
                                      'completed_at': now(), 'elapsed_seconds': time.monotonic()-start})
            save(result)
            completed.add(key)
    except KeyboardInterrupt:
        print('\nStopped. Completed answers are saved; rerun to resume.')
        return
    except Exception as exc:
        result['errors'].append({'at': now(), 'error': str(exc)})
        save(result)
        raise
    result['generation_completed_at'] = now()
    save(result)
    print(f'Saved {len(completed)}/40 answers to {OUT.name}. Human scoring pending.')

if __name__ == '__main__':
    main()
