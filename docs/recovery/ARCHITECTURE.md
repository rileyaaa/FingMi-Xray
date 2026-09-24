# Xray modularization target

## Design objective

FongMi should remain easy to update from upstream. Xray must be owned by a separate module and the app should depend on a small public API instead of directly depending on libXray internals.

## Intended project shape

```text
FingMi-Xray
├── app/                     # FongMi application, minimal integration edits
├── xray/                    # FingMi-owned Android library
│   ├── api/                 # stable interface used by app
│   ├── core/                # libXray invocation and config generation
│   ├── service/             # :xray process lifecycle
│   ├── share/               # share-link parsing/import
│   ├── storage/             # node persistence
│   ├── test/                # connection tests
│   └── ui/                  # Xray-specific settings/import UI where practical
└── docs/recovery/           # reconstruction evidence and decisions
```

## App-to-Xray boundary

The app should eventually talk to a narrow facade similar to:

```java
interface XrayPlaybackGateway {
    void enableForCurrentPlayback(PlaybackRequest request);
    void disableForCurrentPlayback(StopReason reason);
    boolean isEnabledForCurrentPlayback();
}
```

The exact API will be finalized from recovered behavior. The important constraint is that FongMi player activities/fragments must not call libXray directly.

## Process model

The Android library should own the service declaration in its merged manifest:

```xml
<service
    android:name=".service.XrayService"
    android:exported="false"
    android:process=":xray" />
```

The main process communicates with that service through an explicit boundary. Any process termination used for Go/native memory reclamation must be encapsulated inside the module, not scattered through player code.

## Session model

Xray state belongs to a playback session, not global app state.

A session is invalidated by at least:

- next/previous/auto-next episode
- VOD line/source/address change
- live channel/source change
- player change
- playback end
- leaving playback UI
- explicit disable
- relevant application background/lifecycle transition

Every invalidation path should converge on one idempotent stop path.

## libXray boundary

The shipped project uses libXray `v26.7.28`.

That version exposes a structured `Invoke(requestJSON)` API and explicitly warns that temporary Xray instances can affect process-wide Xray/DNS/outbound state when overlapping with a running instance. This reinforces keeping runtime/test work serialized or isolated by process.

The module should wrap libXray behind one internal client rather than exposing generated gomobile classes to `app`.

## Upstream update rule

When updating FongMi:

1. update/rebase the FongMi-derived app code;
2. resolve only the small app adapter hooks;
3. keep `xray/` unchanged unless Android/libXray integration itself needs an update;
4. run lifecycle and playback regression tests.

The success criterion is that future FongMi updates do not require reapplying dozens of Xray edits throughout player, live, settings and network classes.
