# FingMi-Xray｜FongMi 上游一键升级专用工具

此目录只保存 **FongMi/TV 上游同步、候选生成、适配验证**相关代码，不包含可直接发布的 APK 或固定二进制。专用工具集中于此，避免散布在项目运行模块和通用 `tests/` 中。

## 目录

- `*.py`：版本基线、上游同步、Media3 缺口预检、Xray 与 TV 恢复适配、候选验证。
- `baseline.json` / `fork_scope.json`：固定公开源码和已审核的 fork 差异分类。
- `templates/`：仅用于候选生成的 Xray Java、HTML 模板。
- `reference/`：从 5.8.7 试验保存的辅助 Java；不纳入 5.6.3 运行源码。
- `tests/`：一键升级专用离线测试、工作流 Bash 检查和候选 JVM 接口验证。

## 入口与边界

入口：`.github/workflows/manual-upstream-sync.yml`。另外三个日常构建、正式发布、失败续传工作流也保留在 `.github/workflows/`，**全部仅手动 workflow_dispatch**。本目录脚本不能自行触发发布、修改 GitHub Actions 或绕过源码审核。

默认一键升级模式仅预检；`build_without_publish=true` 构建验证后只保留短期私有 Artifact；`apply_to_main=true` 会在全部检查成功后更新 main 并发布，**在公开 Media3 播放器缺失问题未解决前禁止用于排障**。

共享文件不移动：`scripts/build/resolve-release-tag.py`、`tests/test-resolve-release-tag.py`、`tests/test-upstream-update-disabled.py` 同时服务于日常构建/发布。保留原路径是为了不破坏稳定版构建能力。四个工作流 YAML 同目录放置符合 GitHub Actions 的识别要求。

## 快速离线验证（不触发 GitHub Actions）

在仓库根目录执行：

```bash
python3 scripts/upstream/tests/test-upstream-layout.py
python3 scripts/upstream/tests/test-upstream-workflow-shell.py
python3 scripts/upstream/tests/test-upstream-sync.py
python3 scripts/upstream/tests/test-upstream-prepare.py
python3 tests/test-build-hygiene.py
```

注意：上述测试并不等价于 5.8.7 完整 Java 编译或 TV 真机验证。**当前稳定发布仍是 5.6.3**。下一次真正升级时，参照 `docs/DEVELOPMENT.md` 最新「5.6.3 主机名崩溃临时修补与下次上游升级策略」：目标上游如已改用 `Policy(HttpUrl)`，优先采用对应成套上游 `OkProxySelector` / `ProxyRedirectInterceptor` / 认证接口，移除旧版临时补丁，不把 5.6.3 逻辑强行带进新源码。
