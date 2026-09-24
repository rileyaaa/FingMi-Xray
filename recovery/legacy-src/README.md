# Recovered legacy Xray source

This directory is the behavior-faithful reconstruction target for the shipped `v5.6.0-xray.5` APK.

It is intentionally separate from the experimental `:xray` module.

Rules:

1. Recover shipped behavior first.
2. Preserve compatibility quirks, lifecycle rules, error text, timeouts and cleanup semantics.
3. Do not simplify code merely because a cleaner design exists.
4. Where JADX control flow is visibly damaged by R8/decompiler reconstruction, resolve only the smallest condition needed to make the surrounding behavior internally consistent, and document it.
5. Refactoring into `:xray` starts only after the legacy layer and upstream integration patch matrix are complete.

The class names in this directory are readable recovered names; original deleted local class names cannot always be proven because the release APK was R8-minified.
