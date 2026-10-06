"""Desktop shell: one server, one reusable window and an explicit native bridge."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import threading
import time

from .app import create_app
from .bridge import Bridge
from .windows import WindowsServices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--smoke-result', type=Path)
    args = parser.parse_args()
    # Only one resident desktop instance per Windows user session.
    icon = None
    mutex = None
    if os.name == 'nt' and not args.browser and not args.smoke_result:
        import ctypes
        kernel, user = ctypes.windll.kernel32, ctypes.windll.user32
        kernel.CreateMutexW.restype = ctypes.c_void_p
        mutex = kernel.CreateMutexW(None, False, 'Local\\VeloraDock.Launcher')
        if kernel.GetLastError() == 183:
            user.FindWindowW.restype = ctypes.c_void_p
            user.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user.SetForegroundWindow.argtypes = [ctypes.c_void_p]
            handle = user.FindWindowW(None, 'VeloraDock')
            if handle:
                user.ShowWindow(handle, 9)
                user.SetForegroundWindow(handle)
            return
    directory = args.data_dir or Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'VeloraDock'
    app = create_app(directory, args.debug)
    import uvicorn
    bound = socket.socket()
    bound.bind(('127.0.0.1', 0))
    bound.listen(128)
    url = f'http://127.0.0.1:{bound.getsockname()[1]}/'
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [bound]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 30
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError('Local server did not start')
            time.sleep(.05)
        if args.browser:
            print(url, flush=True)
            while thread.is_alive():
                time.sleep(.5)
            return
        # Build/serve the shell before starting WebView2.
        import urllib.request
        with urllib.request.urlopen(url, timeout=30) as response:
            if b'VeloraDock' not in response.read():
                raise RuntimeError('The launcher page was not generated')
        import webview
        bridge = Bridge(app)
        window = webview.create_window('VeloraDock', url, js_api=bridge, width=850, height=680, min_size=(650, 500))
        bridge._window = window
        def show():
            bridge._started = time.perf_counter()
            window.show()
            if os.name == 'nt':
                user = __import__('ctypes').windll.user32
                user.SetForegroundWindow.argtypes = [__import__('ctypes').c_void_p]
                user.FindWindowW.restype = __import__('ctypes').c_void_p
                handle = user.FindWindowW(None, 'VeloraDock')
                if handle:
                    user.SetForegroundWindow(handle)
            window.evaluate_js('window.veloraSceneVisibility && window.veloraSceneVisibility(true); window.veloraFocus && window.veloraFocus()')
        services = WindowsServices(app, show)
        bridge._services = services
        tray = None
        quit_requested = threading.Event()
        def exit_app(*unused):
            quit_requested.set()
            services.stop()
            if tray:
                tray.stop()
            window.destroy()
        def closing():
            if not quit_requested.is_set() and not args.smoke_result:
                window.evaluate_js("window.veloraSceneVisibility && window.veloraSceneVisibility(false)")
                window.hide()
                return False
        window.events.closing += closing
        def ready():
            nonlocal tray, icon
            if not window.events.loaded.wait(30):
                if args.smoke_result:
                    args.smoke_result.write_text(json.dumps({'ok': False, 'error': 'Window did not load'}))
                    exit_app()
                return
            from .branding import set_window_icon
            icon = set_window_icon('VeloraDock')
            if args.smoke_result:
                deadline = time.monotonic() + 15
                ok = False
                while time.monotonic() < deadline:
                    ok = window.evaluate_js('Boolean(document.querySelector("#search-box"))')
                    if ok:
                        break
                    time.sleep(.1)
                args.smoke_result.parent.mkdir(parents=True, exist_ok=True)
                args.smoke_result.write_text(json.dumps({'ok': bool(ok), 'title': 'VeloraDock'}))
                exit_app()
                return
            from PIL import Image
            import pystray
            image = Image.open(Path(__file__).parent / 'public' / 'logo.png').copy()
            tray = pystray.Icon('veloradock', image, 'VeloraDock', pystray.Menu(
                pystray.MenuItem('Open', lambda *a: show(), default=True),
                pystray.MenuItem('Quit', exit_app)))
            tray.run_detached()
            services.start()
        webview.start(ready, gui='edgechromium' if os.name == 'nt' else None, debug=args.debug)
        services.stop()
        if tray:
            tray.stop()
    except KeyboardInterrupt:
        pass
    finally:
        from .branding import release_icon
        release_icon(icon)
        server.should_exit = True
        thread.join(timeout=5)
        bound.close()
        shutil.rmtree(app.runtime, ignore_errors=True)
        if mutex:
            import ctypes
            ctypes.windll.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            ctypes.windll.kernel32.CloseHandle(mutex)

if __name__ == '__main__':
    main()
