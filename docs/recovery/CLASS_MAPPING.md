# Recovered class mapping

These names are proposed readable replacements for R8/decompiler symbols found in the shipped APK. They are not assumed to be the original deleted source names.

| Decompiled symbol | Recovered responsibility | Proposed maintained name |
|---|---|---|
| `yz3` | per-playback Xray state machine, operation generations, start/cleanup timeouts | `XraySessionController` |
| `hz3` | bind/unbind `:xray` service, Binder death, bind timeout, operation dispatch | `XrayServiceClient` |
| `ez3` | Android `ServiceConnection` + `DeathRecipient` | `XrayServiceConnection` |
| `gz3` | queued service operation data | `XrayOperation` |
| `rz3` | callback/result payload | `XrayOperationResult` |
| `xz3` | playback UI state callback | `XraySessionListener` |
| `fz3` | service-operation callback contract | `XrayServiceCallback` |
| `lz3` | global monotonic operation ids | `XrayOperationIds` |
| `pz3` | per-session SOCKS OkHttp client and connection resources | `XrayHttpClient` |
| `oz3` | SOCKS proxy-aware socket factory | `XrayProxySocketFactory` |
| `qz3` | blocks private/reserved/non-HTTP(S) playback destinations | `PublicPlaybackDestinationInterceptor` |
| `lu2` | encrypted share-link + UDP preference storage in Android Keystore | `XrayPreferences` |
| `a04` | share-link validation and normalization | `XrayShareLinkNormalizer` |
| `kz3` | error sanitization/redaction of credentials and share links | `XrayErrorSanitizer` |
| `et1` | isolated node latency test using libXray pingBatch | `XrayConnectionTester` |
| `uz3` | Binder-side implementation of IXrayService | `XrayServiceBinder` |
| `j91` | Binder service interface | `IXrayService` |
| `h91` | Binder callback interface | `IXrayCallback` |
| `dz3` | callback Binder implementation | `XrayCallbackBinder` |

## Important recovered details

### Encrypted node storage

The saved share link is not plain SharedPreferences text.

The final APK stores AES-GCM ciphertext/IV in `xray_secure` and stores the AES key in AndroidKeyStore under:

`fongmi_xray_share_link_v1`

UDP preference is stored beside the encrypted link.

### Error redaction

The shipped build contains explicit sanitization for:

- complete VMess/VLESS/Trojan/Shadowsocks/Hysteria2 URLs;
- UUIDs;
- password/passwd/token/secret/auth;
- obfs-password;
- private/public keys;
- short ids and seeds.

This should remain a module-level utility so Binder/service errors cannot accidentally leak node credentials to logs or UI.

### Connection test

The recovered tester uses libXray `pingBatch` against:

`https://www.gstatic.com/generate_204`

with a 10-second timeout and targets the generated outbound tag `fongmi-xray-proxy`.

Connection testing is performed without leaving a playback Xray session running.

### Binder contract

The shipped APK has real Binder descriptors:

- `com.fongmi.android.tv.xray.IXrayService`
- `com.fongmi.android.tv.xray.IXrayCallback`

The reconstruction should define readable AIDL or equivalent Binder interfaces instead of preserving generated/decompiled Binder code manually.
