# Frozen 5.6.3-xray.2 signing handoff

This is a separate maintenance entry, not the FongMi 5.9.0 adaptation and not an Xray Core upgrade. Keep main at 4a52de1daa465d81df7ac06e886a1f184053253c. Do not change repository visibility.

## Immutable inputs and evidence

- Source commit: 97a23d8fc2163c2c2b277e6c0e86a595a4638fa2
- Source tree: 9a166475155cb5a897627fef6838f965e74afd5f
- Archive ref: refs/tags/archive/frozen-public-validation-97a23d8
- Previous successful test-only build: [45547887003](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45547887003)
- Archive verification and Core branch cleanup: [45569613541](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45569613541)
- Unsigned handoff workflow commit: 4b3fa6fc481c8bf84b02026276abeb9f627813ff
- Initial handoff run: [45570721364](https://github.com/rileyaaa/FingMi-Xray/actions/runs/45570721364). Use its actual conclusion and artifact metadata, not this document, as proof of successful generation.

The workflow `.github/workflows/04-frozen-signing-handoff.yml` checks out the pinned source in a shallow checkout and checks all 1522 locked blobs, archive ref and exact tree. It cannot publish and does not accept production signing credentials. It reconstructs the existing test-verified inputs, validates both APKs, removes all test signatures, verifies payload hashes and compression methods, aligns to 16 KiB, and checks both unsigned APKs again before uploading only the handoff directory. The handoff contains README.md, SHA256SUMS, PAYLOAD_SHA256.json, BUILD_RESULT.txt, media3-linkage.json, verify_handoff.py and exactly two unsigned APKs.

The only automatic trigger is a push on this development branch changing the dedicated workflow or the explicit request path `scripts/maintenance/request-frozen-signing-handoff.txt`. Do not touch either solely to check status or repeat a passing build. The independent upstream adaptation workflow has its own path filter. Retention is 14 days; download and verify the handoff before expiration.

## Offline formal signing and acceptance

Original .1 (both ABIs) package com.fongmi.android.tv, versionCode 563001, public signing certificate SHA-256:
```
3cd86f4fdf6044e7e60307624bf0d8c892dfd83b81ce21748504fcbba28763c2
```

Use the existing original signing identity only, on an authorized controlled offline machine. Follow the handoff README; verify the public certificate from the local keystore against the pinned fingerprint first, and never transfer the private key or password into chat, public AC, logs or artifacts. Public repository visibility is not a private environment. If historical key exposure is confirmed, preserve the explicit owner decision and do not claim the original identity is uncompromised.

Run `sha256sum -c SHA256SUMS` and `python3 verify_handoff.py --handoff . --sdk "$ANDROID_HOME"` before signing. Use local interactive apksigner with the matching original key, sign both candidates, then run `python3 verify_handoff.py --handoff . --signed-dir signed --sdk "$ANDROID_HOME"`. This checks the original certificate, exact payload contents, ABI, package, versionName v5.6.3-xray.2, versionCode 563002, embedded source revision, v2 signature and alignment. Keep only final signed APKs and public verification evidence for publication. Never publish the unsigned or test-signed APKs.

Verify covering .1 using `adb install -r` on appropriate test devices (do not uninstall); confirm retained data and versionCode. Report device coverage honestly. A formal GitHub Release for .2 is a separate, once-only operation after acceptance; do not replace .1 or treat an Actions Artifact as a Release.

The temporary frozen validation branch remains until the handoff is successfully accepted and no longer needed. Only then use an exact, lease-guarded same-repository maintenance job to retire that branch after reading back the archive ref and checking current heads. Keep main and this development branch. No signing, publishing or unrelated builds in cleanup jobs. Core candidate is archived, not merged.
