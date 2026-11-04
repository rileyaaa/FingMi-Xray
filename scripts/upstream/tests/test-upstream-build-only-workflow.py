#!/usr/bin/env python3
"""No publish, tag mutation, or main push is allowed in build-only mode."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
text = (ROOT / ".github/workflows/04-上游一键升级.yml").read_text(encoding="utf-8")
parts = text.split("      - name: ")


def section(name):
    item = next((p for p in parts if p.startswith(name + "\n")), None)
    assert item is not None, "Missing workflow step: " + name
    return item


assert re.search(r"(?m)^      build_without_publish:\n"
                 r"        description: [^\n]+\n"
                 r"        type: boolean\n"
                 r"        default: false$", text)
assert 'if [[ "$APPLY_TO_MAIN" == "true" && "$BUILD_WITHOUT_PUBLISH" == "true" ]]' in section(
    "离线检查一键升级工具")
assert 'BUILD_CANDIDATE: ${{ inputs.apply_to_main || inputs.build_without_publish }}' in section(
    "三方同步上游并重新生成适配代码")
assert 'if [[ "$BUILD_CANDIDATE" != "true" ]]' in section(
    "三方同步上游并重新生成适配代码")
build_gate = 'if: ${{ inputs.apply_to_main || inputs.build_without_publish }}'
for name in (
    "运行项目源码检查",
    "准备 Android SDK 36 与 37",
    "检查上游 Gradle 工具链",
    "检查项目固定签名配置",
    "重建并校验固定播放器及原生依赖",
    "准备公开播放器与 Xray 原生依赖",
    "对照已发布 v7 与 arm64 原生库验证 Xray",
    "Libass 前清理已验证的 Xray 临时文件",
    "重建并导入 Libass 兼容组件",
    "验证播放器组件启动",
    "验证 Xray 图片加载生命周期",
    "验证代理主机名崩溃回归",
    "编译升级后的 Leanback 源码",
    "打包 Android TV Release APK",
    "校验最终 APK 中的 MPEG-H",
    "校验最终 APK 中的原生运行库",
    "验证最终 Media3 DEX 依赖",
    "验证最终 Leanback Manifest 安全约束",
):
    assert build_gate in section(name), "Build-only skips a required check: " + name

shared = 'if: ${{ (inputs.apply_to_main || inputs.build_without_publish) && success() }}'
for name in ("记录构建输入与输出", "暂存已验证的双 ABI APK"):
    assert shared in section(name), "Build-only doesn't package verified outputs: " + name
asset = section("仅上传已验证 APK 供内部构建测试")
assert 'if: ${{ inputs.build_without_publish && !inputs.apply_to_main && success() }}' in asset
assert "release/*.apk" in asset and "BUILD_RESULT.txt" in asset
assert "if-no-files-found: error" in asset and "retention-days: 2" in asset
assert 'if: ${{ (inputs.apply_to_main || inputs.build_without_publish) && failure() }}' in section(
    "失败时上传构建报告")
assert 'if: ${{ inputs.apply_to_main && !inputs.build_without_publish }}' in section(
    "将验证通过的候选代码推送到 main")
assert 'if: ${{ inputs.apply_to_main && !inputs.build_without_publish && success() }}' in section(
    "发布已验证的 APK")
assert text.count("git push origin HEAD:refs/heads/main") == 1
assert text.count("python3 scripts/build/publish-current-release.py") == 1
assert text.index("暂存已验证的双 ABI APK") < text.index("仅上传已验证 APK 供内部构建测试") < text.index(
    "将验证通过的候选代码推送到 main")
assert 'APPLY_TO_MAIN: ${{ inputs.apply_to_main }}' in text
print("PASS: build-only validates full APK pipeline and uploads private artifacts without main push or Release")
