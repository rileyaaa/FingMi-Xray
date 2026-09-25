# Deep recovery audit — 2026-09-25

This pass performs static APK/README/FongMi-5.6.0 cross-checking only. No GitHub Actions or compilation may be triggered until the recovery layer is judged complete and the user explicitly approves the first faithful build.

Primary audit targets: Exo cache/network routing, side-network requests, Binder/process teardown, session races, standby network recovery, share-link compatibility, and recovery-code/API completeness.


## Published APK dual-ABI bytecode audit

The released APKs were re-downloaded from GitHub Releases and verified against
their published SHA-256 values before analysis.

Primary runtime baseline (the ABI actually used in deployment):

- armeabi-v7a SHA-256: `cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda`

Cross-check baseline:

- arm64-v8a SHA-256: `b5ac05193c1e19809fc7ffb3048f7d75aaa2124eace9953d669f4a81a477c21d`

The three top-level DEX files are not byte-identical across ABIs, so ABI parity
was checked at the recovered Xray code level instead of assuming identical DEX
containers.

Results:

- 57 decompiled source files contain Xray / Hysteria / libXray references.
- 56 are byte-for-byte identical between v7 and v8 JADX output.
- The only differing file is R8 class `ip0`, the generated EventBus subscriber
  index. The registered class/subscriber entries are identical; only the order
  of `HashMap.put` calls differs.
- All focused recovery classes, including `a04`, `th2`, `nq0`, `pz3`,
  `or2`, `qz3`, `XrayService`, and `SettingXrayActivity`, are identical
  between the two published ABIs.

### Hysteria2 authority port-hopping predicate

The last normalizer `DEX_VERIFY` item was resolved from raw DEX instructions
in both published APKs.

In R8 class `a04.f`:

1. `String.indexOf(',')` is followed by `if-gez` to the hopping rewrite.
2. If not found, `String.indexOf('-')` is followed by `if-gez` to the same
   hopping rewrite.
3. If neither character is found, execution jumps back to the non-hopping path.

Therefore the recovered predicate is confirmed: an authority port is treated as
a hopping expression iff it contains `,` **or** `-`. The contradictory JADX
condition is decompiler damage, not shipped behavior.

## Xray data-source close after failed open

The v7 JADX `or2.mo2561i` method sets its open flag immediately before
calling the delegated `DataSource.open`. Its `close` method checks that flag,
clears it, and closes the delegate. The legacy reconstruction previously set
the flag after `delegate.open` returned; if the delegate threw, cleanup would
be skipped. `LegacyXraySchemeGuardDataSource.open` now sets the flag before
delegation to preserve the shipped cleanup path. This was a static v7 source
comparison; runtime behavior remains untested pending the authorized build.

## Static faithful-overlay interface inventory

The source overlay contains 46 upstream-shaped files. Together with the
separate readable Xray implementation, it contains 62 Java files. A static
import inventory against the local FongMi-derived source found no missing
project class imports: the two `IXray*` imports are supplied by the recovery
AIDL files, while the two `PlayerEngine.Type.*` imports are static enum
members. Resource-name inspection found no missing Xray-specific IDs or
strings. It cannot verify method signatures, generated view binding, or
Gradle integration; those remain part of the faithful-variant static gate.

This execution environment has Java but no configured Android SDK or local
Gradle cache. Do not run a build merely to discover these expected toolchain
gaps. The owner authorized local compilation after thorough recovery review;
ask before using GitHub Actions instead.
