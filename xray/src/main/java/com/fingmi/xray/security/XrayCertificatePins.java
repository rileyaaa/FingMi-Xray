package com.fingmi.xray.security;

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

public final class XrayCertificatePins {

    private static final String PREFS = "xray_hy2_pins";
    private static final String LEGACY_PREFS = "xray_secure";
    private static final String KEY_ALIAS = "fongmi_xray_hy2_pins_v1";
    private static final String PREFIX = "hy2_pin_";

    private final SharedPreferences preferences;
    private final SharedPreferences legacyPreferences;

    public XrayCertificatePins(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        legacyPreferences = context.getSharedPreferences(LEGACY_PREFS, Context.MODE_PRIVATE);
        migrateLegacyPins();
    }

    public synchronized String get(String identity) throws Exception {
        String key = key(identity);
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
        byte[] encrypted = cipher.doFinal(sha256.getBytes(StandardCharsets.US_ASCII));
        String key = key(identity);

        if (!preferences.edit()
                .putString(key + "_ct", Base64.encodeToString(encrypted, Base64.NO_WRAP))
                .putString(key + "_iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
                .commit()) {
            throw new IllegalStateException("Xray certificate pin was not persisted");
        }
    }

    public synchronized void clear() throws Exception {
        clearPinEntries(preferences);
        clearPinEntries(legacyPreferences);

        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        if (keyStore.containsAlias(KEY_ALIAS)) keyStore.deleteEntry(KEY_ALIAS);
    }

    private void migrateLegacyPins() {
        try {
            SharedPreferences.Editor target = preferences.edit();
            SharedPreferences.Editor source = legacyPreferences.edit();
            boolean targetChanged = false;
            boolean sourceChanged = false;

            for (Map.Entry<String, ?> entry : legacyPreferences.getAll().entrySet()) {
                if (!entry.getKey().startsWith(PREFIX) || !(entry.getValue() instanceof String value)) {
                    continue;
                }
                if (!preferences.contains(entry.getKey())) {
                    target.putString(entry.getKey(), value);
                    targetChanged = true;
                }
                source.remove(entry.getKey());
                sourceChanged = true;
            }

            if (!targetChanged || target.commit()) {
                if (sourceChanged) source.commit();
            }
        } catch (RuntimeException ignored) {
            // Migration is best effort. Existing encrypted pins remain usable
            // in their old store until a later successful migration/reset.
        }
    }

    private static void clearPinEntries(SharedPreferences prefs) {
        SharedPreferences.Editor editor = prefs.edit();
        for (String key : prefs.getAll().keySet()) {
            if (key.startsWith(PREFIX)) editor.remove(key);
        }
        if (!editor.commit()) {
            throw new IllegalStateException("Xray certificate pins were not removed");
        }
    }

    private static String key(String identity) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256")
                .digest(identity.getBytes(StandardCharsets.UTF_8));
        StringBuilder result = new StringBuilder(PREFIX);
        for (byte value : digest) {
            result.append(String.format(Locale.ROOT, "%02x", value & 0xff));
        }
        return result.toString();
    }

    private static SecretKey getOrCreateKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        KeyStore.Entry entry = keyStore.getEntry(KEY_ALIAS, null);
        if (entry instanceof KeyStore.SecretKeyEntry secretKeyEntry) {
            return secretKeyEntry.getSecretKey();
        }

        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES,
                "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build());
        return generator.generateKey();
    }
}
