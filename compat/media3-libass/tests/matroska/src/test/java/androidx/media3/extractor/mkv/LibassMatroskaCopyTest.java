package androidx.media3.extractor.mkv;
import static org.junit.Assert.*;
import androidx.media3.extractor.text.DefaultSubtitleParserFactory;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
@RunWith(RobolectricTestRunner.class)
@Config(sdk=28,manifest=Config.NONE)
public final class LibassMatroskaCopyTest {
 @Test public void copiesAllExtractionFlagCombinations() throws Exception {
  for(int flags=0;flags<4;flags++) {
   MatroskaExtractor source=new MatroskaExtractor(new DefaultSubtitleParserFactory(),flags);
   MatroskaExtractor copy=new MatroskaExtractor(source,new DefaultSubtitleParserFactory());
   for(String name:new String[]{"seekForCuesEnabled","parseSubtitlesDuringExtraction"}) {
    java.lang.reflect.Field f=MatroskaExtractor.class.getDeclaredField(name);f.setAccessible(true);
    assertEquals(name+":"+flags,f.getBoolean(source),f.getBoolean(copy));
   }
  }
 }
}
