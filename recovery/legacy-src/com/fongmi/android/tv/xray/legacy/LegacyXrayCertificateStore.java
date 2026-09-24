package com.fongmi.android.tv.xray.legacy;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * Behavior-faithful reconstruction of the shipped certificate-pin store
 * (the Xray-specific responsibilities recovered from R8 class j81).
 */
public final class LegacyXrayCertificateStore {

    public static final String PREFS = "xray_hy2_pins";
    public static final String LEGACY_PREFS = "xray_secure";
    public static final String KEY_ALIAS = "fongmi_xray_hy2_pins_v1";

    private static final String PIN_PREFIX = "hy2_pin_";

    private final SharedPreferences preferences;

    public LegacyXrayCertificateStore(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        migrateLegacyPins(
                preferences,
                context.getSharedPreferences(LEGACY_PREFS, Context.MODE_PRIVATE));
    }

    public synchronized String get(String identity) throws Exception {
        String key = pinKey(identity);
        String ciphertext = preferences.getString(key + "_ct", "");
        String iv = preferences.getString(key + "_iv", "");
        if (ciphertext.isEmpty() || iv.isEmpty()) return "";

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(
                Cipher.DECRYPT_MODE,
                getOrCreateKey(),
                new GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)));
        return new String(
                cipher.doFinal(Base64.decode(ciphertext, Base64.NO_WRAP)),
                StandardCharsets.US_ASCII);
    }

    public synchronized void put(String identity, String sha256) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());

        byte[] ciphertext = cipher.doFinal(sha256.getBytes(StandardCharsets.US_ASCII));
        String key = pinKey(identity);
        if (!preferences.edit()
                .putString(
                        key + "_ct",
                        Base64.encodeToString(ciphertext, Base64.NO_WRAP))
                .putString(
                        key + "_iv",
                        Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                .commit()) {
            throw new IllegalStateException("Hysteria2 certificate pin was not persisted");
        }
    }

    public synchronized void clearPins() {
        SharedPreferences.Editor editor = preferences.edit();
        for (String key : preferences.getAll().keySet()) {
            if (key.startsWith(PIN_PREFIX)) {
                editor.remove(key);
            }
        }
        if (!editor.commit()) {
            throw new IllegalStateException("Hysteria2 certificate pins were not removed");
        }
    }

    public static void deleteEncryptionKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        if (keyStore.containsAlias(KEY_ALIAS)) {
            keyStore.deleteEntry(KEY_ALIAS);
        }
    }

    private static synchronized void migrateLegacyPins(
            SharedPreferences current,
            SharedPreferences legacy) {
        SharedPreferences.Editor currentEditor = current.edit();
        SharedPreferences.Editor legacyEditor = legacy.edit();
        boolean legacyChanged = false;
        boolean currentChanged = false;

        for (Map.Entry<String, ?> entry : legacy.getAll().entrySet()) {
            if (!entry.getKey().startsWith(PIN_PREFIX)) continue;
            if (!(entry.getValue() instanceof String)) continue;

            if (!current.contains(entry.getKey())) {
                currentEditor.putString(entry.getKey(), (String) entry.getValue());
                currentChanged = true;
            }
            legacyEditor.remove(entry.getKey());
            legacyChanged = true;
        }

        if (!legacyChanged) return;

        // Shipped behavior: never delete the old copy if writing a newly migrated
        // value into the new store failed.
        if (!currentChanged || currentEditor.commit()) {
            legacyEditor.commit();
        }
    }

    private static String pinKey(String identity) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256")
                .digest(identity.getBytes(StandardCharsets.UTF_8));
        StringBuilder result = new StringBuilder(PIN_PREFIX);
        for (byte value : digest) {
            result.append(String.format(Locale.ROOT, "%02x", value & 0xff));
        }
        return result.toString();
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
