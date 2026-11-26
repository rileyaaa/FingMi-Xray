/* SPDX-License-Identifier: Apache-2.0 */
import androidx.media3.extractor.iso.IsoConstants;
import androidx.media3.extractor.iso.IsoFileEntry;
import java.util.Arrays;

/** Host-only metadata contract of pinned official classes; no UDF parsing or I/O. */
public final class IsoExtentContract {
    private static void require(boolean pass, String name) {
        if (!pass) throw new AssertionError(name);
    }
    private static void rejected(Runnable test) {
        try { test.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("invalid extent array accepted");
    }
    public static void main(String[] args) {
        require(IsoConstants.SECTOR_SIZE == 2048, "sector size");
        IsoFileEntry single = new IsoFileEntry("one", 4096L, 17L);
        require(single.byteOffset == 4096L && single.length == 17L &&
                Arrays.equals(single.extentOffsets, new long[]{4096L}) &&
                Arrays.equals(single.extentLengths, new long[]{17L}), "single extent");
        System.out.println("PASS_ISO_SINGLE_EXTENT_AND_SECTOR_SIZE");
        long[] offsets = {8192L, IsoFileEntry.UNRECORDED_EXTENT_OFFSET, 32768L};
        long[] lengths = {2048L, 2048L, 37L};
        IsoFileEntry multi = new IsoFileEntry("multi", offsets, lengths, 4133L);
        require(multi.byteOffset == 8192L && multi.length == 4133L &&
                multi.extentOffsets[1] == -1 && Arrays.equals(multi.extentOffsets, offsets) &&
                Arrays.equals(multi.extentLengths, lengths), "ordered multi extent");
        System.out.println("PASS_ISO_NONCONTIGUOUS_AND_ZERO_EXTENT_METADATA");
        offsets[0] = 0; lengths[0] = 0;
        require(multi.extentOffsets[0] == 8192L && multi.extentLengths[0] == 2048L,
                "defensive copies of constructor arrays");
        System.out.println("PASS_ISO_INPUT_ARRAY_OWNERSHIP");
        long largeOffset = 1L << 34, largeLength = 1L << 32;
        IsoFileEntry large = new IsoFileEntry("large", largeOffset, largeLength);
        require(large.byteOffset == largeOffset && large.length == largeLength &&
                large.extentOffsets[0] == largeOffset && large.extentLengths[0] == largeLength,
                "64-bit extent metadata");
        System.out.println("PASS_ISO_64BIT_METADATA");
        rejected(() -> new IsoFileEntry("empty", new long[0], new long[0], 0));
        rejected(() -> new IsoFileEntry("mismatch", new long[]{4096L}, new long[0], 1));
        System.out.println("PASS_ISO_INVALID_ARRAY_SHAPES_REJECTED");
        System.out.println("PASS_PINNED_ISO_METADATA_HOST_ONLY");
    }
}
