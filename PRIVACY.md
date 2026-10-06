# VeloraDock privacy

VeloraDock stores its settings, selected-folder paths, indexed filenames/paths,
registered action paths/arguments and extension manifests locally in
`%LOCALAPPDATA%\VeloraDock\veloradock.sqlite3` by default.

Clipboard collection is off by default. When enabled, text may include personal
or sensitive information. Saved clipboard text is protected using Windows DPAPI
for the current Windows account. It is not a password vault and has no automatic
secret-detection guarantee. Pause collection, change retention or clear all
history in Settings. Pinned entries survive expiry until removed or cleared.

The app does not upload this data, use analytics or require an account. Performance
samples stay in memory unless you export results. No cloud sync exists. A local
loopback server serves the interface; it does not listen on the LAN.

Registered actions execute on explicit confirmation under your account. Their
own network access, data processing and privacy behavior are controlled by those
programs, not VeloraDock. Opening an extension bookmark uses your browser and
contacts the requested website. Windows/Store services may have their own policies.

Disconnecting a folder removes its index, not the original files. Removing an
action or extension removes its registration. To remove all app-managed data,
quit VeloraDock and delete its data directory. Back up anything you want to keep.
The generated UI runtime is temporary and removed on normal shutdown.

Publisher contact/support details must be added before Store submission.
