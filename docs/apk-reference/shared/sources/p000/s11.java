package p000;

import android.R;
import android.content.Context;
import android.content.res.TypedArray;
import android.os.Bundle;
import android.os.Parcel;
import android.os.Parcelable;
import android.text.InputFilter;
import android.text.TextUtils;
import android.text.method.TransformationMethod;
import android.util.AttributeSet;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.appcompat.widget.LinearLayoutCompat;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.chip.Chip;
import com.google.android.material.chip.ChipGroup;
import com.google.android.material.materialswitch.MaterialSwitch;
import java.io.IOException;
import java.io.StringReader;
import java.nio.BufferUnderflowException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.MappedByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import kotlin.Result;
import kotlin.ResultKt;
import kotlin.UShort;
import kotlin.Unit;
import kotlin.collections.ArrayDeque;
import kotlin.coroutines.Continuation;
import kotlin.coroutines.CoroutineContext;
import kotlin.jvm.internal.Intrinsics;
import libXray.LibXray;
import okhttp3.internal.http2.Http2Connection;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.mozilla.javascript.Token;
import sun.misc.Unsafe;

public abstract class s11 {

    public static final byte[] f16258h = {-75, 0, 60, 0, 1, 4};

    public static final y83 f16259i = new y83("UNDEFINED", 1);

    public static final y83 f16260j = new y83("REUSABLE_CLAIMED", 1);

    public static final int[] f16261k = {R.attr.theme, com.fongmi.android.p002tv.R.attr.theme};

    public static final int[] f16262l = {com.fongmi.android.p002tv.R.attr.materialThemeOverlay};

    public static final int[] f16263m = {1, 5, 9, 13, 17, 25, 33, 41, 49, 65, 81, 97, Token.ASSIGN_EXP, Token.TARGET, Token.METHOD, 209, 241, 305, 369, 497, 753, 1265, 2289, 4337, 8433, 16625};

    public static final int[] f16264n = {2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 7, 8, 9, 10, 11, 12, 13, 24};

    public static final int[] f16265o = {0, 1, 2, 3, 4, 5, 6, 8, 10, 14, 18, 26, 34, 50, 66, 98, 130, 194, 322, 578, 1090, 2114, 6210, 22594};

    public static final int[] f16266p = {0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9, 10, 12, 14, 24};

    public static final int[] f16267q = {2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 18, 22, 30, 38, 54, 70, 102, Token.CONTINUE, 198, 326, 582, 1094, 2118};

    public static final int[] f16268r = {0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9, 10, 24};

    public static final int[] f16269s = {0, 0, 8, 8, 0, 16, 8, 16, 16};

    public static final int[] f16270t = {0, 8, 0, 8, 16, 0, 16, 8, 16};

    public static final byte[] f16271u = new byte[1024];

    public static final int[] f16272v = new int[1024];

    public final int f16273c;

    public s11(int i) {
        this.f16273c = i;
    }

    /* JADX WARN: Multi-variable type inference failed */
    /* JADX WARN: Type inference failed for: r8v1, types: [byte[], java.io.Serializable] */
    public static C1141m6 m8827A(byte[] bArr) {
        UUID[] uuidArr;
        kc2 kc2Var = new kc2(bArr);
        if (kc2Var.f9797c < 32) {
            return null;
        }
        kc2Var.m5332N(0);
        int iM5334a = kc2Var.m5334a();
        int iM5343m = kc2Var.m5343m();
        if (iM5343m != iM5334a) {
            q11.m7960V("PsshAtomUtil", "Advertised atom size (" + iM5343m + ") does not match buffer size: " + iM5334a);
            return null;
        }
        int iM5343m2 = kc2Var.m5343m();
        if (iM5343m2 != 1886614376) {
            AbstractC1163ml.m6241t(iM5343m2, "Atom type is not pssh: ", "PsshAtomUtil");
            return null;
        }
        int iM8219e = AbstractC1537qm.m8219e(kc2Var.m5343m());
        if (iM8219e > 1) {
            AbstractC1163ml.m6241t(iM8219e, "Unsupported pssh version: ", "PsshAtomUtil");
            return null;
        }
        UUID uuid = new UUID(kc2Var.m5351u(), kc2Var.m5351u());
        if (iM8219e == 1) {
            int iM5323E = kc2Var.m5323E();
            UUID[] uuidArr2 = new UUID[iM5323E];
            for (int i = 0; i < iM5323E; i++) {
                uuidArr2[i] = new UUID(kc2Var.m5351u(), kc2Var.m5351u());
            }
            uuidArr = uuidArr2;
        } else {
            uuidArr = null;
        }
        int iM5323E2 = kc2Var.m5323E();
        int iM5334a2 = kc2Var.m5334a();
        if (iM5323E2 == iM5334a2) {
            ?? r8 = new byte[iM5323E2];
            kc2Var.m5341k(0, iM5323E2, r8);
            return new C1141m6(uuid, iM8219e, r8, uuidArr, 5);
        }
        q11.m7960V("PsshAtomUtil", "Atom data size (" + iM5323E2 + ") does not match the bytes left: " + iM5334a2);
        return null;
    }

    public static byte[] m8828B(UUID uuid, byte[] bArr) {
        C1141m6 c1141m6M8827A = m8827A(bArr);
        if (c1141m6M8827A == null) {
            return null;
        }
        UUID uuid2 = (UUID) c1141m6M8827A.f11197i;
        if (uuid.equals(uuid2)) {
            return (byte[]) c1141m6M8827A.f11198j;
        }
        q11.m7960V("PsshAtomUtil", "UUID mismatch. Expected: " + uuid + ", got: " + uuid2 + ".");
        return null;
    }

    public static q12 m8829C(MappedByteBuffer mappedByteBuffer) throws IOException {
        long j;
        ByteBuffer byteBufferDuplicate = mappedByteBuffer.duplicate();
        byteBufferDuplicate.order(ByteOrder.BIG_ENDIAN);
        byteBufferDuplicate.position(byteBufferDuplicate.position() + 4);
        int i = byteBufferDuplicate.getShort() & UShort.MAX_VALUE;
        if (i > 100) {
            kg0.m5396l("Cannot read metadata.");
            return null;
        }
        byteBufferDuplicate.position(byteBufferDuplicate.position() + 6);
        int i2 = 0;
        while (true) {
            if (i2 >= i) {
                j = -1;
                break;
            }
            int i3 = byteBufferDuplicate.getInt();
            byteBufferDuplicate.position(byteBufferDuplicate.position() + 4);
            j = ((long) byteBufferDuplicate.getInt()) & 4294967295L;
            byteBufferDuplicate.position(byteBufferDuplicate.position() + 4);
            if (1835365473 == i3) {
                break;
            }
            i2++;
        }
        if (j != -1) {
            byteBufferDuplicate.position(byteBufferDuplicate.position() + ((int) (j - ((long) byteBufferDuplicate.position()))));
            byteBufferDuplicate.position(byteBufferDuplicate.position() + 12);
            long j2 = ((long) byteBufferDuplicate.getInt()) & 4294967295L;
            for (int i4 = 0; i4 < j2; i4++) {
                int i5 = byteBufferDuplicate.getInt();
                long j3 = ((long) byteBufferDuplicate.getInt()) & 4294967295L;
                byteBufferDuplicate.getInt();
                if (1164798569 == i5 || 1701669481 == i5) {
                    byteBufferDuplicate.position((int) (j3 + j));
                    q12 q12Var = new q12();
                    byteBufferDuplicate.order(ByteOrder.LITTLE_ENDIAN);
                    int iPosition = byteBufferDuplicate.position() + byteBufferDuplicate.getInt(byteBufferDuplicate.position());
                    q12Var.f19076d = byteBufferDuplicate;
                    q12Var.f19073a = iPosition;
                    int i6 = iPosition - byteBufferDuplicate.getInt(iPosition);
                    q12Var.f19074b = i6;
                    q12Var.f19075c = ((ByteBuffer) q12Var.f19076d).getShort(i6);
                    return q12Var;
                }
            }
        }
        kg0.m5396l("Cannot read metadata.");
        return null;
    }

    public static Object m8830D(Parcel parcel, Parcelable.Creator creator) {
        if (parcel.readInt() != 0) {
            return creator.createFromParcel(parcel);
        }
        return null;
    }

    public static final void m8831E(Object obj, Continuation continuation) {
        if (!(continuation instanceof hh0)) {
            continuation.resumeWith(obj);
            return;
        }
        hh0 hh0Var = (hh0) continuation;
        v10 v10Var = hh0Var.f7148j;
        Continuation continuation2 = hh0Var.f7149k;
        Throwable thM11135exceptionOrNullimpl = Result.m11135exceptionOrNullimpl(obj);
        Object c0457cx = thM11135exceptionOrNullimpl == null ? obj : new C0457cx(thM11135exceptionOrNullimpl, false);
        if (v10Var.mo6044o(continuation2.get$context())) {
            hh0Var.f7150l = c0457cx;
            hh0Var.f9179i = 1;
            v10Var.mo4186k(continuation2.get$context(), hh0Var);
            return;
        }
        jp0 jp0VarM9767a = ue3.m9767a();
        if (jp0VarM9767a.f9353h >= 4294967296L) {
            hh0Var.f7150l = c0457cx;
            hh0Var.f9179i = 1;
            ArrayDeque arrayDeque = jp0VarM9767a.f9355j;
            if (arrayDeque == null) {
                arrayDeque = new ArrayDeque();
                jp0VarM9767a.f9355j = arrayDeque;
            }
            arrayDeque.addLast(hh0Var);
            return;
        }
        jp0VarM9767a.m5138v(true);
        try {
            ie1 ie1Var = (ie1) continuation2.get$context().get(he1.f7095c);
            if (ie1Var == null || ie1Var.mo4303a()) {
                Object obj2 = hh0Var.f7151m;
                CoroutineContext context = continuation2.get$context();
                Object objM8970b = se3.m8970b(context, obj2);
                io3 io3VarM9143b = objM8970b != se3.f16586a ? t10.m9143b(continuation2, context, objM8970b) : null;
                try {
                    continuation2.resumeWith(obj);
                    Unit unit = Unit.INSTANCE;
                    if (io3VarM9143b == null || io3VarM9143b.m4347M()) {
                        se3.m8969a(context, objM8970b);
                    }
                } catch (Throwable th) {
                    if (io3VarM9143b == null || io3VarM9143b.m4347M()) {
                        se3.m8969a(context, objM8970b);
                    }
                    throw th;
                }
            } else {
                hh0Var.resumeWith(Result.m11132constructorimpl(ResultKt.createFailure(((qe1) ie1Var).m8167o())));
            }
            while (jp0VarM9767a.m5140x()) {
            }
        } catch (Throwable th2) {
            try {
                hh0Var.m5085i(th2);
            } finally {
                jp0VarM9767a.m5137u(true);
            }
        }
    }

    public static void m8832H(ByteBuffer byteBuffer, boolean z) {
        for (x92 x92Var : p11.m7589Y(byteBuffer.asReadOnlyBuffer())) {
            int i = x92Var.f20647a;
            ByteBuffer byteBuffer2 = x92Var.f20648b;
            if (i == 5) {
                try {
                    q80.m8097i(i == 5);
                    ByteBuffer byteBufferAsReadOnlyBuffer = byteBuffer2.asReadOnlyBuffer();
                    if (p11.m7571G(byteBufferAsReadOnlyBuffer) == 4) {
                        if (z && byteBufferAsReadOnlyBuffer.remaining() >= 6) {
                            int iPosition = byteBufferAsReadOnlyBuffer.position();
                            for (int i2 = 0; i2 < 6; i2++) {
                                if (byteBufferAsReadOnlyBuffer.get(iPosition + i2) == f16258h[i2]) {
                                }
                            }
                        }
                        byteBuffer.put(byteBuffer2.position(), (byte) 31);
                        break;
                    }
                } catch (BufferUnderflowException unused) {
                }
            }
        }
    }

    public static void m8833I(JSONObject jSONObject) throws JSONException {
        m8849q("testXray", new JSONObject().put("xrayJson", jSONObject.toString()));
    }

    public static Context m8834J(int i, int i2, Context context, AttributeSet attributeSet, int[] iArr) {
        TypedArray typedArrayObtainStyledAttributes = context.obtainStyledAttributes(attributeSet, f16262l, i, i2);
        int[] iArr2 = {typedArrayObtainStyledAttributes.getResourceId(0, 0)};
        typedArrayObtainStyledAttributes.recycle();
        int i3 = iArr2[0];
        boolean z = (context instanceof j10) && ((j10) context).f8863a == i3;
        if (i3 == 0 || z) {
            return context;
        }
        j10 j10Var = new j10(context, i3);
        int length = iArr.length;
        int[] iArr3 = new int[length];
        if (iArr.length > 0) {
            TypedArray typedArrayObtainStyledAttributes2 = context.obtainStyledAttributes(attributeSet, iArr, i, i2);
            for (int i4 = 0; i4 < iArr.length; i4++) {
                iArr3[i4] = typedArrayObtainStyledAttributes2.getResourceId(i4, 0);
            }
            typedArrayObtainStyledAttributes2.recycle();
        }
        for (int i5 = 0; i5 < length; i5++) {
            int i6 = iArr3[i5];
            if (i6 != 0) {
                j10Var.getTheme().applyStyle(i6, true);
            }
        }
        TypedArray typedArrayObtainStyledAttributes3 = context.obtainStyledAttributes(attributeSet, f16261k);
        int resourceId = typedArrayObtainStyledAttributes3.getResourceId(0, 0);
        int resourceId2 = typedArrayObtainStyledAttributes3.getResourceId(1, 0);
        typedArrayObtainStyledAttributes3.recycle();
        if (resourceId == 0) {
            resourceId = resourceId2;
        }
        if (resourceId != 0) {
            j10Var.getTheme().applyStyle(resourceId, true);
        }
        return j10Var;
    }

    public static Context m8835K(Context context, AttributeSet attributeSet, int i, int i2) {
        return m8834J(i, i2, context, attributeSet, new int[0]);
    }

    public static void m8836M(Parcel parcel, List list) {
        if (list == null) {
            parcel.writeInt(-1);
            return;
        }
        int size = list.size();
        parcel.writeInt(size);
        for (int i = 0; i < size; i++) {
            m8837N(parcel, (Parcelable) list.get(i));
        }
    }

    public static void m8837N(Parcel parcel, Parcelable parcelable) {
        if (parcelable == null) {
            parcel.writeInt(0);
        } else {
            parcel.writeInt(1);
            parcelable.writeToParcel(parcel, 0);
        }
    }

    public static final void m8838a(C0472db c0472db, int i) {
        c0472db.f4089c = new int[i];
        c0472db.f4090h = new Object[i];
    }

    public static ta1 m8839b(d81 d81Var) {
        ArrayList arrayList = new ArrayList(2);
        C1643th c1643th = (C1643th) d81Var.f4036h;
        C1643th c1643th2 = (C1643th) d81Var.f4037i;
        if (c1643th != null) {
            Iterator it = ((ArrayList) c1643th.f17517j).iterator();
            long j = 0;
            while (it.hasNext()) {
                j += ((ov2) it.next()).f13538d;
            }
            arrayList.add(new cu1(0, j, "Stereo", c1643th2 == null));
        }
        if (c1643th2 != null) {
            Iterator it2 = ((ArrayList) c1643th2.f17517j).iterator();
            long j2 = 0;
            while (it2.hasNext()) {
                j2 += ((ov2) it2.next()).f13538d;
            }
            arrayList.add(new cu1(1, j2, "Multi-channel", true));
        }
        return ta1.m9244l(arrayList);
    }

    public static byte[] m8840c(UUID uuid, UUID[] uuidArr, byte[] bArr) {
        int length = (bArr != null ? bArr.length : 0) + 32;
        if (uuidArr != null) {
            length += (uuidArr.length * 16) + 4;
        }
        ByteBuffer byteBufferAllocate = ByteBuffer.allocate(length);
        byteBufferAllocate.putInt(length);
        byteBufferAllocate.putInt(1886614376);
        byteBufferAllocate.putInt(uuidArr != null ? Http2Connection.OKHTTP_CLIENT_WINDOW_SIZE : 0);
        byteBufferAllocate.putLong(uuid.getMostSignificantBits());
        byteBufferAllocate.putLong(uuid.getLeastSignificantBits());
        if (uuidArr != null) {
            byteBufferAllocate.putInt(uuidArr.length);
            for (UUID uuid2 : uuidArr) {
                byteBufferAllocate.putLong(uuid2.getMostSignificantBits());
                byteBufferAllocate.putLong(uuid2.getLeastSignificantBits());
            }
        }
        if (bArr == null || bArr.length == 0) {
            byteBufferAllocate.putInt(0);
        } else {
            byteBufferAllocate.putInt(bArr.length);
            byteBufferAllocate.put(bArr);
        }
        return byteBufferAllocate.array();
    }

    public static long[] m8841d(long[]... jArr) {
        long length = 0;
        for (long[] jArr2 : jArr) {
            length += (long) jArr2.length;
        }
        int i = (int) length;
        q80.m8093g("the total number of elements (%s) in the arrays must fit in an int", length, length == ((long) i));
        long[] jArr3 = new long[i];
        int length2 = 0;
        for (long[] jArr4 : jArr) {
            System.arraycopy(jArr4, 0, jArr3, length2, jArr4.length);
            length2 += jArr4.length;
        }
        return jArr3;
    }

    public static int m8842i(String str, byte[] bArr, int i, int i2) {
        byte[] bytes = str.getBytes(StandardCharsets.UTF_8);
        if (bytes.length - i > i2) {
            throw new ArrayIndexOutOfBoundsException("Not enough space in output buffer to encode UTF-8 string");
        }
        System.arraycopy(bytes, 0, bArr, i, bytes.length);
        return i + bytes.length;
    }

    public static ah0 m8843j(tu1 tu1Var) {
        String str;
        String str2;
        Bundle bundle = tu1Var.f17867f.f14365c;
        LinkedHashMap linkedHashMap = new LinkedHashMap();
        String str3 = null;
        if (bundle != null) {
            str2 = null;
            for (String str4 : bundle.keySet()) {
                String string = bundle.getString(str4);
                if (!TextUtils.isEmpty(string)) {
                    if ("User-Agent".equalsIgnoreCase(str4)) {
                        str3 = string;
                    } else if ("Referer".equalsIgnoreCase(str4)) {
                        str2 = string;
                    } else {
                        linkedHashMap.put(str4, string);
                    }
                }
            }
            str = str3;
        } else {
            str = null;
            str2 = null;
        }
        return new ah0(str, str2, linkedHashMap, 24, false);
    }

    public static int m8844k() {
        int iM7611r = p11.m7611r(0, "decode_dolby_vision_output_policy");
        if (iM7611r < 0 || iM7611r > 2) {
            return 0;
        }
        return iM7611r;
    }

    public static int m8845m() throws JSONException {
        JSONArray jSONArrayOptJSONArray = m8855y(m8849q("getFreePorts", new JSONObject().put("count", 1))).optJSONArray("ports");
        if (jSONArrayOptJSONArray == null || jSONArrayOptJSONArray.length() != 1) {
            throw new JSONException("Xray did not return a free port");
        }
        return jSONArrayOptJSONArray.getInt(0);
    }

    public static final C1214np m8846n(Continuation continuation) {
        Unsafe unsafe;
        C1214np c1214np;
        C1214np c1214np2;
        if (!(continuation instanceof hh0)) {
            return new C1214np(1, continuation);
        }
        hh0 hh0Var = (hh0) continuation;
        long j = hh0.f7147n;
        loop0: while (true) {
            unsafe = vp2.f19356a;
            Object objectVolatile = unsafe.getObjectVolatile(hh0Var, j);
            c1214np = null;
            y83 y83Var = f16260j;
            if (objectVolatile == null) {
                unsafe.putObjectVolatile(hh0Var, j, y83Var);
                c1214np2 = null;
                break;
            }
            if (objectVolatile instanceof C1214np) {
                do {
                    unsafe = vp2.f19356a;
                    if (unsafe.compareAndSwapObject(hh0Var, hh0.f7147n, objectVolatile, y83Var)) {
                        c1214np2 = (C1214np) objectVolatile;
                        break loop0;
                    }
                } while (unsafe.getObjectVolatile(hh0Var, j) == objectVolatile);
            } else if (objectVolatile != y83Var && !(objectVolatile instanceof Throwable)) {
                e81.m3054n(objectVolatile, "Inconsistent state ");
                return null;
            }
        }
        if (c1214np2 != null) {
            long j2 = C1214np.f12374n;
            Object objectVolatile2 = unsafe.getObjectVolatile(c1214np2, j2);
            if (!(objectVolatile2 instanceof C0195bx) || ((C0195bx) objectVolatile2).f2261d == null) {
                unsafe.putIntVolatile(c1214np2, C1214np.f12372l, 536870911);
                unsafe.putObjectVolatile(c1214np2, j2, C1476p3.f13761a);
                c1214np = c1214np2;
            } else {
                c1214np2.m6583o();
            }
            if (c1214np != null) {
                return c1214np;
            }
        }
        return new C1214np(2, continuation);
    }

    public static final int m8847o(C0472db c0472db, Object obj, int i) {
        int i2 = c0472db.f4091i;
        if (i2 == 0) {
            return -1;
        }
        try {
            int iM4051b = hc2.m4051b(i2, i, c0472db.f4089c);
            if (iM4051b < 0 || Intrinsics.areEqual(obj, c0472db.f4090h[iM4051b])) {
                return iM4051b;
            }
            int i3 = iM4051b + 1;
            while (i3 < i2 && c0472db.f4089c[i3] == i) {
                if (Intrinsics.areEqual(obj, c0472db.f4090h[i3])) {
                    return i3;
                }
                i3++;
            }
            for (int i4 = iM4051b - 1; i4 >= 0 && c0472db.f4089c[i4] == i; i4--) {
                if (Intrinsics.areEqual(obj, c0472db.f4090h[i4])) {
                    return i4;
                }
            }
            return ~i3;
        } catch (IndexOutOfBoundsException unused) {
            C1687uo.m9817j();
            return 0;
        }
    }

    public static bg0 m8848p(LayoutInflater layoutInflater, ViewGroup viewGroup) {
        View viewInflate = layoutInflater.inflate(com.fongmi.android.p002tv.R.layout.dialog_speed_setting, viewGroup, false);
        int i = com.fongmi.android.p002tv.R.id.longPressSpeed;
        View viewM8781l = rw1.m8781l(com.fongmi.android.p002tv.R.id.longPressSpeed, viewInflate);
        if (viewM8781l != null) {
            su3 su3VarM9095a = su3.m9095a(viewM8781l);
            i = com.fongmi.android.p002tv.R.id.preset01;
            Chip chip = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset01, viewInflate);
            if (chip != null) {
                i = com.fongmi.android.p002tv.R.id.preset02;
                Chip chip2 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset02, viewInflate);
                if (chip2 != null) {
                    i = com.fongmi.android.p002tv.R.id.preset03;
                    Chip chip3 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset03, viewInflate);
                    if (chip3 != null) {
                        i = com.fongmi.android.p002tv.R.id.preset04;
                        Chip chip4 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset04, viewInflate);
                        if (chip4 != null) {
                            i = com.fongmi.android.p002tv.R.id.preset05;
                            Chip chip5 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset05, viewInflate);
                            if (chip5 != null) {
                                i = com.fongmi.android.p002tv.R.id.preset06;
                                Chip chip6 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset06, viewInflate);
                                if (chip6 != null) {
                                    i = com.fongmi.android.p002tv.R.id.preset07;
                                    Chip chip7 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset07, viewInflate);
                                    if (chip7 != null) {
                                        i = com.fongmi.android.p002tv.R.id.preset08;
                                        Chip chip8 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset08, viewInflate);
                                        if (chip8 != null) {
                                            i = com.fongmi.android.p002tv.R.id.preset09;
                                            Chip chip9 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset09, viewInflate);
                                            if (chip9 != null) {
                                                i = com.fongmi.android.p002tv.R.id.preset10;
                                                Chip chip10 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset10, viewInflate);
                                                if (chip10 != null) {
                                                    i = com.fongmi.android.p002tv.R.id.preset11;
                                                    Chip chip11 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset11, viewInflate);
                                                    if (chip11 != null) {
                                                        i = com.fongmi.android.p002tv.R.id.preset12;
                                                        Chip chip12 = (Chip) rw1.m8781l(com.fongmi.android.p002tv.R.id.preset12, viewInflate);
                                                        if (chip12 != null) {
                                                            i = com.fongmi.android.p002tv.R.id.presetGroup;
                                                            if (((ChipGroup) rw1.m8781l(com.fongmi.android.p002tv.R.id.presetGroup, viewInflate)) != null) {
                                                                i = com.fongmi.android.p002tv.R.id.reset;
                                                                MaterialButton materialButton = (MaterialButton) rw1.m8781l(com.fongmi.android.p002tv.R.id.reset, viewInflate);
                                                                if (materialButton != null) {
                                                                    i = com.fongmi.android.p002tv.R.id.skipSilenceRow;
                                                                    LinearLayoutCompat linearLayoutCompat = (LinearLayoutCompat) rw1.m8781l(com.fongmi.android.p002tv.R.id.skipSilenceRow, viewInflate);
                                                                    if (linearLayoutCompat != null) {
                                                                        i = com.fongmi.android.p002tv.R.id.skipSilenceSwitch;
                                                                        MaterialSwitch materialSwitch = (MaterialSwitch) rw1.m8781l(com.fongmi.android.p002tv.R.id.skipSilenceSwitch, viewInflate);
                                                                        if (materialSwitch != null) {
                                                                            i = com.fongmi.android.p002tv.R.id.speed;
                                                                            View viewM8781l2 = rw1.m8781l(com.fongmi.android.p002tv.R.id.speed, viewInflate);
                                                                            if (viewM8781l2 != null) {
                                                                                return new bg0((LinearLayoutCompat) viewInflate, su3VarM9095a, chip, chip2, chip3, chip4, chip5, chip6, chip7, chip8, chip9, chip10, chip11, chip12, materialButton, linearLayoutCompat, materialSwitch, su3.m9095a(viewM8781l2));
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        h00.m3905e("Missing required view with ID: ".concat(viewInflate.getResources().getResourceName(i)));
        return null;
    }

    public static Object m8849q(String str, JSONObject jSONObject) throws JSONException {
        JSONObject jSONObjectPut = new JSONObject().put("apiVersion", 2).put("method", str);
        if (jSONObject != null) {
            jSONObjectPut.put("payload", jSONObject);
        }
        JSONObject jSONObject2 = new JSONObject(LibXray.invoke(jSONObjectPut.toString()));
        if (jSONObject2.optBoolean("success")) {
            return jSONObject2.opt("data");
        }
        String strOptString = jSONObject2.optString("error");
        if (strOptString != null) {
            int length = strOptString.length();
            int iCharCount = 0;
            while (iCharCount < length) {
                int iCodePointAt = strOptString.codePointAt(iCharCount);
                if (Character.isWhitespace(iCodePointAt)) {
                    iCharCount += Character.charCount(iCodePointAt);
                }
            }
            strOptString = "Xray operation failed";
        } else {
            strOptString = "Xray operation failed";
        }
        throw new IllegalStateException(strOptString);
    }

    public static boolean m8850r() {
        return p11.m7608o("decode_audio_pass_through", p11.m7608o("audio_pass_through", true));
    }

    public static boolean m8851t() {
        return p11.m7608o("decode_tunnel", p11.m7608o("tunnel", false));
    }

    public static String m8852v(int i, String str, String str2) {
        return m8853w(Pattern.compile(str), str2, i);
    }

    public static String m8853w(Pattern pattern, String str, int i) throws vc2 {
        Matcher matcher = pattern.matcher(str);
        if (matcher.find()) {
            return matcher.group(i);
        }
        String strM6233l = AbstractC1163ml.m6233l("Failed to find pattern \"", pattern.pattern(), "\"");
        if (str.length() <= 1024) {
            strM6233l = xp0.m10582l(strM6233l, " inside of \"", str, "\"");
        }
        throw new vc2(strM6233l);
    }

    public static Matcher m8854x(Pattern[] patternArr, String str) throws vc2 {
        vc2 vc2Var = null;
        for (Pattern pattern : patternArr) {
            Matcher matcher = pattern.matcher(str);
            if (matcher.find()) {
                return matcher;
            }
            if (vc2Var == null) {
                vc2Var = new vc2(xp0.m10582l("Failed to find pattern \"", pattern.pattern(), "\"", str.length() <= 1000 ? AbstractC1163ml.m6233l("inside of \"", str, "\"") : ""));
            }
        }
        if (vc2Var != null) {
            throw vc2Var;
        }
        throw new vc2("Empty patterns array passed to matchMultiplePatterns");
    }

    public static JSONObject m8855y(Object obj) throws JSONException {
        if (obj instanceof JSONObject) {
            return (JSONObject) obj;
        }
        throw new JSONException("Xray returned an invalid response");
    }

    public static th0 m8856z(String str) {
        q61 q61Var = new q61();
        StringReader stringReader = new StringReader(str);
        xc2 xc2Var = new xc2(q61Var);
        th0 th0Var = new th0();
        q61Var.f14671d = th0Var;
        th0Var.f17519q = xc2Var;
        q61Var.f14668a = xc2Var;
        q61Var.f14675h = xc2Var.f20705h;
        C0564fs c0564fs = new C0564fs(stringReader);
        q61Var.f14669b = c0564fs;
        c0564fs.f6019p = null;
        q61Var.f14670c = new pg3(q61Var);
        q61Var.f14672e = new ArrayList(32);
        dd3 dd3Var = xc2Var.f20706i;
        if (dd3Var == null) {
            dd3Var = new dd3(dd3.f4141d, null);
            xc2Var.f20706i = dd3Var;
        }
        q61Var.f14676i = dd3Var;
        jg3 jg3Var = new jg3(2, q61Var);
        q61Var.f14677j = jg3Var;
        q61Var.f14674g = jg3Var;
        q61Var.f14673f = "";
        q61Var.f14679l = p71.f13879c;
        q61Var.f14680m = null;
        q61Var.f14681n = false;
        q61Var.f14682o = null;
        q61Var.f14683p = null;
        q61Var.f14684q = new ArrayList();
        q61Var.f14685r = new ArrayList();
        q61Var.f14686s = new ArrayList();
        q61Var.f14687t = new ig3(3, q61Var);
        q61Var.f14688u = true;
        q61Var.f14689v = false;
        while (true) {
            if (q61Var.f14674g.f11411a == 7) {
                ArrayList arrayList = q61Var.f14672e;
                if (arrayList == null) {
                    break;
                }
                if (arrayList.isEmpty()) {
                    q61Var.f14672e = null;
                } else {
                    q61Var.m8017F();
                }
            } else {
                pg3 pg3Var = q61Var.f14670c;
                eg3 eg3Var = pg3Var.f14090j;
                while (!pg3Var.f14085e) {
                    pg3Var.f14083c.mo323c(pg3Var, pg3Var.f14081a);
                }
                boolean zM2609z = eg3Var.f4955d.m2609z();
                mg3 mg3Var = eg3Var;
                if (!zM2609z) {
                    pg3Var.f14085e = false;
                    mg3Var = pg3Var.f14084d;
                }
                q61Var.f14674g = mg3Var;
                q61Var.m8020I(mg3Var);
                mg3Var.mo3149f();
            }
        }
        C0564fs c0564fs2 = q61Var.f14669b;
        if (c0564fs2 != null) {
            c0564fs2.close();
            q61Var.f14669b = null;
            q61Var.f14670c = null;
            q61Var.f14672e = null;
        }
        return q61Var.f14671d;
    }

    public abstract void mo8857F(boolean z);

    public abstract void mo8858G(boolean z);

    public abstract TransformationMethod mo8859L(TransformationMethod transformationMethod);

    public abstract String mo4361e(int i, int i2, byte[] bArr);

    public abstract Object mo47g();

    public abstract int mo4362h(String str, byte[] bArr, int i, int i2);

    public abstract InputFilter[] mo8860l(InputFilter[] inputFilterArr);

    public abstract boolean mo8861s();

    public String toString() {
        switch (this.f16273c) {
            case 10:
                return mo47g().toString();
            default:
                return super.toString();
        }
    }

    public abstract boolean mo4363u(int i, int i2, byte[] bArr);
}
