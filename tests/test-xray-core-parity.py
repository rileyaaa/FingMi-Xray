#!/usr/bin/env python3
"""Guard core Xray behavior recovered from v5.6.0-xray.5."""

from pathlib import Path
import re
import subprocess
import sys

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


JAVA_COMMENT_OR_LITERAL = re.compile(
    r'"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
    r"|/\*[\s\S]*?\*/|//[^\r\n]*"
)


def strip_java_comments(text: str) -> str:
    # Match literals before comments so URLs, cipher names and escaped quotes
    # cannot hide executable-code differences from the behavioral mirror.
    return JAVA_COMMENT_OR_LITERAL.sub(
        lambda match: " " if match.group().startswith(("//", "/*")) else match.group(),
        text,
    )


def check_comment_stripping() -> None:
    literals = r"""String cipher = "AES/GCM/NoPadding";
String url = "https://example.invalid/a/*literal*/";
String escaped = "quote: \" // still a string";
char quote = '\''; char slash = '/';"""
    with_comments = "/* removed block */\n" + literals + " // removed line\n"
    if strip_java_comments(with_comments).strip() != literals:
        raise SystemExit("Java mirror comment stripping altered string/char literals")
    original = "".join(strip_java_comments(with_comments).split())
    changed = "".join(strip_java_comments(
        with_comments.replace("AES/GCM/NoPadding", "AES/ECB/NoPadding")).split())
    if original == changed:
        raise SystemExit("Java mirror comment stripping hid an AES mode change")


check_comment_stripping()


def normalized_java_mirror(path: str, package_name: str, class_name: str) -> str:
    text = read(path)
    text = strip_java_comments(text)
    text = text.replace(f"package {package_name};", "package parity;")
    text = text.replace(class_name, "PlaybackDestinationInterceptor")
    return " ".join(text.split())


def normalized_legacy_mirror(path: str, package_name: str, class_name: str) -> str:
    text = read(path)
    if class_name == "XrayPreferences":
        # User-authorized optional TLS fragmentation adds one default-off flag.
        # Project only that extension out; the released encrypted store remains
        # an exact mirror, including its save/clear failure behavior.
        text = text.replace('    private static final String TLS_FRAGMENT = "tls_fragment";\n', '')
        text = text.replace('''    public synchronized boolean isTlsFragmentEnabled() {
        return preferences.getBoolean(TLS_FRAGMENT, false);
    }
''', '')
        text = text.replace('''    public synchronized void save(String shareLink, boolean udp) throws Exception {
        save(shareLink, udp, false);
    }
''', '')
        text = text.replace('save(String shareLink, boolean udp, boolean tlsFragment)',
                            'save(String shareLink, boolean udp)')
        text = text.replace('.putBoolean(TLS_FRAGMENT, tlsFragment)', '')
        text = text.replace('.remove(TLS_FRAGMENT)', '')
    text = strip_java_comments(text)
    text = re.sub(r"^package .*?$", "", text, flags=re.M)
    text = re.sub(r"^import .*?$", "", text, flags=re.M)
    text = text.replace(class_name, "Mirror")
    text = text.replace("Legacy", "")
    return "".join(text.split())


for current_path, current_package, current_class, legacy_path, legacy_package, legacy_class in (
    (
        "xray/src/main/java/com/fingmi/xray/config/XrayPreferences.java",
        "com.fingmi.xray.config",
        "XrayPreferences",
        "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayConfigStore.java",
        "com.fongmi.android.tv.xray.legacy",
        "LegacyXrayConfigStore",
    ),
    (
        "xray/src/main/java/com/fingmi/xray/security/XrayCertificatePins.java",
        "com.fingmi.xray.security",
        "XrayCertificatePins",
        "recovery/legacy-src/com/fongmi/android/tv/xray/legacy/LegacyXrayCertificateStore.java",
        "com.fongmi.android.tv.xray.legacy",
        "LegacyXrayCertificateStore",
    ),
):
    current_mirror = normalized_legacy_mirror(current_path, current_package, current_class)
    legacy_mirror = normalized_legacy_mirror(legacy_path, legacy_package, legacy_class)
    if current_mirror != legacy_mirror:
        raise SystemExit(
            f"{current_class} diverged from the released v5.6.0-xray.5 behavioral mirror"
        )
    if current_class == "XrayPreferences":
        # A real encrypted-store difference must survive the TLS-flag projection
        # and comment stripping, otherwise the equality above proves too little.
        changed_cipher = current_mirror.replace("AES/GCM/NoPadding", "AES/ECB/NoPadding")
        if changed_cipher == current_mirror or changed_cipher == legacy_mirror:
            raise SystemExit("XrayPreferences mirror failed to detect an AES mode change")


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
# Current intentionally denies local/reserved absolute DNS names as well as
# their undotted equivalents. Project out only this reviewed extension; the
# rest of qz3 (including all reserved-address ranges) remains an exact mirror.
root_dot_guard = (
    'while (value.endsWith(".")) { value = value.substring(0, value.length() - 1); } '
    'if (value.isEmpty()) return true; '
)
if current_destination.count(root_dot_guard) != 1:
    raise SystemExit("PublicPlaybackDestinationInterceptor lost the DNS root-dot guard")
if current_destination.replace(root_dot_guard, "", 1) != released_destination:
    raise SystemExit(
        "PublicPlaybackDestinationInterceptor diverged outside the documented qz3 root-dot repair"
    )


# oz3 is retained as the released behavioral reference, but current intentionally
# fixes its failed bind/connect socket leak. Address-resolution and SOCKS semantics
# remain guarded below instead of requiring byte-for-byte mirror equality.


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
    'TLS_FRAGMENT = "tls_fragment"',
    'preferences.getBoolean(TLS_FRAGMENT, false)',
    '.putBoolean(TLS_FRAGMENT, tlsFragment)',
    '.remove(TLS_FRAGMENT)',
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
    '"::ffff:0:0:0/96"',
)

forbid(
    "xray/src/main/java/com/fingmi/xray/core/LibXrayBridge.java",
    "System.err.println",
    "FingMiXray native invoke begin",
    "FingMiXray native invoke end",
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
    "pins.put(identity, fingerprint)",
)

require(
    "xray/src/main/java/com/fingmi/xray/security/XrayShareLinkSecurity.java",
    "public PreparedLink prepare(String normalizedLink)",
    "PreparedLink prepared = prepare(normalizedLink);",
    "prepared.commitTrust();",
    "new PendingTrust(identity, normalizedObserved, kind)",
    "public void commitTrust() throws Exception",
)

require(
    "xray/src/main/java/com/fingmi/xray/config/XrayConfigFactory.java",
    "public PreparedConfig prepare(int socksPort, String shareLink, boolean udp)",
    "XrayShareLinkSecurity.PreparedLink preparedLink = security.prepare(normalized);",
    "createFromSecuredLink(socksPort, normalized, udp, tlsFragment)",
    "return prepare(socksPort, shareLink, udp, false);",
    "public void commitTrust() throws Exception",
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
    "String target = requirePublicDestination(host);",
    "PublicPlaybackDestinationInterceptor.isPrivateOrReserved(target)",
    "InetSocketAddress.createUnresolved(target, port)",
    "socket.bind(new InetSocketAddress(localAddress, localPort));",
    "catch (IOException | RuntimeException error)",
    "closeQuietly(socket);",
    "private static void closeQuietly(Socket socket)",
    "socket.close();",
)

proxy_socket_source = read(
    "xray/src/main/java/com/fingmi/xray/network/XrayProxySocketFactory.java"
)
# The two hostname overloads must connect to the guarded, normalized
# target, not resolve the original hostname locally or bypass the check.
if (proxy_socket_source.count("String target = requirePublicDestination(host);") != 2
        or proxy_socket_source.count("InetSocketAddress.createUnresolved(target, port)") != 2):
    raise SystemExit("Both RTSP hostname overloads must use the validated unresolved target")
if proxy_socket_source.count("closeQuietly(socket);") != 4:
    raise SystemExit(
        "Xray RTSP socket factory must close every newly-created SOCKS socket when bind/connect fails"
    )

require(
    "xray/src/main/java/com/fingmi/xray/service/XrayGenerationGate.java",
    "synchronized void begin(long operationId)",
    "current.accumulateAndGet(operationId, Math::max)",
    "synchronized boolean cancel(long operationId)",
    "current.compareAndSet(operationId, Long.MAX_VALUE)",
    "synchronized void invalidateAll()",
    "current.set(Long.MAX_VALUE)",
    "synchronized boolean runIfCurrent(long operationId, ThrowingAction action)",
    "action.run();",
)
forbid(
    "xray/src/main/java/com/fingmi/xray/service/XrayGenerationGate.java",
    "current.set(operationId)",
    "getAndSet(",
)



require(
    "xray/src/main/java/com/fingmi/xray/service/XrayService.java",
    "for (int attempt = 0; attempt < 3; attempt++)",
    "configFactory.prepare(port, shareLink, udp, tlsFragment)",
    "XrayConfigFactory.PreparedConfig prepared",
    "bridge.validateConfig(config)",
    "bridge.testLatency(config, XrayConfigFactory.PROXY_TAG)",
    "bridge.run(config)",
    "commitOperationTrust(operationId, prepared);",
    "operationGate.runIfCurrent(operationId, prepared::commitTrust)",
    "sessionGate.runIfCurrent(operationId, prepared::commitTrust)",
    "if (!bridge.isRunning())",
    "for (int attempt = 0; attempt < 2; attempt++)",
    "catch (Exception | LinkageError ignored)",
    "callback.onResult(",
    "} catch (Exception | LinkageError ignored) {",
    "XrayCertificatePins.resetAll(this)",
    "if (!operationGate.runIfCurrent(operationId, () -> {",
    "XrayCertificatePins.resetAll(this);",
    "certificatePins = new XrayCertificatePins(this);",
    "ensureOperationCurrent(operationId);\n            send(callback, operationId, XrayOperation.RESET_SECURITY, true",
    'value.contains("address already in use")',
    'value.contains("failed to listen")',
    "if (!cleaned || !delivered) cancelInternal(XrayOperation.START, operationId);",
    "if (!delivered) cancelInternal(XrayOperation.STOP, operationId);",
    "if (!sessionGate.isCurrent(operationId)) {\n            send(callback, operationId, XrayOperation.STOP, true",
    "if (!sessionGate.isCurrent(operationId)) {\n                send(callback, operationId, XrayOperation.STOP, true",
    "sessionGate.cancel(operationId)",
    "operationGate.cancel(operationId)",
    "sessionGate.invalidateAll();",
    "operationGate.invalidateAll();",
    "killPrivateProcess();",
    'new Thread(runnable, "fongmi-xray-core")',
)

require(
    "xray/src/main/java/com/fingmi/xray/core/LibXrayBridge.java",
    'outbound.put("targetStrategy", "AsIs");',
    '"pingBatch"',
    '.put("timeout", 10)',
    '.put("url", "https://www.gstatic.com/generate_204")',
    '"Xray connectivity test returned no result"',
)

require(
    "xray/src/main/java/com/fingmi/xray/security/XrayCertificatePins.java",
    'PREFS = "xray_hy2_pins"',
    'LEGACY_PREFS = "xray_secure"',
    'KEY_ALIAS = "fongmi_xray_hy2_pins_v1"',
    "XrayCertificatePins current = new XrayCertificatePins(context);",
    "clearPins(\n                context.getSharedPreferences(\n                        LEGACY_PREFS",
    "current.clearPins();",
    "deleteEncryptionKey();",
    'KeyStore.getInstance("AndroidKeyStore")',
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySessionController.java",
    "CLEANUP_TIMEOUT_MS = 1_500L",
    "STARTUP_TIMEOUT_MS = 30_000L",
    "Previous Xray session cleanup timed out",
    "abortReplacementStartAfterCleanupFailure(",
    "currentOperationId = NO_OPERATION;",
    "if (currentOperationId == NO_OPERATION) {\n            serviceClient.cancel(XrayOperation.START, replacementOperationId);",
    "fail(\"Xray startup timed out\");\n            if (currentOperationId == operationId) {\n                serviceClient.cancel(XrayOperation.START, operationId);",
    "fail(result.message);\n                if (currentOperationId == result.operationId) {\n                    serviceClient.disconnect();",
    "notifyState(XraySessionListener.ERROR, 0, safe);",
    "if (state == XraySessionListener.IDLE) {\n            notifyState(XraySessionListener.IDLE, 0, \"\");",
    "if (currentOperationId == operationId) {\n            serviceClient.disconnect();",
    "if (currentOperationId == result.operationId) {\n                serviceClient.cancel(XrayOperation.STOP, result.operationId);",
    "serviceClient.execute(new XrayServiceClient.Request(\n                    operationId,\n                    XrayOperation.START",
    "() -> scheduleStartupTimeout(operationId)));\n            notifyState(XraySessionListener.STARTING, 0, \"\");",
    "serviceClient.execute(new XrayServiceClient.Request(\n                operationId,\n                XrayOperation.STOP",
    "() -> scheduleCleanupTimeout(operationId)));\n        notifyState(XraySessionListener.IDLE, 0, \"\");",
    "disposed = true;\n        if (state != XraySessionListener.IDLE) {\n            stopSession();",
)

forbid(
    "xray/src/main/java/com/fingmi/xray/session/XraySessionController.java",
    "fail(\"Previous Xray session cleanup timed out\");\n            }\n            serviceClient.cancel(XrayOperation.STOP, operationId);",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XrayServiceClient.java",
    "catch (Exception | LinkageError ignored)",
    "finally {\n            disconnectLocked();",
    "catch (LinkageError error) {\n            failLocked(next, XrayErrorSanitizer.sanitize(error));",
    "service = IXrayService.Stub.asInterface(binder);",
    "catch (RuntimeException error) {\n                    failLocked(this, XrayErrorSanitizer.fromException(error));",
    "catch (LinkageError error) {\n                    failLocked(this, XrayErrorSanitizer.sanitize(error));",
    "binder.unlinkToDeath(this, 0);\n                } catch (Exception | LinkageError ignored)",
    "context.unbindService(old);\n            } catch (RuntimeException | LinkageError ignored)",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySessionController.java",
    "catch (LinkageError error)",
    "finishStartFailure(startOperationId, XrayErrorSanitizer.sanitize(error));",
    "finishStartFailure(startOperationId, XrayErrorSanitizer.fromException(error));",
    "if (disposed || (operationId != NO_OPERATION\n                && currentOperationId != operationId)) return;",
    "if (operationId != NO_OPERATION) currentOperationId = NO_OPERATION;",
    "if (operationId != NO_OPERATION && currentOperationId == NO_OPERATION) {\n                serviceClient.cancel(XrayOperation.START, operationId);",
)

require(
    "app/src/leanback/java/com/fongmi/android/tv/ui/activity/SettingActivity.java",
    "XrayDisplay.describe(preferences.getShareLink())",
    "} catch (Exception | LinkageError ignored) {",
)

require(
    "xray/src/main/java/com/fingmi/xray/session/XraySettingsController.java",
    "OPERATION_TIMEOUT_MS = 45_000L",
    "XrayOperation.VALIDATE",
    "XrayOperation.TEST",
    "XrayOperation.RESET_SECURITY",
    "replaceClient()",
    "replaceClient();\n        XrayServiceClient ownerClient = serviceClient;\n        boolean localClearedCallbackDelivered = false;",
    "localClearedCallbackDelivered = notifyLocalCleared(onLocalCleared);",
    "activeOperationId != operationId",
    "activeOperation != XrayOperation.RESET_SECURITY",
    "serviceClient != ownerClient",
    "ownerClient.execute(new XrayServiceClient.Request(",
    "!localClearedCallbackDelivered && !preferences.isConfigured()",
    "if (!closed\n                    && activeOperationId == operationId\n                    && activeOperation == XrayOperation.RESET_SECURITY\n                    && serviceClient == ownerClient) {\n                clearActive();\n                replaceClient();",
    "private static boolean notifyLocalCleared(Runnable action)",
    "UI cleanup failure must not prevent remote RESET_SECURITY.",
    "XrayServiceClient ownerClient = serviceClient;",
    "activeOperationId == NO_OPERATION\n                && serviceClient == ownerClient",
    "ownerClient.cancel(operation, operationId);",
    "private void notifyResult(",
    "catch (RuntimeException | LinkageError ignored)",
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
    "mBinding.tlsFragmentSwitch.isChecked() == mTestTlsFragment",
    "mBinding.tlsFragmentSwitch.setChecked(mXray.isTlsFragmentEnabled());",
    "mBinding.tlsFragmentSwitch.setChecked(false);",
    "mOperationId = mXray.test(mTestLink, mTestUdp, mTestTlsFragment);",
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
    "Notify.dismiss();",
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

subprocess.run(
    [sys.executable, str(ROOT / "tests/test-xray-service-execution.py")],
    check=True,
)

print("Xray core released-behavior parity guards passed")
