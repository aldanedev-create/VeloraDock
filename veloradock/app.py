"""Local SPA and token-protected APIs. Heavy search/index work runs off the event loop."""
from pathlib import Path
import secrets
import shutil
import tempfile

from flaxon import Flaxon

from .routes import register_routes
from .clipboard import Clipboard
from .providers import Search
from .store import Store


def create_app(directory: Path, debug=False):
    app = Flaxon('VeloraDock', debug=debug)
    app.store = Store(directory)
    app.clipboard = Clipboard(app.store)
    app.search = Search(app.store, app.clipboard)
    app.token = secrets.token_urlsafe(32)
    app.metrics = []
    app.index_lock = __import__('threading').Lock()
    app.runtime = Path(tempfile.mkdtemp(prefix='veloradock-ui-'))
    shutil.copytree(Path(__file__).parent / 'ui', app.runtime / 'ui')
    shutil.copytree(Path(__file__).parent / 'public', app.runtime / 'public')
    app.mount_static('/assets', str(app.runtime / 'public'))
    app.use_teloce(project_root=app.runtime, ui_dir='ui', title='VeloraDock', favicon='/assets/logo.svg', stylesheets=['/assets/app.css'], options={
        'minifier': 'minifyjs', 'bundler': 'minifyjs', 'bundle': not debug,
        'entry': 'ui/app.js', 'bundle_outfile': 'ui/launcher.js', 'tree_shake': True,
    })

    register_routes(app)
    return app
