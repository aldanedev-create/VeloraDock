"""Register token-protected local launcher APIs."""
import asyncio
import json
import time

from flaxon import Request
from flaxon.http import JSONResponse

from .actions import register_action, validate_manifest
from .providers import index_apps, index_folder


def register_routes(app):
    def local(request):
        return request.headers.get('host', '').split(':')[0] in {'127.0.0.1', 'localhost', 'testserver'}

    def endpoint(path, function):
        @app.post(path)
        async def call(request: Request):
            if not local(request) or request.headers.get('x-velora-token') != app.token:
                return JSONResponse({'error': 'Local authorization required'}, status_code=403)
            try:
                payload = await request.json()
                if not isinstance(payload, dict):
                    raise ValueError('Expected a JSON object')
                return await asyncio.to_thread(function, payload)
            except (ValueError, OSError, TypeError, KeyError) as error:
                return JSONResponse({'error': str(error)}, status_code=400)

    @app.get('/')
    async def home(request: Request):
        if not local(request):
            return JSONResponse({'error': 'Local access only'}, status_code=403)
        response = await request.compile('app.html', {'token': app.token})
        response.headers['referrer-policy'] = 'no-referrer'
        return response

    endpoint('/api/search', lambda p: app.search.query(str(p.get('query', ''))))
    endpoint('/api/state', lambda p: {
        'roots': app.store.rows('SELECT * FROM roots'),
        'actions': app.store.rows('SELECT * FROM actions'),
        'extensions': app.store.rows('SELECT id,manifest FROM extensions'),
        'clipboard_enabled': app.store.setting('clipboard_enabled', False),
        'clipboard_days': app.store.setting('clipboard_days', 7),
        'hotkey': app.store.setting('hotkey', 'Ctrl+Alt+Space'),
        'file_count': app.store.rows('SELECT count(*) AS n FROM files')[0]['n'],
        'app_count': app.store.rows('SELECT count(*) AS n FROM apps')[0]['n'],
    })
    def index(payload):
        if not app.index_lock.acquire(blocking=False):
            raise ValueError('An index operation is already running')
        try:
            return index_folder(app.store, str(payload.get('path', '')))
        finally:
            app.index_lock.release()
    endpoint('/api/index', index)
    endpoint('/api/apps', lambda p: {'count': index_apps(app.store)})
    endpoint('/api/action', lambda p: {'id': register_action(app.store, p)})
    def remove(payload):
        kind, identifier = payload.get('kind'), payload.get('id')
        if kind == 'root':
            with app.store.connect() as connection:
                connection.execute('DELETE FROM files WHERE root_id=?', (int(identifier),))
                connection.execute('DELETE FROM roots WHERE id=?', (int(identifier),))
        elif kind == 'action':
            app.store.execute('DELETE FROM actions WHERE id=?', (int(identifier),))
        elif kind == 'extension':
            app.store.execute('DELETE FROM extensions WHERE id=?', (str(identifier),))
        else:
            raise ValueError('Unknown record type')
        return {'ok': True}
    endpoint('/api/remove', remove)
    def extension(payload):
        manifest = validate_manifest(payload.get('manifest'), app.store)
        app.store.execute('INSERT OR REPLACE INTO extensions VALUES (?,?)', (manifest['id'], json.dumps(manifest)))
        return {'ok': True}
    endpoint('/api/extension', extension)
    def settings(payload):
        if 'clipboard_enabled' in payload:
            if type(payload['clipboard_enabled']) != bool:
                raise ValueError('Clipboard option must be boolean')
            app.store.set_setting('clipboard_enabled', payload['clipboard_enabled'])
        if 'clipboard_days' in payload:
            days = int(payload['clipboard_days'])
            if days not in {1, 7, 30}:
                raise ValueError('Choose 1, 7 or 30 days')
            app.store.set_setting('clipboard_days', days)
            app.clipboard.prune()
        return {'ok': True}
    endpoint('/api/settings', settings)
    endpoint('/api/clips/clear', lambda p: app.clipboard.clear() or {'ok': True})
    def favorite(payload):
        app.store.execute('UPDATE clips SET favorite=? WHERE id=?', (int(bool(payload.get('favorite'))), int(payload['id'])))
        return {'ok': True}
    endpoint('/api/clips/favorite', favorite)
    endpoint('/api/clips', lambda p: {'items': app.clipboard.list()})
    def metric(payload):
        duration = float(payload['duration_ms'])
        if not 0 <= duration <= 60000:
            raise ValueError('Invalid duration')
        app.metrics.append({'kind': str(payload.get('kind', 'search'))[:20], 'duration_ms': duration, 'time': time.time()})
        app.metrics[:] = app.metrics[-500:]
        return {'ok': True}
    endpoint('/api/metric', metric)
    endpoint('/api/metrics', lambda p: {'samples': app.metrics, 'latest_search_ms': app.search.last_duration_ms})
