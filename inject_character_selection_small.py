#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

BASE_ADDR = 0x0100000
INPUT_BIN = Path("files/full_padded.bin")
POINTER_CSV = Path("files/character_selection_small.csv")
OUTPUT_BIN = Path("files/full_patched_small.bin")

def parse_separators(sep_field: str) -> bytes:
    if sep_field.strip() == "(aucun)":
        return b""
    parts = sep_field.split()
    return bytes(int(p, 16) for p in parts)

def main():
    print("🔧 SMALL TRANSLATION INJECTION (2 entries)")
    
    data = bytearray(INPUT_BIN.read_bytes())
    orig_len = len(data)
    print(f"⚙ Loaded: {orig_len:,} bytes")

    with POINTER_CSV.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)

    cursor = orig_len
    
    for idx, row in enumerate(rows):
        txt = row['extract'].replace('†', '\n')
        utf16_bytes = txt.encode('utf-16le')
        sep_bytes = parse_separators(row['separators'])
        block = utf16_bytes + sep_bytes

        new_file_off = cursor
        new_addr = BASE_ADDR + new_file_off

        for off_s in row['pointer_offsets'].split(','):
            addr_virt = int(off_s.strip(), 16)
            off = addr_virt - BASE_ADDR
            
            if off < 0 or off + 4 > len(data):
                print(f"   ⚠️ Invalid pointer: {hex(addr_virt)}")
                continue
                
            data[off:off + 4] = new_addr.to_bytes(4, 'little')
            print(f"✅ Updated pointer @ {hex(addr_virt)} → {hex(new_addr)}")

        data.extend(block)
        cursor += len(block)
        print(f"📍 Added {len(block)} bytes ({row['context']})")

    OUTPUT_BIN.write_bytes(data)
    
    print(f"\n✅ SMALL INJECTION COMPLETE")
    print(f"📁 Output: {OUTPUT_BIN}")
    print(f"📊 Added: {len(data) - orig_len} bytes")

if __name__ == "__main__":
    main()
