"""Package the built navigation bundle with the upstream Android ARM runtime."""
import argparse
import hashlib
import struct
import zlib
from zipfile import ZipFile

parser = argparse.ArgumentParser()
parser.add_argument("official_apk")
parser.add_argument("output_apk")
args = parser.parse_args()
original = b"io.gh.reisxd.tizentube.cobalt"
variant = b"io.gh.dipesh.tizentube.navapp"
original_url = b"https://cdn.jsdelivr.net/npm/@foxreis/tizentube/dist/userScript.js?v="
bundle = b"https://cdn.jsdelivr.net/gh/dipespandey/tt-nav@a2a3ff5f2d/n.js?"
assert len(variant) == len(original)
# Cobalt appends a timestamp, so retain a query parameter of equal length.
bundle = bundle + b"v" * (len(original_url) - len(bundle) - 1) + b"="
with ZipFile(args.official_apk) as source, ZipFile(args.output_apk, "w") as target:
    for entry in source.infolist():
        if entry.filename.startswith("META-INF/") and entry.filename.endswith((".SF", ".RSA", ".DSA", ".MF")):
            continue
        data = source.read(entry)
        if entry.filename.endswith("/libchrobalt.so"):
            assert data.count(original_url) == 1
            data = data.replace(original_url, bundle)
        if entry.filename in ("AndroidManifest.xml", "resources.arsc") or entry.filename.endswith(".dex"):
            before = data
            for encoding in ("ascii", "utf-16le"):
                for old, new in ((original, variant), (b"TizenTube", b"TT Nav TV")):
                    if old == b"TizenTube" and entry.filename != "resources.arsc":
                        continue
                    data = data.replace(old.decode().encode(encoding), new.decode().encode(encoding))
            if entry.filename.endswith(".dex") and before != data:
                data = data[:12] + hashlib.sha1(data[32:]).digest() + data[32:]
                data = data[:8] + struct.pack("<I", zlib.adler32(data[12:])) + data[12:]
        target.writestr(entry, data)
