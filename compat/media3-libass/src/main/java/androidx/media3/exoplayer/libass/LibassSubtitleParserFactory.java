package androidx.media3.exoplayer.libass;

import androidx.media3.common.Format;
import androidx.media3.common.MimeTypes;
import androidx.media3.common.util.Consumer;
import androidx.media3.extractor.text.CuesWithTiming;
import androidx.media3.extractor.text.DefaultSubtitleParserFactory;
import androidx.media3.extractor.text.SubtitleParser;
import java.nio.ByteBuffer;
import java.nio.charset.Charset;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.StandardCharsets;
import java.util.Objects;

/** Reconstructed published5.6.5 yk1/ax0 glue; each parser retains exactly one media owner. */
final class LibassSubtitleParserFactory implements SubtitleParser.Factory {
    private final LibassMediaState media;
    private final SubtitleParser.Factory delegate;
    private final boolean originalMatroskaSamples;

    LibassSubtitleParserFactory(LibassMediaState media) { this(media,new DefaultSubtitleParserFactory(),false); }
    LibassSubtitleParserFactory(LibassMediaState media,SubtitleParser.Factory delegate) { this(media,delegate,false); }
    private LibassSubtitleParserFactory(LibassMediaState media,SubtitleParser.Factory delegate,boolean originalSamples) {
        this.media=Objects.requireNonNull(media);this.delegate=Objects.requireNonNull(delegate);this.originalMatroskaSamples=originalSamples;
    }
    LibassSubtitleParserFactory forMatroska() { return new LibassSubtitleParserFactory(media,delegate,true); }
    static boolean isAss(Format format) { return MimeTypes.TEXT_SSA.equals(format.sampleMimeType); }
    private boolean handles(Format format) { return media.isAvailable()&&isAss(format); }
    @Override public boolean supportsFormat(Format format) { return handles(format)||delegate.supportsFormat(format); }
    @Override public int getCueReplacementBehavior(Format format) { return handles(format)?Format.CUE_REPLACEMENT_BEHAVIOR_REPLACE:delegate.getCueReplacementBehavior(format); }
    @Override public SubtitleParser create(Format format) {
        if(!handles(format))return delegate.create(format);
        if(originalMatroskaSamples&&(MimeTypes.VIDEO_MATROSKA.equals(format.containerMimeType)||MimeTypes.VIDEO_WEBM.equals(format.containerMimeType)))return new OriginalSampleParser();
        return new ExternalAssParser(media,format);
    }
    private static final class OriginalSampleParser implements SubtitleParser {
        @Override public void parse(byte[] data,int offset,int length,OutputOptions options,Consumer<CuesWithTiming> output) {
            // The paired LibassMatroskaExtractor already delivered these original ASS packets.
        }
        @Override public int getCueReplacementBehavior() { return Format.CUE_REPLACEMENT_BEHAVIOR_REPLACE; }
    }
    private static final class ExternalAssParser implements SubtitleParser {
        private final LibassMediaState media;
        private final Format format;
        private final boolean wholeFile;
        ExternalAssParser(LibassMediaState media,Format format) {
            this.media=media;this.format=format;
            wholeFile=format.containerMimeType==null||MimeTypes.isText(format.containerMimeType);
        }
        @Override public void parse(byte[] data,int offset,int length,OutputOptions options,Consumer<CuesWithTiming> output) {
            if(!media.isAvailable())return;
            if(wholeFile) {
                byte[] utf8=wholeFileUtf8(data,offset,length);
                media.addExternalTrack(format,utf8,0,utf8.length);
            } else media.addExternalTrack(format,data,offset,length);
        }
        @Override public void parse(byte[] data,int offset,int length,long timeUs,OutputOptions options,Consumer<CuesWithTiming> output) {
            if(wholeFile)parse(data,offset,length,options,output);
            else media.processTimedData(format,data,offset,length,timeUs);
        }
        @Override public int getCueReplacementBehavior() { return Format.CUE_REPLACEMENT_BEHAVIOR_REPLACE; }
        // Reset intentionally retains native events, matching ax0.reset; no old nativeFlushEvents ABI.
    }
    private static byte[] wholeFileUtf8(byte[] data,int offset,int length) {
        if(offset<0||length<0||offset>data.length-length)throw new IndexOutOfBoundsException();
        Charset charset=StandardCharsets.UTF_8;
        if(length>=2) {
            int a=data[offset]&255,b=data[offset+1]&255;
            if(a==255&&b==254)charset=StandardCharsets.UTF_16LE;
            else if(a==254&&b==255)charset=StandardCharsets.UTF_16BE;
        }
        try {
            String text=charset.newDecoder().decode(ByteBuffer.wrap(data,offset,length)).toString();
            if(!text.isEmpty()&&text.charAt(0)=='\uFEFF')text=text.substring(1);
            return text.getBytes(StandardCharsets.UTF_8);
        } catch(CharacterCodingException failure) { throw new IllegalArgumentException("Invalid subtitle data for "+charset.name(),failure); }
    }
}
