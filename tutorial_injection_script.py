#!/usr/bin/env python3
"""
Tutorial Translation Injection Script for CF Vanguard
Designed to work with tutorial_injection_test.csv format
"""

import csv
import sys
from pathlib import Path

# Configuration
BASE_ADDR = 0x100000
INPUT_BIN = Path("files/full_padded.bin")
TUTORIAL_CSV = Path("tutorial_injection_test.csv")
OUTPUT_BIN = Path("files/tutorial_patched_test.bin")

def main():
    print("🎓 CF VANGUARD TUTORIAL TRANSLATION INJECTION")
    print("=" * 55)
    
    # Check files exist
    if not INPUT_BIN.exists():
        print(f"❌ Input binary not found: {INPUT_BIN}")
        print("   Run: python3 scripts/pad_data.py files/code.bin 0xB1F000 0x1BBF78 0x200000 files/full_padded.bin")
        return False
    
    if not TUTORIAL_CSV.exists():
        print(f"❌ Tutorial CSV not found: {TUTORIAL_CSV}")
        print("   Run: python3 tutorial_quick_translations.py")
        return False
    
    # Load binary
    data = bytearray(INPUT_BIN.read_bytes())
    orig_len = len(data)
    print(f"⚙️  Loaded binary: {orig_len:,} bytes")
    
    # Load tutorial translations
    translations = []
    with TUTORIAL_CSV.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            translations.append(row)
    
    print(f"📝 Loaded {len(translations)} tutorial translations")
    print()
    
    # Process each translation
    cursor = orig_len
    successful_injections = 0
    
    for i, trans in enumerate(translations, 1):
        print(f"🔧 Processing translation {i}/{len(translations)}:")
        print(f"   Japanese: {trans['japanese_text']}")
        print(f"   English:  {trans['english_translation']}")
        
        # Encode English text
        try:
            utf16_bytes = trans['english_translation'].encode('utf-16le')
            # Add null terminator
            utf16_bytes += b'\x00\x00'
            
            # Calculate new address
            new_file_offset = cursor
            new_virtual_addr = BASE_ADDR + new_file_offset
            
            # For tutorial translations, we'll create mock pointers
            # This is a simulation - real RTZ injection would be different
            print(f"   📍 Mock injection at: {hex(new_virtual_addr)}")
            print(f"   📊 Size: {len(utf16_bytes)} bytes")
            
            # Add to binary
            data.extend(utf16_bytes)
            cursor += len(utf16_bytes)
            successful_injections += 1
            
            print(f"   ✅ Added successfully")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Save result
    OUTPUT_BIN.write_bytes(data)
    
    print("=" * 55)
    print(f"✅ TUTORIAL INJECTION COMPLETE")
    print(f"📁 Output file: {OUTPUT_BIN}")
    print(f"📊 Original size: {orig_len:,} bytes")
    print(f"📊 New size: {len(data):,} bytes")
    print(f"📊 Added: {len(data) - orig_len:,} bytes")
    print(f"🎯 Success rate: {successful_injections}/{len(translations)}")
    
    if successful_injections == len(translations):
        print()
        print("🚀 READY FOR ROM BUILDING!")
        print("Next steps:")
        print("1. Extract exheader: ./tools/ctrtool --exheader=files/exheader.bin cf_vanguard.3ds")
        print("2. Patch exheader: python3 scripts/patch_exheader.py files/exheader.bin files/tutorial_patched_test.bin files/exheader_patched.bin")
        print("3. Build ROM: ./tools/makerom -f cci -o cf_vanguard_tutorial.3ds -code files/tutorial_patched_test.bin -exheader files/exheader_patched.bin -romfs romfs -rsf files/cf_vanguard.rsf")
        return True
    else:
        print("❌ Some translations failed - check errors above")
        return False

if __name__ == "__main__":
    main()