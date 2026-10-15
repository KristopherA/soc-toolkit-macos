Evidence and output folder for the command-line tools.

This folder is mounted inside every CLI container as /case.
Put memory images, backups, samples and URL lists here, and point tools at /case/<file>.
Tool output written to /case/... appears here on the Mac.

Keep one subfolder per investigation, for example cases/2026-10-ir-042/.
Do not sync this folder to iCloud: it may hold malware samples and personal data.
