#!/usr/bin/env python3
"""
Fixed ExHeader Patch Script for CF Vanguard
Handles tutorial translation binary size updates
"""

import sys
import os
import struct
from pathlib import Path

def round_up_0x1000(val):
    """Round up to nearest 0x1000 boundary"""
    return (val + 0xFFF) & ~0xFFF

def patch_exheader(exheader_path, original_padded_path, new_patched_path, output_path):
    """
    Patch exheader to accommodate new binary size
    
    Args:
        exheader_path: Original exheader.bin
        original_padded_path: Original full_padded.bin 
        new_patched_path: New tutorial_patched_test.bin
        output_path: Output exheader_patched.bin
    """
    
    print("🔧 PATCHING EXHEADER FOR TUTORIAL TRANSLATIONS")
    print("=" * 55)
    
    # Get file sizes
    try:
        size_original = os.path.getsize(original_padded_path)
        size_patched = os.path.getsize(new_patched_path)
        delta = size_patched - size_original
        
        print(f"📊 Original padded: {size_original:,} bytes")
        print(f"📊 New patched:     {size_patched:,} bytes") 
        print(f"📊 Delta:           {delta:,} bytes")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return False
    
    # Calculate new data size
    # Base values from CF Vanguard
    base_data_size = 0x001BBF78 + 0x001E16FC  # data + bss from exheader
    raw_new_data_size = base_data_size + delta
    new_data_size = round_up_0x1000(raw_new_data_size)
    pages = new_data_size // 0x1000
    
    print(f"🧮 Base data size:  0x{base_data_size:08X}")
    print(f"📐 New data size:   0x{new_data_size:08X} (aligned)")
    print(f"📑 Pages:           {pages}")
    
    # Load and patch exheader
    try:
        ex = bytearray(Path(exheader_path).read_bytes())
        
        if len(ex) < 0x38:
            print(f"❌ ExHeader too small: {len(ex)} bytes")
            return False
        
        # Calculate new code size 
        code_size = round_up_0x1000(size_patched)
        
        # Patch exheader fields
        # Code text size (offset 0x00)
        ex[0x00:0x04] = struct.pack('<I', code_size)
        
        # Code ro size (offset 0x08) - set to 0 since we're expanding
        ex[0x08:0x0C] = struct.pack('<I', 0)
        
        # Code data size (offset 0x0C)
        ex[0x0C:0x10] = struct.pack('<I', new_data_size)
        
        # Physical region size in pages (offset 0x34)
        ex[0x34:0x38] = struct.pack('<I', pages)
        
        # Save patched exheader
        Path(output_path).write_bytes(ex)
        
        print(f"✅ ExHeader patched successfully!")
        print(f"📁 Output: {output_path}")
        print(f"📊 Code size:  0x{code_size:08X}")
        print(f"📊 Data size:  0x{new_data_size:08X}")
        print(f"📊 Pages:      {pages}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error patching exheader: {e}")
        return False

def main():
    if len(sys.argv) != 5:
        print("Usage: python3 patch_exheader_fixed.py <exheader.bin> <original_padded.bin> <new_patched.bin> <output_exheader.bin>")
        print()
        print("Example:")
        print("python3 patch_exheader_fixed.py files/exheader.bin files/full_padded.bin files/tutorial_patched_test.bin files/exheader_patched.bin")
        sys.exit(1)
    
    exheader_path = sys.argv[1]
    original_padded_path = sys.argv[2] 
    new_patched_path = sys.argv[3]
    output_path = sys.argv[4]
    
    success = patch_exheader(exheader_path, original_padded_path, new_patched_path, output_path)
    
    if success:
        print("\n🚀 READY FOR ROM BUILDING!")
        print("Next step:")
        print(f"./tools/makerom -f cci -o cf_vanguard_tutorial.3ds -code {new_patched_path} -exheader {output_path} -romfs romfs -rsf files/cf_vanguard.rsf")
    else:
        print("\n❌ ExHeader patching failed")
        sys.exit(1)

if __name__ == "__main__":
    main()