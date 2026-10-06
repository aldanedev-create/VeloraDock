"""Reproducible filename-search benchmark; native timings come from the desktop app."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import tempfile
import time

from veloradock.clipboard import Clipboard
from veloradock.providers import Search
from veloradock.store import Store

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', type=int, default=10000)
    parser.add_argument('--out', type=Path, default=Path('benchmark-results.json'))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory))
        with store.connect() as connection:
            connection.executemany('INSERT INTO files(root_id,path,name,folded) VALUES (?,?,?,?)',
                ((1, f'/fixture/document-{i}.txt', f'document-{i}.txt', f'document-{i}.txt') for i in range(args.files)))
        search = Search(store, Clipboard(store))
        samples = []
        for iteration in range(120):
            started = time.perf_counter()
            search.query(f'file document-{iteration % 10}')
            elapsed = (time.perf_counter() - started) * 1000
            if iteration >= 20:
                samples.append(elapsed)
        samples.sort()
        result = {'platform': platform.platform(), 'python': platform.python_version(),
                  'fixture_files':args.files,'samples':len(samples),'warmup':20,
                  'median_ms':statistics.median(samples),'p95_ms':samples[int(len(samples)*.95)-1],
                  'max_ms':max(samples), 'scope':'Warm Python provider + SQLite search; excludes UI/network/native hotkey',
                  'hotkey_to_ui':'Not measured on this host','windows_idle_memory':'Not measured on this host'}
        args.out.write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
