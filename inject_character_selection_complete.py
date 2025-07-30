#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

BASE_ADDR = 0x0100000
INPUT_BIN = Path("files/full_padded.bin")
TRANSLATION_CSV = Path("files/character_selection_complete.csv")
OUTPUT_BIN = Path("files/full_patched_complete.bin")

try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

def parse_separators(sep_field: str) -> bytes:
    if sep_field.strip() == "(aucun)":
        return b""
    parts = sep_field.split()
    return bytes(int(p, 16) for p in parts)

def main():
    print("=" * 60)
    print("   COMPLETE CHARACTER TRANSLATION INJECTION")
    print("=" * 60)
    
    if not INPUT_BIN.exists():
        print(f"❌ Input file not found: {INPUT_BIN}")
        return False
    
    if not TRANSLATION_CSV.exists():
        print(f"❌ Translation file not found: {TRANSLATION_CSV}")
        return False
    
    data = bytearray(INPUT_BIN.read_bytes())
    orig_len = len(data)
    print(f"⚙ Loaded binary: {orig_len:,} bytes")
    
    with TRANSLATION_CSV.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        translations = list(reader)
    
    print(f"📝 Loaded {len(translations)} translations")
    
    cursor = orig_len
    successful_injections = 0
    
    for trans in translations:
        priority = trans.get('priority', '?')
        print(f"\n🔧 Processing translation {priority}/7:")
        print(f"   Context: {trans.get('context', 'Unknown')}")
        
        txt = trans['extract'].replace('†', '\n')
        utf16_bytes = txt.encode('utf-16le')
        sep_bytes = parse_separators(trans['separators'])
        block = utf16_bytes + sep_bytes
        
        new_file_off = cursor
        new_addr = BASE_ADDR + new_file_off
        
        # Update pointer
        addr_virt = int(trans['pointer_offsets'], 16)
        off = addr_virt - BASE_ADDR
        
        if 0 <= off < len(data) - 4:
            data[off:off + 4] = new_addr.to_bytes(4, 'little')
            data.extend(block)
            cursor += len(block)
            successful_injections += 1
            
            print(f"   ✅ Updated pointer @ {hex(addr_virt)} → {hex(new_addr)}")
            print(f"   📍 Added {len(block)} bytes")
        else:
            print(f"   ❌ Invalid pointer: {hex(addr_virt)}")
    
    OUTPUT_BIN.write_bytes(data)
    
    print(f"\n" + "=" * 60)
    print(f"✅ SUCCESS: {successful_injections}/{len(translations)} translations injected")
    print(f"📁 Output: {OUTPUT_BIN}")
    print(f"📊 Added: {len(data) - orig_len:,} bytes")
    
    return successful_injections == len(translations)

if __name__ == "__main__":
    main()
