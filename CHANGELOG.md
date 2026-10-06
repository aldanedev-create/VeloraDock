# Changelog

## 1.0.1

- Fix the island canvas mount for Teloce, preserve the canvas across reactive UI updates, and remove input handlers when disabling 3D.
- Collapse the failed/disabled world instead of leaving an empty panel.
- Test rendered islands, exploration, re-enabling, and settings navigation in Windows Chromium.
- Prevent negative keyboard selection on empty results and report native action failures.
- Reject empty folder paths; report inaccessible directories while indexing.
- Verify registered-folder containment before revealing files.
- Validate clipboard settings before saving them in one transaction.
- Increase Windows package version to 1.0.1.0 so the previous local build can be updated.

## 1.0.0

Initial launcher with apps, file search, registered actions, unit conversion, calculator, optional encrypted clipboard history, and local extensions.
