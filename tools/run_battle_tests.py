"""
Runs tests/copyability.test.js against the Showdown simulator bundled inside the Cobblemon jar.

Cobblemon ships its simulator as data/cobblemon/showdown.zip. This script locates the Cobblemon jar that Gradle
already downloaded (or takes a path), extracts the simulator into build/showdown and runs the Node test.

usage: python tools/run_battle_tests.py [path/to/Cobblemon-fabric-1.8.1+1.21.1.jar]
requires: Node.js 18+
"""
import glob
import io
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "showdown"


def find_jar():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    home = Path(os.environ.get("GRADLE_USER_HOME", Path.home() / ".gradle"))
    hits = glob.glob(str(home / "caches/modules-2/files-2.1/maven.modrinth/cobblemon/*/*/*.jar"))
    hits = [h for h in hits if not h.endswith("-sources.jar")]
    if not hits:
        sys.exit("Cobblemon jar not found in the Gradle cache; run './gradlew build' first or pass the jar path.")
    return Path(hits[0])


def main():
    jar = find_jar()
    print("Cobblemon jar:", jar)
    if not (OUT / "index.js").exists():
        with zipfile.ZipFile(jar) as z:
            data = z.read("data/cobblemon/showdown.zip")
        OUT.mkdir(parents=True, exist_ok=True)
        zipfile.ZipFile(io.BytesIO(data)).extractall(OUT)
    env = dict(os.environ, SHOWDOWN_DIR=str(OUT))
    sys.exit(subprocess.call(["node", str(ROOT / "tests" / "copyability.test.js")], env=env))


if __name__ == "__main__":
    main()
