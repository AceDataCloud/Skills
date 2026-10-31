#!/usr/bin/env python3
"""One fixed media submission per private state file; resume the original task."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

ORIGIN = 'https://api.acedata.cloud'
RECIPES = {
    'video': ('wan', '/videos', {'model': 'wan3.0-video', 'duration': 5, 'resolution': '720P', 'ratio': '16:9', 'audio': False}),
    'image': ('seedream', '/images', {'model': 'doubao-seedream-5-0-lite-260128', 'size': '2K', 'sequential_image_generation': 'disabled', 'response_format': 'url'}),
    'audio': ('fish', '/tts', {'reference_id': 'd7900c21663f485ab63ebdb7e5905036', 'format': 'mp3'}),
}


def call(path, payload, token, headers=None):
    request = urllib.request.Request(ORIGIN + path, data=json.dumps(payload).encode(), headers={
        'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as error:
        # Do not expose request headers or provider response bodies containing secrets.
        raise RuntimeError(f'API returned HTTP {error.code}; preserve the original state file.') from None
    if len(raw) > 4 * 1024 * 1024:
        raise RuntimeError('API response exceeds the result limit.')
    return json.loads(raw)


def save(path, state):
    temporary = path.with_suffix(path.suffix + '.tmp')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(state, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def asset_urls(value):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'url', 'video_url', 'image_url', 'audio_url'} and isinstance(child, str) and child.startswith('https://'):
                found.append(child)
            elif isinstance(child, (dict, list)):
                found.extend(asset_urls(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(asset_urls(child))
    return list(dict.fromkeys(found))


def terminal(value):
    # /tasks returns a persisted task envelope; its result lives in response.
    result = value.get('response', value)
    if isinstance(result, dict):
        if result.get('success') is False or result.get('error'):
            return {'status': 'failed', 'error': result.get('error') or 'Media generation failed.'}
        urls = asset_urls(result)
        if urls:
            return {'status': 'completed', 'urls': urls}
    if value.get('finished_at'):
        return {'status': 'failed', 'error': 'The finished task contains no deliverable URL.'}
    return None


def run(kind, prompt, path, *, api=call, token=None, timeout=480, pause=time.sleep):
    if kind not in RECIPES or not prompt.strip() or len(prompt) > (300 if kind == 'audio' else 1200):
        raise ValueError('Choose video/image/audio and a bounded nonempty brief (audio: 300 characters; others: 1200).')
    token = token or os.environ.get('ACEDATACLOUD_API_TOKEN')
    if not token:
        raise ValueError('Set ACEDATACLOUD_API_TOKEN in the process environment.')
    family, endpoint, fixed = RECIPES[kind]
    payload = {**fixed, 'async': True, 'text' if kind == 'audio' else 'prompt': prompt}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        state = json.loads(path.read_text())
        if state['fingerprint'] != fingerprint:
            raise ValueError('This state file belongs to another request. Do not overwrite it.')
    else:
        state = {'version': 1, 'kind': kind, 'fingerprint': fingerprint, 'phase': 'submitting'}
        # Persist submission intent before network I/O; interrupted dispatch must not resubmit.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(state, stream)
            stream.flush()
            os.fsync(stream.fileno())
        created = api('/' + family + endpoint, payload, token, {'model': 's2-pro'} if kind == 'audio' else None)
        state['task_id'] = created.get('task_id') or created.get('id')
        state['result'] = terminal(created)
        state['phase'] = 'terminal' if state['result'] else 'polling'
        save(path, state)
        print(json.dumps({'task_id': state['task_id'], 'phase': state['phase']}), flush=True)
    if state.get('result'):
        return {**state['result'], 'task_id': state.get('task_id')}
    if not state.get('task_id'):
        raise RuntimeError('Submission outcome is unknown. Reconcile this request; never submit it again automatically.')
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = api('/' + family + '/tasks', {'id': state['task_id']}, token)
        result = terminal(value)
        if result:
            state.update(phase='terminal', result=result)
            save(path, state)
            return {**result, 'task_id': state['task_id']}
        pause(10)
    return {'status': 'pending', 'task_id': state['task_id'], 'state_file': str(path), 'message': 'Resume with this same state file; do not generate again.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=RECIPES)
    parser.add_argument('--state', required=True, help='Private persistent JSON path unique to this customer task; reuse it for recovery.')
    parser.add_argument('--prompt', required=True)
    args = parser.parse_args()
    try:
        result = run(args.kind, args.prompt, args.state)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0 if result['status'] in {'completed', 'pending'} else 2
    except Exception as error:
        # Errors contain only bounded local descriptions, never credentials.
        print(json.dumps({'status': 'error', 'message': str(error), 'state_file': args.state}), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
