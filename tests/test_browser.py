import os
import socket
import threading
import time

import pytest

@pytest.mark.skipif(os.getenv('VELORA_BROWSER_TESTS') != '1', reason='Enable Windows/browser test explicitly')
def test_launcher_browser(tmp_path):
    import uvicorn
    from playwright.sync_api import sync_playwright
    from veloradock.app import create_app
    app = create_app(tmp_path / 'data')
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    sock.listen(128)
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning'))
    thread = threading.Thread(target=server.run, kwargs={'sockets':[sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 20
        while not server.started:
            if time.monotonic() > deadline:
                raise RuntimeError('Server did not start')
            time.sleep(.05)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=["--enable-unsafe-swiftshader"])
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{sock.getsockname()[1]}/')
            page.get_by_text('Six islands. Your files stay on your computer.', exact=True).wait_for(timeout=20000)
            assert page.locator('#island-canvas').evaluate('(canvas) => canvas.width > 100 && canvas.height > 100')
            page.get_by_role('button', name='Explore', exact=True).click()
            page.get_by_role('button', name='Files', exact=True).click()
            assert page.locator('#island-canvas').evaluate('(canvas) => canvas.isConnected')
            page.get_by_role('button', name='Disable 3D', exact=True).click()
            page.get_by_text('3D disabled. Search works as usual.', exact=True).wait_for()
            page.reload()
            page.get_by_role('button', name='Enable 3D', exact=True).wait_for()
            page.get_by_role('button', name='Enable 3D', exact=True).click()
            page.get_by_text('Six islands. Your files stay on your computer.', exact=True).wait_for(timeout=20000)
            page.locator('#search-box').fill('zzzz-no-match-zzzz')
            page.get_by_text('0 results', exact=True).wait_for()
            page.locator('#search-box').press('ArrowDown')
            page.locator('#search-box').fill('12 km to mi')
            page.get_by_role('option').filter(has_text='7.456454307 mi').wait_for()
            page.locator('#search-box').fill('= 2 * (3 + 4)')
            page.get_by_role('option').filter(has_text='14').wait_for()
            page.get_by_role('button', name='Settings', exact=True).click()
            page.get_by_role('heading', name='Clipboard history').wait_for()
            assert page.locator('#island-canvas').evaluate('(canvas) => canvas.isConnected')
            __import__('pathlib').Path('build').mkdir(exist_ok=True)
            page.screenshot(path='build/browser-workspace.png', full_page=True)
            page.get_by_role('button', name='Review and install manifest').click()
            # Installation confirms in a native browser dialog; Playwright dismisses by default.
            assert page.title() == 'VeloraDock'
            assert not errors
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        import shutil
        shutil.rmtree(app.runtime, ignore_errors=True)
