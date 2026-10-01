package p000;

import android.R;
import android.content.ContentResolver;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.Resources;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Rect;
import android.media.Rating;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Looper;
import android.os.Message;
import android.os.Messenger;
import android.os.Parcelable;
import android.os.RemoteException;
import android.provider.MediaStore;
import android.security.keystore.KeyGenParameterSpec;
import android.support.v4.media.MediaBrowserCompat$MediaItem;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import androidx.appcompat.widget.ActionBarContextView;
import androidx.media3.exoplayer.ExoPlayer;
import com.fongmi.android.p002tv.App;
import com.hierynomus.protocol.commons.buffer.Buffer;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Array;
import java.lang.reflect.Method;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.InvalidAlgorithmParameterException;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.UnrecoverableEntryException;
import java.security.cert.CertificateException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import kotlin.UByte;
import kotlin.collections.CollectionsKt;
import kotlin.p013io.ConstantsKt;
import kotlin.p013io.encoding.Base64;
import okhttp3.internal.http2.Http2;
import okhttp3.internal.http2.Http2Connection;
import okhttp3.internal.http2.Settings;
import org.mozilla.javascript.Token;

public final class j81 implements InterfaceC1210nl, bf3, ua2, bs2, np1, wb0, u92, xs0, ps3 {

    public static final short[] f8993h = {128, 64, 32, 16, 8, 4, 2, 1};

    public static final int[] f8994i = {8388608, 4194304, 2097152, 1048576, 524288, 262144, 131072, 65536, 32768, Http2.INITIAL_MAX_FRAME_SIZE, 8192, 4096, 2048, 1024, ConstantsKt.MINIMUM_BLOCK_SIZE, Buffer.DEFAULT_SIZE, 128, 64, 32, 16, 8, 4, 2, 1};

    public static final byte[] f8995j = {56, 48, 40, 32, 24, 16, 8, 0, 57, 49, 41, 33, 25, 17, 9, 1, 58, 50, 42, 34, 26, 18, 10, 2, 59, 51, 43, 35, 62, 54, 46, 38, 30, 22, 14, 6, Base64.padSymbol, 53, 45, 37, 29, 21, 13, 5, 60, 52, 44, 36, 28, 20, 12, 4, 27, 19, 11, 3};

    public static final byte[] f8996k = {1, 2, 4, 6, 8, 10, 12, 14, 15, 17, 19, 21, 23, 25, 27, 28};

    public static final byte[] f8997l = {13, 16, 10, 23, 0, 4, 2, 27, 14, 5, 20, 9, 22, 18, 11, 3, 25, 7, 15, 6, 26, 19, 12, 1, 40, 51, 30, 36, 46, 54, 29, 39, 50, 44, 32, 47, 43, 48, 38, 55, 33, 52, 45, 41, 49, 35, 28, 31};

    public static final int[] f8998m = {R.attr.transitionName, 0, 65536, R.attr.fillColor, R.attr.manageSpaceActivity, 66564, 4, 65536, 1024, R.attr.transitionName, R.attr.fillColor, 1024, 16778244, R.attr.manageSpaceActivity, Http2Connection.OKHTTP_CLIENT_WINDOW_SIZE, 4, 1028, 16778240, 16778240, 66560, 66560, R.attr.theme, R.attr.theme, 16778244, 65540, 16777220, 16777220, 65540, 0, 1028, 66564, Http2Connection.OKHTTP_CLIENT_WINDOW_SIZE, 65536, R.attr.fillColor, 4, R.attr.theme, R.attr.transitionName, Http2Connection.OKHTTP_CLIENT_WINDOW_SIZE, Http2Connection.OKHTTP_CLIENT_WINDOW_SIZE, 1024, R.attr.manageSpaceActivity, 65536, 66560, 16777220, 1024, 4, 16778244, 66564, R.attr.fillColor, 65540, R.attr.theme, 16778244, 16777220, 1028, 66564, R.attr.transitionName, 1028, 16778240, 16778240, 0, 65540, 66560, 0, R.attr.manageSpaceActivity};

    public static final int[] f8999n = {-2146402272, -2147450880, 32768, 1081376, 1048576, 32, -2146435040, -2147450848, -2147483616, -2146402272, -2146402304, Integer.MIN_VALUE, -2147450880, 1048576, 32, -2146435040, 1081344, 1048608, -2147450848, 0, Integer.MIN_VALUE, 32768, 1081376, -2146435072, 1048608, -2147483616, 0, 1081344, 32800, -2146402304, -2146435072, 32800, 0, 1081376, -2146435040, 1048576, -2147450848, -2146435072, -2146402304, 32768, -2146435072, -2147450880, 32, -2146402272, 1081376, 32, 32768, Integer.MIN_VALUE, 32800, -2146402304, 1048576, -2147483616, 1048608, -2147450848, -2147483616, 1048608, 1081344, 0, -2147450880, 32800, Integer.MIN_VALUE, -2146435040, -2146402272, 1081344};

    public static final int[] f9000o = {520, 134349312, 0, 134348808, 134218240, 0, 131592, 134218240, 131080, 134217736, 134217736, 131072, 134349320, 131080, 134348800, 520, 134217728, 8, 134349312, ConstantsKt.MINIMUM_BLOCK_SIZE, 131584, 134348800, 134348808, 131592, 134218248, 131584, 131072, 134218248, 8, 134349320, ConstantsKt.MINIMUM_BLOCK_SIZE, 134217728, 134349312, 134217728, 131080, 520, 131072, 134349312, 134218240, 0, ConstantsKt.MINIMUM_BLOCK_SIZE, 131080, 134349320, 134218240, 134217736, ConstantsKt.MINIMUM_BLOCK_SIZE, 0, 134348808, 134218248, 131072, 134217728, 134349320, 8, 131592, 131584, 134217736, 134348800, 134218248, 520, 134348800, 131592, 8, 134348808, 131584};

    public static final int[] f9001p = {8396801, 8321, 8321, 128, 8396928, 8388737, 8388609, 8193, 0, 8396800, 8396800, 8396929, Token.DEFAULT, 0, 8388736, 8388609, 1, 8192, 8388608, 8396801, 128, 8388608, 8193, 8320, 8388737, 1, 8320, 8388736, 8192, 8396928, 8396929, Token.DEFAULT, 8388736, 8388609, 8396800, 8396929, Token.DEFAULT, 0, 0, 8396800, 8320, 8388736, 8388737, 1, 8396801, 8321, 8321, 128, 8396929, Token.DEFAULT, 1, 8192, 8388609, 8193, 8396928, 8388737, 8193, 8320, 8388608, 8396801, 128, 8388608, 8192, 8396928};

    public static final int[] f9002q = {Buffer.DEFAULT_SIZE, 34078976, 34078720, 1107296512, 524288, Buffer.DEFAULT_SIZE, Buffer.MAX_SIZE, 34078720, 1074266368, 524288, 33554688, 1074266368, 1107296512, 1107820544, 524544, Buffer.MAX_SIZE, 33554432, 1074266112, 1074266112, 0, 1073742080, 1107820800, 1107820800, 33554688, 1107820544, 1073742080, 0, 1107296256, 34078976, 33554432, 1107296256, 524544, 524288, 1107296512, Buffer.DEFAULT_SIZE, 33554432, Buffer.MAX_SIZE, 34078720, 1107296512, 1074266368, 33554688, Buffer.MAX_SIZE, 1107820544, 34078976, 1074266368, Buffer.DEFAULT_SIZE, 33554432, 1107820544, 1107820800, 524544, 1107296256, 1107820800, 34078720, 0, 1074266112, 1107296256, 524544, 33554688, 1073742080, 524288, 0, 1074266112, 34078976, 1073742080};

    public static final int[] f9003r = {536870928, 541065216, Http2.INITIAL_MAX_FRAME_SIZE, 541081616, 541065216, 16, 541081616, 4194304, 536887296, 4210704, 4194304, 536870928, 4194320, 536887296, 536870912, 16400, 0, 4194320, 536887312, Http2.INITIAL_MAX_FRAME_SIZE, 4210688, 536887312, 16, 541065232, 541065232, 0, 4210704, 541081600, 16400, 4210688, 541081600, 536870912, 536887296, 16, 541065232, 4210688, 541081616, 4194304, 16400, 536870928, 4194304, 536887296, 536870912, 16400, 536870928, 541081616, 4210688, 541065216, 4210704, 541081600, 0, 541065232, 16, Http2.INITIAL_MAX_FRAME_SIZE, 541065216, 4210704, Http2.INITIAL_MAX_FRAME_SIZE, 4194320, 536887312, 0, 541081600, 536870912, 4194320, 536887312};

    public static final int[] f9004s = {2097152, 69206018, 67110914, 0, 2048, 67110914, 2099202, 69208064, 69208066, 2097152, 0, 67108866, 2, 67108864, 69206018, 2050, 67110912, 2099202, 2097154, 67110912, 67108866, 69206016, 69208064, 2097154, 69206016, 2048, 2050, 69208066, 2099200, 2, 67108864, 2099200, 67108864, 2099200, 2097152, 67110914, 67110914, 69206018, 69206018, 2, 2097154, 67108864, 67110912, 2097152, 69208064, 2050, 2099202, 69208064, 2050, 67108866, 69208066, 69206016, 2099200, 0, 2, 69208066, 0, 2099202, 69206016, 2048, 67108866, 67110912, 2048, 2097154};

    public static final int[] f9005t = {268439616, 4096, 262144, 268701760, 268435456, 268439616, 64, 268435456, 262208, 268697600, 268701760, 266240, 268701696, 266304, 4096, 64, 268697600, 268435520, 268439552, 4160, 266240, 262208, 268697664, 268701696, 4160, 0, 0, 268697664, 268435520, 268439552, 266304, 262144, 266304, 262144, 268701696, 4096, 64, 268697664, 4096, 266304, 268439552, 64, 268435520, 268697600, 268697664, 268435456, 262144, 268439616, 0, 268701760, 262208, 268435520, 268697600, 268439552, 268439616, 0, 268701760, 266240, 266240, 4160, 4160, 262208, 268435456, 268701696};

    public static final String[] f9006u = {"_data"};

    public Object f9007c;

    /* JADX WARN: Illegal instructions before constructor call */
    public j81(Context context) {
        boolean z = false;
        SharedPreferences sharedPreferences = context.getSharedPreferences("xray_hy2_pins", 0);
        this(sharedPreferences);
        SharedPreferences sharedPreferences2 = context.getSharedPreferences("xray_secure", 0);
        synchronized (this) {
            try {
                SharedPreferences.Editor editorEdit = sharedPreferences.edit();
                SharedPreferences.Editor editorEdit2 = sharedPreferences2.edit();
                boolean z2 = false;
                for (Map.Entry<String, ?> entry : sharedPreferences2.getAll().entrySet()) {
                    if (entry.getKey().startsWith("hy2_pin_")) {
                        Object value = entry.getValue();
                        if (value instanceof String) {
                            String str = (String) value;
                            if (!((SharedPreferences) this.f9007c).contains(entry.getKey())) {
                                editorEdit.putString(entry.getKey(), str);
                                z2 = true;
                            }
                            editorEdit2.remove(entry.getKey());
                            z = true;
                        }
                    }
                }
                if (z) {
                    if (!z2 || editorEdit.commit()) {
                        editorEdit2.commit();
                    }
                }
            } catch (Throwable th) {
                throw th;
            }
        }
    }

    public static String m4995D(URI uri, ArrayList arrayList, String str) {
        ArrayList arrayList2 = new ArrayList();
        Iterator it = arrayList.iterator();
        while (it.hasNext()) {
            i81 i81Var = (i81) it.next();
            String str2 = i81Var.f7851h;
            if (!str2.equalsIgnoreCase("insecure") && !str2.equalsIgnoreCase("allowInsecure")) {
                String str3 = "pcs";
                if (str.isEmpty() || !str2.equalsIgnoreCase("pcs")) {
                    String strConcat = i81Var.f7850c;
                    if (!str2.equalsIgnoreCase("pcs")) {
                        str3 = "vcn";
                        if (!str2.equalsIgnoreCase("vcn")) {
                            str3 = "sni";
                            if (!str2.equalsIgnoreCase("sni")) {
                                str3 = null;
                            }
                        }
                    }
                    if (str3 != null) {
                        int iIndexOf = strConcat.indexOf(61);
                        strConcat = iIndexOf < 0 ? str3 : str3.concat(strConcat.substring(iIndexOf));
                    }
                    arrayList2.add(strConcat);
                }
            }
        }
        if (!str.isEmpty()) {
            arrayList2.add("pcs=".concat(str));
        }
        StringBuilder sb = new StringBuilder(uri.getScheme());
        sb.append(':');
        sb.append(uri.getRawSchemeSpecificPart());
        int iIndexOf2 = sb.indexOf("?");
        if (iIndexOf2 >= 0) {
            sb.setLength(iIndexOf2);
        }
        sb.append('?');
        StringBuilder sb2 = new StringBuilder();
        Iterator it2 = arrayList2.iterator();
        if (it2.hasNext()) {
            while (true) {
                sb2.append((CharSequence) it2.next());
                if (!it2.hasNext()) {
                    break;
                }
                sb2.append((CharSequence) "&");
            }
        }
        sb.append(sb2.toString());
        if (uri.getRawFragment() != null) {
            sb.append('#');
            sb.append(uri.getRawFragment());
        }
        return sb.toString();
    }

    public static String m4996E(ArrayList arrayList, String str) {
        Iterator it = arrayList.iterator();
        while (it.hasNext()) {
            i81 i81Var = (i81) it.next();
            if (i81Var.f7851h.equalsIgnoreCase(str)) {
                return i81Var.f7852i;
            }
        }
        return "";
    }

    public static int m4997m(ExoPlayer exoPlayer) {
        App app = App.f2949l;
        String str = qp3.f15065a;
        final int iGenerateAudioSessionId = AbstractC1240od.m6948k(app).generateAudioSessionId();
        if (iGenerateAudioSessionId == -1) {
            iGenerateAudioSessionId = 0;
        }
        final mr0 mr0Var = (mr0) exoPlayer;
        mr0Var.m6313m2();
        C0551fh c0551fh = mr0Var.f11587J;
        if (((Integer) c0551fh.m3542d()).intValue() == iGenerateAudioSessionId) {
            return iGenerateAudioSessionId;
        }
        rz0 rz0Var = new rz0() {
            @Override
            public final Object apply(Object obj) {
                int i = iGenerateAudioSessionId;
                if (i == 0) {
                    Context context = mr0Var.f11628l;
                    String str2 = qp3.f15065a;
                    int iGenerateAudioSessionId2 = AbstractC1240od.m6948k(context).generateAudioSessionId();
                    if (iGenerateAudioSessionId2 == -1) {
                        iGenerateAudioSessionId2 = 0;
                    }
                    i = iGenerateAudioSessionId2;
                }
                return Integer.valueOf(i);
            }
        };
        q80.m8106r(Looper.myLooper() == ((sc3) c0551fh.f5808c).f16522a.getLooper());
        c0551fh.f5806a++;
        c0551fh.m3543e(new RunnableC0541f7(c0551fh, rz0Var, 11));
        c0551fh.m3545g(Integer.valueOf(iGenerateAudioSessionId != 0 ? iGenerateAudioSessionId : ((Integer) c0551fh.f5810e).intValue()));
        return iGenerateAudioSessionId;
    }

    public static SecretKey m4998o() throws NoSuchAlgorithmException, IOException, KeyStoreException, CertificateException, NoSuchProviderException, UnrecoverableEntryException, InvalidAlgorithmParameterException {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        KeyStore.Entry entry = keyStore.getEntry("fongmi_xray_hy2_pins_v1", null);
        if (entry instanceof KeyStore.SecretKeyEntry) {
            return ((KeyStore.SecretKeyEntry) entry).getSecretKey();
        }
        KeyGenerator keyGenerator = KeyGenerator.getInstance("AES", "AndroidKeyStore");
        keyGenerator.init(new KeyGenParameterSpec.Builder("fongmi_xray_hy2_pins_v1", 3).setBlockModes("GCM").setEncryptionPaddings("NoPadding").setRandomizedEncryptionRequired(true).build());
        return keyGenerator.generateKey();
    }

    public static boolean m4999r(String str) {
        String[] strArrSplit = str.split("\\.", -1);
        if (strArrSplit.length == 4) {
            for (String str2 : strArrSplit) {
                if (!str2.isEmpty() && str2.length() <= 3 && (str2.length() <= 1 || str2.charAt(0) != '0')) {
                    int i = 0;
                    for (int i2 = 0; i2 < str2.length(); i2++) {
                        char cCharAt = str2.charAt(i2);
                        if (cCharAt >= '0' && cCharAt <= '9') {
                            i = ((i * 10) + cCharAt) - 48;
                        }
                    }
                    if (i <= 255) {
                    }
                }
            }
            return true;
        }
        return false;
    }

    public static String m5000s(String str) {
        byte[] bArrDigest = MessageDigest.getInstance("SHA-256").digest(str.getBytes(StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder("hy2_pin_");
        for (byte b : bArrDigest) {
            sb.append(String.format(Locale.ROOT, "%02x", Integer.valueOf(b & UByte.MAX_VALUE)));
        }
        return sb.toString();
    }

    public void m5001A(String str, String str2) {
        Integer num = (Integer) qv1.f15249j.get(str);
        if (num == null || num.intValue() == 1) {
            ((Bundle) this.f9007c).putCharSequence(str, str2);
        } else {
            C1566re.m8586j(AbstractC1163ml.m6233l("The ", str, " key cannot be used to put a String"));
        }
    }

    public void m5002B(String str, CharSequence charSequence) {
        Integer num = (Integer) qv1.f15249j.get(str);
        if (num == null || num.intValue() == 1) {
            ((Bundle) this.f9007c).putCharSequence(str, charSequence);
        } else {
            C1566re.m8586j(AbstractC1163ml.m6233l("The ", str, " key cannot be used to put a CharSequence"));
        }
    }

    public void m5003C() {
        C0175bd c0175bd;
        if (Build.VERSION.SDK_INT >= 28 && (c0175bd = (C0175bd) this.f9007c) != null) {
            c0175bd.m1181d();
        }
        this.f9007c = null;
    }

    public void m5004F(int i, Object obj, qw2 qw2Var) {
        AbstractC0937jv abstractC0937jv = (AbstractC0937jv) this.f9007c;
        abstractC0937jv.mo3869t(i, 3);
        qw2Var.mo4960j((AbstractC1811y0) obj, this);
        abstractC0937jv.mo3869t(i, 4);
    }

    public void m5005G(int i, Object obj, qw2 qw2Var) {
        AbstractC1811y0 abstractC1811y0 = (AbstractC1811y0) obj;
        AbstractC0937jv abstractC0937jv = (AbstractC0937jv) this.f9007c;
        abstractC0937jv.mo3869t(i, 2);
        abstractC0937jv.mo3871v(abstractC1811y0.getSerializedSize(qw2Var));
        qw2Var.mo4960j(abstractC1811y0, this);
    }

    @Override
    public pr2 mo288H(pr2 pr2Var, mb2 mb2Var) {
        Resources resources = (Resources) this.f9007c;
        if (pr2Var == null) {
            return null;
        }
        return new C0669il(resources, pr2Var);
    }

    @Override
    public void mo1463a(boolean z, InterfaceC0565ft interfaceC0565ft) {
        byte[] bArr;
        int i;
        if (!(interfaceC0565ft instanceof pf1)) {
            C1566re.m8586j("invalid parameter passed to DES init - ".concat(interfaceC0565ft.getClass().getName()));
            return;
        }
        byte[] bArr2 = ((pf1) interfaceC0565ft).f14066a;
        if (bArr2.length > 8) {
            C1566re.m8586j("DES key too long - should be 8 bytes");
            return;
        }
        int[] iArr = new int[32];
        boolean[] zArr = new boolean[56];
        boolean[] zArr2 = new boolean[56];
        int i2 = 0;
        while (true) {
            boolean z2 = true;
            if (i2 >= 56) {
                break;
            }
            byte b = f8995j[i2];
            if ((f8993h[b & 7] & bArr2[b >>> 3]) == 0) {
                z2 = false;
            }
            zArr[i2] = z2;
            i2++;
        }
        for (int i3 = 0; i3 < 16; i3++) {
            int i4 = z ? i3 << 1 : (15 - i3) << 1;
            int i5 = i4 + 1;
            iArr[i5] = 0;
            iArr[i4] = 0;
            int i6 = 0;
            while (true) {
                bArr = f8996k;
                if (i6 >= 28) {
                    break;
                }
                int i7 = bArr[i3] + i6;
                if (i7 < 28) {
                    zArr2[i6] = zArr[i7];
                } else {
                    zArr2[i6] = zArr[i7 - 28];
                }
                i6++;
            }
            for (i = 28; i < 56; i++) {
                int i8 = bArr[i3] + i;
                if (i8 < 56) {
                    zArr2[i] = zArr[i8];
                } else {
                    zArr2[i] = zArr[i8 - 28];
                }
            }
            for (int i9 = 0; i9 < 24; i9++) {
                byte[] bArr3 = f8997l;
                boolean z3 = zArr2[bArr3[i9]];
                int[] iArr2 = f8994i;
                if (z3) {
                    iArr[i4] = iArr[i4] | iArr2[i9];
                }
                if (zArr2[bArr3[i9 + 24]]) {
                    iArr[i5] = iArr[i5] | iArr2[i9];
                }
            }
        }
        for (int i10 = 0; i10 != 32; i10 += 2) {
            int i11 = iArr[i10];
            int i12 = i10 + 1;
            int i13 = iArr[i12];
            iArr[i10] = ((16515072 & i13) >>> 10) | ((i11 & 16515072) << 6) | ((i11 & 4032) << 10) | ((i13 & 4032) >>> 6);
            iArr[i12] = ((i11 & 63) << 16) | ((i11 & 258048) << 12) | ((258048 & i13) >>> 4) | (i13 & 63);
        }
        this.f9007c = iArr;
        if (interfaceC0565ft instanceof n20) {
            C1566re.m8586j("params should not be CryptoServicePurpose");
        } else {
            ((p20) q20.f14575b.get()).getClass();
        }
    }

    @Override
    public int mo5006b() {
        return mo5010h() | (mo5010h() << 8);
    }

    @Override
    public int mo1464c(int i, int i2, byte[] bArr, byte[] bArr2) {
        int[] iArr = (int[]) this.f9007c;
        if (iArr == null) {
            xw2.m10661h("DES engine not initialised");
            return 0;
        }
        if (i + 8 > bArr.length) {
            throw new C0493dx("input buffer too short");
        }
        if (i2 + 8 > bArr2.length) {
            throw new tb2("output buffer too short");
        }
        int iM8495c = r11.m8495c(i, bArr);
        int iM8495c2 = r11.m8495c(i + 4, bArr);
        int i3 = ((iM8495c >>> 4) ^ iM8495c2) & 252645135;
        int i4 = iM8495c2 ^ i3;
        int i5 = (i3 << 4) ^ iM8495c;
        int i6 = ((i5 >>> 16) ^ i4) & Settings.DEFAULT_INITIAL_WINDOW_SIZE;
        int i7 = i4 ^ i6;
        int i8 = i5 ^ (i6 << 16);
        int i9 = ((i7 >>> 2) ^ i8) & 858993459;
        int i10 = i8 ^ i9;
        int i11 = i7 ^ (i9 << 2);
        int i12 = ((i11 >>> 8) ^ i10) & 16711935;
        int i13 = i10 ^ i12;
        int i14 = i11 ^ (i12 << 8);
        int i15 = (i14 >>> 31) | (i14 << 1);
        int i16 = (i13 ^ i15) & (-1431655766);
        int i17 = i13 ^ i16;
        int i18 = i15 ^ i16;
        int i19 = (i17 >>> 31) | (i17 << 1);
        for (int i20 = 0; i20 < 8; i20++) {
            int i21 = i20 * 4;
            int i22 = ((i18 << 28) | (i18 >>> 4)) ^ iArr[i21];
            int[] iArr2 = f9004s;
            int i23 = iArr2[i22 & 63];
            int[] iArr3 = f9002q;
            int i24 = i23 | iArr3[(i22 >>> 8) & 63];
            int[] iArr4 = f9000o;
            int i25 = i24 | iArr4[(i22 >>> 16) & 63];
            int[] iArr5 = f8998m;
            int i26 = iArr5[(i22 >>> 24) & 63] | i25;
            int i27 = iArr[i21 + 1] ^ i18;
            int[] iArr6 = f9005t;
            int i28 = i26 | iArr6[i27 & 63];
            int[] iArr7 = f9003r;
            int i29 = i28 | iArr7[(i27 >>> 8) & 63];
            int[] iArr8 = f9001p;
            int i30 = i29 | iArr8[(i27 >>> 16) & 63];
            int[] iArr9 = f8999n;
            i19 ^= i30 | iArr9[(i27 >>> 24) & 63];
            int i31 = ((i19 << 28) | (i19 >>> 4)) ^ iArr[i21 + 2];
            int i32 = iArr5[(i31 >>> 24) & 63] | iArr2[i31 & 63] | iArr3[(i31 >>> 8) & 63] | iArr4[(i31 >>> 16) & 63];
            int i33 = iArr[i21 + 3] ^ i19;
            i18 ^= (((i32 | iArr6[i33 & 63]) | iArr7[(i33 >>> 8) & 63]) | iArr8[(i33 >>> 16) & 63]) | iArr9[(i33 >>> 24) & 63];
        }
        int i34 = (i18 >>> 1) | (i18 << 31);
        int i35 = (i19 ^ i34) & (-1431655766);
        int i36 = i19 ^ i35;
        int i37 = i34 ^ i35;
        int i38 = (i36 >>> 1) | (i36 << 31);
        int i39 = ((i38 >>> 8) ^ i37) & 16711935;
        int i40 = i37 ^ i39;
        int i41 = i38 ^ (i39 << 8);
        int i42 = ((i41 >>> 2) ^ i40) & 858993459;
        int i43 = i40 ^ i42;
        int i44 = i41 ^ (i42 << 2);
        int i45 = ((i43 >>> 16) ^ i44) & Settings.DEFAULT_INITIAL_WINDOW_SIZE;
        int i46 = i44 ^ i45;
        int i47 = i43 ^ (i45 << 16);
        int i48 = ((i47 >>> 4) ^ i46) & 252645135;
        r11.m8478K(i47 ^ (i48 << 4), i2, bArr2);
        r11.m8478K(i46 ^ i48, i2 + 4, bArr2);
        return 8;
    }

    @Override
    public Object create() {
        vj3 vj3Var = (vj3) this.f9007c;
        return new wn0((c21) vj3Var.f19284h, (c21) vj3Var.f19285i, (c21) vj3Var.f19286j, (c21) vj3Var.f19287k, (sn0) vj3Var.f19288l, (sn0) vj3Var.f19289m, (ah0) vj3Var.f19290n);
    }

    @Override
    public int mo1465d() {
        return 8;
    }

    public void m5007e(float[][] fArr) {
        float[][] fArr2 = (float[][]) this.f9007c;
        if (fArr2 != null) {
            r11.m8502j(fArr2);
            r11.m8502j(fArr);
            int length = fArr2.length;
            q80.m8097i(fArr.length == length);
            float[][] fArr3 = (float[][]) Array.newInstance((Class<?>) Float.TYPE, length, length);
            for (int i = 0; i < length; i++) {
                for (int i2 = 0; i2 < length; i2++) {
                    float f = fArr[i][i2];
                    if (f != 0.0f) {
                        for (int i3 = 0; i3 < length; i3++) {
                            float[] fArr4 = fArr3[i];
                            fArr4[i3] = (fArr2[i2][i3] * f) + fArr4[i3];
                        }
                    }
                }
            }
            this.f9007c = fArr3;
        }
    }

    public void m5008f(StringBuilder sb, Iterator it) {
        wm0 wm0Var = (wm0) this.f9007c;
        if (it.hasNext()) {
            Map.Entry entry = (Map.Entry) it.next();
            sb.append(wm0.m10392d(entry.getKey()));
            sb.append("=");
            sb.append(wm0.m10392d(entry.getValue()));
            while (it.hasNext()) {
                sb.append((CharSequence) wm0Var.f20146c);
                Map.Entry entry2 = (Map.Entry) it.next();
                sb.append(wm0.m10392d(entry2.getKey()));
                sb.append("=");
                sb.append(wm0.m10392d(entry2.getValue()));
            }
        }
    }

    public r10 m5009g(r10 r10Var) {
        return r10Var instanceof up2 ? r10Var : new C0466d5(-((sp1) this.f9007c).m9024l(), r10Var);
    }

    @Override
    public View getRoot() {
        return (FrameLayout) this.f9007c;
    }

    @Override
    public short mo5010h() throws IOException {
        int i = ((InputStream) this.f9007c).read();
        if (i != -1) {
            return (short) i;
        }
        throw new vb0();
    }

    public synchronized void m5011i() {
        try {
            SharedPreferences.Editor editorEdit = ((SharedPreferences) this.f9007c).edit();
            for (String str : ((SharedPreferences) this.f9007c).getAll().keySet()) {
                if (str.startsWith("hy2_pin_")) {
                    editorEdit.remove(str);
                }
            }
            if (!editorEdit.commit()) {
                throw new IllegalStateException("Hysteria2 certificate pins were not removed");
            }
        } catch (Throwable th) {
            throw th;
        }
    }

    @Override
    public Cursor mo1234j(Uri uri) {
        String lastPathSegment = uri.getLastPathSegment();
        return ((ContentResolver) this.f9007c).query(MediaStore.Video.Thumbnails.EXTERNAL_CONTENT_URI, f9006u, "kind = 1 AND video_id = ?", new String[]{lastPathSegment}, null);
    }

    @Override
    public int mo5012k(int i, byte[] bArr) throws vb0 {
        int i2 = 0;
        int i3 = 0;
        while (i2 < i && (i3 = ((InputStream) this.f9007c).read(bArr, i2, i - i2)) != -1) {
            i2 += i3;
        }
        if (i2 == 0 && i3 == -1) {
            throw new vb0();
        }
        return i2;
    }

    @Override
    public void mo3209l(Object obj) {
        qh1 qh1Var = (qh1) obj;
        ag0 ag0Var = (ag0) this.f9007c;
        if (qh1Var == null || !ag0Var.f308k0) {
            return;
        }
        View viewM7533O = ag0Var.m7533O();
        if (viewM7533O.getParent() != null) {
            xw2.m10661h("DialogFragment can not be attached to a container view");
            return;
        }
        if (ag0Var.f312o0 != null) {
            if (ey0.m3312G(3)) {
                Log.d("FragmentManager", "DialogFragment " + this + " setting the content view on " + ag0Var.f312o0);
            }
            ag0Var.f312o0.setContentView(viewM7533O);
        }
    }

    public synchronized String m5013n(String str) {
        String strM5000s = m5000s(str);
        String string = ((SharedPreferences) this.f9007c).getString(strM5000s.concat("_ct"), "");
        String string2 = ((SharedPreferences) this.f9007c).getString(strM5000s.concat("_iv"), "");
        if (!string.isEmpty() && !string2.isEmpty()) {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(2, m4998o(), new GCMParameterSpec(128, android.util.Base64.decode(string2, 2)));
            return new String(cipher.doFinal(android.util.Base64.decode(string, 2)), StandardCharsets.US_ASCII);
        }
        return "";
    }

    public void m5014p(Set set) {
        Object objectVolatile;
        int[] iArr;
        y83 y83Var = q80.f14733i;
        set.getClass();
        if (set.isEmpty()) {
            return;
        }
        x73 x73Var = (x73) this.f9007c;
        do {
            objectVolatile = vp2.f19356a.getObjectVolatile(x73Var, x73.f20607b);
            if (objectVolatile == y83Var) {
                objectVolatile = null;
            }
            int[] iArr2 = (int[]) objectVolatile;
            int length = iArr2.length;
            iArr = new int[length];
            for (int i = 0; i < length; i++) {
                iArr[i] = set.contains(Integer.valueOf(i)) ? iArr2[i] + 1 : iArr2[i];
            }
            if (objectVolatile == null) {
                objectVolatile = y83Var;
            }
        } while (!x73Var.m10476a(objectVolatile, iArr));
    }

    @Override
    public ky3 mo2600q(View view, ky3 ky3Var) {
        boolean z;
        boolean z2;
        int iM5732d = ky3Var.m5732d();
        LayoutInflaterFactory2C0951k8 layoutInflaterFactory2C0951k8 = (LayoutInflaterFactory2C0951k8) this.f9007c;
        Context context = layoutInflaterFactory2C0951k8.f9708q;
        int iM5732d2 = ky3Var.m5732d();
        ActionBarContextView actionBarContextView = layoutInflaterFactory2C0951k8.f9668A;
        if (actionBarContextView == null || !(actionBarContextView.getLayoutParams() instanceof ViewGroup.MarginLayoutParams)) {
            z = false;
        } else {
            ViewGroup.MarginLayoutParams marginLayoutParams = (ViewGroup.MarginLayoutParams) layoutInflaterFactory2C0951k8.f9668A.getLayoutParams();
            boolean z3 = true;
            if (layoutInflaterFactory2C0951k8.f9668A.isShown()) {
                if (layoutInflaterFactory2C0951k8.f9702i0 == null) {
                    layoutInflaterFactory2C0951k8.f9702i0 = new Rect();
                    layoutInflaterFactory2C0951k8.f9703j0 = new Rect();
                }
                Rect rect = layoutInflaterFactory2C0951k8.f9702i0;
                Rect rect2 = layoutInflaterFactory2C0951k8.f9703j0;
                rect.set(ky3Var.m5730b(), ky3Var.m5732d(), ky3Var.m5731c(), ky3Var.m5729a());
                ViewGroup viewGroup = layoutInflaterFactory2C0951k8.f9674G;
                if (Build.VERSION.SDK_INT >= 29) {
                    boolean z4 = zu3.f22297a;
                    xu3.m10615a(viewGroup, rect, rect2);
                } else {
                    if (!zu3.f22297a) {
                        zu3.f22297a = true;
                        try {
                            Method declaredMethod = View.class.getDeclaredMethod("computeFitSystemWindows", Rect.class, Rect.class);
                            zu3.f22298b = declaredMethod;
                            if (!declaredMethod.isAccessible()) {
                                zu3.f22298b.setAccessible(true);
                            }
                        } catch (NoSuchMethodException unused) {
                            Log.d("ViewUtils", "Could not find method computeFitSystemWindows. Oh well.");
                        }
                    }
                    Method method = zu3.f22298b;
                    if (method != null) {
                        try {
                            method.invoke(viewGroup, rect, rect2);
                        } catch (Exception e) {
                            Log.d("ViewUtils", "Could not invoke computeFitSystemWindows", e);
                        }
                    }
                }
                int i = rect.top;
                int i2 = rect.left;
                int i3 = rect.right;
                ViewGroup viewGroup2 = layoutInflaterFactory2C0951k8.f9674G;
                WeakHashMap weakHashMap = ft3.f6034a;
                ky3 ky3VarM10827a = ys3.m10827a(viewGroup2);
                int iM5730b = ky3VarM10827a == null ? 0 : ky3VarM10827a.m5730b();
                int iM5731c = ky3VarM10827a == null ? 0 : ky3VarM10827a.m5731c();
                if (marginLayoutParams.topMargin == i && marginLayoutParams.leftMargin == i2 && marginLayoutParams.rightMargin == i3) {
                    z2 = false;
                } else {
                    marginLayoutParams.topMargin = i;
                    marginLayoutParams.leftMargin = i2;
                    marginLayoutParams.rightMargin = i3;
                    z2 = true;
                }
                if (i <= 0 || layoutInflaterFactory2C0951k8.f9676I != null) {
                    View view2 = layoutInflaterFactory2C0951k8.f9676I;
                    if (view2 != null) {
                        ViewGroup.MarginLayoutParams marginLayoutParams2 = (ViewGroup.MarginLayoutParams) view2.getLayoutParams();
                        int i4 = marginLayoutParams2.height;
                        int i5 = marginLayoutParams.topMargin;
                        if (i4 != i5 || marginLayoutParams2.leftMargin != iM5730b || marginLayoutParams2.rightMargin != iM5731c) {
                            marginLayoutParams2.height = i5;
                            marginLayoutParams2.leftMargin = iM5730b;
                            marginLayoutParams2.rightMargin = iM5731c;
                            layoutInflaterFactory2C0951k8.f9676I.setLayoutParams(marginLayoutParams2);
                        }
                    }
                } else {
                    View view3 = new View(context);
                    layoutInflaterFactory2C0951k8.f9676I = view3;
                    view3.setVisibility(8);
                    FrameLayout.LayoutParams layoutParams = new FrameLayout.LayoutParams(-1, marginLayoutParams.topMargin, 51);
                    layoutParams.leftMargin = iM5730b;
                    layoutParams.rightMargin = iM5731c;
                    layoutInflaterFactory2C0951k8.f9674G.addView(layoutInflaterFactory2C0951k8.f9676I, -1, layoutParams);
                }
                View view4 = layoutInflaterFactory2C0951k8.f9676I;
                z3 = view4 != null;
                if (z3 && view4.getVisibility() != 0) {
                    View view5 = layoutInflaterFactory2C0951k8.f9676I;
                    view5.setBackgroundColor((view5.getWindowSystemUiVisibility() & 8192) != 0 ? context.getColor(com.fongmi.android.p002tv.R.color.abc_decor_view_status_guard_light) : context.getColor(com.fongmi.android.p002tv.R.color.abc_decor_view_status_guard));
                }
                if (!layoutInflaterFactory2C0951k8.f9681N && z3) {
                    iM5732d2 = 0;
                }
                z = z3;
                z3 = z2;
            } else if (marginLayoutParams.topMargin != 0) {
                marginLayoutParams.topMargin = 0;
                z = false;
            } else {
                z = false;
                z3 = false;
            }
            if (z3) {
                layoutInflaterFactory2C0951k8.f9668A.setLayoutParams(marginLayoutParams);
            }
        }
        View view6 = layoutInflaterFactory2C0951k8.f9676I;
        if (view6 != null) {
            view6.setVisibility(z ? 0 : 8);
        }
        return ft3.m3649j(view, iM5732d != iM5732d2 ? ky3Var.m5733f(ky3Var.m5730b(), iM5732d2, ky3Var.m5731c(), ky3Var.m5729a()) : ky3Var);
    }

    @Override
    public long skip(long j) throws IOException {
        InputStream inputStream = (InputStream) this.f9007c;
        if (j < 0) {
            return 0L;
        }
        long j2 = j;
        while (j2 > 0) {
            long jSkip = inputStream.skip(j2);
            if (jSkip <= 0) {
                if (inputStream.read() == -1) {
                    break;
                }
                jSkip = 1;
            }
            j2 -= jSkip;
        }
        return j - j2;
    }

    public void m5015t(String str, List list, Bundle bundle, Bundle bundle2) throws RemoteException {
        Bundle bundle3 = new Bundle();
        bundle3.putString("data_media_item_id", str);
        bundle3.putBundle("data_options", bundle);
        bundle3.putBundle("data_notify_children_changed_options", bundle2);
        if (list != null) {
            bundle3.putParcelableArrayList("data_media_item_list", tp3.m9429i(list, MediaBrowserCompat$MediaItem.CREATOR));
        }
        Message messageObtain = Message.obtain();
        messageObtain.what = 3;
        messageObtain.arg1 = 2;
        messageObtain.setData(bundle3);
        ((Messenger) this.f9007c).send(messageObtain);
    }

    public he2 m5016u(String... strArr) {
        List<String> listListOf = CollectionsKt.listOf(Arrays.copyOf(strArr, strArr.length));
        listListOf.getClass();
        LinkedHashSet linkedHashSet = new LinkedHashSet();
        LinkedHashSet linkedHashSet2 = new LinkedHashSet();
        int i = Build.VERSION.SDK_INT;
        AbstractActivityC1142m7 abstractActivityC1142m7 = (AbstractActivityC1142m7) this.f9007c;
        abstractActivityC1142m7.getClass();
        int i2 = abstractActivityC1142m7.getApplicationInfo().targetSdkVersion;
        for (String str : listListOf) {
            if (ie2.f7929a.contains(str)) {
                linkedHashSet2.add(str);
            } else {
                linkedHashSet.add(str);
            }
        }
        if (linkedHashSet2.contains("android.permission.ACCESS_BACKGROUND_LOCATION") && (i == 29 || (i == 30 && i2 < 30))) {
            linkedHashSet2.remove("android.permission.ACCESS_BACKGROUND_LOCATION");
            linkedHashSet.add("android.permission.ACCESS_BACKGROUND_LOCATION");
        }
        if (linkedHashSet2.contains("android.permission.POST_NOTIFICATIONS") && i >= 33 && i2 >= 33) {
            linkedHashSet2.remove("android.permission.POST_NOTIFICATIONS");
            linkedHashSet.add("android.permission.POST_NOTIFICATIONS");
        }
        he2 he2Var = new he2();
        he2Var.f7097b = -1;
        he2Var.f7100e = new LinkedHashSet();
        he2Var.f7101f = new LinkedHashSet();
        he2Var.f7102g = new LinkedHashSet();
        he2Var.f7103h = new LinkedHashSet();
        new LinkedHashSet();
        he2Var.f7104i = new LinkedHashSet();
        he2Var.f7105j = new LinkedHashSet();
        he2Var.f7096a = abstractActivityC1142m7;
        he2Var.f7098c = linkedHashSet;
        he2Var.f7099d = linkedHashSet2;
        return he2Var;
    }

    public void m5017v(y20 y20Var) {
        int i = 0;
        while (i < 3) {
            y20[] y20VarArr = (y20[]) this.f9007c;
            y20 y20Var2 = y20VarArr[i];
            y20VarArr[i] = y20Var;
            i++;
            y20Var = y20Var2;
        }
    }

    public synchronized void m5018w(String str, String str2) {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(1, m4998o());
        byte[] bArrDoFinal = cipher.doFinal(str2.getBytes(StandardCharsets.US_ASCII));
        String strM5000s = m5000s(str);
        if (!((SharedPreferences) this.f9007c).edit().putString(strM5000s.concat("_ct"), android.util.Base64.encodeToString(bArrDoFinal, 2)).putString(strM5000s.concat("_iv"), android.util.Base64.encodeToString(cipher.getIV(), 2)).commit()) {
            throw new IllegalStateException("Hysteria2 certificate pin was not persisted");
        }
    }

    public void m5019x(String str, Bitmap bitmap) {
        Integer num = (Integer) qv1.f15249j.get(str);
        if (num == null || num.intValue() == 2) {
            ((Bundle) this.f9007c).putParcelable(str, bitmap);
        } else {
            C1566re.m8586j(AbstractC1163ml.m6233l("The ", str, " key cannot be used to put a Bitmap"));
        }
    }

    public void m5020y(long j, String str) {
        Integer num = (Integer) qv1.f15249j.get(str);
        if (num == null || num.intValue() == 0) {
            ((Bundle) this.f9007c).putLong(str, j);
        } else {
            C1566re.m8586j(AbstractC1163ml.m6233l("The ", str, " key cannot be used to put a long"));
        }
    }

    public void m5021z(String str, pn2 pn2Var) {
        float f = pn2Var.f14219h;
        Integer num = (Integer) qv1.f15249j.get(str);
        if (num != null && num.intValue() != 3) {
            C1566re.m8586j(AbstractC1163ml.m6233l("The ", str, " key cannot be used to put a Rating"));
            return;
        }
        Bundle bundle = (Bundle) this.f9007c;
        Object objNewUnratedRating = pn2Var.f14220i;
        if (objNewUnratedRating == null) {
            boolean zM7867c = pn2Var.m7867c();
            int i = pn2Var.f14218c;
            if (zM7867c) {
                switch (i) {
                    case 1:
                        objNewUnratedRating = Rating.newHeartRating(i == 1 && f == 1.0f);
                        pn2Var.f14220i = objNewUnratedRating;
                        break;
                    case 2:
                        objNewUnratedRating = Rating.newThumbRating(i == 2 && f == 1.0f);
                        pn2Var.f14220i = objNewUnratedRating;
                        break;
                    case 3:
                    case 4:
                    case 5:
                        objNewUnratedRating = Rating.newStarRating(i, pn2Var.m7866b());
                        pn2Var.f14220i = objNewUnratedRating;
                        break;
                    case 6:
                        if (i != 6 || !pn2Var.m7867c()) {
                            f = -1.0f;
                        }
                        objNewUnratedRating = Rating.newPercentageRating(f);
                        pn2Var.f14220i = objNewUnratedRating;
                        break;
                    default:
                        objNewUnratedRating = null;
                        break;
                }
            } else {
                objNewUnratedRating = Rating.newUnratedRating(i);
                pn2Var.f14220i = objNewUnratedRating;
            }
        }
        bundle.putParcelable(str, (Parcelable) objNewUnratedRating);
    }

    @Override
    public void reset() {
    }

    public j81(j81 j81Var, e81 e81Var) {
        this.f9007c = j81Var;
    }

    public j81(Object obj) {
        this.f9007c = obj;
    }

    public j81(int i, boolean z) {
        switch (i) {
            case 20:
                this.f9007c = new y20[3];
                break;
            case 23:
                this.f9007c = new Bundle();
                break;
            default:
                this.f9007c = new oz0(5, 1.0f, false, 0);
                break;
        }
    }
}
