# Recovered behavior notes

> Status: reconstructed from the shipped `v5.6.0-xray.5` arm64 APK with JADX.  
> Decompiled names are evidence only; final maintained classes will use readable names and be compared against FongMi/TV 5.6.0.

## Confirmed Android components

The final APK contains:

- `SettingXrayActivity`
- `XrayService`
- `XrayService` runs in the private Android process `:xray`
- a dedicated `activity_setting_xray.xml` layout
- Xray hooks in `SettingActivity`, `PushActivity`, `VideoActivity` and `LiveActivity`

## Session transport

The shipped build does not use `VpnService`.

For an active playback session, Xray creates a local SOCKS inbound bound to:

`127.0.0.1:<dynamic-port>`

The playback side creates a dedicated OkHttp client using:

`Proxy.Type.SOCKS -> 127.0.0.1:<session-port>`

That client owns a dedicated Dispatcher and ConnectionPool. The normal FongMi client remains in use when the playback session has no active Xray session.

The recovered player control code also refuses to provide an Xray-backed HTTP client when the active engine is not the ExoPlayer engine. This is why the UI checks that Xray playback is supported before starting a session.

## Playback destination guard

The Xray-specific OkHttp client includes a network interceptor that:

- accepts only HTTP and HTTPS playback requests;
- blocks localhost / `.localhost` / `.local`;
- blocks private, loopback, link-local, multicast/reserved and documentation/test IPv4/IPv6 ranges;
- lets public playback destinations continue through the local SOCKS proxy.

The Xray routing config repeats the private/local protection on the Xray side using a blackhole outbound. This is intentional defense-in-depth and should be retained.

## Xray runtime config

The service reconstructs one outbound from the configured share link and requires exactly one outbound.

It then creates:

- proxy outbound tag: `fongmi-xray-proxy`
- private-block outbound tag: `fongmi-xray-private-block`
- SOCKS inbound tag: `fongmi-xray-session`
- DNS tag: `fongmi-xray-dns`

Recovered DNS servers:

- `https://1.1.1.1/dns-query`
- `https://8.8.8.8/dns-query`
- `tcp://1.1.1.1:53`
- `tcp://8.8.8.8:53`

The runtime config uses `ForceIP` for the proxy outbound and `IPOnDemand` routing.

## Supported link handling

The shipped code has explicit handling for:

- VLESS
- VMess
- Trojan
- Shadowsocks
- Hysteria2 / `hy2`

There is extra normalization/validation around ports and URI forms instead of blindly passing user input to libXray.

Hysteria2 and TLS certificate changes are explicitly detected. A changed saved certificate is treated as an error that requires the user to delete/re-trust the saved Xray configuration rather than silently trusting a new certificate.

## Process and cleanup behavior

The Xray service serializes work on a single-thread executor.

Stopping a session calls libXray `stopXray` with retry behavior.

When cleanup cannot be proven safe, the service reports that a process reset is required and terminates its own `:xray` process. `onDestroy()` also terminates the private process after attempting orderly executor shutdown.

This confirms that private-process termination is part of the final resource-reclamation design, not an accidental artifact.

## Operation generations and race protection

The shipped implementation uses a monotonically increasing operation/session generation id.

This protects against stale callbacks when:

- a newer start supersedes an older start;
- a stop races with startup;
- a service connection dies;
- an Activity is destroyed;
- a test/import request finishes after the user has changed configuration.

A stale start can report:

`Xray startup superseded by newer request`

The session controller also has explicit timeout handling for:

- previous-session cleanup;
- Xray startup;
- service binding.

Do not replace this with a single global boolean during refactoring.

## Service/Binder boundary

The main process binds to `XrayService` instead of invoking libXray directly.

Recovered service operations include distinct requests for:

- configuration validation;
- connection/latency testing;
- starting a playback Xray session;
- stopping a playback Xray session;
- resetting stored Xray security/certificate state;
- cancelling an operation.

The exact public names will be reconstructed from behavior rather than preserving R8 names.

The service connection code registers Binder-death handling, unbinds stale connections and times out service binding after roughly five seconds.

## Playback lifecycle

Both `LiveActivity` and `VideoActivity` own a playback-session Xray controller.

Confirmed stop/cleanup hooks include:

- player/playback reset paths;
- channel/source changes;
- VOD navigation/reset paths;
- `onStop()`;
- `onDestroy()`.

`onDestroy()` fully disposes the Xray controller. State is therefore intentionally scoped to the current playback screen/session.

The next playback item does not simply reuse a global Xray state.

## Settings and import

`SettingActivity` contains an Xray settings entry.

`SettingXrayActivity` supports:

- save/delete;
- connection test;
- phone import;
- stale-operation cancellation using generation ids.

`PushActivity` is reused for LAN/phone import rather than introducing a separate embedded web server.

## Refactoring implications

The recovered design already has the beginnings of a good module boundary. The refactor should preserve it and make it explicit:

- `XrayService` + Binder contract -> `xray/service`
- generation/session state machine -> `xray/session`
- share-link normalization/security -> `xray/config`
- SOCKS OkHttp client + destination guard -> `xray/network`
- settings persistence/test/import -> `xray/settings`
- app-side Live/Video code -> only small calls into a stable facade

The highest-risk mistake would be to "simplify" away the generation state machine, timeout handling, destination guard, certificate pin handling or private-process reset logic. Those are precisely the pieces most likely to represent fixes accumulated across the many APK revisions.
