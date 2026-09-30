#!/usr/bin/env python3
"""Guard core Xray behavior recovered from v5.6.0-xray.5."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    text = read(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"{path}: missing released-Xray contract: {missing}")


def forbid(path: str, *needles: str) -> None:
    text = read(path)
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"{path}: released-Xray contract forbids: {present}")


def normalized_java_mirror(path: str, package_name: str, class_name: str) -> str:
    text = read(path)
    text = re.sub(r"/\\*.*?\\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\\n]*", "", text)
    text = text.replace(f"package {package_name};", "package parity;")
    text = text.replace(class_name, "PlaybackDestinationInterceptor")
    return " ".join(text.split())


current_destination = normalized_java_mirror(
    "xray/src/main/java/com/fingmi/xray/network/PublicPlaybackDestinationInterceptor.java",
    "com.fingmi.xray.network",
    "PublicPlaybackDestinationInterceptor",
)
released_destination = normalized_java_mirror(
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyPublicPlaybackDestinationInterceptor.java",
    "com.fongmi.android.tv.xray.legacy",
    "LegacyPublicPlaybackDestinationInterceptor",
)
if current_destination != released_destination:
    raise SystemExit(
        "PublicPlaybackDestinationInterceptor diverged from the released qz3 behavioral mirror"
    )


current_proxy_socket = normalized_java_mirror(
    "xray/src/main/java/com/fingmi/xray/network/XrayProxySocketFactory.java",
    "com.fingmi.xray.network",
    "XrayProxySocketFactory",
)
released_proxy_socket = normalized_java_mirror(
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayProxySocketFactory.java",
    "com.fongmi.android.tv.xray.legacy",
    "LegacyXrayProxySocketFactory",
)
if current_proxy_socket != released_proxy_socket:
    raise SystemExit(
        "XrayProxySocketFactory diverged from the released oz3 behavioral mirror"
    )


require(
    "xray/src/main/AndroidManifest.xml",
    'android:name=".service.XrayService"',
    'android:exported="false"',
    'android:process=":xray"',
)
forbid(
    "xray/src/main/AndroidManifest.xml",
    "VpnService",
    "android.permission.BIND_VPN_SERVICE",
)

require(
    "xray/src/main/java/com/fingmi/xray/config/XrayShareLinkNormalizer.java",
    '"vless".equals(scheme)',
    '"vmess".equals(scheme)',
    '"trojan".equals(scheme)',
    '"ss".equals(scheme)',
    '"hy2".equals(scheme)',
    '"hysteria2".equals(scheme)',
    "normalizeLegacyShadowsocks(",
    "normalizeShadowsocksPlugin(",
    "ensureTrojanTls(",
    "normalizeHysteria2(",
    "normalizeHysteriaAuthorityPortHopping(",
    "ensureHysteriaDefaultPort(",
    "validateHysteriaObfuscation(",
    "validateVmessJsonPorts(",
)

require(
    "xray/src/main/java/com/fingmi/xray/config/XrayDisplay.java",
    'return "Not configured";',
    'uri.getScheme().toUpperCase(Locale.ROOT)',
    'if (host.length() <= 2)',
    'host.charAt(0)',
    '+ "***"',
    'host.substring(lastDot)',
    '(port > 0 ? ":" + port : "")',
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java",
    "XrayDisplay.describe(preferences.getShareLink())",
    "mBinding.xrayText.setText(R.string.xray_not_configured);",
)

require(
    "xray/src/main/java/com/fingmi/xray/config/XrayPreferences.java",
    'PREFS = "xray_secure"',
    'KEY_ALIAS = "fongmi_xray_share_link_v1"',
    'LINK_CIPHERTEXT = "link_ciphertext"',
    'LINK_IV = "link_iv"',
    'UDP = "udp"',
    "AES/GCM/NoPadding",
    "XrayShareLinkNormalizer.normalize(plaintext)",
)

require(
    "xray/src/main/java/com/fingmi/xray/config/XrayConfigFactory.java",
    'PROXY_TAG = "fongmi-xray-proxy"',
    'PRIVATE_BLOCK_TAG = "fongmi-xray-private-block"',
    'SESSION_INBOUND_TAG = "fongmi-xray-session"',
    'DNS_TAG = "fongmi-xray-dns"',
    'proxy.put("targetStrategy", "ForceIP")',
    'sockopt.put("domainStrategy", "AsIs")',
    '.put("auth", "noauth")',
    '.put("udp", udp)',
    '"https://1.1.1.1/dns-query"',
    '"https://8.8.8.8/dns-query"',
    '.put("network", "tcp,udp")',
)

require(
    "xray/src/main/java/com/fingmi/xray/core/LibXrayBridge.java",
    'outbound.put("targetStrategy", "AsIs")',
    '"pingBatch"',
    '.put("timeout", 10)',
    '.put("url", "https://www.gstatic.com/generate_204")',
    '"testXray"',
    '"runXray"',
    '"stopXray"',
)

require(
    "xray/src/main/java/com/fingmi/xray/security/XrayShareLinkSecurity.java",
    "PROBE_TIMEOUT_MS = 10_000",
    "probeHysteria2Certificate(",
    "probeTlsCertificate(",
    "requestsInsecure(",
    "pins.get(identity)",
    "pins.put(identity, normalizedObserved)",
)

require(
    "xray/src/main/java/com/fingmi/xray/security/XrayCertificatePins.java",
    'PREFS = "xray_hy2_pins"',
    'LEGACY_PREFS = "xray_secure"',
    'KEY_ALIAS = "fongmi_xray_hy2_pins_v1"',
    'PIN_PREFIX = "hy2_pin_"',
    "AES/GCM/NoPadding",
    "migrateLegacyPins(",
    "deleteEncryptionKey()",
)

require(
    "xray/src/main/java/com/fingmi/xray/network/XrayHttpClient.java",
    "closed.compareAndSet(false, true)",
    "new Dispatcher()",
    "new ConnectionPool(5, 5, TimeUnit.MINUTES)",
    'InetSocketAddress.createUnresolved("127.0.0.1", socksPort)',
    ".cache(null)",
    ".proxy(proxy)",
    ".addNetworkInterceptor(new PublicPlaybackDestinationInterceptor())",
    "public OkHttpClient client() {\n        return client;\n    }",
    "public XrayProxySocketFactory rtspSocketFactory() {\n        return rtspSocketFactory;\n    }",
    "dispatcher.executorService().shutdown();",
    "dispatcher.cancelAll();",
    "connectionPool.evictAll();",
)
forbid(
    "xray/src/main/java/com/fingmi/xray/network/XrayHttpClient.java",
    'if (closed.get()) throw new IllegalStateException("Xray HTTP client is closed")',
)

require(
    "xray/src/main/java/com/fingmi/xray/network/XrayProxySocketFactory.java",
    "return new Socket(proxy);",
    "InetSocketAddress.createUnresolved(host, port)",
    "socket.bind(new InetSocketAddress(localAddress, localPort));",
)

require(
    "xray/src/main/java/com/fingmi/xray/service/XrayGenerationGate.java",
    "current.accumulateAndGet(operationId, Math::max)",
    "current.compareAndSet(operationId, Long.MAX_VALUE)",
    "current.set(Long.MAX_VALUE)",
)
forbid(
    "xray/src/main/java/com/fingmi/xray/service/XrayGenerationGate.java",
    "current.set(operationId)",
    "getAndSet(",
)



require(
    "xray/src/main/java/com/fingmi/xray/service/XrayService.java",
    "for (int attempt = 0; attempt < 3; attempt++)",
    "bridge.validateConfig(config)",
    "bridge.testLatency(config, XrayConfigFactory.PROXY_TAG)",
    "bridge.run(config)",
    "if (!bridge.isRunning())",
    "for (int attempt = 0; attempt < 2; attempt++)",
    "XrayCertificatePins.resetAll(this)",
    'value.contains("address already in use")',
    'value.contains("failed to listen")',
    "if (!cleaned || !delivered) cancelInternal(XrayOperation.START, operationId);",
    "if (!delivered) cancelInternal(XrayOperation.STOP, operationId);",
    "sessionGate.cancel(operationId)",
    "operationGate.cancel(operationId)",
    "sessionGate.invalidateAll();",
    "operationGate.invalidateAll();",
    "killPrivateProcess();",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySessionController.java",
    "CLEANUP_TIMEOUT_MS = 1_500L",
    "STARTUP_TIMEOUT_MS = 30_000L",
    "Previous Xray session cleanup timed out",
    "if (state != XraySessionListener.RUNNING)",
    "fail(\"Xray startup timed out\");\n            serviceClient.cancel(XrayOperation.START, operationId);",
    "fail(result.message);\n                serviceClient.disconnect();",
    "notifyState(XraySessionListener.ERROR, 0, safe);\n        notifyState(XraySessionListener.IDLE, 0, \"\");",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySettingsController.java",
    "OPERATION_TIMEOUT_MS = 45_000L",
    "XrayOperation.VALIDATE",
    "XrayOperation.TEST",
    "XrayOperation.RESET_SECURITY",
    "replaceClient()",
    "replaceClient();\n        try {\n            preferences.clear();",
    "if (onLocalCleared != null) onLocalCleared.run();\n\n            serviceClient.execute",
)

require(
    "app/src/leanback/res/layout/activity_setting_xray.xml",
    'android:id="@+id/udpSwitch"',
    'android:id="@+id/save"',
    'android:id="@+id/test"',
    'android:id="@+id/phone"',
    'android:id="@+id/delete"',
)

require(
    "app/src/leanback/res/layout/view_control_vod_action.xml",
    'android:id="@+id/xray"',
    'android:text="@string/xray_off"',
)

require(
    "app/src/leanback/res/layout/view_control_live_action.xml",
    'android:id="@+id/xray"',
    'android:text="@string/xray_off"',
)

require(
    "app/src/leanback/res/values/strings.xml",
    'name="xray_changed_retry"',
    'name="xray_phone_scan_info"',
    'name="xray_public_http_required"',
    'name="xray_vod_public_http_required"',
    'name="xray_test_success"',
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingXrayActivity.java",
    "PushActivity.start(this, 6);",
    "@Subscribe(threadMode = ThreadMode.MAIN)",
    "if (event == null || isBlank(event.link())) return;",
    "if (mOperationId != Long.MIN_VALUE && mOperation != XrayOperation.RESET_SECURITY)",
    "mXray.abandon();",
    "String link = event.link().trim();",
    "mBinding.link.setText(link);",
    "if (finishedOperation == XrayOperation.TEST && !testInputUnchanged())",
    "Notify.show(R.string.xray_changed_retry);",
    "XrayShareLinkNormalizer.normalize(readLink()).equals(mTestLink)",
    "mBinding.udpSwitch.isChecked() == mTestUdp",
)
forbid(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingXrayActivity.java",
    "mXray.save(link",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/PushActivity.java",
    "intent.putExtra(\"tab\", tab);",
    "if (getTab() == 6)",
    "R.string.xray_phone_scan_info",
    "mBinding.clip.setVisibility(View.GONE);",
)

require(
    "app/src/main/assets/index.html",
    '<textarea id="xray_link"',
    'onclick="sendXray()"',
    '<span class="md-nav-label">Xray</span>',
)

require(
    "app/src/main/assets/js/script.js",
    "function sendXray()",
    "const link = $('#xray_link').val().trim();",
    "doAction('xray', { link });",
    "$('#xray_link').val('');",
)

require(
    "app/src/main/java/com/fongmi/android/tv/server/process/Action.java",
    'case "xray" -> onXray(params);',
    'String link = params.get("link");',
    "if (TextUtils.isEmpty(link)) return;",
    "XrayImportEvent.post(link.trim());",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/base/BaseActivity.java",
    "EventBus.getDefault().register(this);",
    "EventBus.getDefault().unregister(this);",
)

require(
    "xray/src/main/java/com/fingmi/xray/util/XrayErrorSanitizer.java",
    '"password"',
    '"passwd"',
    '"token"',
    '"secret"',
    '"auth"',
    '"obfs-password"',
    '"uuid"',
    '"privatekey"',
    '"publickey"',
    '"shortid"',
    '"seed"',
    "<redacted-share-link>",
    "<redacted-uuid>",
    "<redacted>",
    "result.length() > 1024 ? result.substring(0, 1024) : result",
)

require(
    "xray/src/main/java/com/fingmi/xray/service/XrayService.java",
    "XrayErrorSanitizer.sanitize(message)",
    "return XrayErrorSanitizer.fromException(error);",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySettingsController.java",
    "XrayErrorSanitizer.sanitize(result.message)",
    "XrayErrorSanitizer.sanitize(message)",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingXrayActivity.java",
    "Notify.show(XrayErrorSanitizer.sanitize(error));",
)

# Keep the recovered behavioral reference in-tree so future refactors can be
# checked against the decompiled v5.6.0-xray.5 reconstruction rather than memory.
for reference in (
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayShareLinkNormalizer.java",
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayRuntimeConfigFactory.java",
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXraySessionController.java",
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXraySettingsController.java",
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayProxySocketFactory.java",
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayGenerationGate.java",
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayErrorSanitizer.java",
    "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyPublicPlaybackDestinationInterceptor.java",
    "docs/apk-reference/shared/sources/p000/pz3.java",
    "docs/apk-reference/shared/sources/p000/nz3.java",
):
    if not (ROOT / reference).is_file():
        raise SystemExit(f"missing released-Xray behavioral reference: {reference}")

print("Xray core released-behavior parity guards passed")
