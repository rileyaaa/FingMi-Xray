#!/usr/bin/env python3
"""Compile the Xray transport/engine identity policy without Android dependencies."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "app/src/main/java/com/fingmi/integration/xray/XrayPlaybackRouting.java"
FACTORY = ROOT / "app/src/main/java/com/fongmi/android/tv/player/engine/PlayerEngineFactory.java"
MANAGER = ROOT / "app/src/main/java/com/fongmi/android/tv/player/PlayerManager.java"

if "XrayPlaybackRouting.canReuseEngine(" not in FACTORY.read_text(encoding="utf-8"):
    raise SystemExit("Engine factory must delegate Xray identity decisions")
if "XrayPlaybackRouting.activeProxy(" not in MANAGER.read_text(encoding="utf-8"):
    raise SystemExit("PlayerManager must use the shared active-transport policy")

HARNESS = """import com.fingmi.integration.xray.XrayPlaybackRouting;
public final class TestXrayPlaybackRouting {
    static void check(boolean state,String reason) {if(!state)throw new AssertionError(reason);}
    public static void main(String... args) {
        Object a = new String("same"), b = new String("same");
        check(a != b && a.equals(b), "must prove distinct equal-value identities");
        check(XrayPlaybackRouting.activeProxy(a, b) == b,"engine bound client wins");
        check(XrayPlaybackRouting.activeProxy(a, null) == a,"requested client fallback");
        check(XrayPlaybackRouting.activeProxy(null, null) == null,"upstream fallback only");
        check(!XrayPlaybackRouting.hasSession(null,null),"no session");
        check(XrayPlaybackRouting.hasSession(a,null),"requested session");
        check(XrayPlaybackRouting.hasSession(null,a),"engine still active at boundary");
        check(XrayPlaybackRouting.canReuseEngine(a,a,true,()->false,()->false),"reuse exact Exo identity");
        check(!XrayPlaybackRouting.canReuseEngine(a,b,true,()->true,()->false),"cannot reuse different endpoint");
        check(!XrayPlaybackRouting.canReuseEngine(a,null,true,()->true,()->false),"cannot reuse direct engine for Xray");
        check(!XrayPlaybackRouting.canReuseEngine(a,a,false,()->true,()->false),"cannot reuse MPV for Xray");
        check(!XrayPlaybackRouting.canReuseEngine(a,a,true,()->true,()->true),"changed native render config");
        check(XrayPlaybackRouting.canReuseEngine(null,null,false,()->true,()->false),"direct upstream MPV");
        check(XrayPlaybackRouting.canReuseEngine(null,null,true,()->true,()->false),"direct upstream Exo");
        check(!XrayPlaybackRouting.canReuseEngine(null,a,true,()->true,()->false),"direct must unbind Xray");
        check(!XrayPlaybackRouting.canReuseEngine(null,null,true,()->false,()->false),"follow upstream selection");
        check(!XrayPlaybackRouting.canReuseEngine(null,null,true,()->true,()->true),"upstream rebuild gate");
        check(!XrayPlaybackRouting.canReuseEngine(a,b,true,
            ()->{throw new AssertionError("upstream resolution on Xray path");},
            ()->{throw new AssertionError("rebuild on unmatched Xray");}), "lazy mismatch");
        check(!XrayPlaybackRouting.canReuseEngine(null,a,true,
            ()->{throw new AssertionError("upstream should not be selected for bound Xray");},
            ()->false), "lazy engine-to-direct");
        System.out.println("PASS Xray player identity: strict proxy references, Exo-only and direct upstream routing");
    }
}"""

with tempfile.TemporaryDirectory(prefix="xray-playback-routing-") as directory:
    path = Path(directory)
    source = path / "TestXrayPlaybackRouting.java"
    source.write_text(HARNESS, encoding="utf-8")
    subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8", "-d", str(path),
                    str(SOURCE), str(source)], check=True)
    subprocess.run(["java", "-cp", str(path), "TestXrayPlaybackRouting"], check=True)
