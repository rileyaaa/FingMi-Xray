package androidx.media3.exoplayer.libass;

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;

/**
 * Reconstructed upstream-missing font metadata reader for FongMi Media3 1.11.0.
 *
 * <p>Reads the OpenType/TrueType {@code name} table without loading font glyphs. Typographic
 * family name (name ID 16) is preferred, with legacy family name (name ID 1) as fallback.
 */
public final class LibassFontFile {

    private static final int TTC_TAG = 0x74746366; // ttcf
    private static final int NAME_TAG = 0x6E616D65; // name
    private static final int MAX_TABLES = 4096;
    private static final int MAX_NAMES = 16384;

    private LibassFontFile() {
    }

    public static String getFamilyName(File file) throws IOException {
        if (file == null || !file.isFile()) throw new IOException("Font file is missing");
        try (RandomAccessFile input = new RandomAccessFile(file, "r")) {
            long faceOffset = firstFaceOffset(input);
            return readFamilyName(input, faceOffset);
        }
    }

    private static long firstFaceOffset(RandomAccessFile input) throws IOException {
        requireRange(input, 0, 4);
        input.seek(0);
        int tag = input.readInt();
        if (tag != TTC_TAG) return 0L;

        requireRange(input, 0, 16);
        input.seek(8);
        long faceCount = readUInt32(input);
        if (faceCount < 1 || faceCount > 0xFFFFL) throw new IOException("Invalid TrueType collection");
        long firstOffset = readUInt32(input);
        requireRange(input, firstOffset, 12);
        return firstOffset;
    }

    private static String readFamilyName(RandomAccessFile input, long faceOffset) throws IOException {
        requireRange(input, faceOffset, 12);
        input.seek(faceOffset + 4);
        int tableCount = input.readUnsignedShort();
        if (tableCount < 1 || tableCount > MAX_TABLES) throw new IOException("Invalid font table directory");

        long directory = faceOffset + 12;
        requireRange(input, directory, (long) tableCount * 16);
        long nameOffset = -1;
        long nameLength = -1;
        for (int i = 0; i < tableCount; i++) {
            input.seek(directory + (long) i * 16);
            int tag = input.readInt();
            input.skipBytes(4);
            long offset = readUInt32(input);
            long length = readUInt32(input);
            if (tag == NAME_TAG) {
                nameOffset = offset;
                nameLength = length;
                break;
            }
        }
        if (nameOffset < 0) throw new IOException("Font name table is missing");
        return readNameTable(input, nameOffset, nameLength);
    }

    private static String readNameTable(RandomAccessFile input, long tableOffset, long tableLength) throws IOException {
        requireRange(input, tableOffset, tableLength);
        if (tableLength < 6) throw new IOException("Invalid font name table");

        input.seek(tableOffset);
        input.readUnsignedShort(); // format 0/1; name records have the same layout.
        int count = input.readUnsignedShort();
        int stringOffset = input.readUnsignedShort();
        if (count < 1 || count > MAX_NAMES) throw new IOException("Invalid font name record count");

        long recordsOffset = tableOffset + 6;
        long stringsBase = tableOffset + stringOffset;
        requireRange(input, recordsOffset, (long) count * 12);
        requireRange(input, stringsBase, 0);

        Candidate best = null;
        for (int i = 0; i < count; i++) {
            input.seek(recordsOffset + (long) i * 12);
            int platform = input.readUnsignedShort();
            int encoding = input.readUnsignedShort();
            int language = input.readUnsignedShort();
            int nameId = input.readUnsignedShort();
            int length = input.readUnsignedShort();
            int offset = input.readUnsignedShort();
            if (nameId != 1 && nameId != 16 || length == 0) continue;

            long valueOffset = stringsBase + offset;
            if (!isRangeInside(input, tableOffset, tableLength, valueOffset, length)) continue;
            byte[] value = new byte[length];
            input.seek(valueOffset);
            input.readFully(value);
            String decoded = decodeName(platform, encoding, value);
            if (decoded == null) continue;
            decoded = decoded.replace("\u0000", "").trim();
            if (decoded.isEmpty()) continue;

            int score = score(nameId, platform, language);
            if (best == null || score > best.score) best = new Candidate(decoded, score);
        }
        if (best == null) throw new IOException("Font family name is missing");
        return best.value;
    }

    private static int score(int nameId, int platform, int language) {
        int score = nameId == 16 ? 100 : 0;
        if (platform == 3) score += 20;
        else if (platform == 0) score += 15;
        else if (platform == 1) score += 5;
        if (language == 0x0409) score += 4;
        else if (language == 0) score += 2;
        return score;
    }

    private static String decodeName(int platform, int encoding, byte[] value) {
        try {
            if (platform == 0 || platform == 3) {
                if ((value.length & 1) != 0) return null;
                return new String(value, StandardCharsets.UTF_16BE);
            }
            if (platform == 1) {
                Charset charset = Charset.isSupported("x-MacRoman")
                        ? Charset.forName("x-MacRoman")
                        : StandardCharsets.ISO_8859_1;
                return new String(value, charset);
            }
            return encoding == 0 ? new String(value, StandardCharsets.ISO_8859_1) : null;
        } catch (RuntimeException ignored) {
            return null;
        }
    }

    private static long readUInt32(RandomAccessFile input) throws IOException {
        return Integer.toUnsignedLong(input.readInt());
    }

    private static void requireRange(RandomAccessFile input, long offset, long length) throws IOException {
        if (offset < 0 || length < 0 || offset > input.length() || length > input.length() - offset) {
            throw new IOException("Invalid font table bounds");
        }
    }

    private static boolean isRangeInside(
            RandomAccessFile input, long tableOffset, long tableLength, long offset, long length)
            throws IOException {
        if (offset < tableOffset || length < 0 || offset > input.length() || length > input.length() - offset) {
            return false;
        }
        long tableEnd = tableOffset + tableLength;
        return tableEnd >= tableOffset && offset <= tableEnd && length <= tableEnd - offset;
    }

    private record Candidate(String value, int score) {
    }
}
