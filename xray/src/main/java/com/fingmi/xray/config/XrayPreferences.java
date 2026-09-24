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

public final class XrayPreferences {

    private static final String PREFS = "xray_secure";
    private static final String KEY_ALIAS = "fongmi_xray_share_link_v1";
    private static final String LINK_CIPHERTEXT = "link_ciphertext";
    private static final String LINK_IV = "link_iv";
    private static final String UDP = "udp";

    private final SharedPreferences preferences;

    public XrayPreferences(Context context) {
        this.preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public synchronized boolean isConfigured() {
        return preferences.contains(LINK_CIPHERTEXT) && preferences.contains(LINK_IV);
    }

    public synchronized String getShareLink() throws Exception {
        if (!isConfigured()) return "";
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        byte[] iv = Base64.decode(preferences.getString(LINK_IV, ""), Base64.NO_WRAP);
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), new GCMParameterSpec(128, iv));
        byte[] encrypted = Base64.decode(preferences.getString(LINK_CIPHERTEXT, ""), Base64.NO_WRAP);
        return new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8).trim();
    }

    public synchronized boolean isUdpEnabled() {
        return preferences.getBoolean(UDP, false);
    }

    public synchronized void save(String shareLink, boolean udp) throws Exception {
        String normalized = shareLink == null ? "" : shareLink.trim();
        if (normalized.isEmpty()) throw new IllegalArgumentException("Xray link is empty");

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        String ciphertext = Base64.encodeToString(
                cipher.doFinal(normalized.getBytes(StandardCharsets.UTF_8)),
                Base64.NO_WRAP);
        String iv = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP);

        if (!preferences.edit()
                .putString(LINK_CIPHERTEXT, ciphertext)
                .putString(LINK_IV, iv)
                .putBoolean(UDP, udp)
                .commit()) {
            throw new IllegalStateException("Xray configuration was not persisted");
        }
    }

    public synchronized void clear() throws Exception {
        if (!preferences.edit()
                .remove(LINK_CIPHERTEXT)
                .remove(LINK_IV)
                .remove(UDP)
                .commit()) {
            throw new IllegalStateException("Xray configuration was not removed");
        }

        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        if (keyStore.containsAlias(KEY_ALIAS)) keyStore.deleteEntry(KEY_ALIAS);
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
