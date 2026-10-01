package com.fongmi.android.p002tv.xray;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.IBinder;
import android.os.Process;
import android.os.RemoteException;
import com.hierynomus.msdtyp.FileTime;
import java.net.InetAddress;
import java.net.URI;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Iterator;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import kotlin.jvm.internal.LongCompanionObject;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.slf4j.Marker;
import p000.C1566re;
import p000.a04;
import p000.ch0;
import p000.e63;
import p000.e81;
import p000.h91;
import p000.i81;
import p000.j81;
import p000.kz3;
import p000.nz3;
import p000.s11;
import p000.u11;
import p000.uz3;
import p000.x82;
import p000.xg1;
import p000.xp0;
import p000.xw2;
import p009j$.net.URLDecoder;

public final class XrayService extends Service {

    public static final int f3215n = 0;

    public j81 f3220k;

    public x82 f3221l;

    public final ExecutorService f3216c = Executors.newSingleThreadExecutor(new ch0(4));

    public final e63 f3217h = new e63(5);

    public final e63 f3218i = new e63(5);

    public volatile long f3219j = Long.MIN_VALUE;

    public final uz3 f3222m = new uz3(this);

    public static boolean m2086d(Exception exc) {
        String message = exc.getMessage();
        if (message == null) {
            return false;
        }
        String lowerCase = message.toLowerCase(Locale.ROOT);
        return lowerCase.contains("address already in use") || lowerCase.contains("bind:") || lowerCase.contains("failed to listen") || lowerCase.contains("cannot assign requested address");
    }

    public static boolean m2087f(h91 h91Var, long j, int i, boolean z, int i2, long j2, String str) {
        if (h91Var == null) {
            return false;
        }
        try {
            h91Var.mo2941m(j, i, z, i2, j2, kz3.m5739b(str));
            return true;
        } catch (RemoteException unused) {
            return false;
        }
    }

    public final boolean m2088a(long j, h91 h91Var) {
        if (this.f3217h.m3022f(j)) {
            return false;
        }
        m2087f(h91Var, j, 3, false, 0, -1L, "Xray startup superseded by newer request");
        return true;
    }

    /* JADX WARN: Code duplicated, block: B:118:0x02bc  */
    /* JADX WARN: Code duplicated, block: B:161:0x03f9  */
    /* JADX WARN: Code duplicated, block: B:173:0x042f  */
    /* JADX WARN: Code duplicated, block: B:226:0x0523  */
    /* JADX WARN: Code duplicated, block: B:228:0x052f  */
    /* JADX WARN: Code duplicated, block: B:261:0x063c  */
    /* JADX WARN: Code duplicated, block: B:263:0x0661  */
    /* JADX WARN: Code duplicated, block: B:268:0x0673  */
    /* JADX WARN: Code duplicated, block: B:271:0x0684  */
    /* JADX WARN: Code duplicated, block: B:278:0x06a5  */
    /* JADX WARN: Code duplicated, block: B:280:0x06ab  */
    /* JADX WARN: Code duplicated, block: B:305:0x0714  */
    /* JADX WARN: Code duplicated, block: B:326:0x090a  */
    /* JADX WARN: Code duplicated, block: B:337:0x061f A[SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:355:0x0532 A[SYNTHETIC] */
    /* JADX WARN: Code duplicated, block: B:94:0x0263  */
    /* JADX WARN: Code duplicated, block: B:96:0x0269  */
    /* JADX WARN: Code duplicated, block: B:97:0x026c  */
    public final JSONObject m2089b(int i, String str, boolean z) throws JSONException {
        Object obj;
        String str2;
        String str3;
        String str4;
        Locale locale;
        String strOptString;
        String lowerCase;
        String lowerCase2;
        boolean zM4999r;
        String str5;
        Iterator it;
        String str6;
        String str7;
        String strDecode;
        String strM10482C;
        int i2;
        String strTrim;
        String str8;
        String strM19f;
        Object objM8849q;
        JSONObject jSONObject;
        String lowerCase3;
        String rawAuthority;
        JSONArray jSONArrayOptJSONArray;
        int iLastIndexOf;
        JSONArray jSONArrayOptJSONArray2;
        JSONObject jSONObjectOptJSONObject;
        x82 x82Var = this.f3221l;
        j81 j81Var = (j81) this.f3220k.f9007c;
        String strM19f2 = a04.m19f(str);
        URI uriCreate = URI.create(strM19f2);
        String scheme = uriCreate.getScheme();
        String lowerCase4 = scheme == null ? "" : scheme.toLowerCase(Locale.ROOT);
        String str9 = "serverName";
        String str10 = "sni";
        String strM4995D = strM19f2;
        String str11 = "";
        String str12 = "&";
        URI uri = uriCreate;
        String str13 = "(?i)[0-9a-f]{64}";
        String str14 = "port";
        String str15 = "sha256";
        String str16 = "\n";
        String str17 = "timeout";
        if (lowerCase4.equals("hy2") || lowerCase4.equals("hysteria2")) {
            String rawQuery = uri.getRawQuery();
            obj = "hysteria2";
            ArrayList arrayList = new ArrayList();
            if (rawQuery == null || rawQuery.isEmpty()) {
                str2 = "&";
                str3 = "port";
            } else {
                String[] strArrSplit = rawQuery.split("&", -1);
                int length = strArrSplit.length;
                int i3 = 0;
                while (i3 < length) {
                    int i4 = i3;
                    String str18 = strArrSplit[i4];
                    String str19 = str12;
                    int i5 = length;
                    int iIndexOf = str18.indexOf(61);
                    String strSubstring = iIndexOf < 0 ? str18 : str18.substring(0, iIndexOf);
                    Charset charset = StandardCharsets.UTF_8;
                    arrayList.add(new i81(str18, URLDecoder.decode(strSubstring, charset), URLDecoder.decode(iIndexOf < 0 ? str11 : str18.substring(iIndexOf + 1), charset)));
                    i3 = i4 + 1;
                    length = i5;
                    str12 = str19;
                    str14 = str14;
                }
                str2 = str12;
                str3 = str14;
            }
            Iterator it2 = arrayList.iterator();
            while (true) {
                if (it2.hasNext()) {
                    i81 i81Var = (i81) it2.next();
                    String str20 = i81Var.f7851h;
                    String str21 = i81Var.f7852i;
                    if (str20.equalsIgnoreCase("insecure") || str20.equalsIgnoreCase("allowInsecure")) {
                        if (str21.equals("1") || str21.equalsIgnoreCase("true")) {
                            if (j81.m4996E(arrayList, "pcs").isEmpty() && j81.m4996E(arrayList, "vcn").isEmpty()) {
                                String host = uri.getHost();
                                if (host != null && host.length() > 1 && host.charAt(0) == '[' && host.charAt(host.length() - 1) == ']') {
                                    host = xp0.m10576f(1, 1, host);
                                }
                                if (host != null) {
                                    int length2 = host.length();
                                    int iCharCount = 0;
                                    while (true) {
                                        if (iCharCount < length2) {
                                            int iCodePointAt = host.codePointAt(iCharCount);
                                            if (!Character.isWhitespace(iCodePointAt)) {
                                                int port = uri.getPort() > 0 ? uri.getPort() : 443;
                                                String strM4996E = j81.m4996E(arrayList, "ports");
                                                if (!strM4996E.isEmpty()) {
                                                    port = a04.m17d(strM4996E);
                                                }
                                                String strM4996E2 = j81.m4996E(arrayList, str10);
                                                if (strM4996E2.isEmpty()) {
                                                    int length3 = host.length();
                                                    int iCharCount2 = 0;
                                                    while (true) {
                                                        if (iCharCount2 < length3) {
                                                            int iCodePointAt2 = host.codePointAt(iCharCount2);
                                                            if (Character.isWhitespace(iCodePointAt2)) {
                                                                iCharCount2 = Character.charCount(iCodePointAt2) + iCharCount2;
                                                            } else {
                                                                if (host.indexOf(58) < 0) {
                                                                    zM4999r = j81.m4999r(host);
                                                                    break;
                                                                }
                                                                if (host.indexOf(37) >= 0 || !host.matches("(?i)^[0-9a-f:.]+$")) {
                                                                    break;
                                                                }
                                                                String strSubstring2 = host.substring(host.lastIndexOf(58) + 1);
                                                                if (strSubstring2.indexOf(46) < 0 || j81.m4999r(strSubstring2)) {
                                                                    try {
                                                                        InetAddress.getByName(host);
                                                                        zM4999r = true;
                                                                        break;
                                                                    } catch (Exception unused) {
                                                                        zM4999r = false;
                                                                        break;
                                                                    }
                                                                }
                                                            }
                                                        }
                                                        zM4999r = false;
                                                        break;
                                                    }
                                                    if (!zM4999r) {
                                                        str4 = host;
                                                    }
                                                    StringBuilder sbM10588r = xp0.m10588r(lowerCase4, str16);
                                                    locale = Locale.ROOT;
                                                    str10 = str10;
                                                    sbM10588r.append(host.toLowerCase(locale));
                                                    sbM10588r.append(str16);
                                                    sbM10588r.append(port);
                                                    sbM10588r.append(str16);
                                                    sbM10588r.append(str4.toLowerCase(locale));
                                                    String string = sbM10588r.toString();
                                                    String strM5013n = j81Var.m5013n(string);
                                                    str16 = str16;
                                                    str3 = str3;
                                                    JSONObject jSONObjectPut = new JSONObject().put("server", host).put(str3, port).put("serverName", str4);
                                                    str17 = str17;
                                                    strOptString = s11.m8855y(s11.m8849q("probeHysteria2Certificate", jSONObjectPut.put(str17, FileTime.NANO100_TO_MILLI))).optString(str15);
                                                    str13 = str13;
                                                    if (strOptString.matches(str13)) {
                                                        throw new JSONException("Hysteria2 certificate probe returned an invalid fingerprint");
                                                    }
                                                    lowerCase = strOptString.toLowerCase(locale);
                                                    if (lowerCase == null) {
                                                        lowerCase2 = str11;
                                                    } else {
                                                        lowerCase2 = lowerCase.toLowerCase(locale);
                                                    }
                                                    if (lowerCase2 != null || !lowerCase2.matches(str13)) {
                                                        xw2.m10661h("Stored Hysteria2 certificate fingerprint is invalid");
                                                        return null;
                                                    }
                                                    if (strM5013n.isEmpty()) {
                                                        j81Var.m5018w(string, lowerCase2);
                                                        strM5013n = lowerCase2;
                                                    } else {
                                                        if (!strM5013n.matches(str13)) {
                                                            xw2.m10661h("Stored Hysteria2 certificate fingerprint is invalid");
                                                            return null;
                                                        }
                                                        Charset charset2 = StandardCharsets.US_ASCII;
                                                        if (!MessageDigest.isEqual(strM5013n.getBytes(charset2), lowerCase2.getBytes(charset2))) {
                                                            xw2.m10661h("Hysteria2 server certificate changed; delete the saved Xray configuration before trusting the new certificate");
                                                            return null;
                                                        }
                                                    }
                                                    strM4995D = j81.m4995D(uri, arrayList, strM5013n);
                                                    str11 = str11;
                                                    str15 = str15;
                                                    str9 = str9;
                                                    break;
                                                }
                                                str4 = strM4996E2;
                                                StringBuilder sbM10588r2 = xp0.m10588r(lowerCase4, str16);
                                                locale = Locale.ROOT;
                                                str10 = str10;
                                                sbM10588r2.append(host.toLowerCase(locale));
                                                sbM10588r2.append(str16);
                                                sbM10588r2.append(port);
                                                sbM10588r2.append(str16);
                                                sbM10588r2.append(str4.toLowerCase(locale));
                                                String string2 = sbM10588r2.toString();
                                                String strM5013n2 = j81Var.m5013n(string2);
                                                str16 = str16;
                                                str3 = str3;
                                                JSONObject jSONObjectPut2 = new JSONObject().put("server", host).put(str3, port).put("serverName", str4);
                                                str17 = str17;
                                                strOptString = s11.m8855y(s11.m8849q("probeHysteria2Certificate", jSONObjectPut2.put(str17, FileTime.NANO100_TO_MILLI))).optString(str15);
                                                str13 = str13;
                                                if (strOptString.matches(str13)) {
                                                    throw new JSONException("Hysteria2 certificate probe returned an invalid fingerprint");
                                                }
                                                lowerCase = strOptString.toLowerCase(locale);
                                                if (lowerCase == null) {
                                                    lowerCase2 = str11;
                                                } else {
                                                    lowerCase2 = lowerCase.toLowerCase(locale);
                                                }
                                                if (lowerCase2 != null) {
                                                }
                                                xw2.m10661h("Stored Hysteria2 certificate fingerprint is invalid");
                                                return null;
                                            }
                                            String str22 = str10;
                                            uri = uri;
                                            length2 = length2;
                                            lowerCase4 = lowerCase4;
                                            str10 = str22;
                                            str16 = str16;
                                            str15 = str15;
                                            j81Var = j81Var;
                                            str13 = str13;
                                            iCharCount = Character.charCount(iCodePointAt) + iCharCount;
                                        }
                                    }
                                }
                                C1566re.m8586j("Hysteria2 server is invalid");
                                return null;
                            }
                            strM4995D = j81.m4995D(uri, arrayList, str11);
                        }
                    }
                } else {
                    str16 = "\n";
                    str10 = "sni";
                    str11 = str11;
                    str13 = str13;
                    str15 = str15;
                    str17 = str17;
                    str9 = str9;
                    str3 = str3;
                }
            }
        } else {
            obj = "hysteria2";
            str2 = "&";
            str16 = "\n";
            str10 = "sni";
            str3 = "port";
            str9 = "serverName";
            str11 = str11;
            str13 = str13;
            str15 = str15;
            str17 = str17;
        }
        j81 j81Var2 = (j81) x82Var.f20639h;
        String strM19f3 = a04.m19f(strM4995D);
        URI uriCreate2 = URI.create(strM19f3);
        String rawQuery2 = uriCreate2.getRawQuery();
        String str23 = str11;
        ArrayList arrayList2 = new ArrayList();
        if (rawQuery2 == null || rawQuery2.isEmpty()) {
            str5 = str15;
        } else {
            String[] strArrSplit2 = rawQuery2.split(str2, -1);
            int length4 = strArrSplit2.length;
            int i6 = 0;
            while (i6 < length4) {
                String[] strArr = strArrSplit2;
                String str24 = strArr[i6];
                int i7 = length4;
                int i8 = i6;
                int iIndexOf2 = str24.indexOf(61);
                String strSubstring3 = iIndexOf2 < 0 ? str24 : str24.substring(0, iIndexOf2);
                Charset charset3 = StandardCharsets.UTF_8;
                arrayList2.add(new xg1(str24, URLDecoder.decode(strSubstring3, charset3), URLDecoder.decode(iIndexOf2 < 0 ? str23 : str24.substring(iIndexOf2 + 1), charset3)));
                i6 = i8 + 1;
                strArrSplit2 = strArr;
                length4 = i7;
                str15 = str15;
            }
            str5 = str15;
        }
        String strM10487y = x82.m10487y(uriCreate2.getScheme());
        String strM10487y2 = x82.m10487y(x82.m10483D(arrayList2, "security"));
        if (!strM10487y.equals("trojan")) {
            if ((strM10487y.equals("vless") || strM10487y.equals("vmess")) && strM10487y2.equals("tls")) {
                it = arrayList2.iterator();
                while (true) {
                    if (it.hasNext()) {
                        xg1 xg1Var = (xg1) it.next();
                        str6 = xg1Var.f20765h;
                        str7 = xg1Var.f20766i;
                        if (!str6.equalsIgnoreCase("insecure")) {
                        }
                        if (!str7.equals("1")) {
                        }
                        if (!x82.m10483D(arrayList2, "pcs").isEmpty()) {
                            strDecode = str23;
                            strM10482C = x82.m10482C(uriCreate2, arrayList2, strDecode);
                        } else {
                            strDecode = str23;
                            strM10482C = x82.m10482C(uriCreate2, arrayList2, strDecode);
                        }
                    }
                }
            }
            strM19f = a04.m19f(strM10482C);
            objM8849q = s11.m8849q("convertShareLinksToXrayJson", new JSONObject().put("text", strM19f));
            if (!(objM8849q instanceof JSONObject)) {
                throw new JSONException("Xray conversion returned an invalid config");
            }
            jSONObject = (JSONObject) objM8849q;
            String strSubstring4 = strM19f.substring(0, strM19f.indexOf(58));
            Locale locale2 = Locale.ROOT;
            lowerCase3 = strSubstring4.toLowerCase(locale2);
            if (lowerCase3.equals("trojan")) {
                rawAuthority = URI.create(a04.m19f(strM19f)).getRawAuthority();
                if (rawAuthority != null) {
                    strDecode = URLDecoder.decode(rawAuthority.substring(0, iLastIndexOf).replace(Marker.ANY_NON_NULL_MARKER, "%2B"), StandardCharsets.UTF_8);
                }
                if (strDecode.contains(Marker.ANY_NON_NULL_MARKER)) {
                    jSONArrayOptJSONArray = jSONObject.optJSONArray("outbounds");
                    if (jSONArrayOptJSONArray != null) {
                    }
                    throw new JSONException("Xray conversion returned an invalid outbound count");
                }
            } else {
                rawAuthority = URI.create(a04.m19f(strM19f)).getRawAuthority();
                if (rawAuthority != null) {
                    strDecode = URLDecoder.decode(rawAuthority.substring(0, iLastIndexOf).replace(Marker.ANY_NON_NULL_MARKER, "%2B"), StandardCharsets.UTF_8);
                }
                if (strDecode.contains(Marker.ANY_NON_NULL_MARKER)) {
                    jSONArrayOptJSONArray = jSONObject.optJSONArray("outbounds");
                    if (jSONArrayOptJSONArray != null) {
                    }
                    throw new JSONException("Xray conversion returned an invalid outbound count");
                }
            }
            JSONObject jSONObject2 = new JSONObject(jSONObject.toString());
            jSONArrayOptJSONArray2 = jSONObject2.optJSONArray("outbounds");
            if (jSONArrayOptJSONArray2 != null) {
            }
            throw new JSONException("Exactly one Xray outbound is required");
        }
        if (strM10487y2.isEmpty() || strM10487y2.equals("tls")) {
            it = arrayList2.iterator();
            while (true) {
                if (it.hasNext()) {
                    xg1 xg1Var2 = (xg1) it.next();
                    str6 = xg1Var2.f20765h;
                    str7 = xg1Var2.f20766i;
                    if (!str6.equalsIgnoreCase("insecure") || str6.equalsIgnoreCase("allowInsecure")) {
                        if (!str7.equals("1") || str7.equalsIgnoreCase("true")) {
                            if (!x82.m10483D(arrayList2, "pcs").isEmpty() && x82.m10483D(arrayList2, "vcn").isEmpty()) {
                                String host2 = uriCreate2.getHost();
                                if (host2 != null && host2.length() > 1 && host2.charAt(0) == '[' && host2.charAt(host2.length() - 1) == ']') {
                                    host2 = xp0.m10576f(1, 1, host2);
                                }
                                if (host2 != null) {
                                    int length5 = host2.length();
                                    int iCharCount3 = 0;
                                    while (true) {
                                        if (iCharCount3 < length5) {
                                            int iCodePointAt3 = host2.codePointAt(iCharCount3);
                                            if (!Character.isWhitespace(iCodePointAt3)) {
                                                int port2 = uriCreate2.getPort() > 0 ? uriCreate2.getPort() : 443;
                                                String strM10483D = x82.m10483D(arrayList2, str10);
                                                if (strM10483D.isEmpty()) {
                                                    Iterator it3 = arrayList2.iterator();
                                                    while (true) {
                                                        if (!it3.hasNext()) {
                                                            str8 = str23;
                                                            break;
                                                        }
                                                        xg1 xg1Var3 = (xg1) it3.next();
                                                        if (xg1Var3.f20765h.equals("type")) {
                                                            str8 = xg1Var3.f20766i;
                                                            break;
                                                        }
                                                    }
                                                    if (!str8.equals("ws") && !str8.equals("websocket")) {
                                                        strM10483D = str23;
                                                        break;
                                                    }
                                                    Iterator it4 = arrayList2.iterator();
                                                    while (true) {
                                                        if (!it4.hasNext()) {
                                                            strM10483D = str23;
                                                            break;
                                                        }
                                                        xg1 xg1Var4 = (xg1) it4.next();
                                                        if (xg1Var4.f20765h.equals("host")) {
                                                            strM10483D = xg1Var4.f20766i;
                                                            break;
                                                        }
                                                    }
                                                }
                                                String strM10483D2 = x82.m10483D(arrayList2, "fp");
                                                String strM10483D3 = x82.m10483D(arrayList2, "alpn");
                                                ArrayList arrayList3 = new ArrayList();
                                                String strTrim2 = strM10483D3.trim();
                                                if (!strTrim2.isEmpty()) {
                                                    if (strTrim2.startsWith("[")) {
                                                        try {
                                                            JSONArray jSONArray = new JSONArray(strTrim2);
                                                            for (int i9 = 0; i9 < jSONArray.length(); i9++) {
                                                                String strTrim3 = jSONArray.optString(i9).trim();
                                                                if (!strTrim3.isEmpty()) {
                                                                    arrayList3.add(strTrim3);
                                                                }
                                                            }
                                                        } catch (Exception unused2) {
                                                            for (String str25 : strTrim2.split(",", -1)) {
                                                                strTrim = str25.trim();
                                                                if (!strTrim.isEmpty()) {
                                                                    arrayList3.add(strTrim);
                                                                }
                                                            }
                                                        }
                                                    } else {
                                                        while (i2 < r12) {
                                                            strTrim = str25.trim();
                                                            if (!strTrim.isEmpty()) {
                                                                arrayList3.add(strTrim);
                                                            }
                                                        }
                                                    }
                                                }
                                                StringBuilder sb = new StringBuilder("tcp-tls\n");
                                                sb.append(x82.m10487y(uriCreate2.getScheme()));
                                                String str26 = str16;
                                                sb.append(str26);
                                                sb.append(x82.m10487y(host2));
                                                sb.append(str26);
                                                sb.append(port2);
                                                sb.append(str26);
                                                sb.append(x82.m10487y(strM10483D));
                                                String string3 = sb.toString();
                                                String strM5013n3 = j81Var2.m5013n(string3);
                                                String strOptString2 = s11.m8855y(s11.m8849q("probeTLSCertificate", new JSONObject().put("server", host2).put(str3, port2).put(str9, strM10483D).put("fingerprint", strM10483D2).put("alpn", new JSONArray((Collection) arrayList3)).put(str17, FileTime.NANO100_TO_MILLI))).optString(str5);
                                                String str27 = str13;
                                                if (!strOptString2.matches(str27)) {
                                                    throw new JSONException("TLS certificate probe returned an invalid fingerprint");
                                                }
                                                String strM10487y3 = x82.m10487y(strOptString2.toLowerCase(Locale.ROOT));
                                                if (strM10487y3 != null && strM10487y3.matches(str27)) {
                                                    if (strM5013n3.isEmpty()) {
                                                        j81Var2.m5018w(string3, strM10487y3);
                                                        strM5013n3 = strM10487y3;
                                                    } else {
                                                        if (!strM5013n3.matches(str27)) {
                                                            xw2.m10661h("Stored TLS certificate fingerprint is invalid");
                                                            return null;
                                                        }
                                                        Charset charset4 = StandardCharsets.US_ASCII;
                                                        if (!MessageDigest.isEqual(strM5013n3.getBytes(charset4), strM10487y3.getBytes(charset4))) {
                                                            xw2.m10661h("TLS server certificate changed; delete the saved Xray configuration before trusting the new certificate");
                                                            return null;
                                                        }
                                                    }
                                                    strM10482C = x82.m10482C(uriCreate2, arrayList2, strM5013n3);
                                                    strDecode = str23;
                                                    break;
                                                }
                                                xw2.m10661h("Stored TLS certificate fingerprint is invalid");
                                                return null;
                                            }
                                            iCharCount3 += Character.charCount(iCodePointAt3);
                                        }
                                    }
                                }
                                C1566re.m8586j("TLS server is invalid");
                                return null;
                            }
                            strDecode = str23;
                            strM10482C = x82.m10482C(uriCreate2, arrayList2, strDecode);
                        }
                    }
                }
            }
        }
        strM19f = a04.m19f(strM10482C);
        objM8849q = s11.m8849q("convertShareLinksToXrayJson", new JSONObject().put("text", strM19f));
        if (!(objM8849q instanceof JSONObject)) {
            throw new JSONException("Xray conversion returned an invalid config");
        }
        jSONObject = (JSONObject) objM8849q;
        String strSubstring5 = strM19f.substring(0, strM19f.indexOf(58));
        Locale locale3 = Locale.ROOT;
        lowerCase3 = strSubstring5.toLowerCase(locale3);
        if (lowerCase3.equals("trojan") || lowerCase3.equals("hy2") || lowerCase3.equals(obj)) {
            rawAuthority = URI.create(a04.m19f(strM19f)).getRawAuthority();
            if (rawAuthority != null && (iLastIndexOf = rawAuthority.lastIndexOf(64)) >= 0) {
                strDecode = URLDecoder.decode(rawAuthority.substring(0, iLastIndexOf).replace(Marker.ANY_NON_NULL_MARKER, "%2B"), StandardCharsets.UTF_8);
            }
            if (strDecode.contains(Marker.ANY_NON_NULL_MARKER)) {
                jSONArrayOptJSONArray = jSONObject.optJSONArray("outbounds");
                if (jSONArrayOptJSONArray != null || jSONArrayOptJSONArray.length() != 1) {
                    throw new JSONException("Xray conversion returned an invalid outbound count");
                }
                JSONObject jSONObjectOptJSONObject2 = jSONArrayOptJSONArray.optJSONObject(0);
                if (jSONObjectOptJSONObject2 == null) {
                    throw new JSONException("Xray conversion returned an invalid outbound");
                }
                String lowerCase5 = jSONObjectOptJSONObject2.optString("protocol").toLowerCase(locale3);
                if (lowerCase3.equals("trojan")) {
                    if (!lowerCase5.equals("trojan")) {
                        throw new JSONException("Trojan conversion returned the wrong protocol");
                    }
                    JSONObject jSONObjectOptJSONObject3 = jSONObjectOptJSONObject2.optJSONObject("settings");
                    if (jSONObjectOptJSONObject3 == null) {
                        throw new JSONException("Trojan conversion returned invalid settings");
                    }
                    jSONObjectOptJSONObject3.put("password", strDecode);
                } else {
                    if (!lowerCase5.equals("hysteria")) {
                        throw new JSONException("Hysteria2 conversion returned the wrong protocol");
                    }
                    JSONObject jSONObjectOptJSONObject4 = jSONObjectOptJSONObject2.optJSONObject("streamSettings");
                    JSONObject jSONObjectOptJSONObject5 = jSONObjectOptJSONObject4 == null ? null : jSONObjectOptJSONObject4.optJSONObject("hysteriaSettings");
                    if (jSONObjectOptJSONObject5 == null) {
                        throw new JSONException("Hysteria2 conversion returned invalid settings");
                    }
                    jSONObjectOptJSONObject5.put("auth", strDecode);
                }
            }
        }
        JSONObject jSONObject3 = new JSONObject(jSONObject.toString());
        jSONArrayOptJSONArray2 = jSONObject3.optJSONArray("outbounds");
        if (jSONArrayOptJSONArray2 != null || jSONArrayOptJSONArray2.length() != 1) {
            throw new JSONException("Exactly one Xray outbound is required");
        }
        JSONObject jSONObject4 = jSONArrayOptJSONArray2.getJSONObject(0);
        jSONObject4.remove("sendThrough");
        jSONObject4.put("tag", "fongmi-xray-proxy");
        jSONObject4.put("targetStrategy", "ForceIP");
        JSONObject jSONObjectOptJSONObject6 = jSONObject4.optJSONObject("streamSettings");
        if (jSONObjectOptJSONObject6 != null && (jSONObjectOptJSONObject = jSONObjectOptJSONObject6.optJSONObject("sockopt")) != null) {
            jSONObjectOptJSONObject.put("domainStrategy", "AsIs");
        }
        jSONArrayOptJSONArray2.put(new JSONObject().put("tag", "fongmi-xray-private-block").put("protocol", "blackhole").put("settings", new JSONObject()));
        jSONObject3.put("inbounds", new JSONArray().put(new JSONObject().put("tag", "fongmi-xray-session").put("listen", "127.0.0.1").put(str3, i).put("protocol", "socks").put("settings", new JSONObject().put("auth", "noauth").put("udp", z).put("ip", "127.0.0.1"))));
        jSONObject3.put("dns", new JSONObject().put("tag", "fongmi-xray-dns").put("queryStrategy", "UseIP").put("enableParallelQuery", true).put("servers", new JSONArray().put(u11.m9644y("https://1.1.1.1/dns-query")).put(u11.m9644y("https://8.8.8.8/dns-query")).put(u11.m9644y("tcp://1.1.1.1:53")).put(u11.m9644y("tcp://8.8.8.8:53"))));
        JSONArray jSONArrayM9645y0 = u11.m9645y0();
        jSONObject3.put("routing", new JSONObject().put("domainStrategy", "IPOnDemand").put("rules", new JSONArray().put(new JSONObject().put("type", "field").put("inboundTag", new JSONArray().put("fongmi-xray-dns")).put("outboundTag", "fongmi-xray-proxy")).put(new JSONObject().put("type", "field").put("inboundTag", new JSONArray().put("fongmi-xray-session")).put("domain", new JSONArray().put("localhost").put("domain:localhost").put("regexp:.*\\.localhost$").put("regexp:.*\\.local$")).put("outboundTag", "fongmi-xray-private-block")).put(new JSONObject().put("type", "field").put("inboundTag", new JSONArray().put("fongmi-xray-session")).put("ip", jSONArrayM9645y0).put("outboundTag", "fongmi-xray-private-block")).put(new JSONObject().put("type", "field").put("inboundTag", new JSONArray().put("fongmi-xray-session")).put("network", "tcp,udp").put("outboundTag", "fongmi-xray-proxy"))));
        jSONObject3.put("log", new JSONObject().put("loglevel", "warning"));
        return jSONObject3;
        strDecode = str23;
        strM10482C = strM19f3;
        strM19f = a04.m19f(strM10482C);
        objM8849q = s11.m8849q("convertShareLinksToXrayJson", new JSONObject().put("text", strM19f));
        if (!(objM8849q instanceof JSONObject)) {
            throw new JSONException("Xray conversion returned an invalid config");
        }
        jSONObject = (JSONObject) objM8849q;
        String strSubstring6 = strM19f.substring(0, strM19f.indexOf(58));
        Locale locale4 = Locale.ROOT;
        lowerCase3 = strSubstring6.toLowerCase(locale4);
        if (lowerCase3.equals("trojan")) {
            rawAuthority = URI.create(a04.m19f(strM19f)).getRawAuthority();
            if (rawAuthority != null) {
                strDecode = URLDecoder.decode(rawAuthority.substring(0, iLastIndexOf).replace(Marker.ANY_NON_NULL_MARKER, "%2B"), StandardCharsets.UTF_8);
            }
            if (strDecode.contains(Marker.ANY_NON_NULL_MARKER)) {
                jSONArrayOptJSONArray = jSONObject.optJSONArray("outbounds");
                if (jSONArrayOptJSONArray != null) {
                }
                throw new JSONException("Xray conversion returned an invalid outbound count");
            }
        } else {
            rawAuthority = URI.create(a04.m19f(strM19f)).getRawAuthority();
            if (rawAuthority != null) {
                strDecode = URLDecoder.decode(rawAuthority.substring(0, iLastIndexOf).replace(Marker.ANY_NON_NULL_MARKER, "%2B"), StandardCharsets.UTF_8);
            }
            if (strDecode.contains(Marker.ANY_NON_NULL_MARKER)) {
                jSONArrayOptJSONArray = jSONObject.optJSONArray("outbounds");
                if (jSONArrayOptJSONArray != null) {
                }
                throw new JSONException("Xray conversion returned an invalid outbound count");
            }
        }
        JSONObject jSONObject5 = new JSONObject(jSONObject.toString());
        jSONArrayOptJSONArray2 = jSONObject5.optJSONArray("outbounds");
        if (jSONArrayOptJSONArray2 != null) {
        }
        throw new JSONException("Exactly one Xray outbound is required");
    }

    public final void m2090c(long j) {
        if (this.f3218i.m3022f(j)) {
            return;
        }
        xw2.m10661h("Xray operation superseded by newer request");
    }

    public final void m2091e(int i, long j) {
        boolean zCompareAndSet;
        e63 e63Var = this.f3217h;
        e63 e63Var2 = this.f3218i;
        if (i == 3 || i == 4) {
            zCompareAndSet = ((AtomicLong) e63Var.f4726c).compareAndSet(j, LongCompanionObject.MAX_VALUE);
        } else if (i != 1 && i != 2 && i != 5) {
            return;
        } else {
            zCompareAndSet = ((AtomicLong) e63Var2.f4726c).compareAndSet(j, LongCompanionObject.MAX_VALUE);
        }
        if (zCompareAndSet) {
            ((AtomicLong) e63Var.f4726c).set(LongCompanionObject.MAX_VALUE);
            ((AtomicLong) e63Var2.f4726c).set(LongCompanionObject.MAX_VALUE);
            Process.killProcess(Process.myPid());
        }
    }

    public final void m2092g() {
        Exception e = null;
        for (int i = 0; i < 2; i++) {
            try {
                try {
                    s11.m8849q("stopXray", null);
                    this.f3219j = Long.MIN_VALUE;
                    return;
                } catch (Exception e2) {
                    e = e2;
                }
            } catch (Throwable th) {
                this.f3219j = Long.MIN_VALUE;
                throw th;
            }
        }
        if (e != null) {
            throw e;
        }
        this.f3219j = Long.MIN_VALUE;
    }

    @Override
    public final IBinder onBind(Intent intent) {
        if (this.f3220k == null) {
            this.f3220k = new j81(new j81((Context) this), new e81(3));
        }
        if (this.f3221l == null) {
            this.f3221l = new x82(new j81((Context) this), new e81(13));
        }
        return this.f3222m;
    }

    /* JADX WARN: Multi-variable type inference failed */
    /* JADX WARN: Type inference failed for: r4v0, types: [android.app.Service, com.fongmi.android.tv.xray.XrayService, java.lang.Object] */
    /* JADX WARN: Type inference failed for: r4v1, types: [android.app.Service] */
    /* JADX WARN: Type inference failed for: r4v3, types: [int] */
    @Override
    public final void onDestroy() {
        ((AtomicLong) this.f3217h.f4726c).set(LongCompanionObject.MAX_VALUE);
        ((AtomicLong) this.f3218i.f4726c).set(LongCompanionObject.MAX_VALUE);
        nz3 nz3Var = new nz3(this, 1);
        ExecutorService executorService = this.f3216c;
        executorService.execute(nz3Var);
        executorService.shutdown();
        try {
            try {
                if (!executorService.awaitTermination(3L, TimeUnit.SECONDS)) {
                    executorService.shutdownNow();
                }
            } catch (InterruptedException unused) {
                Thread.currentThread().interrupt();
                executorService.shutdownNow();
            }
        } finally {
            super.onDestroy();
            Process.killProcess(Process.myPid());
        }
    }
}
