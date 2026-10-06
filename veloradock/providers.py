"""Search providers return data; searching never executes a command."""
import time
from pathlib import Path

from .calculations import calculate, conversion


def item(identifier, title, subtitle, kind, value="", confirm=False):
    return dict(id=identifier, title=title, subtitle=subtitle, kind=kind, value=value, confirm=confirm)

class Search:
    def __init__(self, store, clipboard):
        self.store = store
        self.clipboard = clipboard
        self.last_duration_ms = 0

    def query(self, query: str):
        started = time.perf_counter()
        query = query.strip()[:200]
        results = []
        mode = "all"
        for prefix, name in [("app ", "apps"), ("file ", "files"), ("run ", "actions"), ("clip ", "clips")]:
            if query.lower().startswith(prefix):
                mode, query = name, query[len(prefix):]
                break
        if mode == "all":
            try:
                answer = conversion(query)
                if answer:
                    results.append(item("copy:" + answer, answer, "Unit conversion · Enter to copy", "copy", answer))
                if query.startswith("="):
                    answer = f"{calculate(query[1:]):.12g}"
                    results.append(item("copy:" + answer, answer, "Calculator · Enter to copy", "copy", answer))
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError):
                pass
        folded = query.casefold()
        if mode in {"all", "apps"}:
            rows = self.store.rows("SELECT * FROM apps WHERE instr(lower(name),?)>0 ORDER BY name LIMIT 15", (folded,))
            results.extend(item(f"app:{r['id']}", r['name'], r['path'], "app") for r in rows)
        if mode in {"all", "files"} and query:
            rows = self.store.rows("SELECT * FROM files WHERE instr(folded,?)>0 ORDER BY length(name),name LIMIT 20", (folded,))
            results.extend(item(f"file:{r['id']}", r['name'], r['path'], "file") for r in rows)
        if mode in {"all", "actions"}:
            rows = self.store.rows("SELECT * FROM actions ORDER BY favorite DESC,name")
            for row in rows:
                if folded in (row['name'] + ' ' + row['keyword']).casefold():
                    results.append(item(f"action:{row['id']}", row['name'], f"Registered action · {row['path']}", "action", confirm=True))
        if mode == "clips":
            for clip in self.clipboard.list():
                if folded in clip['text'].casefold():
                    results.append(item(f"clip:{clip['id']}", clip['text'][:100], "Clipboard · Enter to copy", "clip"))
        if mode == "all":
            import json
            for row in self.store.rows("SELECT manifest FROM extensions ORDER BY id"):
                manifest = json.loads(row['manifest'])
                for entry in manifest['entries']:
                    if folded in (entry['title'] + ' ' + entry['keyword']).casefold():
                        results.append(item(f"extension:{manifest['id']}:{entry['id']}", entry['title'], manifest['name'], "extension", confirm=entry['kind'] == 'action'))
        self.last_duration_ms = (time.perf_counter() - started) * 1000
        return dict(items=results[:40], elapsed_ms=round(self.last_duration_ms, 3))


def index_folder(store, path: str):
    if not path.strip():
        raise ValueError("Enter a folder path or use Browse")
    root = Path(path).expanduser().resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Choose a real folder")
    if root == store.directory or store.directory.is_relative_to(root):
        raise ValueError("Do not index the app data folder or its parents")
    store.execute("INSERT OR IGNORE INTO roots(path) VALUES (?)", (str(root),))
    identifier = store.rows("SELECT id FROM roots WHERE path=?", (str(root),))[0]['id']
    import os
    entries, skipped = [], 0
    def inaccessible(error):
        nonlocal skipped
        skipped += 1
    for directory, folders, files in os.walk(root, followlinks=False, onerror=inaccessible):
        folders[:] = [name for name in folders if not name.startswith('.') and not Path(directory, name).is_symlink() and not getattr(Path(directory, name), 'is_junction', lambda: False)()]
        for name in files:
            candidate = Path(directory, name)
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                entries.append((identifier, str(candidate), name, name.casefold()))
            except OSError:
                skipped += 1
            if len(entries) >= 50000:
                break
        if len(entries) >= 50000:
            break
    with store.lock, store.connect() as connection:
        connection.execute("DELETE FROM files WHERE root_id=?", (identifier,))
        connection.executemany("INSERT OR IGNORE INTO files(root_id,path,name,folded) VALUES (?,?,?,?)", entries)
    return dict(count=len(entries), skipped=skipped, truncated=len(entries) >= 50000)


def index_apps(store):
    import os
    paths = [Path(os.environ.get('PROGRAMDATA', '')) / 'Microsoft/Windows/Start Menu/Programs',
             Path(os.environ.get('APPDATA', '')) / 'Microsoft/Windows/Start Menu/Programs']
    entries = []
    if os.name == 'nt':
        for root in paths:
            if root.exists():
                for candidate in root.rglob('*.lnk'):
                    if candidate.is_file() and not candidate.is_symlink():
                        entries.append((str(candidate), candidate.stem))
    with store.connect() as connection:
        connection.execute("DELETE FROM apps")
        connection.executemany("INSERT OR IGNORE INTO apps(path,name) VALUES (?,?)", entries)
    return len(entries)
