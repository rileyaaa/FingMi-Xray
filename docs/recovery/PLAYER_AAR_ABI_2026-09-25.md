# 播放器候选 AAR 静态接口与 v7 原生库对照

日期：2026-09-25。验证输入为 AC 运行 `36124817040`、工件 `10859533459`，固定 `FongMi/media@3c2cbe8ac742c2fe15eff52f03eeb3b1b648848d`。候选 ZIP SHA-256：`0ed42581af11ac7163ebde148b318807c244e2a318f40c41d33f50b70bf967ee`。原 v7 APK SHA-256：`cacc7a90ce082adf955fc80a444b54f8cc86d5b5c3ac7acb13d1392b59928bda`。

## 实际结论

1. `lib-mpvplayer-release.aar` 和 `lib-decoder-ffmpeg-release.aar` 的 `jni/armeabi-v7a/` 中，`libmpv.so`、`libplayer.so`、`libc++_shared.so`、`libavcodec.so`、`libavdevice.so`、`libavfilter.so`、`libavformat.so`、`libavutil.so`、`libswresample.so`、`libswscale.so`，与已核过发布 APK 的十个播放器原生库 **SHA-256 全部逐文件相同**。因此这些二进制不是仅仅名称/版本相似，而是十份字节完全相同的原生库；额外的 AAR 原生库（如 `libffmpegJNI.so`）不在本次十份对照范围。
2. 从两份 AAR 的实际 `classes.jar` 解析 JVM class 文件的方法表，对固定 FongMi/TV 5.6.0 直接用到的 8 个播放器类、38 个精选公开方法的名称及 JVM 描述符进行检查，**38 项匹配**。覆盖 mpv 播放器及设置构造器、媒体数据源提供者、解码轨选择器和预加载构造器；脚本的 `EXPECTED` 是精确可复核的选取清单。
3. 本次工作区随会话失效，先从上轮持久保存的候选 ZIP 重新取回 44,336,768 字节工件，重新执行两项脚本，均通过。故任何新会话须以远端 `main` 与该工件为准，不能把上次临时 `app/libs/` 当成持久输入。

## 复核命令

```bash
python3 scripts/check-player-native-against-v7.py --artifact /path/to/FingMi-media3-player-AARs-1.11.0-candidate.zip
python3 scripts/check-player-java-api.py /path/to/FingMi-media3-player-AARs-1.11.0-candidate.zip
```

脚本均先检查候选 ZIP 的整体 SHA-256；原生库校验读取已有 `extract-v7-player-native.py` 的发布版逐文件 SHA-256，避免另立一套基线。ZIP 保存位置、取得方式和手动导入 `app/libs/` 的步骤见 `WORKLOG.md`。

## 尚不能据此宣称的内容

- 38 项不是完整 Java 类/API 差异扫描。生成的 ViewBinding、其余依赖、资源、libXray AAR、混淆后的运行逻辑尚未经 Gradle/javac 验证。
- v7 的十个核心 `.so` 字节相同，不等于 v8 交叉验证、其余 `.so`、设备/系统 API 与所有原生调用完全可用。
- 本轮没有重新编译 faithful APK，也没有 Android TV 实机待机/播放回归。按 `PROJECT_REQUIREMENTS.md`，Xray 行为是第一目标，电视长期后台后的网络恢复是第二目标；这两项尚未完成最终验收。
