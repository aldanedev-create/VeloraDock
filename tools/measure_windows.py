"""Measure a running VeloraDock process after it has been idle for 30 seconds."""
import argparse
import json
from pathlib import Path
import statistics
import time
import psutil

parser = argparse.ArgumentParser()
parser.add_argument('--pid', required=True, type=int)
parser.add_argument('--seconds', type=int, default=60)
parser.add_argument('--out', type=Path, default=Path('windows-idle.json'))
args = parser.parse_args()
process = psutil.Process(args.pid)
samples = []
for index in range(args.seconds):
    memory = process.memory_info().rss
    # Include WebView2 children; parent memory alone understates footprint.
    children = process.children(recursive=True)
    for child in children:
        try:
            memory += child.memory_info().rss
        except psutil.NoSuchProcess:
            pass
    samples.append(memory / (1024 * 1024))
    time.sleep(1)
result = {'pid':args.pid, 'samples':len(samples), 'median_process_tree_rss_mb':statistics.median(samples),
          'max_process_tree_rss_mb':max(samples), 'note':'Sum of RSS includes shared pages; record OS, app state and clipboard/index settings separately.'}
args.out.write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
