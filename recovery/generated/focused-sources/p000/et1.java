package p000;

import android.os.Bundle;
import com.fongmi.android.p002tv.xray.XrayService;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public final class et1 implements gt1, wy1, p42, fu3 {

    public final long f5230c;

    public final Object f5231h;

    public et1(Object obj, long j) {
        this.f5231h = obj;
        this.f5230c = j;
    }

    @Override
    public Object mo3260a(eu3 eu3Var) {
        zv3 zv3Var = (zv3) this.f5231h;
        return new gf2(zv3Var, ha3.m4008t(zv3Var.f22312b, zv3Var.f22311a, zv3Var.f22313c, eu3Var, this.f5230c));
    }

    @Override
    public void mo969b(r81 r81Var, int i) {
        kt1 kt1Var = (kt1) this.f5231h;
        r81Var.mo7671f0(kt1Var.f10149c, i, this.f5230c);
    }

    public Object m3261c(JSONObject jSONObject) throws JSONException {
        JSONObject jSONObjectOptJSONObject;
        XrayService xrayService = (XrayService) this.f5231h;
        int i = XrayService.f3215n;
        long j = this.f5230c;
        xrayService.m2090c(j);
        s11.m8833I(jSONObject);
        xrayService.m2090c(j);
        JSONObject jSONObject2 = new JSONObject();
        JSONObject jSONObject3 = new JSONObject(jSONObject.toString());
        JSONArray jSONArrayOptJSONArray = jSONObject3.optJSONArray("outbounds");
        if (jSONArrayOptJSONArray == null || jSONArrayOptJSONArray.length() == 0) {
            throw new JSONException("Xray ping config has no outbound");
        }
        int iCharCount = 0;
        int i2 = 0;
        while (true) {
            if (i2 >= jSONArrayOptJSONArray.length()) {
                jSONObjectOptJSONObject = null;
                break;
            }
            jSONObjectOptJSONObject = jSONArrayOptJSONArray.optJSONObject(i2);
            if (jSONObjectOptJSONObject != null && "fongmi-xray-proxy".equals(jSONObjectOptJSONObject.optString("tag"))) {
                break;
            }
            i2++;
        }
        if (jSONObjectOptJSONObject == null) {
            throw new JSONException("Xray ping proxy outbound is missing");
        }
        jSONObjectOptJSONObject.put("targetStrategy", "AsIs");
        JSONArray jSONArrayOptJSONArray2 = s11.m8855y(s11.m8849q("pingBatch", new JSONObject().put("configs", new JSONArray().put(jSONObject2.put("xrayJson", jSONObject3.toString()).put("outboundTag", "fongmi-xray-proxy"))).put("timeout", 10).put("url", "https://www.gstatic.com/generate_204"))).optJSONArray("results");
        if (jSONArrayOptJSONArray2 == null || jSONArrayOptJSONArray2.length() != 1) {
            throw new JSONException("Xray connectivity test returned no result");
        }
        JSONObject jSONObject4 = jSONArrayOptJSONArray2.getJSONObject(0);
        if (jSONObject4.optBoolean("success")) {
            long jOptLong = jSONObject4.optLong("delay", -1L);
            xrayService.m2090c(j);
            return Long.valueOf(jOptLong);
        }
        String strOptString = jSONObject4.optString("error");
        if (strOptString != null) {
            int length = strOptString.length();
            while (iCharCount < length) {
                int iCodePointAt = strOptString.codePointAt(iCharCount);
                if (Character.isWhitespace(iCodePointAt)) {
                    iCharCount += Character.charCount(iCodePointAt);
                }
            }
            strOptString = "Xray connectivity test failed";
        } else {
            strOptString = "Xray connectivity test failed";
        }
        throw new IllegalStateException(strOptString);
    }

    @Override
    public Object mo2408g(mv1 mv1Var, fw1 fw1Var, int i) {
        try {
            return mv1Var.m6404z(fw1Var, ta1.m9247p(tu1.m9483b(fw1Var.f6096c, (Bundle) this.f5231h)), 0, this.f5230c);
        } catch (RuntimeException e) {
            q11.m7961W("MediaSessionStub", "Ignoring malformed Bundle for MediaItem", e);
            return rw1.m8785r(e);
        }
    }

    @Override
    public boolean mo3262h(C0551fh c0551fh) {
        C1183n4 c1183n4 = ((r42) this.f5231h).f15442b;
        c52 c52Var = (c52) c0551fh.f5809d;
        return c52Var == null || c52Var.mo1551b(c1183n4, this.f5230c);
    }
}
