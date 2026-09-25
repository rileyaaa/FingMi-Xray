# Deep recovery audit — 2026-09-25

This pass performs static APK/README/FongMi-5.6.0 cross-checking only. No GitHub Actions or compilation may be triggered until the recovery layer is judged complete and the user explicitly approves the first faithful build.

Primary audit targets: Exo cache/network routing, side-network requests, Binder/process teardown, session races, standby network recovery, share-link compatibility, and recovery-code/API completeness.
