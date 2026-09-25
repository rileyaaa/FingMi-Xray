# Legacy behavior freeze

This document freezes behavior recovered from the shipped `v5.6.0-xray.5` arm64 APK.

The rule for the recovery phase is simple:

> Do not refactor behavior until the legacy implementation and edge cases are recovered and accounted for.

The current `:xray` module is an experimental destination only. It must not be treated as the source of truth until this freeze is complete.

## Operation contract

The shipped Binder contract uses these operation ids:

1. validate configuration
2. test latency/connectivity
3. start playback Xray session
4. stop playback Xray session
5. reset saved transport-security state

Operation ids are globally monotonically increasing from `System.nanoTime()`.

Two independent generation gates exist:

- playback start/stop gate
- settings/test/reset gate

Each gate stores the maximum observed id. Cancelling the currently active id CASes it to `Long.MAX_VALUE` and terminates the private Xray process.

## Binder lifecycle

The main process does not call libXray directly.

Recovered client behavior:

- explicit bind to `XrayService`
- bind timeout: 5 seconds
- `IBinder.linkToDeath`
- handles service disconnected / binding died / null binding / Binder death
- every bind connection has its own generation
- stale callbacks are ignored
- failure tears down the old Binder and ServiceConnection
- unbind is tolerant of already-unbound connections

## Playback session state machine

Recovered states:

1. off
2. starting
3. running
4. error (immediately followed by off)

Start behavior:

- ignore start while already starting/running/disposed
- read encrypted saved share link
- read UDP preference
- allocate a new operation id
- switch UI to starting
- dispatch operation 3

Timeouts:

- service bind: 5 seconds
- previous-session cleanup: 1.5 seconds
- playback Xray startup: 30 seconds
- settings validate/test/reset operation: 45 seconds

Stop behavior:

- allocate a new generation id
- switch UI to off before the remote stop returns
- dispatch operation 4
- stale stop responses are ignored
- failed cleanup cancels the operation and may force-reset the Xray process

Dispose behavior:

- if active, request stop first
- mark controller disposed
- if no stop is pending, disconnect Binder after 500 ms

## Xray private process

`XrayService` runs in:

`:xray`

It owns:

- libXray runtime
- config conversion/probing
- validate/test/start/stop operations
- certificate-pin storage
- its single-thread operation executor

Start path:

1. stop any old core first
2. up to 3 attempts for bind/listen errors
3. allocate a free local port
4. construct full config
5. `testXray`
6. `runXray`
7. verify `getXrayState.running`
8. report SOCKS port to main process

Stop path:

- `stopXray` is attempted up to 2 times
- active session id is cleared in all cases

The process is terminated when cleanup cannot be trusted or a cancelled generation must invalidate in-flight native work.

`onDestroy()`:

- invalidates both operation gates
- queues one final stop attempt
- shuts down the single-thread executor
- waits up to 3 seconds
- calls `shutdownNow()` if required
- finally kills its own process

## Playback network ownership

The shipped app does not install a global proxy.

For each Xray-enabled ExoPlayer engine it creates a dedicated HTTP stack:

- SOCKS proxy: `127.0.0.1:<session-port>`
- `InetSocketAddress.createUnresolved`
- dedicated OkHttp Dispatcher
- dedicated ConnectionPool
- cache disabled
- network interceptor blocks local/private/reserved destinations
- custom SOCKS SocketFactory keeps hostnames unresolved for remote resolution

The Xray client is only returned for ExoPlayerEngine.

If a different player engine is active while a session port is set, the code fails with:

`Xray session requires ExoPlayerEngine`

Engine release:

1. atomically mark Xray HTTP resources closed
2. shut down the dedicated Dispatcher executor
3. asynchronously `cancelAll()`
4. asynchronously `ConnectionPool.evictAll()`

The cleanup executor has:

- core threads: 0
- max threads: 1
- keepalive: 5 seconds
- core-thread timeout enabled

## VOD integration

`VideoActivity` owns one playback Xray session controller.

Before starting Xray from the playback menu the shipped build requires:

- the current player has reached READY at least once
- there is a current playback session / PlaySpec
- the current resolved media destination is public
- supported destination schemes are `http`, `https`, `rtsp`, and `rtspt`

Xray playback itself is Exo-only. If the normal session is using another
engine, installing the Xray SOCKS port is an engine boundary and rebuilds the
session as Exo rather than silently proxying an unsupported engine.

When Xray becomes running:

- cancel stale VOD DETAIL / PLAYBACK / PRELOAD jobs
- cancel ordinary global HTTP calls which belong to the old network path
- clear Exo next-item preload state
- clear the current asynchronous artwork request
- install the returned SOCKS port
- rebuild the engine only when the engine/port boundary actually changes
- preserve the current playback snapshot when the transition requests it

While a VOD Xray session is requested or active, new artwork requests are
suppressed. This prevents image traffic from racing across the old and new
network paths.

When Xray errors after its port was installed:

- drop the Xray-backed engine/network resources
- preserve the playback snapshot for the normal-network rebuild
- surface the playback error

The old Xray session is not inherited by:

- next/previous episode
- automatic next episode
- line/flag changes
- source changes
- refresh / actual playback-address changes
- player-engine changes
- playback end
- new intent / new video
- playback error/reset
- leaving the playback screen

Opening the player-engine dialog alone does not stop Xray. The final APK runs
the reset callback only when the selected engine actually changes.

`onStop()` always stops the private Xray session. If FongMi is intentionally
keeping normal playback alive in the background, the player snapshot can be
preserved while the Xray port itself is removed.

`onDestroy()` clears outstanding artwork work and disposes the Xray session
controller.

## Live integration

`LiveActivity` also owns one playback Xray session controller.

The same session is not automatically inherited across channel/source changes.

For an already resolved playback session, the resolved URL must be a public
`http`, `https`, `rtsp`, or `rtspt` destination.

When no resolved playback session exists yet, the raw channel URL has an extra
compatibility rule:

- public RTSP/RTSPT may be used directly
- HTTP(S) `.strm` indirections are not started through Xray yet
- YouTube/youtu.be HTTP(S) indirections are not started through Xray yet

Those indirections must first be resolved by FongMi into the real media URL.

Live metadata is part of the session network boundary. EPG/XML metadata requests
receive the current playback HTTP client; when Xray changes state, metadata
calls are cancelled on both the normal client and the session client. Only the
EPG/XML tasks are cancelled -- the active live URL-resolution task is preserved
where the shipped continuation requires it.

When Xray becomes running:

- cancel stale live metadata jobs/calls
- suppress channel-logo and current-logo Glide requests
- clear the current artwork request
- install the returned SOCKS port
- refresh EPG/XML through the session client

There are two distinct startup paths:

1. **Existing playback** -- install the SOCKS port with playback preservation.
2. **Channel still resolving** -- install the SOCKS port without replaying the
   old item, then resubmit the pending live/catch-up request with
   `resetXray=false`. This avoids immediately killing the Xray session that
   just finished starting.

If startup fails while an ordinary live stream was already playing, the Xray
error is reported without turning that still-valid direct stream into a
full-screen playback failure.

Live reset hooks include:

- channel change
- source/line change
- whole live-config change
- player-engine change
- playback end/error/reset
- onStop
- onDestroy

Player-engine reset is callback-based just like VOD: merely opening the engine
dialog does not stop Xray.

## Android TV foreground / standby network recovery

This is a separate stability fix from Xray itself and must survive the later
module refactor.

The shipped TV build maintains a foreground/network generation:

- all activities stopped, or `SCREEN_OFF`, marks a background/screen-off
  transition
- the next foreground start increments the generation
- `SCREEN_ON` also increments it when an activity is still started
- HomeActivity records the generation and checks it from both `onResume()`
  and `onWindowFocusChanged(true)`

When HomeActivity sees a new generation it does not immediately reuse the old
network stack. The recovered sequence is:

1. invalidate the stale home-result request
2. detach the old **normal API** OkHttp client from the singleton
3. reset the DNS/DoH transport while preserving the selected DoH configuration
4. asynchronously cancel the old API client's calls
5. evict its connection pool
6. shut down its Dispatcher executor
7. destroy cached Jar / JavaScript / Python Spider runtimes
8. only after that cleanup finishes, start network-stability polling
9. poll every 500 ms
10. require two consecutive checks with
    `NET_CAPABILITY_INTERNET`
11. stop waiting after roughly 12 checks (~6 seconds)
12. reload Home only if the foreground generation is still the same

The dedicated player client is deliberately not reset by this Home recovery
path. That preserves a normal background playback session when the app's
background-playback setting allows it.

DoH owns a separate OkHttpClient. A network-generation change destroys that
transport too, but retains either the lazy DoH supplier or the concrete selected
DoH configuration so the next lookup can rebuild DoH rather than silently
falling back to system DNS.

The APK uses a serialized daemon cleanup executor named:

`TvNetworkCleanup`

The decompiler damaged the try/catch edges around the three OkHttp cleanup
operations. The recovered implementation intentionally performs all three
operations -- cancel calls, evict pooled connections, and shut down the
Dispatcher executor -- which is consistent with the surrounding lifecycle and
the README's documented stale-Socket/DNS recovery intent.

## Share-link storage

Saved node configuration is encrypted.

Preferences:

`xray_secure`

Fields:

- `link_ciphertext`
- `link_iv`
- `udp`

Android Keystore alias:

`fongmi_xray_share_link_v1`

Cipher:

`AES/GCM/NoPadding`

Reading and saving both run the legacy share-link normalizer.

## Supported share-link protocols

The shipped normalizer explicitly accepts:

- `vless://`
- `vmess://`
- `trojan://`
- `ss://`
- `hy2://`
- `hysteria2://`

The compatibility rules are part of product behavior, not cosmetic parsing. They must be reconstructed before refactoring.

Confirmed special handling includes:

- scheme normalization
- strict port validation (1..65535)
- VMess JSON numeric/string port validation
- legacy Shadowsocks base64 link normalization
- SIP003 `v2ray-plugin` conversion
- Trojan TLS normalization
- Hysteria2 default port 443
- Hysteria2 authority port-hopping conversion
- `mport` -> `ports`
- `pinSHA256` -> canonical `pcs`
- Hysteria2 obfs validation
- Gecko obfs rejected by the shipped native core
- literal `+` credential preservation for Trojan/Hysteria2 after conversion

## Certificate security

There is a separate encrypted certificate-pin store:

Preferences:

`xray_hy2_pins`

Android Keystore alias:

`fongmi_xray_hy2_pins_v1`

Legacy `hy2_pin_*` entries are migrated out of `xray_secure`.

For links that explicitly request insecure TLS and do not already provide a trusted pin/certificate name:

1. probe the real server certificate through libXray
2. verify the returned SHA-256 fingerprint format
3. trust/store it on first use
4. compare later probes using `MessageDigest.isEqual`
5. reject a changed certificate

The shipped error deliberately tells the user to delete the saved Xray configuration before trusting the new certificate.

Reset-security operation clears:

- current pin preferences
- legacy pin preferences
- the pin encryption key

## Settings

Xray settings supports:

- save
- delete
- validate/test
- phone import
- UDP toggle

Save/delete use synchronous preference commits and report persistence failure.

Test and reset are generation-aware Binder operations with a 45 second timeout.

Destroying the settings screen invalidates the generation and unbinds the service.

## Phone import

Phone import reuses the existing `PushActivity`.

Xray mode is selected with:

`tab=6`

The same LAN web server/QR mechanism is reused rather than running a second embedded server.

## Recovery rule

Before architectural refactoring begins, every bullet above must map to recovered source or an explicitly documented deviation.

Especially do not simplify away:

- node compatibility normalization
- certificate probing/pinning
- generation ids
- operation timeouts
- Binder death handling
- process reset rules
- SOCKS client resource cleanup
- ExoPlayer-only enforcement
- public-destination filtering
- playback reset hooks
