# FongMi/TV 5.8.7 升级阻断审计（2026-11-02）

> **结论：尚未达到正式升级发布门槛。未启动 GitHub Actions、未合并 5.8.7 到 main、未编译/发布 5.8.7 APK。**
>
> 本文记录自动升级实战预检与后续适配范围；不是构建成功报告。

## 版本与操作边界

- 公开上游：`FongMi/TV` / `fongmi` / `8626650ebcbc0d028e16d859e826fcf439720f3a`；其 `app/build.gradle` 为 `versionName "5.8.7"` / `versionCode 587`。
- 本项目仍使用 5.6.3 源码：原始上游基线 `c616c0aa3613e87529791587a9f71b78c278c991`；现有 Release `v5.6.3-xray.1`，黄金参考 `v5.6.0-xray.5`。
- 基于三个 Git Tree 的纯 blob 比对：上游变更 810 个路径，其中 47 个 **当前需参与通用三方合并、且本 fork 同时存在与旧/新上游不同内容的路径**。这些是潜在文本冲突、接口冲突或语义迁移点，不可把数量误称为已执行 `git merge-file` 后的精确冲突个数。
- 这里只持续维护 Xray 与 Android TV 待机网络恢复（含最小 app/catvod 接线）。已批准的 `OkProxySelector.Policy` NPE 修复在 5.8.7 上游已有等价 `HttpUrl` 修复，采用上游实现，并保留本 fork 主机名、端口与代理重定向回归。

## 已发现并在升级工具中修复的确定性适配缺陷

1. **Home 请求取消接口变更**：5.8.7 `SiteViewModel` 无 `cancelResultRequest()`，但本 fork 恢复回调仍会调用。现改为由 `scripts/upstream/recovery_adapters.py` 对新版上游源码添加仅取消 `TaskType.RESULT` 的最小接线，避免直接搬回旧 `SiteViewModel`。
2. **Spider 清理接口变更**：5.8.7 `BaseLoader` 使用异步 `clear()/destroy()` 和集中式 `SpiderLoader`；原恢复模块需要 `clear(Runnable onComplete)` 完成时序。新增回调式薄适配，等待旧 Spider 清理完成后才进入网络稳定轮询，同时保留新版 Node/JS/Python 运行时模型。
3. **API/DNS 重建接口变更**：5.8.7 原生 `OkHttp` 不含本 fork 的 `resetApiNetworkForResume()`，原生 `OkDns` 也没有待机时 DoH 传输重建。新增只替换普通 API client 的失效入口、串行清理旧 HTTP/DoH 资源和 DoH resolver 代际快照；不清空代理规则、不直接销毁媒体专用 client。
4. **Glide 恢复入口缺失**：官方新 `ImgUtil` 没有 transient failure 清理与旧异步失败代际隔离，`OkGlideModule` 会固定旧 HTTP client。保留最小 `resetNetworkFailures()`、故障 epoch，以及逐请求获取当前 API client。
5. **发布打包基线**：版本转换只对上游 `versionCode × 1000 + fork revision` 操作；继续使用私有固定签名、保留仅本 fork 需要的 Xray/TV recovery module dependencies。修正了早期模板曾把旧版 `:chaquo` / `:quickjs` app 依赖强加到 5.8.7 的问题。
6. **版本与源码回归**：替换硬编码 5.6.3 的一部分 Actions 版本约束；测试新增新一代 SpiderLoader 恢复时序守卫，保留旧版本回归；`scripts/upstream/prepare_release.py` 会根据当前公开树更新被证明 upstream 原样的 blob guard。

## 仍需解决的 47 个上游/本 fork 重叠路径

这些路径覆盖 Xray 播放器会话、代理切换、字幕/DRM/Live 管道、TV 网络恢复与 UI 入口；必须确认升级后**所有 Xray 接线和播放器网络身份不丢失**。自动文本三方合并冲突不能用“直接选 ours”或“直接选 theirs”绕过。

- **播放与 Xray 接线**：`LiveActivity.java`、`VideoActivity.java`、`PlaybackActivity.java`、`LivePlaybackController.java`、`LivePlaybackHost.java`、`VodPlaybackController.java`、`VodPlaybackHost.java`、`VodPlaybackMedia.java`、`PlayerManager.java`、`PlayerEngineFactory.java`、`ExoMediaSourceFactory.java`、`ExoPlayerEngine.java`、`ExoPlayerSession.java`、`MpvPlayerEngine.java`、`MpvUtil.java`、`PlaybackService.java`、`PlayerEngineDialog.java`、`ChannelAdapter.java`。
- **网络/业务调用及脚本装载**：`LiveApi.java`、`SubtitleApi.java`、`JarLoader.java`、`JsLoader.java`、`PyLoader.java`、`EpgParser.java`、`LiveViewModel.java`、`VideoViewModel.java`、`ViewModelTaskRunner.java`、`Action.java`、`Download.java`。
- **界面/资源与应用边界**：`SettingActivity.java`、`PushActivity.java`（上游已删）、`DanmakuSearchDialog.java`、`SubtitleSearchDialog.java`、`Updater.java`、Leanback 与主 `AndroidManifest.xml`、`activity_setting.xml`、`view_control_live_action.xml`、`view_control_vod_action.xml`、三套 `strings.xml`、主页 `assets/index.html` / `assets/js/script.js`、`app/proguard-rules.pro`、`.gitignore`、`website/README.md`。

## 通用 Actions 的正确成功定义

`manual-upstream-sync.yml` 仍然只有 `workflow_dispatch`。在当前冲突适配未完成前，`apply_to_main` **默认关闭（仅预检）**，防止将尚未验收的模板当作正式自动升级工具。

后续只有以下全部满足，才允许把默认值恢复为完整升级模式：

1. 对目标公开上游的差异完成所有 47 个重叠路径的三方语义审查和必要 Xray / TV 接线迁移；未解决路径不覆盖。
2. 独立的 Xray、TV 息屏恢复、启动 Intent 不重放及空 Host/代理重定向回归通过；所有普通业务路径尽可能保持目标公开上游原样。
3. 完整重建当前 FongMi/media/native/Libass 所需输入，确认 5.8.7 实际 API / ABI 兼容，不以旧 5.6.3 兼容代码误装新媒体实现。
4. TV 的两份正式签名 APK 编译成功并核验 app version、混淆/DEX、native、Manifest、证书和 16KB alignment；再执行 Release 安全切换。
5. 正式发布后核对 `main`、tag、Release、两份 APK 的来源 SHA / digests，黄金版不可删除；真机的 Xray、播放交接、待机恢复仍须单独验收。

**目前实际完成的是：代码阅读、Git Tree 三向路径比对、升级工具及恢复接线修补和离线示例测试；没有通过新上游的完整合并、真实 GitHub Actions run 或新 APK 验证。**
