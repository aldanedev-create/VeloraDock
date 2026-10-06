import json
from pathlib import Path
import shutil

import pytest
from flaxon.testing import TestClient

from veloradock.app import create_app
from veloradock.actions import action_command, register_action, validate_manifest
from veloradock.providers import calculate, conversion, index_folder
from veloradock.store import Store

@pytest.fixture
def app(tmp_path):
    value = create_app(tmp_path / 'data')
    yield value
    shutil.rmtree(value.runtime, ignore_errors=True)

def post(app, path, data):
    return TestClient(app).post(path, json_data=data, headers={'x-velora-token': app.token})

@pytest.mark.parametrize('expression,answer', [('2*(3+4)',14), ('-4+2',-2), ('8/4',2), ('8%3',2)])
def test_arithmetic(expression, answer):
    assert calculate(expression) == answer

@pytest.mark.parametrize('expression', ['__import__("os")', '2**100', '1/0', '[1]', '2+float("inf")'])
def test_arithmetic_rejects_code(expression):
    with pytest.raises((ValueError, ZeroDivisionError)):
        calculate(expression)

def test_units():
    assert conversion('1 mi to km') == '1.609344 km'
    assert conversion('32 f to c') == '0 c'
    with pytest.raises(ValueError):
        conversion('1 kg to km')

def test_index_search_and_disconnect(app, tmp_path):
    root = tmp_path / 'documents'
    root.mkdir()
    (root / 'Invoice.txt').write_text('hello')
    assert post(app, '/api/index', {'path': str(root)}).json()['count'] == 1
    results = post(app, '/api/search', {'query': 'file invoice'}).json()['items']
    assert results[0]['title'] == 'Invoice.txt'
    assert post(app, '/api/search', {'query': "file %' OR 1=1"}).json()['items'] == []
    identifier = app.store.rows('SELECT id FROM roots')[0]['id']
    post(app, '/api/remove', {'kind': 'root', 'id': identifier})
    assert app.store.rows('SELECT * FROM files') == []
    assert (root / 'Invoice.txt').exists()

def test_unauthorized_mutations_and_payload(app):
    client = TestClient(app)
    assert client.post('/api/action', json_data={}).status_code == 403
    assert post(app, '/api/index', []).status_code == 400
    assert post(app, '/api/settings', {'clipboard_enabled': 'false'}).status_code == 400

def test_actions_are_explicit_arguments_not_shell(app, tmp_path):
    path = tmp_path / 'action.py'
    path.write_text('print("hello")')
    identifier = register_action(app.store, {'name':'Hello','keyword':'hello','path':str(path),'args':['literal; $(thing)']})
    row = app.store.rows('SELECT * FROM actions WHERE id=?', (identifier,))[0]
    assert action_command(row)[-1] == 'literal; $(thing)'
    from veloradock.bridge import Bridge
    assert 'Confirm' in Bridge(app).execute('action:' + str(identifier))['error']
    assert post(app, '/api/search', {'query':'run hello'}).json()['items'][0]['confirm']

def test_extensions_do_not_import_code(app):
    manifest = {'schema_version':1,'id':'test-tools','name':'Tools','entries':[{'id':'hello','title':'Hello','keyword':'hello','kind':'copy','value':'Hello!'}]}
    assert post(app, '/api/extension', {'manifest':manifest}).status_code == 200
    assert post(app, '/api/search', {'query':'hello'}).json()['items'][0]['kind'] == 'extension'
    manifest['entries'][0]['kind'] = 'python'
    with pytest.raises(ValueError):
        validate_manifest(manifest, app.store)

def test_production_build_emits_js_from_typescript(app):
    response = TestClient(app).get('/')
    assert response.status_code == 200
    assert '/assets/app.css' in response.text
    built = app.teloce.build_dir
    assert (built / 'ui/app.js').exists()
    assert (built / 'ui/api.js').exists()
    assert 'Promise<any>' not in (built / 'ui/api.js').read_text()
    assert app.store.setting('clipboard_enabled', False) is False


def test_calculator_search_accepts_space_after_prefix(app):
    rows = post(app, '/api/search', {'query': '= 2 * (3 + 4)'}).json()['items']
    assert rows[0]['title'] == '14'


def test_index_rejects_app_data_parent(app):
    with pytest.raises(ValueError):
        index_folder(app.store, str(app.store.directory.parent))


@pytest.mark.skipif(__import__('os').name != 'nt', reason='DPAPI is a Windows account service')
def test_windows_clipboard_history_encrypted_roundtrip(app):
    app.store.set_setting('clipboard_enabled', True)
    app.clipboard.capture('Private test text')
    stored = app.store.rows('SELECT data FROM clips')[0]['data']
    assert b'Private test text' not in stored
    assert app.clipboard.list()[0]['text'] == 'Private test text'
    app.clipboard.clear()
    assert app.clipboard.list() == []


def test_store_identity_matches_reserved_values():
    import xml.etree.ElementTree as ET
    root = ET.parse(Path(__file__).parents[1] / 'packaging/AppxManifest.xml').getroot()
    ns = {'p': 'http://schemas.microsoft.com/appx/manifest/foundation/windows10'}
    identity = root.find('p:Identity', ns)
    assert identity.attrib['Name'] == 'HappyRecorder3D.VeloraDock'
    assert identity.attrib['Publisher'] == 'CN=50CA2AC2-0155-44AC-B2B0-47100A3FB6E2'
    assert identity.attrib['Version'] == '1.0.0.0'
    assert root.find('p:Properties/p:PublisherDisplayName', ns).text == 'Happy Recorder 3D'


def test_store_closes_connections_and_rolls_back(tmp_path):
    import sqlite3
    from veloradock.store import Store
    store = Store(tmp_path / 'database')
    with store.connect() as connection:
        connection.execute("INSERT INTO settings VALUES (?, ?)", ('saved', 'true'))
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute('SELECT 1')
    with pytest.raises(RuntimeError):
        with store.connect() as transaction:
            transaction.execute("INSERT INTO settings VALUES (?, ?)", ('discarded', 'true'))
            raise RuntimeError('Abort transaction')
    assert store.setting('saved') is True
    assert store.setting('discarded') is None
    with pytest.raises(sqlite3.ProgrammingError):
        transaction.execute('SELECT 1')
