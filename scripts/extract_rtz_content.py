#!/usr/bin/env python3
import sys
import re
import json
import requests
from pathlib import Path
from dataclasses import dataclass

# Pour nettoyer :
#  1) <|漢字|読み|> → 漢字
#  2) {$123456} et {$} → ""
CLEANER_KANA = re.compile(r'<\|([^|]+)\|[^|]*\|>')
CLEANER_TAGS = re.compile(r'\{\$\d+\}|\{\$\}')

@dataclass
class Segment:
    prefix_pos: int      # position du préfixe (5 octets)
    content_start: int   # début du contenu
    content_end: int     # fin du contenu
    raw: str             # chaîne brute UTF-16LE
    clean: str           # texte nettoyé
    translation: str = ""# texte traduit

def clean_text(s: str) -> str:
    # 1) <|漢字|読み|> → 漢字
    s = CLEANER_KANA.sub(r'\1', s)
    # 2) supprimer {$123456} et {$}
    s = CLEANER_TAGS.sub('', s)
    return s.strip()

def translate(text: str) -> str:
    # Préserver la position du/des newline(s)
    line_positions = []
    total_len = len(text)
    for i, ch in enumerate(text):
        if ch == "\n":
            line_positions.append(i / total_len)
    # on traduit sur une seule ligne
    single_line = text.replace("\n", " ")
    # appel LibreTranslate
    resp = requests.post(
        "http://localhost:5001/translate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "q": single_line,
            "source": "ja",
            "target": "en",
            "format": "text"
        })
    )
    resp.raise_for_status()
    translated = resp.json().get("translatedText", "")
    # réinsertion approximative des newline
    if line_positions:
        chars = list(translated)
        for pct in line_positions:
            pos = int(pct * len(chars))
            # reculer jusqu'à un espace ou début
            while pos > 0 and chars[pos] not in (" ", "-", "\u2014"):
                pos -= 1
            if pos > 0:
                chars[pos] = "\n"
        translated = "".join(chars)
    return translated

def extract_segments(data: bytes, start_offset: int) -> list[Segment]:
    pos = start_offset
    segments: list[Segment] = []
    idx = 1
    print("== Extraction des segments ==")
    while pos + 5 <= len(data):
        # arrêt sur terminator
        if data[pos:pos+5] == b'\xFF\xFF\xFF\xFF\x00':
            print(f"Reached terminator at 0x{pos:X}, stopping.\n")
            break

        L = data[pos+4]           # nombre d'unités UTF-16
        byte_len = L * 2
        cs, ce = pos+5, pos+5+byte_len
        if ce > len(data):
            print(f"⚠ Segment [{idx}] hors limites, aborting.\n")
            break

        raw_bytes = data[cs:ce]
        raw_str = raw_bytes.decode("utf-16-le", errors="ignore")
        clean = clean_text(raw_str)

        print(f"[{idx}] prefix@0x{pos:X}: L={L} → {byte_len} bytes")
        print(f"    → ORIGINAL: {repr(raw_str)}")
        print(f"    → CLEAN:    {repr(clean)}\n")

        segments.append(Segment(pos, cs, ce, raw_str, clean))
        pos = ce
        idx += 1

    print(f"Total segments extraits: {len(segments)}\n")
    return segments

def patch_file(input_file: str, start_offset: int):
    buf = bytearray(Path(input_file).read_bytes())
    segments = extract_segments(buf, start_offset)

    print("== Traduction des segments ==")
    for i, seg in enumerate(segments, 1):
        seg.translation = translate(seg.clean)
        print(f"[{i}] CLEAN:       '{seg.clean}'")
        print(f"    → TRANSLATED: '{seg.translation}'\n")

    print("== Réinsertion (du dernier au premier) ==")
    for seg in reversed(segments):
        orig_len = seg.content_end - seg.content_start
        new_raw = seg.translation.encode("utf-16-le")
        # on pad ou on tronque
        if len(new_raw) < orig_len:
            pad = (orig_len - len(new_raw)) // 2
            new_raw += b"\x20\x00" * pad
        else:
            new_raw = new_raw[:orig_len]
        # mise à jour du 5ᵉ octet
        new_units = len(new_raw) // 2
        buf[seg.prefix_pos + 4] = new_units & 0xFF
        # remplacement
        buf[seg.content_start:seg.content_end] = new_raw

    out_path = Path(input_file).with_name(Path(input_file).stem + "_patched")
    Path(out_path).write_bytes(buf)
    print(f"✔ Fichier patché écrit sous {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python patch_translate_fixedsize.py <input> <start_offset>")
        sys.exit(1)
    patch_file(sys.argv[1], int(sys.argv[2], 0))
