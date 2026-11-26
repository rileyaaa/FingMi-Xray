#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage exact reference frame behavior for host javac.
Only Nullable/UnstableApi annotations (no runtime behavior used here) removed.
No fake Guava, Java frame DTOs or native methods.
"""
import hashlib, re, subprocess, sys
from pathlib import Path
REF="3382803f11e129af8676a0a775f98293b079797f"
PINS={
 "LibassNative.java":"a08a6b94b48f2582048dda07ae6ffebf8c801dc2",
 "LibassFrame.java":"a6504f47296d992556a2dd8ae2f71a35ff4ee7fa",
 "LibassImage.java":"921185b97e3a7e86717f55eafa02aa4ebca60a31",
}
def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*map(str,args)],text=True).strip()
def main():
    ref,dst=map(lambda p:Path(p).resolve(),sys.argv[1:])
    assert git(ref,"rev-parse","HEAD")==REF and not git(ref,"status","--porcelain")
    src=ref/"libraries/exoplayer/src/main/java/androidx/media3/exoplayer/libass"
    dst.mkdir(parents=True,exist_ok=False)
    for name,blob in PINS.items():
        p=src/name
        assert git(ref,"hash-object",p)==blob,name
        original=p.read_text()
        assert "Licensed under the Apache License, Version 2.0" in original
        text=original.replace("import androidx.annotation.Nullable;\n","").replace("import androidx.media3.common.util.UnstableApi;\n","")
        text=re.sub(r"(?m)^@UnstableApi\n","",text)
        text=text.replace("@Nullable ","")
        assert "androidx.annotation.Nullable" not in text and "UnstableApi" not in text
        (dst/name).write_text(text,encoding="utf-8")
        print("REFERENCE_HOST_ANNOTATIONS_ONLY",name,blob,hashlib.sha256((dst/name).read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
