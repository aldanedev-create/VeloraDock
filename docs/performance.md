# Performance measurements

No claim of "lightweight" is made. `search-benchmark.json` records one synthetic
Linux measurement: 10,000 rows, 20 warmups, 100 timed searches. It measures the
Python provider/SQLite path, excluding browser/network latency. It is not a
Windows or end-user guarantee.

```powershell
python tools/benchmark.py --files 10000 --out search-results.json
```

The UI also records API round-trip timing, excluding its 90ms input debounce and
paint time. Inspect Settings → Show measurements. Distinguish these timings from
provider time rather than comparing different measurement boundaries.

## Windows hotkey-to-interface latency

The RegisterHotKey callback starts a monotonic timer, restores/focuses the window,
and requests UI focus. The browser acknowledges after two animation frames;
the Python bridge records `hotkey_to_ui`. This approximates UI readiness, not
physical key-to-photon latency. Measure 30+ invocations after warmup and report
median and p95, including failures and shortcut conflicts. Do not include tray
Open samples when reporting global-hotkey measurements.

## Idle memory

After the desktop is idle for 30 seconds, find its process ID and run:

```powershell
Get-Process VeloraDock | Select-Object Id, WorkingSet64
python tools/measure_windows.py --pid 1234 --seconds 60 --out windows-idle.json
```

Replace 1234 with the actual PID. The script includes WebView2 child RSS;
summing RSS can double-count shared pages. Record Windows version, CPU/RAM,
app version, folder count, clipboard state and whether the window is hidden.
Measure startup separately. Repeat with 10,000 and 50,000 indexed filenames.

Native hotkey and Windows idle results are **unmeasured** in this source package.
Collect them on a real desktop before making performance claims.
