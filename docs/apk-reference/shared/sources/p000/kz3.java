package p000;

import java.util.Locale;
import java.util.regex.Pattern;

public abstract class kz3 {

    public static final String[] f10303a = {"password", "passwd", "token", "secret", "auth", "obfs-password", "uuid", "privatekey", "publickey", "shortid", "seed"};

    public static final Pattern f10304b = Pattern.compile("(?i)\\b(?:vmess|vless|trojan|ss|hy2|hysteria2)://[^\\s]+");

    public static final Pattern f10305c = Pattern.compile("(?i)\\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\b");

    public static final Pattern f10306d = Pattern.compile("(?i)\\b(password|passwd|token|secret|auth|obfs-password|uuid|privatekey|publickey|shortid|seed)(\\s*[=:]\\s*)[^\\s,;&}\\]]+");

    public static String m5738a(Exception exc) {
        String message = exc.getMessage();
        int iCharCount = 0;
        if (message == null) {
            message = exc.getClass().getSimpleName();
            break;
        }
        int length = message.length();
        int iCharCount2 = 0;
        while (true) {
            if (iCharCount2 >= length) {
                message = exc.getClass().getSimpleName();
                break;
            }
            int iCodePointAt = message.codePointAt(iCharCount2);
            if (!Character.isWhitespace(iCodePointAt)) {
                break;
            }
            iCharCount2 += Character.charCount(iCodePointAt);
        }
        String strM5739b = m5739b(message);
        int length2 = strM5739b.length();
        while (iCharCount < length2) {
            int iCodePointAt2 = strM5739b.codePointAt(iCharCount);
            if (!Character.isWhitespace(iCodePointAt2)) {
                return strM5739b;
            }
            iCharCount += Character.charCount(iCodePointAt2);
        }
        return "Xray operation failed";
    }

    public static String m5739b(String str) {
        int iIndexOf;
        char cCharAt;
        if (str == null) {
            return "";
        }
        int length = str.length();
        int iCharCount = 0;
        while (iCharCount < length) {
            int iCodePointAt = str.codePointAt(iCharCount);
            if (!Character.isWhitespace(iCodePointAt)) {
                String strReplaceAll = f10306d.matcher(f10305c.matcher(f10304b.matcher(str).replaceAll("<redacted-share-link>")).replaceAll("<redacted-uuid>")).replaceAll("$1$2<redacted>");
                for (int i = 0; i < 11; i++) {
                    String str2 = f10303a[i];
                    String lowerCase = strReplaceAll.toLowerCase(Locale.ROOT);
                    String strM6233l = AbstractC1163ml.m6233l("\"", str2, "\"");
                    StringBuilder sb = null;
                    int i2 = 0;
                    while (true) {
                        int iIndexOf2 = lowerCase.indexOf(strM6233l, i2);
                        if (iIndexOf2 < 0 || (iIndexOf = lowerCase.indexOf(58, strM6233l.length() + iIndexOf2)) < 0) {
                            break;
                        }
                        i2 = iIndexOf + 1;
                        int i3 = i2;
                        while (i3 < strReplaceAll.length() && Character.isWhitespace(strReplaceAll.charAt(i3))) {
                            i3++;
                        }
                        if (i3 < strReplaceAll.length() && strReplaceAll.charAt(i3) == '\"') {
                            int i4 = i3 + 1;
                            boolean z = false;
                            int i5 = i4;
                            while (i5 < strReplaceAll.length() && ((cCharAt = strReplaceAll.charAt(i5)) != '\"' || z)) {
                                z = cCharAt == '\\' && !z;
                                if (cCharAt != '\\') {
                                    z = false;
                                }
                                i5++;
                            }
                            if (i5 >= strReplaceAll.length()) {
                                break;
                            }
                            if (sb == null) {
                                sb = new StringBuilder(strReplaceAll);
                            }
                            sb.replace(i4, i5, "<redacted>");
                            strReplaceAll = sb.toString();
                            lowerCase = strReplaceAll.toLowerCase(Locale.ROOT);
                            i2 = i3 + 12;
                            sb = new StringBuilder(strReplaceAll);
                        }
                    }
                    if (sb != null) {
                        strReplaceAll = sb.toString();
                    }
                }
                return strReplaceAll.length() > 1024 ? strReplaceAll.substring(0, 1024) : strReplaceAll;
            }
            iCharCount += Character.charCount(iCodePointAt);
        }
        return "";
    }
}
