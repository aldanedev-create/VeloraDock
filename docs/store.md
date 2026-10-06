# Microsoft Store preparation

Reserved name supplied by the publisher: **VeloraDock**.

| Manifest field | Value |
| --- | --- |
| Package/Identity/Name | `HappyRecorder3D.VeloraDock` |
| Package/Identity/Publisher | `CN=50CA2AC2-0155-44AC-B2B0-47100A3FB6E2` |
| Package/Properties/PublisherDisplayName | `Happy Recorder 3D` |
| DisplayName | `VeloraDock` |

The manifest and packaging script now default to these exact values. Optional
repository-variable overrides must agree with the Partner Center identity.

1. Push this source to a dedicated GitHub repository.
2. The Windows workflow runs provider/browser tests, builds the frozen app,
   checks native UI startup and creates `VeloraDock.msix`.
3. Download the `VeloraDock-Windows-x64` artifact after a successful run.
4. Test the installed package on a clean supported Windows system with WebView2,
   run Windows App Certification Kit and complete Store metadata.

First package version: 1.0.0.0. The fourth component stays zero. Local MSIX
installation needs signing and a trusted test certificate matching Publisher;
Store signing is separate. No certificate or secret is included in this source.

The desktop needs `runFullTrust`; explain app launching, selected-folder access,
explicit local script execution, tray hotkeys and optional clipboard collection
in certification notes. Do not silently elevate privileges, bypass PowerShell
policy or download executable extensions. Script functionality must match the
listing. No approval guarantee is implied.

All interface assets are local. Opening an HTTPS bookmark intentionally opens an
external browser. Display accurate limitations: filename-only search, manually
refreshed index, text-only clipboard and separately installed Python for Python
actions. Include a public privacy-policy URL and genuine app screenshots.

Policy reference: https://learn.microsoft.com/en-us/windows/apps/publish/store-policies
Check the policy version effective on the actual submission date.
