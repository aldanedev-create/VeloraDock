# VeloraDock

**Your local commands, one shortcut.**

A Windows desktop launcher built with a Flaxon local server, Teloce `.html`
components and `.ts` helpers. Press **Ctrl+Alt+Space** to search apps, indexed
filenames, registered actions and optional clipboard history. Convert units,
calculate arithmetic and add declarative extension shortcuts.

## Run from source

Use Python 3.12 for the Windows desktop packaging workflow. Install compatible
framework checkouts until the new Flaxon head settings are published:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install -e C:\projects\teloce-py -e C:\projects\flaxon -e . --no-deps
python run_desktop.py
```

For Linux/browser development, `python run_desktop.py --browser --debug` prints
the local address. Native launching, hotkeys and clipboard capture require Windows.

## First run

1. Open Settings and refresh Start Menu apps.
2. Add selected folders to the filename index.
3. Try `12 km to mi`, `= 2 * (3 + 4)`, `file invoice` or `app notepad`.
4. Register a trusted `.ps1`, `.py` or `.exe` and search `run keyword`.
5. Enable clipboard text collection only if wanted; use `clip text` to search.

Close hides to the tray. Escape hides the launcher. Use the tray's Quit command
to stop it. Shortcut conflicts appear in Settings measurements; choose another
shortcut and restart. Python scripts require Python installed separately in the
frozen desktop build. PowerShell execution policy is not bypassed.

**Status:** a working source implementation with provider/API tests and production
SPA interaction checks. Windows-native startup, hotkey latency, idle memory and
installed MSIX behavior need the Windows workflow and local acceptance checks.
The package uses the supplied HappyRecorder3D.VeloraDock Store identity. No
"lightweight" performance claim is made.

[Architecture](docs/architecture.md) · [Extensions](docs/extensions.md) ·
[Performance](docs/performance.md) · [Store preparation](docs/store.md) ·
[Privacy](PRIVACY.md)

### Island workspace

The optional Three.js world includes six islands linked to search categories. Choose Explore, drag to look, scroll to zoom, or focus the canvas and use WASD. Click a beacon to search that category. Pause or disable 3D at any time; the preference is saved locally. Reduced-motion settings start with animation paused. Rendering stops when the desktop window is hidden. WebGL failure leaves search available.

Three.js r160 is bundled locally under the MIT license; no CDN is required. The world increases download size and GPU usage. Windows memory and graphics measurements remain pending; no lightweight performance claim is made.

The same VeloraDock mark is used for the executable, native window, tray, favicon and MSIX assets. GitHub Actions produces an unsigned MSIX for Store submission and the portable desktop folder. Local installation requires appropriate signing; the Store signs the accepted package.
