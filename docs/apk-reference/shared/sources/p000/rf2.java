package p000;

import android.net.Uri;
import com.fongmi.android.p002tv.service.PlaybackService;
import java.io.IOException;
import java.util.Collections;
import java.util.HashSet;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArrayList;

public final class rf2 implements InterfaceC0594gl {

    public static final Set f15700j;

    public final CopyOnWriteArrayList f15701c = new CopyOnWriteArrayList();

    public final h80 f15702h;

    public final PlaybackService f15703i;

    static {
        Object[] objArr = {"file", "asset", "content", "data", "rawresource", "android.resource"};
        HashSet hashSet = new HashSet(6);
        for (int i = 0; i < 6; i++) {
            Object obj = objArr[i];
            Objects.requireNonNull(obj);
            if (!hashSet.add(obj)) {
                C1566re.m8586j(xp0.m10578h(obj, "duplicate element: "));
                return;
            }
        }
        f15700j = Collections.unmodifiableSet(hashSet);
    }

    public rf2(PlaybackService playbackService, h80 h80Var) {
        this.f15703i = playbackService;
        this.f15702h = h80Var;
    }

    @Override
    public final wi1 mo3783e(Uri uri) {
        boolean z = false;
        if (uri != null) {
            String scheme = uri.getScheme();
            if (scheme == null) {
                z = true;
                break;
            }
            int length = scheme.length();
            int iCharCount = 0;
            while (true) {
                if (iCharCount < length) {
                    int iCodePointAt = scheme.codePointAt(iCharCount);
                    if (!Character.isWhitespace(iCodePointAt)) {
                        if (!f15700j.contains(scheme.toLowerCase(Locale.ROOT))) {
                            break;
                        }
                        break;
                    }
                    iCharCount += Character.charCount(iCodePointAt);
                }
                z = true;
                break;
            }
        }
        th2 th2Var = this.f15703i.f3037x;
        if (th2Var != null && th2Var.m9332s() && !z) {
            return rw1.m8785r(new IOException("Remote artwork blocked while Xray is enabled"));
        }
        wi1 wi1VarMo3783e = this.f15702h.mo3783e(uri);
        if (!z) {
            this.f15701c.add(wi1VarMo3783e);
            wi1VarMo3783e.mo46f(new p52(this, wi1VarMo3783e, 11), og0.f13028c);
        }
        return wi1VarMo3783e;
    }

    @Override
    public final wi1 mo3785j(byte[] bArr) {
        return this.f15702h.mo3785j(bArr);
    }
}
