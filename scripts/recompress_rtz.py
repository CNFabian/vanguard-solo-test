#!/usr/bin/env python3
import sys
import gzip
import struct
from pathlib import Path

def recompress_rtz_from_patched(patched_path: Path):
    """
    Lit <fichier>_patched, le recomprime en GZIP (mtime=0 pour stabilité bit-à-bit),
    préfixe par 4 octets little-endian égal à la taille décompressée,
    et écrit <fichier>.rtz (en remplaçant _patched par .rtz).
    """
    raw = patched_path.read_bytes()
    gzip_blob = gzip.compress(raw, mtime=0)
    header = struct.pack('<I', len(raw))
    out_bytes = header + gzip_blob

    # On retire le suffixe "_patched" du nom
    stem = patched_path.stem
    if stem.endswith("_patched"):
        stem = stem[: -len("_patched")]
    out_path = patched_path.with_name(stem + ".rtz")
    out_path.write_bytes(out_bytes)
    print(f"✔ {patched_path.name} → {out_path.name} "
          f"(taille décompressée = {len(raw)} octets)")

def main():
    if len(sys.argv) != 2:
        print("Usage: python recompress_rtz_batch.py <dossier_ou_fichier_patched>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"❌ Introuvable : {target}")
        sys.exit(1)

    if target.is_dir():
        patched_files = list(target.glob('*_patched'))
        if not patched_files:
            print(f"⚠ Aucun fichier se terminant par _patched dans {target}")
            return
        for f in patched_files:
            recompress_rtz_from_patched(f)
    else:
        stem = target.stem
        if not stem.endswith("_patched"):
            print(f"⚠ Le fichier {target.name} ne se termine pas par _patched")
            sys.exit(1)
        recompress_rtz_from_patched(target)

if __name__ == "__main__":
    main()
