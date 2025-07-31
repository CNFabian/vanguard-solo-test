#!/usr/bin/env python3
import struct
import os

print("🔍 Extracting RomFS from CF Vanguard ROM...")

rom_file = "cf_vanguard.3ds"
if not os.path.exists(rom_file):
    print(f"❌ {rom_file} not found!")
    exit(1)

with open(rom_file, 'rb') as f:
    # Read NCSD header
    f.seek(0x100)
    ncsd_magic = f.read(4)
    
    if ncsd_magic != b'NCSD':
        print("❌ Invalid NCSD magic")
        exit(1)
    
    # Get partition table
    f.seek(0x120)
    partitions = []
    for i in range(8):
        offset = struct.unpack('<I', f.read(4))[0] * 0x200
        size = struct.unpack('<I', f.read(4))[0] * 0x200
        if offset and size:
            partitions.append((offset, size))
    
    print(f"Found {len(partitions)} partitions")
    
    # First partition is usually the game
    if partitions:
        game_offset, game_size = partitions[0]
        print(f"Game partition at 0x{game_offset:X}")
        
        # Read NCCH header
        f.seek(game_offset + 0x100)
        ncch_magic = f.read(4)
        
        if ncch_magic != b'NCCH':
            print("❌ Invalid NCCH magic")
            exit(1)
            
        # Get RomFS offset and size
        f.seek(game_offset + 0x1C0)
        romfs_offset = struct.unpack('<I', f.read(4))[0] * 0x200
        romfs_size = struct.unpack('<I', f.read(4))[0] * 0x200
        
        if romfs_offset and romfs_size:
            print(f"RomFS found at 0x{romfs_offset:X}, size: {romfs_size:,} bytes")
            
            # Extract RomFS
            f.seek(game_offset + romfs_offset)
            romfs_data = f.read(romfs_size)
            
            # Save RomFS
            with open('romfs.bin', 'wb') as out:
                out.write(romfs_data)
            
            print("✅ Successfully extracted romfs.bin")
        else:
            print("❌ No RomFS found in NCCH")
    else:
        print("❌ No partitions found")
