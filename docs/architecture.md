# How VeloraDock works

The Windows host runs one Flaxon server on a random loopback port and reuses one
WebView2 window. Teloce compiles the `.html` components and `.ts` modules;
MinifyJS 0.1.3 optimizes the production bundle. The native bridge contains methods,
not public references to the entire app/window object. This prevents pywebview
from recursively exposing internal objects.

## Responsibilities

- `store.py`: SQLite settings, folder/file index, apps, actions and extensions.
- `providers.py`: read-only provider search and folder/app indexing.
- `calculations.py`: bounded arithmetic and unit conversion.
- `actions.py`: registered process argument lists and manifest validation.
- `clipboard.py`: opt-in history, current-account DPAPI encryption and retention.
- `windows.py`: RegisterHotKey and clipboard polling only while enabled.
- `app.py`: configure the application and production UI build.
- `routes.py`: local Host/token checks, JSON APIs and off-thread indexing.
- `desktop.py`: process/window/tray lifecycle.
- `bridge.py`: explicit native operations and file dialogs.
- `ui/app.html`: command view, keyboard selection and run confirmation.
- `ui/components/SettingsPanel.html`: compose five scoped settings components.
- `SourcesSettings`, `ActionsSettings`, `ClipboardSettings`, `ExtensionsSettings`,
  `DiagnosticsSettings`: each owns one settings area.
- `ui/api.ts`, `ui/types.ts`: browser API helper and result contracts.

`tsconfig.json` configures optional editor/type-checking tools for standalone
`.ts` files. Teloce does not consume its compiler options, `paths` aliases or
`strict` flag, and that file does not check scripts embedded in `.html`.

## Limits

Filename indexing is manual, with 50,000 files per root. No document-content/OCR
search or live watcher. Hidden subfolders, symlink directories and junctions are
excluded. Search is substring matching, not fuzzy ranking. Registered folders
stay on disk when disconnected. Stale results may fail until reindexed.

Apps are Start Menu `.lnk` entries, not a complete inventory of every installed
or portable app. Register other executables explicitly. File search opens a
restricted set of document/image/archive extensions; other types need an action.

Clipboard supports text only, up to 10,000 characters and 200 recent rows;
pinned rows can exceed the rolling unpinned limit and survive expiry until cleared.
No automatic password-manager exclusion is promised. Polling runs every .75s;
very rapid intermediate clipboard changes can be missed. Clearing history does
not clear the Windows clipboard. Pausing does not delete saved history.

Extensions are declarative local manifests, not executable Python plugins.
No remote script download, marketplace or automatic extension update exists.
