/*
 * Copyright (c) 2025 peerless2012
 * SPDX-License-Identifier: MIT
 * Based on v0.5.1 AssTrackOutput.kt (38a83589114ed5fa9aaeac4f68d30d1e5f647b4c).
 * FingMi: bound reads to the committed sample, reject missing/stale samples;
 * preserve delegate format and metadata exactly. See NOTICE and source pin.
 */
package io.github.peerless2012.ass.media.text

import androidx.media3.common.C
import androidx.media3.common.Format
import androidx.media3.common.MimeTypes
import androidx.media3.common.util.UnstableApi
import androidx.media3.extractor.TrackOutput
import io.github.peerless2012.ass.media.AssHandler
import io.github.peerless2012.ass.media.extractor.AssMatroskaExtractor

@UnstableApi
class AssTrackOutput(
    private val delegate: TrackOutput,
    private val assHandler: AssHandler,
    private val extractor: AssMatroskaExtractor,
) : TrackOutput by delegate {
    private var isAss = false
    private var trackId: String? = null

    override fun format(format: Format) {
        isAss = format.sampleMimeType == MimeTypes.TEXT_SSA || format.codecs == MimeTypes.TEXT_SSA
        trackId = if (isAss) format.id else null
        delegate.format(format)
    }

    override fun sampleMetadata(
        timeUs: Long, flags: Int, size: Int, offset: Int, cryptoData: TrackOutput.CryptoData?
    ) {
        // Matroska 1.11 emits sampleMetadata even for a subtitle block without
        // duration. In that case size=0 and subtitleSample still refers to
        // old data. Do not feed it as a new ASS event.
        if (isAss && trackId != null && timeUs >= 0 && timeUs != C.TIME_UNSET &&
            size > 0 && offset == 0 && cryptoData == null) {
            forward(timeUs, size)
        }
        delegate.sampleMetadata(timeUs, flags, size, offset, cryptoData)
    }

    private fun forward(timeUs: Long, size: Int) {
        val sample = extractor.subtitleSample
        val bytes = sample.data
        val limit = sample.limit()
        // Original Media3 sample: Dialogue: zero start, duration, ASS packet.
        // A supplemental/encrypted/partial sample is not this proven contract.
        if (limit != size || limit > bytes.size || limit < PREFIX.size) return
        for (i in PREFIX.indices) if (bytes[i] != PREFIX[i]) return
        val end = token(bytes, limit, 1)
        val line = token(bytes, limit, 2)
        if (end < PREFIX.size || line <= end + 1 || line >= limit) return
        val duration = durationUs(bytes.decodeToString(end, line - 1)) ?: return
        if (duration <= 0) return
        assHandler.readTrackDialogue(trackId, timeUs / 1000, duration / 1000,
            bytes, line, limit - line)
    }

    private fun token(bytes: ByteArray, limit: Int, wanted: Int): Int {
        var found = 0
        for (i in 0 until limit) if (bytes[i] == COMMA && ++found == wanted) return i + 1
        return -1
    }

    private fun durationUs(value: String): Long? {
        val match = TIMECODE.matchEntire(value) ?: return null
        val h = match.groupValues[1].toLongOrNull() ?: return null
        val m = match.groupValues[2].toLong()
        val s = match.groupValues[3].toLong()
        val cs = match.groupValues[4].toLong()
        // Avoid overflow from malformed/untrusted media data. All other
        // components are bounded by the regex.
        if (h > (Long.MAX_VALUE - 3_600_000_000L) / 3_600_000_000L) return null
        return (h * 3600 + m * 60 + s) * C.MICROS_PER_SECOND + cs * 10000
    }

    private companion object {
        val PREFIX = "Dialogue: ".toByteArray(Charsets.US_ASCII)
        val TIMECODE = Regex("""(\d+):([0-5]\d):([0-5]\d)[:.](\d{2})""")
        const val COMMA = ','.code.toByte()
    }
}
