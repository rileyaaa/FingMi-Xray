#!/usr/bin/env python3
"""Build only traceable public Media3 modules; never populate TV app/libs."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from prepare_candidate import LOCK, guard_fork, verified_checkout, git


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api(path, scratch):
    with ZipFile(path) as z:
        jar = scratch/(path.name+".jar")
        jar.write_bytes(z.read("classes.jar"))
    with ZipFile(jar) as z:
        names = sorted(n[:-6].replace("/",".") for n in z.namelist()
                       if n.endswith(".class") and not n.endswith("BuildConfig.class")
                       and not n.endswith("/R.class") and "/R$" not in n)
    out = subprocess.check_output(["javap","-classpath",str(jar),"-public","-s",*names],text=True)
    return re.sub(r'(?m)^Compiled from "[^"]+"\n',"",out)


def official_database(scratch, rebuilt):
    base = "https://dl.google.com/dl/android/maven2/androidx/media3/media3-database/1.11.0/"
    paths = {}
    for ext in ("pom","aar"):
        name = "media3-database-1.11.0."+ext
        path = scratch/name
        with urllib.request.urlopen(base+name, timeout=90) as response:
            if not response.geturl().startswith(base):
                raise RuntimeError("Unexpected Maven redirect: "+response.geturl())
            path.write_bytes(response.read())
        paths[ext] = path
        print("OFFICIAL_GOOGLE_MAVEN",base+name,path.stat().st_size,digest(path),flush=True)
    xml = ET.parse(paths["pom"]).getroot()
    ns = {"m":"http://maven.apache.org/POM/4.0.0"}
    assert [xml.findtext("m:"+k,namespaces=ns) for k in ("groupId","artifactId","version")] == ["androidx.media3","media3-database","1.11.0"]
    same = api(paths["aar"],scratch) == api(rebuilt,scratch)
    print("OFFICIAL_DATABASE_PUBLIC_API_EQUAL",same,flush=True)
    if not same:
        raise RuntimeError("Published database API differs; no binary substitution")


def main():
    media = Path(sys.argv[1]).resolve()
    guard_fork()
    verified_checkout(media,"media")
    modules = LOCK["public_media_build"]
    for row in modules:
        assert git(media,"rev-parse","HEAD:"+row["path"]) == row["tree"], row["path"]
    # Use the source repository's exact toolchain/dependency catalog. No media
    # version changes, no borrowed native libraries and no app signing/build.
    cmd = ["bash","gradlew","--no-daemon","--continue","--max-workers=2",
           "-Dorg.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=768m"]
    cmd += [":"+row["module"]+":assembleRelease" for row in modules]
    result = subprocess.run(cmd,cwd=media,check=False)
    errors = []
    with tempfile.TemporaryDirectory(prefix="fingmi-media-public-") as tmp:
        scratch = Path(tmp)
        for row in modules:
            outputs = [p for p in (media/row["path"]).rglob(row["module"]+"-release.aar")
                       if "outputs" in p.parts]
            if len(outputs) != 1:
                errors.append(row["module"]+": missing or ambiguous release AAR")
                continue
            aar = outputs[0]
            with ZipFile(aar) as z:
                with ZipFile(BytesIO(z.read("classes.jar"))) as classes:
                    assert row["class"] in classes.namelist(), row["module"]
            print("REBUILT_PUBLIC_MEDIA",row["module"],row["tree"],aar.stat().st_size,digest(aar),flush=True)
            if row["module"] == "lib-database":
                try:
                    official_database(scratch,aar)
                except Exception as error:
                    errors.append("official database comparison: "+str(error))
            if row["module"] in ("lib-datasource-okhttp","lib-exoplayer-rtsp"):
                jar = scratch/(aar.name+".jar")
                with ZipFile(aar) as z:
                    jar.write_bytes(z.read("classes.jar"))
                clazz = row["class"][:-6].replace("/",".")
                out = subprocess.check_output(["javap","-classpath",str(jar),"-public","-s",clazz],text=True)
                required = "okhttp3.Call$Factory" if row["module"] == "lib-datasource-okhttp" else "setSocketFactory(javax.net.SocketFactory)"
                if required not in out:
                    errors.append(row["module"]+": missing required playback transport API")
                else:
                    print("PASS_MEDIA_TRANSPORT_API",row["module"],required,flush=True)
    if result.returncode or errors:
        raise SystemExit("PARTIAL PUBLIC MEDIA BUILD: gradle="+str(result.returncode)+"; "+"; ".join(errors))
    print("PASS selected public Media3 AAR rebuild and API audit; no complete 5.9 host/native compatibility claim")


if __name__ == "__main__":
    main()
