package p000;

import java.io.IOException;
import java.util.Arrays;
import java.util.Locale;
import kotlin.UByte;
import okhttp3.HttpUrl;
import okhttp3.Interceptor;
import okhttp3.Response;

public final class qz3 implements Interceptor {
    public static boolean m8462a(String str) {
        int iIndexOf;
        if (str != null) {
            int length = str.length();
            int iCharCount = 0;
            while (iCharCount < length) {
                int iCodePointAt = str.codePointAt(iCharCount);
                if (!Character.isWhitespace(iCodePointAt)) {
                    String lowerCase = str.toLowerCase(Locale.ROOT);
                    if (!"localhost".equals(lowerCase) && !lowerCase.endsWith(".localhost") && !lowerCase.endsWith(".local")) {
                        if (lowerCase.indexOf(58) < 0) {
                            if (!lowerCase.isEmpty()) {
                                for (int i = 0; i < lowerCase.length(); i++) {
                                    char cCharAt = lowerCase.charAt(i);
                                    if (cCharAt == '.' || (cCharAt >= '0' && cCharAt <= '9')) {
                                    }
                                }
                                byte[] bArrM8464c = m8464c(lowerCase);
                                if (bArrM8464c != null) {
                                    int i2 = bArrM8464c[0] & UByte.MAX_VALUE;
                                    int i3 = bArrM8464c[1] & UByte.MAX_VALUE;
                                    if (i2 != 0 && i2 != 10 && i2 != 127 && i2 < 224 && ((i2 != 100 || i3 < 64 || i3 > 127) && ((i2 != 169 || i3 != 254) && (i2 != 172 || i3 < 16 || i3 > 31)))) {
                                        int i4 = bArrM8464c[2] & UByte.MAX_VALUE;
                                        if ((i2 != 192 || i3 != 168) && ((i2 != 192 || i3 != 0 || (i4 != 0 && i4 != 2)) && ((i2 != 192 || i3 != 88 || i4 != 99 || (bArrM8464c[3] & UByte.MAX_VALUE) != 2) && ((i2 != 198 || (i3 != 18 && i3 != 19)) && ((i2 != 198 || i3 != 51 || i4 != 100) && (i2 != 203 || i3 != 0 || i4 != 113)))))) {
                                            return false;
                                        }
                                    }
                                }
                                return true;
                            }
                            return false;
                        }
                        byte[] bArr = null;
                        if (!lowerCase.isEmpty() && lowerCase.indexOf(37) < 0 && ((iIndexOf = lowerCase.indexOf("::")) < 0 || lowerCase.indexOf("::", iIndexOf + 2) < 0)) {
                            String strSubstring = iIndexOf < 0 ? lowerCase : lowerCase.substring(0, iIndexOf);
                            String strSubstring2 = iIndexOf < 0 ? "" : lowerCase.substring(iIndexOf + 2);
                            int[] iArrM8465d = m8465d(strSubstring, iIndexOf < 0);
                            int[] iArrM8465d2 = iIndexOf < 0 ? new int[0] : m8465d(strSubstring2, true);
                            if (iArrM8465d != null && iArrM8465d2 != null) {
                                int length2 = iArrM8465d.length + iArrM8465d2.length;
                                if ((iIndexOf >= 0 || length2 == 8) && (iIndexOf < 0 || length2 < 8)) {
                                    int[] iArr = new int[8];
                                    System.arraycopy(iArrM8465d, 0, iArr, 0, iArrM8465d.length);
                                    System.arraycopy(iArrM8465d2, 0, iArr, 8 - iArrM8465d2.length, iArrM8465d2.length);
                                    byte[] bArr2 = new byte[16];
                                    for (int i5 = 0; i5 < 8; i5++) {
                                        int i6 = i5 * 2;
                                        int i7 = iArr[i5];
                                        bArr2[i6] = (byte) (i7 >>> 8);
                                        bArr2[i6 + 1] = (byte) i7;
                                    }
                                    bArr = bArr2;
                                }
                            }
                        }
                        if (bArr != null) {
                            byte b = bArr[0];
                            int i8 = b & UByte.MAX_VALUE;
                            int i9 = bArr[1] & UByte.MAX_VALUE;
                            if (!m8463b(0, 12, bArr) && ((!m8463b(0, 10, bArr) || (bArr[10] & UByte.MAX_VALUE) != 255 || (bArr[11] & UByte.MAX_VALUE) != 255) && ((!m8463b(0, 8, bArr) || (bArr[8] & UByte.MAX_VALUE) != 255 || (bArr[9] & UByte.MAX_VALUE) != 255 || bArr[10] != 0 || bArr[11] != 0) && ((i8 != 0 || i9 != 100 || (bArr[2] & UByte.MAX_VALUE) != 255 || (bArr[3] & UByte.MAX_VALUE) != 155 || (bArr[4] & UByte.MAX_VALUE) != 0 || (bArr[5] & UByte.MAX_VALUE) != 1) && ((i8 != 1 || i9 != 0 || !m8463b(2, 8, bArr)) && ((i8 != 1 || i9 != 0 || !m8463b(2, 7, bArr) || (bArr[7] & UByte.MAX_VALUE) != 1) && ((i8 != 32 || i9 != 1 || (bArr[2] & UByte.MAX_VALUE) != 0 || (bArr[3] & UByte.MAX_VALUE) != 2 || (bArr[4] & UByte.MAX_VALUE) != 0 || (bArr[5] & UByte.MAX_VALUE) != 0) && ((i8 != 32 || i9 != 1 || (bArr[2] & UByte.MAX_VALUE) != 13 || (bArr[3] & UByte.MAX_VALUE) != 184) && ((i8 != 63 || i9 != 255 || (bArr[2] & 240) != 0) && ((i8 != 95 || i9 != 0) && (b & 254) != 252 && i8 != 254 && i8 != 255)))))))))) {
                                return false;
                            }
                        }
                    }
                    return true;
                }
                iCharCount += Character.charCount(iCodePointAt);
            }
        }
        return true;
    }

    public static boolean m8463b(int i, int i2, byte[] bArr) {
        while (i < i2) {
            if (bArr[i] != 0) {
                return false;
            }
            i++;
        }
        return true;
    }

    public static byte[] m8464c(String str) {
        String[] strArrSplit = str.split("\\.", -1);
        if (strArrSplit.length != 4) {
            return null;
        }
        byte[] bArr = new byte[4];
        for (int i = 0; i < strArrSplit.length; i++) {
            String str2 = strArrSplit[i];
            if (str2.isEmpty() || str2.length() > 3) {
                return null;
            }
            int i2 = 0;
            for (int i3 = 0; i3 < str2.length(); i3++) {
                char cCharAt = str2.charAt(i3);
                if (cCharAt < '0' || cCharAt > '9') {
                    return null;
                }
                i2 = ((i2 * 10) + cCharAt) - 48;
            }
            if (i2 > 255) {
                return null;
            }
            bArr[i] = (byte) i2;
        }
        return bArr;
    }

    public static int[] m8465d(String str, boolean z) {
        byte[] bArrM8464c;
        if (str.isEmpty()) {
            return new int[0];
        }
        String[] strArrSplit = str.split(":", -1);
        int[] iArr = new int[strArrSplit.length + 1];
        int i = 0;
        for (int i2 = 0; i2 < strArrSplit.length; i2++) {
            String str2 = strArrSplit[i2];
            if (str2.isEmpty()) {
                return null;
            }
            if (str2.indexOf(46) >= 0) {
                if (!z || i2 != strArrSplit.length - 1 || (bArrM8464c = m8464c(str2)) == null) {
                    return null;
                }
                int i3 = i + 1;
                iArr[i] = ((bArrM8464c[0] & UByte.MAX_VALUE) << 8) | (bArrM8464c[1] & UByte.MAX_VALUE);
                i += 2;
                iArr[i3] = (bArrM8464c[3] & UByte.MAX_VALUE) | ((bArrM8464c[2] & UByte.MAX_VALUE) << 8);
            } else {
                if (str2.length() > 4) {
                    return null;
                }
                int i4 = 0;
                for (int i5 = 0; i5 < str2.length(); i5++) {
                    int iDigit = Character.digit(str2.charAt(i5), 16);
                    if (iDigit < 0) {
                        return null;
                    }
                    i4 = (i4 << 4) | iDigit;
                }
                iArr[i] = i4;
                i++;
            }
        }
        return Arrays.copyOf(iArr, i);
    }

    @Override
    public final Response intercept(Interceptor.Chain chain) throws IOException {
        HttpUrl httpUrlUrl = chain.request().url();
        if (!httpUrlUrl.isHttps() && !"http".equals(httpUrlUrl.scheme())) {
            kg0.m5396l("Xray playback only supports HTTP or HTTPS");
            return null;
        }
        if (!m8462a(httpUrlUrl.host())) {
            return chain.proceed(chain.request());
        }
        kg0.m5396l("Private or reserved playback destination blocked");
        return null;
    }
}
