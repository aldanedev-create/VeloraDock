"""Explicit operations exposed to the local pywebview interface."""
import json
import os
from pathlib import Path
import time
import webbrowser

from .actions import run_action
from .windows import copy_text

class Bridge:
    def __init__(self, app):
        self._app = app
        self._window = None
        self._started = None
        self._services = None

    def choose_folder(self):
        import webview
        paths = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return paths[0] if paths else None

    def choose_action(self):
        import webview
        paths = self._window.create_file_dialog(webview.FileDialog.OPEN, file_types=('Local actions (*.ps1;*.py;*.exe)',))
        return paths[0] if paths else None

    def reveal_file(self, identifier):
        try:
            kind, value = identifier.split(':', 1)
            if kind != 'file':
                raise ValueError('Choose a file result')
            rows = self._app.store.rows('SELECT files.path, roots.path AS root FROM files JOIN roots ON roots.id=files.root_id WHERE files.id=?', (int(value),))
            if not rows or not Path(rows[0]['path']).is_file():
                raise ValueError('File is unavailable')
            if not Path(rows[0]['path']).resolve().is_relative_to(Path(rows[0]['root']).resolve()):
                raise ValueError('File is outside the registered folder')
            import subprocess
            subprocess.Popen(['explorer.exe', '/select,', rows[0]['path']], shell=False)
            return {'message': 'Opened its folder.'}
        except (ValueError, OSError) as error:
            return {'error': str(error)}

    def hide(self):
        self._window.evaluate_js("window.veloraSceneVisibility && window.veloraSceneVisibility(false)")
        self._window.hide()

    def set_hotkey(self, value):
        if value not in {'Ctrl+Alt+Space', 'Ctrl+Shift+Space', 'Alt+Space'}:
            return {'error': 'Unsupported shortcut'}
        self._app.store.set_setting('hotkey', value)
        return {'message': 'Saved. Restart VeloraDock to apply the shortcut.'}

    def diagnostics(self):
        return {'hotkey_error': self._services.hotkey_error if self._services else ''}

    def ui_ready(self):
        if self._started is not None:
            elapsed = (time.perf_counter() - self._started) * 1000
            self._app.metrics.append({'kind': 'hotkey_to_ui', 'duration_ms': elapsed, 'time': time.time()})
            self._app.metrics[:] = self._app.metrics[-500:]
            self._started = None

    def execute(self, identifier, confirmed=False):
        try:
            kind, value = str(identifier).split(':', 1)
            if kind == 'copy':
                if len(value) > 10000:
                    raise ValueError('Text is too long')
                copy_text(value)
                return {'message': 'Copied.'}
            if kind == 'extension':
                extension_id, entry_id = value.split(':', 1)
                rows = self._app.store.rows('SELECT manifest FROM extensions WHERE id=?', (extension_id,))
                if not rows:
                    raise ValueError('Extension removed')
                entry = next((x for x in json.loads(rows[0]['manifest'])['entries'] if x['id'] == entry_id), None)
                if not entry:
                    raise ValueError('Entry removed')
                if entry['kind'] == 'copy':
                    copy_text(entry['value'])
                    return {'message': 'Copied.'}
                if entry['kind'] == 'url':
                    webbrowser.open(entry['value'])
                    return {'message': 'Opened in your browser.'}
                return self.execute('action:' + entry['value'], confirmed)
            if kind == 'clip':
                clip = next((x for x in self._app.clipboard.list() if x['id'] == int(value)), None)
                if not clip:
                    raise ValueError('Clipboard item expired')
                copy_text(clip['text'])
                return {'message': 'Copied.'}
            if kind == 'action':
                if confirmed is not True:
                    raise ValueError('Confirm the registered action before running it')
                rows = self._app.store.rows('SELECT * FROM actions WHERE id=?', (int(value),))
                if not rows:
                    raise ValueError('Action removed')
                return run_action(rows[0])
            if kind not in {'app', 'file'}:
                raise ValueError('Unknown result')
            table = 'apps' if kind == 'app' else 'files'
            rows = self._app.store.rows(f'SELECT * FROM {table} WHERE id=?', (int(value),))
            if not rows:
                raise ValueError('Result removed')
            path = Path(rows[0]['path'])
            if not path.is_file():
                raise ValueError('File no longer exists; refresh the index')
            if kind == 'file':
                root_rows = self._app.store.rows('SELECT path FROM roots WHERE id=?', (rows[0]['root_id'],))
                if not root_rows or not path.resolve().is_relative_to(Path(root_rows[0]['path']).resolve()):
                    raise ValueError('File is outside the registered folder')
                if path.suffix.lower() not in {'.txt', '.md', '.pdf', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.docx', '.xlsx', '.pptx', '.csv', '.json', '.log', '.zip'}:
                    raise ValueError('Register executable files as actions rather than opening them from file search')
            if os.name != 'nt':
                raise ValueError('Launching files requires the Windows desktop build')
            os.startfile(str(path))
            return {'message': 'Opened.'}
        except (ValueError, OSError, RuntimeError) as error:
            return {'error': str(error)}

