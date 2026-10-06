"""Explicit local actions and declarative extensions. No shell command evaluation."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ALLOWED = {'.ps1', '.py', '.exe'}

def register_action(store, payload):
    name = str(payload.get('name', '')).strip()
    keyword = str(payload.get('keyword', '')).strip()
    path = Path(str(payload.get('path', ''))).expanduser().resolve(strict=True)
    args = payload.get('args', [])
    if not name or len(name) > 100 or not re.fullmatch(r'[a-zA-Z0-9_-]{1,30}', keyword):
        raise ValueError('Enter a name and a simple keyword')
    if not path.is_file() or path.suffix.lower() not in ALLOWED or path.is_symlink():
        raise ValueError('Choose a local .ps1, .py or .exe file')
    if not isinstance(args, list) or len(args) > 30 or any(not isinstance(x, str) or len(x) > 1000 for x in args):
        raise ValueError('Arguments must be a JSON array of at most 30 strings')
    return store.execute('INSERT INTO actions(name,keyword,path,args) VALUES (?,?,?,?)',
                         (name, keyword, str(path), json.dumps(args)))

def action_command(row):
    path = Path(row['path'])
    if not path.is_file() or path.suffix.lower() not in ALLOWED:
        raise ValueError('Registered file is unavailable')
    if path.suffix.lower() == '.ps1':
        if os.name != 'nt':
            raise ValueError('PowerShell actions require Windows')
        prefix = ['powershell.exe', '-NoProfile', '-File']
    elif path.suffix.lower() == '.py':
        # Frozen Python cannot serve as a general Python interpreter.
        if getattr(sys, 'frozen', False):
            prefix = ['py', '-3']
        else:
            prefix = [sys.executable]
    else:
        prefix = []
    return prefix + [str(path)] + json.loads(row['args'])

def run_action(row):
    process = subprocess.Popen(action_command(row), cwd=str(Path(row['path']).parent), shell=False)
    return dict(pid=process.pid, message='Action started. Its interpreter may show a separate window.')

def validate_manifest(manifest, store):
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1:
        raise ValueError('Use extension schema_version 1')
    if not re.fullmatch(r'[a-z][a-z0-9_-]{2,40}', str(manifest.get('id', ''))):
        raise ValueError('Invalid extension ID')
    if not isinstance(manifest.get('name'), str) or not 1 <= len(manifest['name']) <= 100:
        raise ValueError('Invalid extension name')
    entries = manifest.get('entries')
    if not isinstance(entries, list) or len(entries) > 30:
        raise ValueError('Use at most 30 entries')
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get('kind') not in {'copy', 'url', 'action'}:
            raise ValueError('Entries support copy, url or action')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,40}', str(entry.get('id', ''))) or entry['id'] in seen:
            raise ValueError('Entry IDs must be valid and unique')
        seen.add(entry['id'])
        for key in ['title', 'keyword', 'value']:
            if not isinstance(entry.get(key), str) or not 1 <= len(entry[key]) <= 2000:
                raise ValueError(f'Invalid entry {key}')
        if entry['kind'] == 'url':
            from urllib.parse import urlsplit
            url = urlsplit(entry['value'])
            if url.scheme != 'https' or not url.hostname or url.username:
                raise ValueError('Bookmarks must use HTTPS without embedded credentials')
        if entry['kind'] == 'action':
            if not entry['value'].isdigit() or not store.rows('SELECT id FROM actions WHERE id=?', (int(entry['value']),)):
                raise ValueError('An extension action must reference an already registered action')
    return manifest
