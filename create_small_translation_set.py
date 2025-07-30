#!/usr/bin/env python3
"""
Create smaller translation set for testing (2-3 entries only)
"""

import csv
from pathlib import Path

def create_small_translation_set():
    """Create 2-3 translation subset for safer testing"""
    
    # Define small translation set (2 entries only)
    small_translations = [
        {
            'pointer_offsets': '0x8D3F50',
            'pointer_value': '0x00949ED8', 
            'separators': '00 00',
            'extract': 'You can change your character\'s appearance and name',
            'context': 'Character customization main description'
        },
        {
            'pointer_offsets': '0x8D3F60', 
            'pointer_value': '0x00949E70',
            'separators': '00 00 00 00',
            'extract': 'Change StreetPass settings',
            'context': 'Communication settings menu'
        }
    ]
    
    # Save small translation set
    output_file = Path("files/character_selection_small.csv")
    
    with output_file.open('w', newline='', encoding='utf-8') as f:
        fieldnames = ['pointer_offsets', 'pointer_value', 'separators', 'extract', 'context']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(small_translations)
    
    print(f"✅ Small translation set created: {output_file}")
    print(f"📊 Translations: {len(small_translations)}")
    
    # Create injection script for small set
    injection_script = '''#!/usr/bin/env python3
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
        txt = row['extract'].replace('†', '\\n')
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
    
    print(f"\\n✅ SMALL INJECTION COMPLETE")
    print(f"📁 Output: {OUTPUT_BIN}")
    print(f"📊 Added: {len(data) - orig_len} bytes")

if __name__ == "__main__":
    main()
'''
    
    script_path = Path("inject_character_selection_small.py")
    script_path.write_text(injection_script)
    print(f"✅ Injection script created: {script_path}")
    
    return len(small_translations)

if __name__ == "__main__":
    count = create_small_translation_set()
    print(f"\\n🚀 NEXT STEPS:")
    print(f"1. python3 inject_character_selection_small.py")
    print(f"2. Build ROM with smaller binary")
    print(f"🎯 Expected: {count}/2 translations (minimal safe test)")