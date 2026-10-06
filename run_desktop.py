"""Desktop entry point with diagnostics for console-free Windows builds."""
import json
import os
from pathlib import Path
import sys
import traceback


def argument_path(name):
    if name in sys.argv:
        position = sys.argv.index(name) + 1
        if position < len(sys.argv):
            return Path(sys.argv[position])
    return None


def start():
    result = argument_path('--smoke-result')
    directory = argument_path('--data-dir') or Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'VeloraDock'
    directory.mkdir(parents=True, exist_ok=True)
    # PyInstaller GUI builds have no stdout/stderr. Uvicorn formatters and
    # native dependency diagnostics still require writable stream objects.
    if sys.stdout is None or sys.stderr is None:
        output = (directory / 'startup.log').open('a', encoding='utf-8', buffering=1)
        sys.stdout = output
        sys.stderr = output
    try:
        from veloradock.desktop import main
        main()
    except Exception:
        error = traceback.format_exc()
        print(error, file=sys.stderr, flush=True)
        if result:
            result.parent.mkdir(parents=True, exist_ok=True)
            result.write_text(json.dumps({'ok': False, 'error': error}), encoding='utf-8')
        raise SystemExit(1)


if __name__ == '__main__':
    start()
