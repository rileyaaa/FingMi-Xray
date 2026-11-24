package com.fingmi.xray.config;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * Behavior-faithful reconstruction of the shipped saved-node store (R8 name: lu2).
 */
public final class XrayPreferences {

    public static final String PREFS = "xray_secure";
    public static final String KEY_ALIAS = "fongmi_xray_share_link_v1";

    private static final String LINK_CIPHERTEXT = "link_ciphertext";
    private static final String LINK_IV = "link_iv";
    private static final String UDP = "udp";
    private static final String TLS_FRAGMENT = "tls_fragment";
    private static final String LIVE_GROUPS = "live_auto_groups";
    private static final String LIVE_CHANNELS = "live_auto_channels";

    private final SharedPreferences preferences;

    public XrayPreferences(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public synchronized boolean isConfigured() {
        return preferences.contains(LINK_CIPHERTEXT)
                && preferences.contains(LINK_IV);
    }

    public synchronized String getShareLink() throws Exception {
        if (!isConfigured()) return "";

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(
                Cipher.DECRYPT_MODE,
                getOrCreateKey(),
                new GCMParameterSpec(
                        128,
                        Base64.decode(preferences.getString(LINK_IV, ""), Base64.NO_WRAP)));

        String plaintext = new String(
                cipher.doFinal(
                        Base64.decode(
                                preferences.getString(LINK_CIPHERTEXT, ""),
                                Base64.NO_WRAP)),
                StandardCharsets.UTF_8);

        // The shipped build re-runs the compatibility normalizer on read.
        return XrayShareLinkNormalizer.normalize(plaintext);
    }

    public synchronized boolean isUdpEnabled() {
        return preferences.getBoolean(UDP, false);
    }

    public synchronized boolean isTlsFragmentEnabled() {
        return preferences.getBoolean(TLS_FRAGMENT, false);
    }

    public synchronized String getLiveAutoGroups() {
        return preferences.getString(LIVE_GROUPS, "");
    }

    public synchronized String getLiveAutoChannels() {
        return preferences.getString(LIVE_CHANNELS, "");
    }

    public synchronized void save(String shareLink, boolean udp) throws Exception {
        save(shareLink, udp, false);
    }

    public synchronized void save(String shareLink, boolean udp, boolean tlsFragment) throws Exception {
        save(shareLink, udp, tlsFragment, getLiveAutoGroups(), getLiveAutoChannels());
    }

    public synchronized void save(String shareLink, boolean udp, boolean tlsFragment,
                                  String groups, String channels) throws Exception {
        XrayLiveAutoRules rules = new XrayLiveAutoRules(groups, channels);
        String normalized = XrayShareLinkNormalizer.normalize(shareLink);

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());

        if (!preferences.edit()
                .putString(
                        LINK_CIPHERTEXT,
                        Base64.encodeToString(
                                cipher.doFinal(normalized.getBytes(StandardCharsets.UTF_8)),
                                Base64.NO_WRAP))
                .putString(
                        LINK_IV,
                        Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                .putBoolean(UDP, udp)
                .putBoolean(TLS_FRAGMENT, tlsFragment)
                .putString(LIVE_GROUPS, rules.groups())
                .putString(LIVE_CHANNELS, rules.channels())
                .commit()) {
            throw new IllegalStateException("Unable to persist Xray configuration");
        }
    }

    public synchronized void clear() throws Exception {
        if (!preferences.edit()
                .remove(LINK_CIPHERTEXT)
                .remove(LINK_IV)
                .remove(UDP)
                .remove(TLS_FRAGMENT)
                .remove(LIVE_GROUPS)
                .remove(LIVE_CHANNELS)
                .commit()) {
            throw new IllegalStateException("Unable to remove Xray configuration");
        }

        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        if (keyStore.containsAlias(KEY_ALIAS)) {
            keyStore.deleteEntry(KEY_ALIAS);
        }
    }

    private static SecretKey getOrCreateKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);

        KeyStore.Entry entry = keyStore.getEntry(KEY_ALIAS, null);
        if (entry instanceof KeyStore.SecretKeyEntry) {
            return ((KeyStore.SecretKeyEntry) entry).getSecretKey();
        }

        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES,
                "AndroidKeyStore");
        generator.init(
                new KeyGenParameterSpec.Builder(
                        KEY_ALIAS,
                        KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                        .setRandomizedEncryptionRequired(true)
                        .build());
        return generator.generateKey();
    }
}

