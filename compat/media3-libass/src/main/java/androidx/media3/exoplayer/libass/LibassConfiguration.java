package androidx.media3.exoplayer.libass;

/** Reconstructed configuration surface used by FongMi5.6.3; published5.6.5 kk1 fields.
 * App explicitly supplies all settings. Zero limits are reconstruction defaults (native defaults
 * and uncapped view size), not a claim about the unavailable original builder's defaults.
 */
public final class LibassConfiguration {
    final String fontConfig, fontsDirectory, defaultFontFamily;
    final int maximumRenderPixels, maximumGlyphCount, maximumBitmapCacheSizeMb;

    private LibassConfiguration(Builder b) {
        fontConfig=b.fontConfig;fontsDirectory=b.fontsDirectory;defaultFontFamily=b.defaultFontFamily;
        maximumRenderPixels=b.maximumRenderPixels;maximumGlyphCount=b.maximumGlyphCount;
        maximumBitmapCacheSizeMb=b.maximumBitmapCacheSizeMb;
    }
    public static final class Builder {
        private String fontConfig, fontsDirectory, defaultFontFamily;
        private int maximumRenderPixels, maximumGlyphCount, maximumBitmapCacheSizeMb;
        public Builder setFontConfig(String value){fontConfig=value;return this;}
        public Builder setFontsDirectory(String value){fontsDirectory=value;return this;}
        public Builder setDefaultFontFamily(String value){family(value);defaultFontFamily=value;return this;}
        public Builder setMaximumRenderPixels(int value){nonnegative(value);maximumRenderPixels=value;return this;}
        public Builder setMaximumGlyphCount(int value){nonnegative(value);maximumGlyphCount=value;return this;}
        public Builder setMaximumBitmapCacheSizeMb(int value){nonnegative(value);maximumBitmapCacheSizeMb=value;return this;}
        public LibassConfiguration build(){return new LibassConfiguration(this);}
        private static void nonnegative(int v){if(v<0)throw new IllegalArgumentException("Limit must be non-negative");}
    }
    static void family(String value){if(value!=null&&value.isEmpty())throw new IllegalArgumentException("Font family must not be empty");}
}
