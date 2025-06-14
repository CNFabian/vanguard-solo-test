#!/usr/bin/env python3
import sys
import gzip
import struct
from pathlib import Path

def decompress_rtz(path: Path):
    data = path.read_bytes()
    # 1) Lire la taille du bloc décompressé
    size, = struct.unpack('<I', data[:4])
    # 2) Extraire le flux GZIP
    gzip_blob = data[4:]
    # 3) Décompression GZIP
    try:
        raw = gzip.decompress(gzip_blob)
    except Exception as e:
        print(f"❌ Erreur GZIP sur {path.name} : {e}")
        return
    if len(raw) != size:
        print(f"⚠ Attention : taille décompressée ({len(raw)}) ≠ header ({size})")

    # 4) Écrire le .bin
    out = path.with_suffix('.bin')
    out.write_bytes(raw)
    print(f"✔ Décompressé → {out.name}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python rtz_tool.py <dossier_ou_fichier.rtz>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"❌ Introuvable : {target}")
        sys.exit(1)

    # Si c'est un dossier, on cherche tous les .rtz dedans
    if target.is_dir():
        rtz_files = list(target.glob('*.rtz'))
        if not rtz_files:
            print(f"⚠ Aucun fichier .rtz dans {target}")
            return
        for f in rtz_files:
            decompress_rtz(f)
    else:
        # Un seul fichier .rtz
        if target.suffix.lower() != '.rtz':
            print(f"⚠ Le fichier {target.name} n'a pas l'extension .rtz")
            sys.exit(1)
        decompress_rtz(target)

if __name__ == "__main__":
    main()
