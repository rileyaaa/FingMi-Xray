package p000;

import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.util.Base64;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.InvalidAlgorithmParameterException;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.UnrecoverableEntryException;
import java.security.cert.CertificateException;
import java.util.ArrayList;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

public final class lu2 {

    public final Object f10948a;

    public lu2(AbstractActivityC1828yh abstractActivityC1828yh) {
        this.f10948a = abstractActivityC1828yh.getSharedPreferences("xray_secure", 0);
    }

    public static SecretKey m5929b() throws NoSuchAlgorithmException, IOException, KeyStoreException, CertificateException, NoSuchProviderException, UnrecoverableEntryException, InvalidAlgorithmParameterException {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        KeyStore.Entry entry = keyStore.getEntry("fongmi_xray_share_link_v1", null);
        if (entry instanceof KeyStore.SecretKeyEntry) {
            return ((KeyStore.SecretKeyEntry) entry).getSecretKey();
        }
        KeyGenerator keyGenerator = KeyGenerator.getInstance("AES", "AndroidKeyStore");
        keyGenerator.init(new KeyGenParameterSpec.Builder("fongmi_xray_share_link_v1", 3).setBlockModes("GCM").setEncryptionPaddings("NoPadding").setRandomizedEncryptionRequired(true).build());
        return keyGenerator.generateKey();
    }

    public synchronized void m5930a() {
        if (!((SharedPreferences) this.f10948a).edit().remove("link_ciphertext").remove("link_iv").remove("udp").commit()) {
            throw new IllegalStateException("Unable to remove Xray configuration");
        }
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        if (keyStore.containsAlias("fongmi_xray_share_link_v1")) {
            keyStore.deleteEntry("fongmi_xray_share_link_v1");
        }
    }

    public synchronized ArrayList m5931c(Class cls, Class cls2) {
        ArrayList arrayList = new ArrayList();
        if (cls2.isAssignableFrom(cls)) {
            arrayList.add(cls2);
            return arrayList;
        }
        for (hl3 hl3Var : (ArrayList) this.f10948a) {
            if ((hl3Var.f7337a.isAssignableFrom(cls) && cls2.isAssignableFrom(hl3Var.f7338b)) && !arrayList.contains(hl3Var.f7338b)) {
                arrayList.add(hl3Var.f7338b);
            }
        }
        return arrayList;
    }

    public synchronized boolean m5932d() {
        return ((SharedPreferences) this.f10948a).contains("link_ciphertext") && ((SharedPreferences) this.f10948a).contains("link_iv");
    }

    public synchronized String m5933e() {
        if (!m5932d()) {
            return "";
        }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(2, m5929b(), new GCMParameterSpec(128, Base64.decode(((SharedPreferences) this.f10948a).getString("link_iv", ""), 2)));
        return a04.m19f(new String(cipher.doFinal(Base64.decode(((SharedPreferences) this.f10948a).getString("link_ciphertext", ""), 2)), StandardCharsets.UTF_8));
    }

    public synchronized void m5934f(String str, boolean z) {
        String strM19f = a04.m19f(str);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(1, m5929b());
        if (!((SharedPreferences) this.f10948a).edit().putString("link_ciphertext", Base64.encodeToString(cipher.doFinal(strM19f.getBytes(StandardCharsets.UTF_8)), 2)).putString("link_iv", Base64.encodeToString(cipher.getIV(), 2)).putBoolean("udp", z).commit()) {
            throw new IllegalStateException("Unable to persist Xray configuration");
        }
    }

    public lu2() {
        this.f10948a = new ArrayList();
    }

    public lu2(Object obj) {
        this.f10948a = obj;
    }
}
