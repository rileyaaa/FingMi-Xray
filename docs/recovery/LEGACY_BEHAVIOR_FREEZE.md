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

- playback screen is ready
- Xray is configured/eligible
- ExoPlayer is the usable engine path
- current media address is public HTTP(S)

When Xray becomes running:

- cancel normal global client requests
- reset the current playback selection/session
- release the current player if needed
- recreate playback with the returned Xray SOCKS port

When Xray errors while a player is using the Xray port:

- release player resources
- drop the Xray-backed engine/network resources
- surface the error

Stop/reset hooks include:

- playback/source reset
- new intent
- playback error/reset path
- engine/player transitions
- onStop
- onDestroy

`onDestroy()` disposes the Xray session controller.

## Live integration

`LiveActivity` also owns one playback Xray session controller.

The same session is not automatically inherited across channel/source changes.

Before Xray start, the selected live source must be public HTTP(S).

When Xray becomes running:

- live artwork/loading state is reset
- current player is recreated with the Xray SOCKS port
- if startup interrupted a pending channel switch, the channel switch is resumed after the new engine is ready

Live reset hooks include:

- channel change
- source/line change
- live player reset
- playback error path
- onStop
- onDestroy

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
