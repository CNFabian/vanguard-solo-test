#!/usr/bin/env python3
"""
CF Vanguard Character Selection Injection Test - FIXED PATHS
Tests injection of 4 validated character selection translations
"""

import csv
import sys
from pathlib import Path

# --- Fixed Configurations for running from main directory ---
BASE_ADDR     = 0x0100000  # Virtual address base of code.bin
INPUT_BIN     = Path("files/full_padded.bin")  # Fixed path for main directory
POINTER_CSV   = Path("files/character_selection_translated.csv")  # Fixed path
OUTPUT_BIN    = Path("files/full_patched_test.bin")  # Fixed path

# --- Increase CSV field size limit ---
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

def parse_separators(sep_field: str) -> bytes:
    """Parse separator field into bytes"""
    if sep_field.strip() == "(aucun)":
        return b""
    parts = sep_field.split()
    return bytes(int(p, 16) for p in parts)

def main():
    print("=" * 60)
    print("   CF VANGUARD CHARACTER SELECTION INJECTION TEST")
    print("=" * 60)
    
    # Check if files exist
    if not INPUT_BIN.exists():
        print(f"❌ Input file not found: {INPUT_BIN}")
        print(f"   Current working directory: {Path.cwd()}")
        return False
    
    if not POINTER_CSV.exists():
        print(f"❌ Translation file not found: {POINTER_CSV}")
        return False
    
    # Load the binary
    data = bytearray(INPUT_BIN.read_bytes())
    orig_len = len(data)
    print(f"⚙ Loaded binary: {orig_len:,} bytes")
    
    # Load translations
    with POINTER_CSV.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)
    
    print(f"📝 Loaded {len(rows)} translations")
    
    # Process each translation
    cursor = orig_len  # Start adding at end of file
    
    for idx, row in enumerate(rows):
        print(f"\n🔧 Processing translation {idx + 1}/4:")
        
        # Prepare text (replace † with newlines)
        txt = row['extract'].replace('†', '\n')
        utf16_bytes = txt.encode('utf-16le')
        sep_bytes = parse_separators(row['separators'])
        block = utf16_bytes + sep_bytes
        
        print(f"   Original: {repr(row['extract'])}")
        print(f"   UTF-16LE: {len(utf16_bytes)} bytes")
        print(f"   Separators: {len(sep_bytes)} bytes")
        
        # Calculate new address
        new_file_off = cursor
        new_addr = BASE_ADDR + new_file_off
        
        # Update pointers
        pointer_count = 0
        for off_s in row['pointer_offsets'].split(','):
            addr_virt = int(off_s.strip(), 16)
            off = addr_virt - BASE_ADDR
            
            if off < 0 or off + 4 > len(data):
                print(f"   ⚠️ Invalid pointer: {hex(addr_virt)}")
                continue
                
            # Update pointer to new location
            data[off:off + 4] = new_addr.to_bytes(4, 'little')
            pointer_count += 1
            print(f"   ✅ Updated pointer @ {hex(addr_virt)} → {hex(new_addr)}")
        
        # Add new string data at end of file
        data.extend(block)
        cursor += len(block)
        
        print(f"   📍 Added {len(block)} bytes at offset {hex(new_file_off)}")
        print(f"   🔗 Updated {pointer_count} pointers")
    
    # Save result
    OUTPUT_BIN.write_bytes(data)
    
    print(f"\n" + "=" * 60)
    print("   INJECTION TEST COMPLETE! ✅")
    print("=" * 60)
    print(f"📁 Output: {OUTPUT_BIN}")
    print(f"📊 Original size: {orig_len:,} bytes")
    print(f"📊 New size: {len(data):,} bytes")
    print(f"📈 Added: {len(data) - orig_len:,} bytes")
    
    print(f"\n🎮 NEXT STEPS:")
    print(f"1. Extract exheader.bin using ctrtool")
    print(f"2. Patch exheader with new binary size")
    print(f"3. Build test ROM and validate in Citra")
    print(f"4. Test character selection sequence in game")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print(f"\n❌ Injection test failed!")
        sys.exit(1)
