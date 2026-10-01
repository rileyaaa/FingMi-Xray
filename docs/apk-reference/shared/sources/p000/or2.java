package p000;

import android.net.Uri;
import java.io.IOException;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public final class or2 implements f80 {

    public final f80 f13196c;

    public boolean f13197h;

    public or2(f80 f80Var, kg0 kg0Var) {
        this.f13196c = f80Var;
    }

    @Override
    public final void mo3059A(qa0 qa0Var) {
        qa0Var.getClass();
        this.f13196c.mo3059A(qa0Var);
    }

    @Override
    public final void close() {
        if (this.f13197h) {
            this.f13197h = false;
            this.f13196c.close();
        }
    }

    @Override
    public final Uri getUri() {
        Uri uri = this.f13196c.getUri();
        if (uri == null) {
            return null;
        }
        return uri;
    }

    @Override
    public final long mo2561i(l80 l80Var) throws IOException {
        boolean zContains;
        String scheme = l80Var.f10484a.getScheme();
        Set set = jz3.f9542a;
        if (scheme == null) {
            zContains = true;
            break;
        }
        int length = scheme.length();
        int iCharCount = 0;
        while (true) {
            if (iCharCount >= length) {
                zContains = true;
                break;
            }
            int iCodePointAt = scheme.codePointAt(iCharCount);
            if (!Character.isWhitespace(iCodePointAt)) {
                zContains = jz3.f9542a.contains(scheme.toLowerCase(Locale.ROOT));
                break;
            }
            iCharCount += Character.charCount(iCodePointAt);
        }
        if (zContains) {
            this.f13197h = true;
            return this.f13196c.mo2561i(l80Var);
        }
        kg0.m5396l("Unsupported data source scheme while Xray is enabled");
        return 0L;
    }

    @Override
    public final int read(byte[] bArr, int i, int i2) {
        return this.f13196c.read(bArr, i, i2);
    }

    @Override
    public final Map mo3060t() {
        return this.f13196c.mo3060t();
    }
}
