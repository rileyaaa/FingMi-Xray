package p000;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.net.URI;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashSet;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import kotlin.text.Typography;
import okhttp3.internal.p016ws.WebSocketProtocol;
import org.slf4j.Marker;
import p009j$.net.URLDecoder;
import p009j$.net.URLEncoder;
import p009j$.util.Base64;

public abstract class a04 {

    public static final Set f3a;

    public static final Pattern f4b;

    public static final BigDecimal f5c;

    public static final BigDecimal f6d;

    static {
        Object[] objArr = {"vless", "vmess", "trojan", "ss", "hy2", "hysteria2"};
        HashSet hashSet = new HashSet(6);
        for (int i = 0; i < 6; i++) {
            Object obj = objArr[i];
            Objects.requireNonNull(obj);
            if (!hashSet.add(obj)) {
                C1566re.m8586j(xp0.m10578h(obj, "duplicate element: "));
                return;
            }
        }
        f3a = Collections.unmodifiableSet(hashSet);
        f4b = Pattern.compile("\\\"port\\\"\\s*:\\s*(?:\\\"([+-]?\\d+)\\\"|([+-]?\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?))");
        f5c = BigDecimal.ONE;
        f6d = BigDecimal.valueOf(WebSocketProtocol.PAYLOAD_SHORT_MAX);
    }

    public static void m14a(StringBuilder sb, String str, String str2) {
        if (!sb.isEmpty()) {
            sb.append(Typography.amp);
        }
        sb.append(str);
        sb.append('=');
        sb.append(URLEncoder.encode(str2, StandardCharsets.UTF_8).replace(Marker.ANY_NON_NULL_MARKER, "%20"));
    }

    public static int m15b(String str) {
        if (str.isEmpty() || !str.chars().allMatch(new zz3())) {
            C1566re.m8586j("Xray link port is invalid");
            return 0;
        }
        try {
            BigDecimal bigDecimal = new BigDecimal(str);
            if (bigDecimal.compareTo(f5c) < 0 || bigDecimal.compareTo(f6d) > 0) {
                throw new IllegalArgumentException("Xray link port is invalid");
            }
            return bigDecimal.intValueExact();
        } catch (ArithmeticException e) {
            e = e;
            throw new IllegalArgumentException("Xray link port is invalid", e);
        } catch (NumberFormatException e2) {
            e = e2;
            throw new IllegalArgumentException("Xray link port is invalid", e);
        }
    }

    public static String m16c(String str) {
        String string;
        int length = str.length() & 3;
        if (length != 0) {
            StringBuilder sb = new StringBuilder(str);
            int i = 4 - length;
            if (i < 0) {
                C1566re.m8586j(w43.m10259d(i, "count is negative: "));
                return null;
            }
            if (i != 0) {
                string = "=";
                if (i != 1) {
                    if (1 > Integer.MAX_VALUE / i) {
                        throw new OutOfMemoryError(xp0.m10577g(i, "Repeating 1 bytes String ", " times will produce a String exceeding maximum size."));
                    }
                    StringBuilder sb2 = new StringBuilder(i);
                    for (int i2 = 0; i2 < i; i2++) {
                        sb2.append("=");
                    }
                    string = sb2.toString();
                }
            } else {
                string = "";
            }
            sb.append(string);
            str = sb.toString();
        }
        Base64.Decoder[] decoderArr = {Base64.getDecoder(), Base64.getUrlDecoder()};
        for (int i3 = 0; i3 < 2; i3++) {
            try {
                return new String(decoderArr[i3].decode(str), StandardCharsets.UTF_8);
            } catch (IllegalArgumentException unused) {
            }
        }
        return null;
    }

    public static int m17d(String str) {
        int iM15b;
        int i = -1;
        String[] strArrSplit = str.split(",", -1);
        if (strArrSplit.length == 0) {
            C1566re.m8586j("Hysteria2 port hopping is invalid");
            return 0;
        }
        for (String str2 : strArrSplit) {
            if (str2.isEmpty()) {
                C1566re.m8586j("Hysteria2 port hopping is invalid");
                return 0;
            }
            int iIndexOf = str2.indexOf(45);
            if (iIndexOf < 0) {
                iM15b = m15b(str2);
            } else {
                if (iIndexOf == 0 || iIndexOf != str2.lastIndexOf(45) || iIndexOf == str2.length() - 1) {
                    C1566re.m8586j("Hysteria2 port hopping is invalid");
                    return 0;
                }
                int iM15b2 = m15b(str2.substring(0, iIndexOf));
                if (iM15b2 > m15b(str2.substring(iIndexOf + 1))) {
                    C1566re.m8586j("Hysteria2 port hopping range is invalid");
                    return 0;
                }
                iM15b = iM15b2;
            }
            if (i < 0) {
                i = iM15b;
            }
        }
        return i;
    }

    public static boolean m18e(String str, String str2) {
        if (!str.isEmpty()) {
            String[] strArrSplit = str.split("&", -1);
            int length = strArrSplit.length;
            for (int i = 0; i < length; i++) {
                String strSubstring = strArrSplit[i];
                int iIndexOf = strSubstring.indexOf(61);
                if (iIndexOf >= 0) {
                    strSubstring = strSubstring.substring(0, iIndexOf);
                }
                if (URLDecoder.decode(strSubstring, StandardCharsets.UTF_8).equals(str2)) {
                    return true;
                }
            }
        }
        return false;
    }

    /* JADX WARN: Can't fix incorrect switch cases order, some code will duplicate */
    /* JADX WARN: Code duplicated, block: B:127:0x024d  */
    /* JADX WARN: Code duplicated, block: B:257:0x0488 A[PHI: r21 r23
      0x0488: PHI (r21v14 java.lang.String) = (r21v12 java.lang.String), (r21v15 java.lang.String) binds: [B:256:0x0486, B:262:0x04a1] A[DONT_GENERATE, DONT_INLINE]
      0x0488: PHI (r23v2 java.lang.String) = (r23v1 java.lang.String), (r23v3 java.lang.String) binds: [B:256:0x0486, B:262:0x04a1] A[DONT_GENERATE, DONT_INLINE]] */
    /* JADX WARN: Code duplicated, block: B:266:0x04b0  */
    /* JADX WARN: Code duplicated, block: B:267:0x04b4  */
    /* JADX WARN: Code duplicated, block: B:269:0x04c0  */
    /* JADX WARN: Code duplicated, block: B:273:0x04d0  */
    /* JADX WARN: Code duplicated, block: B:278:0x0532 A[DONT_INVERT] */
    /* JADX WARN: Code duplicated, block: B:280:0x0535  */
    /* JADX WARN: Code duplicated, block: B:282:0x0555  */
    /* JADX WARN: Code duplicated, block: B:294:0x057b  */
    /* JADX WARN: Code duplicated, block: B:298:0x058e  */
    /* JADX WARN: Code duplicated, block: B:300:0x0598  */
    /* JADX WARN: Code duplicated, block: B:301:0x059b  */
    /* JADX WARN: Code duplicated, block: B:304:0x05ae  */
    /* JADX WARN: Code duplicated, block: B:308:0x05bb  */
    /* JADX WARN: Code duplicated, block: B:309:0x05bd A[ADDED_TO_REGION] */
    /* JADX WARN: Code duplicated, block: B:316:0x05db A[DONT_INVERT] */
    /* JADX WARN: Code duplicated, block: B:317:0x05dd  */
    /* JADX WARN: Code duplicated, block: B:319:0x0605  */
    /* JADX WARN: Code duplicated, block: B:322:0x060f A[LOOP:6: B:320:0x060c->B:322:0x060f, LOOP_END] */
    /* JADX WARN: Code duplicated, block: B:333:0x0644  */
    /* JADX WARN: Code duplicated, block: B:340:0x0664  */
    /* JADX WARN: Code duplicated, block: B:342:0x066c A[ADDED_TO_REGION] */
    /* JADX WARN: Code duplicated, block: B:356:0x06af  */
    /* JADX WARN: Code duplicated, block: B:360:0x06c4  */
    /* JADX WARN: Code duplicated, block: B:362:0x06ce  */
    /* JADX WARN: Code duplicated, block: B:363:0x06d1  */
    /* JADX WARN: Code duplicated, block: B:366:0x06e6  */
    /* JADX WARN: Code duplicated, block: B:369:0x06f0  */
    /* JADX WARN: Code duplicated, block: B:370:0x06f3  */
    /* JADX WARN: Code duplicated, block: B:372:0x06f7 A[ADDED_TO_REGION] */
    /* JADX WARN: Code duplicated, block: B:384:0x0734 A[DONT_INVERT] */
    /* JADX WARN: Code duplicated, block: B:385:0x0736  */
    /* JADX WARN: Code duplicated, block: B:387:0x0750  */
    /* JADX WARN: Code duplicated, block: B:390:0x075a A[LOOP:3: B:388:0x0757->B:390:0x075a, LOOP_END] */
    /* JADX WARN: Code duplicated, block: B:400:0x078f  */
    /* JADX WARN: Code duplicated, block: B:405:0x07a4  */
    /* JADX WARN: Code duplicated, block: B:407:0x07ae  */
    /* JADX WARN: Code duplicated, block: B:408:0x07b0  */
    /* JADX WARN: Code duplicated, block: B:411:0x07bd  */
    /* JADX WARN: Code duplicated, block: B:412:0x07bf  */
    /* JADX WARN: Code duplicated, block: B:415:0x07cd A[DONT_INVERT] */
    /* JADX WARN: Code duplicated, block: B:416:0x07cf  */
    /* JADX WARN: Code duplicated, block: B:419:0x07da  */
    /* JADX WARN: Code duplicated, block: B:421:0x07e2 A[DONT_INVERT] */
    /* JADX WARN: Code duplicated, block: B:422:0x07e4  */
    /* JADX WARN: Code duplicated, block: B:427:0x07f6  */
    /* JADX WARN: Code duplicated, block: B:448:0x083a A[DONT_INVERT] */
    /* JADX WARN: Code duplicated, block: B:449:0x083c A[ADDED_TO_REGION] */
    /* JADX WARN: Code duplicated, block: B:459:0x0858  */
    /* JADX WARN: Code duplicated, block: B:461:0x086c  */
    /* JADX WARN: Code duplicated, block: B:468:0x0885  */
    /* JADX WARN: Code duplicated, block: B:469:0x088c  */
    /* JADX WARN: Code duplicated, block: B:471:0x0890  */
    /* JADX WARN: Code duplicated, block: B:474:0x0899  */
    /* JADX WARN: Code duplicated, block: B:476:0x089f  */
    /* JADX WARN: Code duplicated, block: B:481:0x08b2  */
    /* JADX WARN: Code duplicated, block: B:492:0x08e1  */
    /* JADX WARN: Code duplicated, block: B:494:0x08e9  */
    /* JADX WARN: Code duplicated, block: B:495:0x08f1  */
    /* JADX WARN: Code duplicated, block: B:498:0x0902 A[Catch: NumberFormatException -> 0x092b, TryCatch #4 {NumberFormatException -> 0x092b, blocks: (B:496:0x08f7, B:498:0x0902, B:500:0x0910, B:502:0x0916, B:504:0x091e, B:509:0x092d, B:510:0x0932, B:499:0x090b), top: B:559:0x08f7 }] */
    /* JADX WARN: Code duplicated, block: B:499:0x090b A[Catch: NumberFormatException -> 0x092b, TryCatch #4 {NumberFormatException -> 0x092b, blocks: (B:496:0x08f7, B:498:0x0902, B:500:0x0910, B:502:0x0916, B:504:0x091e, B:509:0x092d, B:510:0x0932, B:499:0x090b), top: B:559:0x08f7 }] */
    /* JADX WARN: Code duplicated, block: B:514:0x093a  */
    /* JADX WARN: Code duplicated, block: B:522:0x0950  */
    /* JADX WARN: Code duplicated, block: B:527:0x095f  */
    /* JADX WARN: Code duplicated, block: B:555:0x0639 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:557:0x0785 A[EXC_TOP_SPLITTER, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:567:0x07eb A[SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:569:0x07d4 A[SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:571:0x07f1 A[SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:574:0x072b A[ADDED_TO_REGION, REMOVE, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:582:0x066f A[ADDED_TO_REGION, REMOVE, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:585:0x05d4 A[ADDED_TO_REGION, REMOVE, SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:588:0x05cf A[SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:62:0x0125  */
    /* JADX WARN: Instruction removed from duplicated block: B:273:0x04d0, please report this as an issue */
    public static String m19f(String str) {
        int i;
        int i2;
        String str2;
        int i3;
        String str3;
        String str4;
        String str5;
        String str6;
        int i4;
        String strSubstring;
        int iM17d;
        int iIndexOf;
        int iIndexOf2;
        String strSubstring2;
        String str7;
        int iIndexOf3;
        int iIndexOf4;
        String strConcat;
        int i5;
        int iIndexOf5;
        int i6;
        int iIndexOf6;
        String[] strArrSplit;
        int i7;
        int i8;
        int i9;
        StringBuilder sb;
        int i10;
        int iIndexOf7;
        String strSubstring3;
        String strDecode;
        URI uriCreate;
        int iIndexOf8;
        char[] cArr;
        int i11;
        int iIndexOf9;
        int iIndexOf10;
        int i12;
        int iIndexOf11;
        String[] strArrSplit2;
        String lowerCase;
        int i13;
        int i14;
        int i15;
        String str8;
        StringBuilder sb2;
        int i16;
        int iIndexOf12;
        String strSubstring4;
        String strDecode2;
        String str9;
        String rawQuery;
        int i17;
        String strDecode3;
        String strDecode4;
        int i18;
        int iIndexOf13;
        String strSubstring5;
        Charset charset;
        String strDecode5;
        String strSubstring6;
        String rawAuthority;
        String strSubstring7;
        String strM16c;
        Matcher matcher;
        int i19;
        int i20;
        String strGroup;
        BigDecimal bigDecimal;
        BigDecimal bigDecimalStripTrailingZeros;
        String strSubstring8;
        int iLastIndexOf;
        String strSubstring9;
        int iIndexOf14;
        int i21;
        String strM16c2;
        String str10 = "";
        String strTrim = str == null ? "" : str.trim();
        if (strTrim.isEmpty()) {
            C1566re.m8586j("Xray link is empty");
            return null;
        }
        if (strTrim.length() > 16384) {
            C1566re.m8586j("Xray link is too long");
            return null;
        }
        if (strTrim.indexOf(10) >= 0 || strTrim.indexOf(13) >= 0) {
            C1566re.m8586j("Only one Xray link is supported");
            return null;
        }
        int iIndexOf15 = strTrim.indexOf(58);
        int i22 = 0;
        String strSubstring10 = iIndexOf15 <= 0 ? null : strTrim.substring(0, iIndexOf15);
        if (strSubstring10 != null) {
            Locale locale = Locale.ROOT;
            if (f3a.contains(strSubstring10.toLowerCase(locale))) {
                String lowerCase2 = strSubstring10.toLowerCase(locale);
                if (!strSubstring10.equals(lowerCase2)) {
                    strTrim = lowerCase2 + strTrim.substring(strSubstring10.length());
                }
                if (strTrim.startsWith("ss://")) {
                    int iIndexOf16 = strTrim.indexOf(35, 5);
                    String strSubstring11 = strTrim.substring(5, iIndexOf16 < 0 ? strTrim.length() : iIndexOf16);
                    if (strSubstring11.indexOf(64) < 0 && (strM16c2 = m16c(strSubstring11)) != null) {
                        int iLastIndexOf2 = strM16c2.lastIndexOf(64);
                        if (iLastIndexOf2 <= 0 || iLastIndexOf2 == strM16c2.length() - 1) {
                            C1566re.m8586j("Shadowsocks legacy link is invalid");
                            return null;
                        }
                        String strSubstring12 = strM16c2.substring(0, iLastIndexOf2);
                        String strSubstring13 = strM16c2.substring(iLastIndexOf2 + 1);
                        if (strSubstring12.indexOf(58) <= 0) {
                            C1566re.m8586j("Shadowsocks legacy credentials are invalid");
                            return null;
                        }
                        try {
                            URI uriCreate2 = URI.create("ss://x@".concat(strSubstring13));
                            if (uriCreate2.getHost() == null || !uriCreate2.getRawPath().isEmpty() || uriCreate2.getRawQuery() != null || uriCreate2.getRawFragment() != null) {
                                C1566re.m8586j("Shadowsocks legacy endpoint is invalid");
                                return null;
                            }
                            if (uriCreate2.getPort() <= 0) {
                                C1566re.m8586j("Shadowsocks legacy endpoint port is invalid");
                                return null;
                            }
                            String strEncodeToString = Base64.getUrlEncoder().withoutPadding().encodeToString(strSubstring12.getBytes(StandardCharsets.UTF_8));
                            StringBuilder sb3 = new StringBuilder("ss://");
                            sb3.append(strEncodeToString);
                            sb3.append("@");
                            sb3.append(strSubstring13);
                            sb3.append(iIndexOf16 < 0 ? "" : strTrim.substring(iIndexOf16));
                            strTrim = sb3.toString();
                        } catch (IllegalArgumentException e) {
                            throw new IllegalArgumentException("Shadowsocks legacy endpoint is invalid", e);
                        }
                    }
                }
                String str11 = "Invalid Xray link";
                if (strTrim.startsWith("ss://")) {
                    try {
                        String rawQuery2 = URI.create(strTrim).getRawQuery();
                        if (rawQuery2 == null || rawQuery2.isEmpty()) {
                            i2 = 1;
                            str2 = "Invalid Xray link";
                            i = 2;
                        } else {
                            i = 2;
                            String[] strArrSplit3 = rawQuery2.split("&", -1);
                            String strDecode6 = null;
                            i2 = 1;
                            int i23 = -1;
                            int i24 = 0;
                            while (i24 < strArrSplit3.length) {
                                int iIndexOf17 = strArrSplit3[i24].indexOf(61);
                                String strSubstring14 = iIndexOf17 < 0 ? strArrSplit3[i24] : strArrSplit3[i24].substring(i22, iIndexOf17);
                                Charset charset2 = StandardCharsets.UTF_8;
                                int i25 = i22;
                                if (URLDecoder.decode(strSubstring14, charset2).equals("plugin")) {
                                    if (i23 >= 0 || iIndexOf17 < 0) {
                                        C1566re.m8586j("Shadowsocks SIP003 plugin is ambiguous");
                                        return null;
                                    }
                                    strDecode6 = URLDecoder.decode(strArrSplit3[i24].substring(iIndexOf17 + 1), charset2);
                                    i23 = i24;
                                }
                                i24++;
                                i22 = i25;
                            }
                            int i26 = i22;
                            if (i23 < 0) {
                                str2 = "Invalid Xray link";
                            } else {
                                String[] strArrSplit4 = strDecode6.split(";", -1);
                                if (strArrSplit4.length == 0 || !strArrSplit4[i26].equals("v2ray-plugin")) {
                                    C1566re.m8586j("Unsupported Shadowsocks SIP003 plugin");
                                    return null;
                                }
                                String str12 = null;
                                String str13 = null;
                                String str14 = "websocket";
                                int i27 = 1;
                                int i28 = i26;
                                int i29 = i28;
                                int i30 = i29;
                                while (true) {
                                    String[] strArr = strArrSplit4;
                                    i28 = i28;
                                    int i31 = i29;
                                    if (i27 < strArrSplit4.length) {
                                        String str15 = strArr[i27];
                                        if (str15.isEmpty()) {
                                            i3 = i27;
                                            str3 = str11;
                                        } else {
                                            if (!str15.equals("tls")) {
                                                int i32 = i30;
                                                int iIndexOf18 = str15.indexOf(61);
                                                String strSubstring15 = iIndexOf18 < 0 ? str15 : str15.substring(i26, iIndexOf18);
                                                String strSubstring16 = iIndexOf18 < 0 ? "" : str15.substring(iIndexOf18 + 1);
                                                i3 = i27;
                                                StringBuilder sb4 = new StringBuilder(strSubstring16.length());
                                                str3 = str11;
                                                int i33 = 0;
                                                boolean z = false;
                                                while (i33 < strSubstring16.length()) {
                                                    char cCharAt = strSubstring16.charAt(i33);
                                                    if (z) {
                                                        sb4.append(cCharAt);
                                                        str4 = strSubstring16;
                                                        z = false;
                                                    } else {
                                                        str4 = strSubstring16;
                                                        if (cCharAt == '\\') {
                                                            z = true;
                                                        } else {
                                                            sb4.append(cCharAt);
                                                        }
                                                    }
                                                    i33++;
                                                    strSubstring16 = str4;
                                                }
                                                if (z) {
                                                    C1566re.m8586j("Shadowsocks v2ray-plugin option has a dangling escape");
                                                    return null;
                                                }
                                                String string = sb4.toString();
                                                switch (strSubstring15) {
                                                    case "mux":
                                                        String str16 = str12;
                                                        String str17 = str13;
                                                        if (i32 != 0) {
                                                            C1566re.m8586j("Shadowsocks v2ray-plugin mux is ambiguous");
                                                            return null;
                                                        }
                                                        if (!string.equals("0")) {
                                                            C1566re.m8586j("Unsupported Shadowsocks v2ray-plugin mux mode");
                                                            return null;
                                                        }
                                                        str13 = str17;
                                                        str12 = str16;
                                                        i30 = 1;
                                                        break;
                                                        break;
                                                    case "host":
                                                        String str18 = str13;
                                                        if (str12 != null) {
                                                            C1566re.m8586j("Shadowsocks v2ray-plugin host is ambiguous");
                                                            return null;
                                                        }
                                                        str12 = string;
                                                        str13 = str18;
                                                        i29 = i31;
                                                        i30 = i32;
                                                        break;
                                                        break;
                                                    case "mode":
                                                        String str19 = str13;
                                                        if (i31 != 0) {
                                                            C1566re.m8586j("Shadowsocks v2ray-plugin mode is ambiguous");
                                                            return null;
                                                        }
                                                        str14 = string;
                                                        str13 = str19;
                                                        i29 = 1;
                                                        i30 = i32;
                                                        break;
                                                        break;
                                                    case "path":
                                                        if (str13 != null) {
                                                            C1566re.m8586j("Shadowsocks v2ray-plugin path is ambiguous");
                                                            return null;
                                                        }
                                                        str13 = string;
                                                        i29 = i31;
                                                        i30 = i32;
                                                        break;
                                                        break;
                                                    default:
                                                        C1566re.m8586j("Unsupported Shadowsocks v2ray-plugin option: ".concat(strSubstring15));
                                                        return null;
                                                }
                                            } else {
                                                if (i28 != 0) {
                                                    C1566re.m8586j("Shadowsocks v2ray-plugin TLS option is ambiguous");
                                                    return null;
                                                }
                                                i3 = i27;
                                                str3 = str11;
                                                i28 = 1;
                                                i29 = i31;
                                            }
                                            i27 = i3 + 1;
                                            strArrSplit4 = strArr;
                                            str11 = str3;
                                            i26 = 0;
                                        }
                                        i28 = i28;
                                        i29 = i31;
                                        i27 = i3 + 1;
                                        strArrSplit4 = strArr;
                                        str11 = str3;
                                        i26 = 0;
                                    } else {
                                        str2 = str11;
                                        String str20 = str12;
                                        String str21 = str13;
                                        if (!str14.equals("websocket")) {
                                            C1566re.m8586j("Unsupported Shadowsocks v2ray-plugin mode");
                                            return null;
                                        }
                                        String[] strArr2 = {"type", "host", "path", "security"};
                                        for (int i34 = 0; i34 < 4; i34++) {
                                            if (m18e(rawQuery2, strArr2[i34])) {
                                                C1566re.m8586j("Shadowsocks transport settings are ambiguous");
                                                return null;
                                            }
                                        }
                                        StringBuilder sb5 = new StringBuilder();
                                        for (int i35 = 0; i35 < strArrSplit3.length; i35++) {
                                            if (i35 != i23 && !strArrSplit3[i35].isEmpty()) {
                                                if (!sb5.isEmpty()) {
                                                    sb5.append(Typography.amp);
                                                }
                                                sb5.append(strArrSplit3[i35]);
                                            }
                                        }
                                        m14a(sb5, "type", "ws");
                                        if (str20 != null && !str20.isEmpty()) {
                                            m14a(sb5, "host", str20);
                                        }
                                        if (str21 != null && !str21.isEmpty()) {
                                            m14a(sb5, "path", str21);
                                        }
                                        if (i28 != 0) {
                                            m14a(sb5, "security", "tls");
                                        }
                                        int iIndexOf19 = strTrim.indexOf(63);
                                        int iIndexOf20 = strTrim.indexOf(35, iIndexOf19 + 1);
                                        if (iIndexOf20 < 0) {
                                            iIndexOf20 = strTrim.length();
                                        }
                                        strTrim = strTrim.substring(0, iIndexOf19) + "?" + ((Object) sb5) + strTrim.substring(iIndexOf20);
                                    }
                                }
                            }
                        }
                    } catch (IllegalArgumentException e2) {
                        throw new IllegalArgumentException("Invalid Xray link", e2);
                    }
                } else {
                    i2 = 1;
                    str2 = "Invalid Xray link";
                    i = 2;
                }
                if (strTrim.startsWith("trojan://")) {
                    int iIndexOf21 = strTrim.indexOf(63);
                    int iIndexOf22 = strTrim.indexOf(35);
                    if (iIndexOf22 < 0) {
                        iIndexOf22 = strTrim.length();
                    }
                    if (iIndexOf21 < 0 || iIndexOf21 >= iIndexOf22) {
                        strTrim = strTrim.substring(0, iIndexOf22) + "?security=tls" + strTrim.substring(iIndexOf22);
                    } else {
                        int i36 = iIndexOf21 + 1;
                        if (i36 >= iIndexOf22) {
                            strTrim = strTrim.substring(0, i36) + "security=tls" + strTrim.substring(iIndexOf22);
                        }
                    }
                }
                String str22 = "ports";
                try {
                    if (strTrim.startsWith("hy2://") || strTrim.startsWith("hysteria2://")) {
                        int iIndexOf23 = strTrim.indexOf("//") + 2;
                        int length = strTrim.length();
                        char[] cArr2 = {'/', '?', '#'};
                        int i37 = 0;
                        for (int i38 = 3; i37 < i38; i38 = 3) {
                            int iIndexOf24 = strTrim.indexOf(cArr2[i37], iIndexOf23);
                            if (iIndexOf24 >= 0 && iIndexOf24 < length) {
                                length = iIndexOf24;
                            }
                            i37++;
                        }
                        String strSubstring17 = strTrim.substring(iIndexOf23, length);
                        int iLastIndexOf3 = strSubstring17.lastIndexOf(64) + 1;
                        String strSubstring18 = strSubstring17.substring(iLastIndexOf3);
                        if (strSubstring18.startsWith("[")) {
                            str5 = "Hysteria2 port hopping is ambiguous";
                            int iIndexOf25 = strSubstring18.indexOf(93);
                            if (iIndexOf25 >= 0 && (i5 = iIndexOf25 + 1) < strSubstring18.length() && strSubstring18.charAt(i5) == ':') {
                                i4 = i5;
                                str6 = "[";
                                strSubstring = strSubstring18.substring(i4 + 1);
                                if (strSubstring.indexOf(44) < 0 || strSubstring.indexOf(45) >= 0) {
                                    iM17d = m17d(strSubstring);
                                    iIndexOf = strTrim.indexOf(63, length);
                                    if (iIndexOf < 0) {
                                        strSubstring2 = "";
                                    } else {
                                        int i39 = iIndexOf + 1;
                                        iIndexOf2 = strTrim.indexOf(35, i39);
                                        if (iIndexOf2 < 0) {
                                            iIndexOf2 = strTrim.length();
                                        }
                                        strSubstring2 = strTrim.substring(i39, iIndexOf2);
                                    }
                                    if (!m18e(strSubstring2, "ports")) {
                                        C1566re.m8586j(str5);
                                        return null;
                                    }
                                    str10 = "";
                                    str7 = strTrim.substring(0, iIndexOf23) + (strSubstring17.substring(0, iLastIndexOf3 + i4 + 1) + iM17d) + strTrim.substring(length);
                                    iIndexOf3 = str7.indexOf(35, iIndexOf23);
                                    iIndexOf4 = str7.indexOf(63, iIndexOf23);
                                    strConcat = "ports=".concat(strSubstring);
                                    if (iIndexOf4 >= 0 || (iIndexOf3 >= 0 && iIndexOf4 >= iIndexOf3)) {
                                        if (iIndexOf3 < 0) {
                                            iIndexOf3 = str7.length();
                                        }
                                        strTrim = str7.substring(0, iIndexOf3) + "?" + strConcat + str7.substring(iIndexOf3);
                                    } else {
                                        int i40 = iIndexOf4 + 1;
                                        strTrim = str7.substring(0, i40) + strConcat + "&" + str7.substring(i40);
                                    }
                                } else {
                                    str10 = "";
                                }
                            }
                        } else {
                            str5 = "Hysteria2 port hopping is ambiguous";
                            int iLastIndexOf4 = strSubstring18.lastIndexOf(58);
                            if (iLastIndexOf4 >= 0) {
                                str6 = "[";
                                if (strSubstring18.indexOf(58) != iLastIndexOf4) {
                                    str10 = "";
                                } else {
                                    i4 = iLastIndexOf4;
                                    strSubstring = strSubstring18.substring(i4 + 1);
                                    if (strSubstring.indexOf(44) < 0) {
                                    }
                                    iM17d = m17d(strSubstring);
                                    iIndexOf = strTrim.indexOf(63, length);
                                    if (iIndexOf < 0) {
                                        strSubstring2 = "";
                                    } else {
                                        int i310 = iIndexOf + 1;
                                        iIndexOf2 = strTrim.indexOf(35, i310);
                                        if (iIndexOf2 < 0) {
                                            iIndexOf2 = strTrim.length();
                                        }
                                        strSubstring2 = strTrim.substring(i310, iIndexOf2);
                                    }
                                    if (!m18e(strSubstring2, "ports")) {
                                        C1566re.m8586j(str5);
                                        return null;
                                    }
                                    str10 = "";
                                    str7 = strTrim.substring(0, iIndexOf23) + (strSubstring17.substring(0, iLastIndexOf3 + i4 + 1) + iM17d) + strTrim.substring(length);
                                    iIndexOf3 = str7.indexOf(35, iIndexOf23);
                                    iIndexOf4 = str7.indexOf(63, iIndexOf23);
                                    strConcat = "ports=".concat(strSubstring);
                                    if (iIndexOf4 >= 0) {
                                        if (iIndexOf3 < 0) {
                                            iIndexOf3 = str7.length();
                                        }
                                        strTrim = str7.substring(0, iIndexOf3) + "?" + strConcat + str7.substring(iIndexOf3);
                                    } else {
                                        if (iIndexOf3 < 0) {
                                            iIndexOf3 = str7.length();
                                        }
                                        strTrim = str7.substring(0, iIndexOf3) + "?" + strConcat + str7.substring(iIndexOf3);
                                    }
                                }
                            }
                        }
                        if ((strTrim.startsWith("hy2://") || strTrim.startsWith("hysteria2://")) && (iIndexOf5 = strTrim.indexOf(63)) >= 0) {
                            i6 = iIndexOf5 + 1;
                            iIndexOf6 = strTrim.indexOf(35, i6);
                            if (iIndexOf6 < 0) {
                                iIndexOf6 = strTrim.length();
                            }
                            strArrSplit = strTrim.substring(i6, iIndexOf6).split("&", -1);
                            i7 = 0;
                            i8 = 0;
                            i9 = -1;
                            while (i7 < strArrSplit.length) {
                                iIndexOf7 = strArrSplit[i7].indexOf(61);
                                if (iIndexOf7 < 0) {
                                    strSubstring3 = strArrSplit[i7];
                                } else {
                                    strSubstring3 = strArrSplit[i7].substring(0, iIndexOf7);
                                }
                                Charset charset3 = StandardCharsets.UTF_8;
                                strDecode = URLDecoder.decode(strSubstring3, charset3);
                                if (strDecode.equals(str22)) {
                                    i8 = i2;
                                }
                                String str23 = str22;
                                if (strDecode.equals("mport")) {
                                    if (i9 < 0 || iIndexOf7 < 0) {
                                        C1566re.m8586j(str5);
                                        return null;
                                    }
                                    m17d(URLDecoder.decode(strArrSplit[i7].substring(iIndexOf7 + 1), charset3));
                                    i9 = i7;
                                }
                                i7++;
                                str22 = str23;
                            }
                            if (i9 >= 0) {
                                if (i8 != 0) {
                                    C1566re.m8586j(str5);
                                    return null;
                                }
                                strArrSplit[i9] = "ports=".concat(strArrSplit[i9].substring(strArrSplit[i9].indexOf(61) + 1));
                                StringBuilder sb6 = new StringBuilder(strTrim.substring(0, i6));
                                sb = new StringBuilder();
                                if (strArrSplit.length > 0) {
                                    sb.append((CharSequence) strArrSplit[0]);
                                    for (i10 = i2; i10 < strArrSplit.length; i10++) {
                                        sb.append((CharSequence) "&");
                                        sb.append((CharSequence) strArrSplit[i10]);
                                    }
                                }
                                sb6.append(sb.toString());
                                sb6.append(strTrim.substring(iIndexOf6));
                                strTrim = sb6.toString();
                            }
                        }
                        if (strTrim.startsWith("hy2://") || strTrim.startsWith("hysteria2://")) {
                            try {
                                uriCreate = URI.create(strTrim);
                                if (uriCreate.getPort() < 0 && uriCreate.getHost() != null && uriCreate.getRawAuthority() != null) {
                                    iIndexOf8 = strTrim.indexOf("//") + 2;
                                    int length2 = strTrim.length();
                                    cArr = new char[]{'/', '?', '#'};
                                    for (i11 = 0; i11 < 3; i11++) {
                                        iIndexOf9 = strTrim.indexOf(cArr[i11], iIndexOf8);
                                        if (iIndexOf9 < 0 && iIndexOf9 < length2) {
                                            length2 = iIndexOf9;
                                        }
                                    }
                                    strTrim = strTrim.substring(0, length2) + ":443" + strTrim.substring(length2);
                                }
                            } catch (IllegalArgumentException e3) {
                                throw new IllegalArgumentException(str2, e3);
                            }
                        }
                        if ((!strTrim.startsWith("hy2://") || strTrim.startsWith("hysteria2://")) && (iIndexOf10 = strTrim.indexOf(63)) >= 0) {
                            i12 = iIndexOf10 + 1;
                            iIndexOf11 = strTrim.indexOf(35, i12);
                            if (iIndexOf11 < 0) {
                                iIndexOf11 = strTrim.length();
                            }
                            strArrSplit2 = strTrim.substring(i12, iIndexOf11).split("&", -1);
                            lowerCase = null;
                            i13 = 0;
                            i14 = 0;
                            i15 = -1;
                            while (i13 < strArrSplit2.length) {
                                iIndexOf12 = strArrSplit2[i13].indexOf(61);
                                if (iIndexOf12 < 0) {
                                    strSubstring4 = strArrSplit2[i13];
                                } else {
                                    strSubstring4 = strArrSplit2[i13].substring(0, iIndexOf12);
                                }
                                Charset charset4 = StandardCharsets.UTF_8;
                                strDecode2 = URLDecoder.decode(strSubstring4, charset4);
                                if (strDecode2.equals("pcs")) {
                                    i14 = i2;
                                }
                                if (!strDecode2.equals("pinSHA256")) {
                                    str9 = str10;
                                } else {
                                    if (i15 < 0 || iIndexOf12 < 0) {
                                        C1566re.m8586j("Hysteria2 certificate pin is invalid");
                                        return null;
                                    }
                                    str9 = str10;
                                    String strReplace = URLDecoder.decode(strArrSplit2[i13].substring(iIndexOf12 + 1), charset4).replace(":", str9).replace("-", str9);
                                    if (!strReplace.matches("(?i)[0-9a-f]{64}")) {
                                        C1566re.m8586j("Hysteria2 certificate pin is invalid");
                                        return null;
                                    }
                                    lowerCase = strReplace.toLowerCase(Locale.ROOT);
                                    i15 = i13;
                                }
                                i13++;
                                str10 = str9;
                            }
                            str8 = str10;
                            if (i15 >= 0) {
                                if (i14 != 0) {
                                    C1566re.m8586j("Hysteria2 certificate pin is ambiguous");
                                    return null;
                                }
                                strArrSplit2[i15] = xp0.m10580j("pcs=", lowerCase);
                                StringBuilder sb7 = new StringBuilder(strTrim.substring(0, i12));
                                sb2 = new StringBuilder();
                                if (strArrSplit2.length > 0) {
                                    sb2.append((CharSequence) strArrSplit2[0]);
                                    for (i16 = i2; i16 < strArrSplit2.length; i16++) {
                                        sb2.append((CharSequence) "&");
                                        sb2.append((CharSequence) strArrSplit2[i16]);
                                    }
                                }
                                sb7.append(sb2.toString());
                                sb7.append(strTrim.substring(iIndexOf11));
                                strTrim = sb7.toString();
                            }
                        } else {
                            str8 = str10;
                        }
                        if (strTrim.startsWith("hy2://") || strTrim.startsWith("hysteria2://")) {
                            try {
                                rawQuery = URI.create(strTrim).getRawQuery();
                                if (rawQuery != null && !rawQuery.isEmpty()) {
                                    i17 = 0;
                                    strDecode3 = null;
                                    strDecode4 = null;
                                    for (String str24 : rawQuery.split("&", -1)) {
                                        iIndexOf13 = str24.indexOf(61);
                                        if (iIndexOf13 < 0) {
                                            strSubstring5 = str24;
                                        } else {
                                            strSubstring5 = str24.substring(0, iIndexOf13);
                                        }
                                        charset = StandardCharsets.UTF_8;
                                        strDecode5 = URLDecoder.decode(strSubstring5, charset);
                                        if (iIndexOf13 < 0) {
                                            strSubstring6 = str8;
                                        } else {
                                            strSubstring6 = str24.substring(iIndexOf13 + 1);
                                        }
                                        if (strDecode5.equals("obfs")) {
                                            if (strDecode3 != null) {
                                                C1566re.m8586j("Hysteria2 obfuscation is ambiguous");
                                                return null;
                                            }
                                            strDecode3 = URLDecoder.decode(strSubstring6, charset);
                                        } else if (strDecode5.equals("obfs-password")) {
                                            continue;
                                        } else {
                                            if (i17 != 0) {
                                                C1566re.m8586j("Hysteria2 obfuscation password is ambiguous");
                                                return null;
                                            }
                                            strDecode4 = URLDecoder.decode(strSubstring6, charset);
                                            i17 = i2;
                                        }
                                    }
                                    if (strDecode3 == null && !strDecode3.isEmpty()) {
                                        String lowerCase3 = strDecode3.toLowerCase(Locale.ROOT);
                                        if (!strDecode3.equals(lowerCase3)) {
                                            C1566re.m8586j("Hysteria2 obfuscation type must be lowercase");
                                            return null;
                                        }
                                        if (lowerCase3.equals("gecko")) {
                                            C1566re.m8586j("Hysteria2 Gecko obfuscation is unsupported by this native core");
                                            return null;
                                        }
                                        if (!lowerCase3.equals("salamander")) {
                                            C1566re.m8586j("Unsupported Hysteria2 obfuscation type");
                                            return null;
                                        }
                                        if (strDecode4 == null || strDecode4.isEmpty()) {
                                            C1566re.m8586j("Hysteria2 obfuscation password is missing");
                                            return null;
                                        }
                                    } else if (i17 != 0 && strDecode4 != null && !strDecode4.isEmpty()) {
                                        C1566re.m8586j("Hysteria2 obfuscation type is missing");
                                        return null;
                                    }
                                }
                            } catch (IllegalArgumentException e4) {
                                throw new IllegalArgumentException(str2, e4);
                            }
                        }
                        rawAuthority = URI.create(strTrim).getRawAuthority();
                        if (rawAuthority != null) {
                            strSubstring8 = rawAuthority.substring(rawAuthority.lastIndexOf(64) + 1);
                            if (strSubstring8.startsWith(str6)) {
                                iIndexOf14 = strSubstring8.indexOf(93);
                                if (iIndexOf14 >= 0 && (i21 = iIndexOf14 + 1) != strSubstring8.length()) {
                                    if (strSubstring8.charAt(i21) == ':') {
                                        C1566re.m8586j("Xray link port is invalid");
                                        return null;
                                    }
                                    strSubstring9 = strSubstring8.substring(iIndexOf14 + 2);
                                    m15b(strSubstring9);
                                }
                            } else {
                                iLastIndexOf = strSubstring8.lastIndexOf(58);
                                if (iLastIndexOf >= 0) {
                                    if (strSubstring8.indexOf(58) == iLastIndexOf) {
                                        C1566re.m8586j("Xray link port is invalid");
                                        return null;
                                    }
                                    strSubstring9 = strSubstring8.substring(iLastIndexOf + 1);
                                    m15b(strSubstring9);
                                }
                            }
                        }
                        if (strTrim.startsWith("vmess://")) {
                            strSubstring7 = strTrim.substring(8);
                            if (strSubstring7.indexOf(64) < 0 && (strM16c = m16c(strSubstring7)) != null && strM16c.trim().startsWith("{")) {
                                matcher = f4b.matcher(strM16c);
                                while (matcher.find()) {
                                    i19 = i2;
                                    if (matcher.group(i19) != null) {
                                        strGroup = matcher.group(i19);
                                        i20 = i;
                                    } else {
                                        i20 = i;
                                        strGroup = matcher.group(i20);
                                    }
                                    try {
                                        bigDecimal = new BigDecimal(strGroup);
                                        if (bigDecimal.signum() == 0) {
                                            bigDecimalStripTrailingZeros = new BigDecimal(BigInteger.ZERO, 0);
                                        } else {
                                            bigDecimalStripTrailingZeros = bigDecimal.stripTrailingZeros();
                                        }
                                        if (bigDecimalStripTrailingZeros.scale() <= 0 || bigDecimalStripTrailingZeros.compareTo(f5c) < 0 || bigDecimalStripTrailingZeros.compareTo(f6d) > 0) {
                                            throw new IllegalArgumentException("Xray link port is invalid");
                                        }
                                        i2 = i19;
                                        i = i20;
                                    } catch (NumberFormatException e5) {
                                        throw new IllegalArgumentException("Xray link port is invalid", e5);
                                    }
                                }
                            }
                        }
                        return strTrim;
                    }
                    str5 = "Hysteria2 port hopping is ambiguous";
                    rawAuthority = URI.create(strTrim).getRawAuthority();
                    if (rawAuthority != null) {
                        strSubstring8 = rawAuthority.substring(rawAuthority.lastIndexOf(64) + 1);
                        if (strSubstring8.startsWith(str6)) {
                            iIndexOf14 = strSubstring8.indexOf(93);
                            if (iIndexOf14 >= 0) {
                                if (strSubstring8.charAt(i21) == ':') {
                                    C1566re.m8586j("Xray link port is invalid");
                                    return null;
                                }
                                strSubstring9 = strSubstring8.substring(iIndexOf14 + 2);
                                m15b(strSubstring9);
                            }
                        } else {
                            iLastIndexOf = strSubstring8.lastIndexOf(58);
                            if (iLastIndexOf >= 0) {
                                if (strSubstring8.indexOf(58) == iLastIndexOf) {
                                    C1566re.m8586j("Xray link port is invalid");
                                    return null;
                                }
                                strSubstring9 = strSubstring8.substring(iLastIndexOf + 1);
                                m15b(strSubstring9);
                            }
                        }
                    }
                    if (strTrim.startsWith("vmess://")) {
                        strSubstring7 = strTrim.substring(8);
                        if (strSubstring7.indexOf(64) < 0) {
                            matcher = f4b.matcher(strM16c);
                            while (matcher.find()) {
                                i19 = i2;
                                if (matcher.group(i19) != null) {
                                    strGroup = matcher.group(i19);
                                    i20 = i;
                                } else {
                                    i20 = i;
                                    strGroup = matcher.group(i20);
                                }
                                bigDecimal = new BigDecimal(strGroup);
                                if (bigDecimal.signum() == 0) {
                                    bigDecimalStripTrailingZeros = new BigDecimal(BigInteger.ZERO, 0);
                                } else {
                                    bigDecimalStripTrailingZeros = bigDecimal.stripTrailingZeros();
                                }
                                if (bigDecimalStripTrailingZeros.scale() <= 0) {
                                }
                                throw new IllegalArgumentException("Xray link port is invalid");
                            }
                        }
                    }
                    return strTrim;
                } catch (IllegalArgumentException e6) {
                    throw new IllegalArgumentException(str2, e6);
                }
                str6 = "[";
                if (strTrim.startsWith("hy2://")) {
                    i6 = iIndexOf5 + 1;
                    iIndexOf6 = strTrim.indexOf(35, i6);
                    if (iIndexOf6 < 0) {
                        iIndexOf6 = strTrim.length();
                    }
                    strArrSplit = strTrim.substring(i6, iIndexOf6).split("&", -1);
                    i7 = 0;
                    i8 = 0;
                    i9 = -1;
                    while (i7 < strArrSplit.length) {
                        iIndexOf7 = strArrSplit[i7].indexOf(61);
                        if (iIndexOf7 < 0) {
                            strSubstring3 = strArrSplit[i7];
                        } else {
                            strSubstring3 = strArrSplit[i7].substring(0, iIndexOf7);
                        }
                        Charset charset5 = StandardCharsets.UTF_8;
                        strDecode = URLDecoder.decode(strSubstring3, charset5);
                        if (strDecode.equals(str22)) {
                            i8 = i2;
                        }
                        String str25 = str22;
                        if (strDecode.equals("mport")) {
                            if (i9 < 0) {
                            }
                            C1566re.m8586j(str5);
                            return null;
                        }
                        i7++;
                        str22 = str25;
                    }
                    if (i9 >= 0) {
                        if (i8 != 0) {
                            C1566re.m8586j(str5);
                            return null;
                        }
                        strArrSplit[i9] = "ports=".concat(strArrSplit[i9].substring(strArrSplit[i9].indexOf(61) + 1));
                        StringBuilder sb8 = new StringBuilder(strTrim.substring(0, i6));
                        sb = new StringBuilder();
                        if (strArrSplit.length > 0) {
                            sb.append((CharSequence) strArrSplit[0]);
                            while (i10 < strArrSplit.length) {
                                sb.append((CharSequence) "&");
                                sb.append((CharSequence) strArrSplit[i10]);
                            }
                        }
                        sb8.append(sb.toString());
                        sb8.append(strTrim.substring(iIndexOf6));
                        strTrim = sb8.toString();
                    }
                } else {
                    i6 = iIndexOf5 + 1;
                    iIndexOf6 = strTrim.indexOf(35, i6);
                    if (iIndexOf6 < 0) {
                        iIndexOf6 = strTrim.length();
                    }
                    strArrSplit = strTrim.substring(i6, iIndexOf6).split("&", -1);
                    i7 = 0;
                    i8 = 0;
                    i9 = -1;
                    while (i7 < strArrSplit.length) {
                        iIndexOf7 = strArrSplit[i7].indexOf(61);
                        if (iIndexOf7 < 0) {
                            strSubstring3 = strArrSplit[i7];
                        } else {
                            strSubstring3 = strArrSplit[i7].substring(0, iIndexOf7);
                        }
                        Charset charset6 = StandardCharsets.UTF_8;
                        strDecode = URLDecoder.decode(strSubstring3, charset6);
                        if (strDecode.equals(str22)) {
                            i8 = i2;
                        }
                        String str26 = str22;
                        if (strDecode.equals("mport")) {
                            if (i9 < 0) {
                            }
                            C1566re.m8586j(str5);
                            return null;
                        }
                        i7++;
                        str22 = str26;
                    }
                    if (i9 >= 0) {
                        if (i8 != 0) {
                            C1566re.m8586j(str5);
                            return null;
                        }
                        strArrSplit[i9] = "ports=".concat(strArrSplit[i9].substring(strArrSplit[i9].indexOf(61) + 1));
                        StringBuilder sb9 = new StringBuilder(strTrim.substring(0, i6));
                        sb = new StringBuilder();
                        if (strArrSplit.length > 0) {
                            sb.append((CharSequence) strArrSplit[0]);
                            while (i10 < strArrSplit.length) {
                                sb.append((CharSequence) "&");
                                sb.append((CharSequence) strArrSplit[i10]);
                            }
                        }
                        sb9.append(sb.toString());
                        sb9.append(strTrim.substring(iIndexOf6));
                        strTrim = sb9.toString();
                    }
                }
                if (strTrim.startsWith("hy2://")) {
                    uriCreate = URI.create(strTrim);
                    if (uriCreate.getPort() < 0) {
                        iIndexOf8 = strTrim.indexOf("//") + 2;
                        int length3 = strTrim.length();
                        cArr = new char[]{'/', '?', '#'};
                        while (i11 < 3) {
                            iIndexOf9 = strTrim.indexOf(cArr[i11], iIndexOf8);
                            if (iIndexOf9 < 0) {
                            }
                        }
                        strTrim = strTrim.substring(0, length3) + ":443" + strTrim.substring(length3);
                    }
                } else {
                    uriCreate = URI.create(strTrim);
                    if (uriCreate.getPort() < 0) {
                        iIndexOf8 = strTrim.indexOf("//") + 2;
                        int length4 = strTrim.length();
                        cArr = new char[]{'/', '?', '#'};
                        while (i11 < 3) {
                            iIndexOf9 = strTrim.indexOf(cArr[i11], iIndexOf8);
                            if (iIndexOf9 < 0) {
                            }
                        }
                        strTrim = strTrim.substring(0, length4) + ":443" + strTrim.substring(length4);
                    }
                }
                if (strTrim.startsWith("hy2://")) {
                    i12 = iIndexOf10 + 1;
                    iIndexOf11 = strTrim.indexOf(35, i12);
                    if (iIndexOf11 < 0) {
                        iIndexOf11 = strTrim.length();
                    }
                    strArrSplit2 = strTrim.substring(i12, iIndexOf11).split("&", -1);
                    lowerCase = null;
                    i13 = 0;
                    i14 = 0;
                    i15 = -1;
                    while (i13 < strArrSplit2.length) {
                        iIndexOf12 = strArrSplit2[i13].indexOf(61);
                        if (iIndexOf12 < 0) {
                            strSubstring4 = strArrSplit2[i13];
                        } else {
                            strSubstring4 = strArrSplit2[i13].substring(0, iIndexOf12);
                        }
                        Charset charset7 = StandardCharsets.UTF_8;
                        strDecode2 = URLDecoder.decode(strSubstring4, charset7);
                        if (strDecode2.equals("pcs")) {
                            i14 = i2;
                        }
                        if (!strDecode2.equals("pinSHA256")) {
                            if (i15 < 0) {
                            }
                            C1566re.m8586j("Hysteria2 certificate pin is invalid");
                            return null;
                        }
                        str9 = str10;
                        i13++;
                        str10 = str9;
                    }
                    str8 = str10;
                    if (i15 >= 0) {
                        if (i14 != 0) {
                            C1566re.m8586j("Hysteria2 certificate pin is ambiguous");
                            return null;
                        }
                        strArrSplit2[i15] = xp0.m10580j("pcs=", lowerCase);
                        StringBuilder sb10 = new StringBuilder(strTrim.substring(0, i12));
                        sb2 = new StringBuilder();
                        if (strArrSplit2.length > 0) {
                            sb2.append((CharSequence) strArrSplit2[0]);
                            while (i16 < strArrSplit2.length) {
                                sb2.append((CharSequence) "&");
                                sb2.append((CharSequence) strArrSplit2[i16]);
                            }
                        }
                        sb10.append(sb2.toString());
                        sb10.append(strTrim.substring(iIndexOf11));
                        strTrim = sb10.toString();
                    }
                } else {
                    i12 = iIndexOf10 + 1;
                    iIndexOf11 = strTrim.indexOf(35, i12);
                    if (iIndexOf11 < 0) {
                        iIndexOf11 = strTrim.length();
                    }
                    strArrSplit2 = strTrim.substring(i12, iIndexOf11).split("&", -1);
                    lowerCase = null;
                    i13 = 0;
                    i14 = 0;
                    i15 = -1;
                    while (i13 < strArrSplit2.length) {
                        iIndexOf12 = strArrSplit2[i13].indexOf(61);
                        if (iIndexOf12 < 0) {
                            strSubstring4 = strArrSplit2[i13];
                        } else {
                            strSubstring4 = strArrSplit2[i13].substring(0, iIndexOf12);
                        }
                        Charset charset8 = StandardCharsets.UTF_8;
                        strDecode2 = URLDecoder.decode(strSubstring4, charset8);
                        if (strDecode2.equals("pcs")) {
                            i14 = i2;
                        }
                        if (!strDecode2.equals("pinSHA256")) {
                            if (i15 < 0) {
                            }
                            C1566re.m8586j("Hysteria2 certificate pin is invalid");
                            return null;
                        }
                        str9 = str10;
                        i13++;
                        str10 = str9;
                    }
                    str8 = str10;
                    if (i15 >= 0) {
                        if (i14 != 0) {
                            C1566re.m8586j("Hysteria2 certificate pin is ambiguous");
                            return null;
                        }
                        strArrSplit2[i15] = xp0.m10580j("pcs=", lowerCase);
                        StringBuilder sb11 = new StringBuilder(strTrim.substring(0, i12));
                        sb2 = new StringBuilder();
                        if (strArrSplit2.length > 0) {
                            sb2.append((CharSequence) strArrSplit2[0]);
                            while (i16 < strArrSplit2.length) {
                                sb2.append((CharSequence) "&");
                                sb2.append((CharSequence) strArrSplit2[i16]);
                            }
                        }
                        sb11.append(sb2.toString());
                        sb11.append(strTrim.substring(iIndexOf11));
                        strTrim = sb11.toString();
                    }
                }
                if (strTrim.startsWith("hy2://")) {
                    rawQuery = URI.create(strTrim).getRawQuery();
                    if (rawQuery != null) {
                        i17 = 0;
                        strDecode3 = null;
                        strDecode4 = null;
                        while (i18 < r2) {
                            iIndexOf13 = str24.indexOf(61);
                            if (iIndexOf13 < 0) {
                                strSubstring5 = str24;
                            } else {
                                strSubstring5 = str24.substring(0, iIndexOf13);
                            }
                            charset = StandardCharsets.UTF_8;
                            strDecode5 = URLDecoder.decode(strSubstring5, charset);
                            if (iIndexOf13 < 0) {
                                strSubstring6 = str8;
                            } else {
                                strSubstring6 = str24.substring(iIndexOf13 + 1);
                            }
                            if (strDecode5.equals("obfs")) {
                                if (strDecode3 != null) {
                                    C1566re.m8586j("Hysteria2 obfuscation is ambiguous");
                                    return null;
                                }
                                strDecode3 = URLDecoder.decode(strSubstring6, charset);
                            } else if (strDecode5.equals("obfs-password")) {
                                continue;
                            } else {
                                if (i17 != 0) {
                                    C1566re.m8586j("Hysteria2 obfuscation password is ambiguous");
                                    return null;
                                }
                                strDecode4 = URLDecoder.decode(strSubstring6, charset);
                                i17 = i2;
                            }
                        }
                        if (strDecode3 == null) {
                            if (i17 != 0) {
                                C1566re.m8586j("Hysteria2 obfuscation type is missing");
                                return null;
                            }
                        } else if (i17 != 0) {
                            C1566re.m8586j("Hysteria2 obfuscation type is missing");
                            return null;
                        }
                    }
                } else {
                    rawQuery = URI.create(strTrim).getRawQuery();
                    if (rawQuery != null) {
                        i17 = 0;
                        strDecode3 = null;
                        strDecode4 = null;
                        while (i18 < r2) {
                            iIndexOf13 = str24.indexOf(61);
                            if (iIndexOf13 < 0) {
                                strSubstring5 = str24;
                            } else {
                                strSubstring5 = str24.substring(0, iIndexOf13);
                            }
                            charset = StandardCharsets.UTF_8;
                            strDecode5 = URLDecoder.decode(strSubstring5, charset);
                            if (iIndexOf13 < 0) {
                                strSubstring6 = str8;
                            } else {
                                strSubstring6 = str24.substring(iIndexOf13 + 1);
                            }
                            if (strDecode5.equals("obfs")) {
                                if (strDecode3 != null) {
                                    C1566re.m8586j("Hysteria2 obfuscation is ambiguous");
                                    return null;
                                }
                                strDecode3 = URLDecoder.decode(strSubstring6, charset);
                            } else if (strDecode5.equals("obfs-password")) {
                                continue;
                            } else {
                                if (i17 != 0) {
                                    C1566re.m8586j("Hysteria2 obfuscation password is ambiguous");
                                    return null;
                                }
                                strDecode4 = URLDecoder.decode(strSubstring6, charset);
                                i17 = i2;
                            }
                        }
                        if (strDecode3 == null) {
                            if (i17 != 0) {
                                C1566re.m8586j("Hysteria2 obfuscation type is missing");
                                return null;
                            }
                        } else if (i17 != 0) {
                            C1566re.m8586j("Hysteria2 obfuscation type is missing");
                            return null;
                        }
                    }
                }
            }
        }
        C1566re.m8586j("Unsupported Xray link protocol");
        return null;
    }

    public static String m20g(String str) {
        String str2;
        if (str.isEmpty()) {
            return "Not configured";
        }
        URI uriCreate = URI.create(str);
        String upperCase = uriCreate.getScheme() == null ? "Xray" : uriCreate.getScheme().toUpperCase(Locale.ROOT);
        String host = uriCreate.getHost();
        if (host == null || host.isEmpty()) {
            return xp0.m10592v(upperCase, " configured");
        }
        int port = uriCreate.getPort();
        StringBuilder sb = new StringBuilder();
        sb.append(upperCase);
        sb.append("  ");
        if (host.length() <= 2) {
            str2 = "**";
        } else {
            int iLastIndexOf = host.lastIndexOf(46);
            str2 = host.charAt(0) + "***" + (iLastIndexOf > 0 ? host.substring(iLastIndexOf) : "");
        }
        sb.append(str2);
        sb.append(port > 0 ? w43.m10259d(port, ":") : "");
        return sb.toString();
    }
}
