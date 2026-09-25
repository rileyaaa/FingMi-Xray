#!/usr/bin/env python3
"""Check selected FongMi/TV 5.6.0 player method descriptors in the candidate AARs.

This checks the non-upstream Media3 interfaces directly used by the fixed TV
source. It is not a complete javac, dependency, or released-DEX comparison.
"""

import argparse
import hashlib
from io import BytesIO
from pathlib import Path
import runpy
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
ARTIFACT_SHA256 = runpy.run_path(str(ROOT / "import-player-aar-candidate.py"))[
    "ARTIFACT_SHA256"
]
MPV = "androidx/media3/mpvplayer/"
EXO = "androidx/media3/exoplayer/"

# Method names and JVM descriptors are deliberately explicit: presence of a
# class alone cannot show whether the recovered Java can call its methods.
EXPECTED = {
    "lib-mpvplayer-release.aar": {
        MPV + "MpvPlayer": {
            ("isAvailable", "()Z"), ("setDecode", "(I)V"),
            ("addSubtitle", "(Landroidx/media3/common/MediaItem$SubtitleConfiguration;)Z"),
            ("setSubtitleOptions", "(Landroidx/media3/mpvplayer/MpvSubtitleOptions;)V"),
            ("setAudioOutputListener", "(Landroidx/media3/mpvplayer/MpvPlayer$AudioOutputListener;)V"),
            ("getAudioChannelCount", "()I"), ("getAudioEffectsSupport", "()I"),
            ("getVideoEffectsSupport", "()I"), ("isVideoSharpnessSupported", "()Z"),
            ("setAudioFilter", "(Landroidx/media3/mpvplayer/audio/MpvAudioFilter;)Z"),
        },
        MPV + "MpvPlayer$Builder": {
            ("<init>", "(Landroid/content/Context;)V"),
            ("setDecode", "(I)Landroidx/media3/mpvplayer/MpvPlayer$Builder;"),
            ("setConfig", "(Landroidx/media3/mpvplayer/MpvPlayerConfig;)Landroidx/media3/mpvplayer/MpvPlayer$Builder;"),
            ("build", "()Landroidx/media3/mpvplayer/MpvPlayer;"),
        },
        MPV + "MpvPlayerConfig$Builder": {
            ("addConfigDirectory", "(Ljava/io/File;)Landroidx/media3/mpvplayer/MpvPlayerConfig$Builder;"),
            ("addAndroidFontConfig", "(Ljava/io/File;Ljava/io/File;)Landroidx/media3/mpvplayer/MpvPlayerConfig$Builder;"),
            ("addAndroidDefaults", "(Landroidx/media3/mpvplayer/MpvAndroidOptions;)Landroidx/media3/mpvplayer/MpvPlayerConfig$Builder;"),
            ("addTlsCaFileFromAsset", "(Landroid/content/Context;Ljava/lang/String;Ljava/io/File;)Landroidx/media3/mpvplayer/MpvPlayerConfig$Builder;"),
            ("addAndroidSubtitleOptions", "(Landroid/content/Context;Landroidx/media3/mpvplayer/MpvSubtitleOptions;)Landroidx/media3/mpvplayer/MpvPlayerConfig$Builder;"),
            ("addDiskCacheOptions", "(Ljava/io/File;I)Landroidx/media3/mpvplayer/MpvPlayerConfig$Builder;"),
        },
        MPV + "MpvAndroidOptions$Builder": {
            ("setShaderCacheDirectory", "(Ljava/io/File;)Landroidx/media3/mpvplayer/MpvAndroidOptions$Builder;"),
            ("setAudioPassthroughEnabled", "(Z)Landroidx/media3/mpvplayer/MpvAndroidOptions$Builder;"),
            ("setDolbyVisionOutputPolicy", "(I)Landroidx/media3/mpvplayer/MpvAndroidOptions$Builder;"),
            ("setGpuNextEnabled", "(Z)Landroidx/media3/mpvplayer/MpvAndroidOptions$Builder;"),
            ("setVulkanEnabled", "(Z)Landroidx/media3/mpvplayer/MpvAndroidOptions$Builder;"),
        },
        MPV + "MpvSubtitleOptions$Builder": {
            ("setPosition", "(D)Landroidx/media3/mpvplayer/MpvSubtitleOptions$Builder;"),
            ("setScale", "(D)Landroidx/media3/mpvplayer/MpvSubtitleOptions$Builder;"),
            ("setSecondarySubtitle", "(IDZ)Landroidx/media3/mpvplayer/MpvSubtitleOptions$Builder;"),
            ("setCustomStyle", "(IIIIDD)Landroidx/media3/mpvplayer/MpvSubtitleOptions$Builder;"),
            ("setSystemCaptionStyle", "()Landroidx/media3/mpvplayer/MpvSubtitleOptions$Builder;"),
        },
    },
    "lib-exoplayer-release.aar": {
        EXO + "DefaultLoadControl$Builder": {
            ("setPlayerTargetBufferBytes", "(Ljava/lang/String;I)Landroidx/media3/exoplayer/DefaultLoadControl$Builder;"),
        },
        EXO + "DefaultRenderersFactory": {
            ("setDolbyVisionOutputPolicy", "(I)Landroidx/media3/exoplayer/DefaultRenderersFactory;"),
        },
        EXO + "trackselection/DecodeTrackSelector": {
            ("<init>", "(Landroid/content/Context;)V"),
            ("setRendererDecodePreferences", "(II)V"),
        },
        EXO + "source/preload/MediaSourceFactorySupplier": {
            ("setCache", "(Landroidx/media3/datasource/cache/Cache;)Landroidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier;"),
            ("setDataSourceFactory", "(Landroidx/media3/datasource/DataSource$Factory;)Landroidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier;"),
        },
        EXO + "source/preload/DefaultPreloadManager$Builder": {
            ("<init>", "(Landroid/content/Context;Landroidx/media3/exoplayer/source/preload/TargetPreloadStatusControl;)V"),
            ("build", "()Landroidx/media3/exoplayer/source/preload/DefaultPreloadManager;"),
            ("buildExoPlayer", "(Landroidx/media3/exoplayer/ExoPlayer$Builder;)Landroidx/media3/exoplayer/ExoPlayer;"),
            ("setMediaSourceFactorySupplier", "(Landroidx/media3/exoplayer/source/preload/MediaSourceFactorySupplier;)Landroidx/media3/exoplayer/source/preload/DefaultPreloadManager$Builder;"),
            ("setRenderersFactory", "(Landroidx/media3/exoplayer/RenderersFactory;)Landroidx/media3/exoplayer/source/preload/DefaultPreloadManager$Builder;"),
            ("setTrackSelectorFactory", "(Landroidx/media3/exoplayer/trackselection/TrackSelector$Factory;)Landroidx/media3/exoplayer/source/preload/DefaultPreloadManager$Builder;"),
            ("setLoadControl", "(Landroidx/media3/exoplayer/LoadControl;)Landroidx/media3/exoplayer/source/preload/DefaultPreloadManager$Builder;"),
        },
        EXO + "source/preload/DefaultPreloadManager$PreloadStatus": {
            ("specifiedRangeLoaded", "(JJ)Landroidx/media3/exoplayer/source/preload/DefaultPreloadManager$PreloadStatus;"),
        },
        EXO + "source/preload/BasePreloadManager": {
            ("add", "(Landroidx/media3/common/MediaItem;Ljava/lang/Object;)V"),
            ("addListener", "(Landroidx/media3/exoplayer/source/preload/PreloadManagerListener;)V"),
            ("getMediaSource", "(Landroidx/media3/common/MediaItem;)Landroidx/media3/exoplayer/source/MediaSource;"),
            ("invalidate", "()V"),
            ("remove", "(Landroidx/media3/common/MediaItem;)Z"),
            ("release", "()V"),
        },
    },
}


def class_methods(data: bytes) -> set[tuple[str, str]]:
    if data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("Invalid Java class header")
    offset = 8

    def read(count: int) -> bytes:
        nonlocal offset
        value = data[offset:offset + count]
        if len(value) != count:
            raise ValueError("Truncated Java class")
        offset += count
        return value

    def number(width: int) -> int:
        return int.from_bytes(read(width), "big")

    pool = [None] * number(2)
    index = 1
    while index < len(pool):
        tag = number(1)
        if tag == 1:
            pool[index] = read(number(2)).decode("utf-8", "replace")
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            read(4)
        elif tag in (5, 6):
            read(8)
            index += 1
        elif tag in (7, 8, 16, 19, 20):
            read(2)
        elif tag == 15:
            read(3)
        else:
            raise ValueError(f"Unknown class-pool tag {tag}")
        index += 1

    read(6)  # access flags, this class, super class
    for _ in range(number(2)):
        read(2)
    for _ in range(number(2)):
        read(6)
        for _ in range(number(2)):
            read(2)
            read(number(4))
    result = set()
    for _ in range(number(2)):
        flags, name, descriptor = number(2), pool[number(2)], pool[number(2)]
        if flags & 0x0001:  # public declarations only
            result.add((name, descriptor))
        for _ in range(number(2)):
            read(2)
            read(number(4))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.artifact.read_bytes()).hexdigest() != ARTIFACT_SHA256:
        parser.error("Candidate ZIP differs from the verified AC artifact")
    count = 0
    class_count = sum(len(classes) for classes in EXPECTED.values())
    with ZipFile(args.artifact) as artifact:
        for aar_name, classes in EXPECTED.items():
            with ZipFile(BytesIO(artifact.read(aar_name))) as aar:
                with ZipFile(BytesIO(aar.read("classes.jar"))) as jar:
                    for class_name, required in classes.items():
                        found = class_methods(jar.read(class_name + ".class"))
                        missing = required - found
                        if missing:
                            parser.error(f"{class_name}: missing {sorted(missing)}")
                        count += len(required)
    print(f"EXACT: {count} selected public Java method descriptors across {class_count} player classes")
    print("Class presence and selected signatures do not establish complete build compatibility.")


if __name__ == "__main__":
    main()
