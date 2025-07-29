#!/usr/bin/env python3
"""
CF Vanguard Extraction Clarification Script
Helps identify what files you have vs what you need
"""

from pathlib import Path
import os

def scan_directory_structure():
    """Scan current directory to understand what files exist"""
    print("=" * 60)
    print("   CF VANGUARD FILE ANALYSIS")
    print("=" * 60)
    
    current_dir = Path(".")
    
    # Look for ROM file
    rom_files = list(current_dir.glob("*.3ds"))
    print("🎮 ROM FILES:")
    if rom_files:
        for rom in rom_files:
            size = rom.stat().st_size
            print(f"  ✅ {rom.name} ({size:,} bytes)")
    else:
        print("  ❌ No .3ds ROM file found")
    print()
    
    # Look for code.bin related files
    print("💾 CODE.BIN SEARCH:")
    code_candidates = []
    
    # Check obvious locations
    locations_to_check = [
        Path("files/code.bin"),
        Path("code.bin"),
        Path("extracted/code.bin"),
        Path("dump/code.bin"),
    ]
    
    for path in locations_to_check:
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ Found: {path} ({size:,} bytes)")
            code_candidates.append(path)
        else:
            print(f"  ❌ Not found: {path}")
    
    # Look for code.bin folder (user mentioned this)
    code_bin_folder = Path("code.bin")
    if code_bin_folder.exists() and code_bin_folder.is_dir():
        print(f"\n📁 FOUND 'code.bin' FOLDER:")
        files_in_folder = list(code_bin_folder.iterdir())
        print(f"  Contains {len(files_in_folder)} files:")
        for f in files_in_folder[:10]:  # Show first 10
            if f.is_file():
                size = f.stat().st_size
                print(f"    📄 {f.name} ({size:,} bytes)")
            else:
                print(f"    📁 {f.name}/ (directory)")
        if len(files_in_folder) > 10:
            print(f"    ... and {len(files_in_folder) - 10} more files")
    print()
    
    # Look for ExeFS dumps
    print("🔧 EXEFS DUMP SEARCH:")
    exefs_candidates = []
    
    # Common Citra dump locations
    possible_exefs_locations = [
        Path("dump"),
        Path("extracted"),
        Path("files"),
        current_dir,
    ]
    
    for location in possible_exefs_locations:
        if not location.exists():
            continue
            
        # Look for .code files
        code_files = list(location.rglob("*.code")) + list(location.rglob(".code"))
        for code_file in code_files:
            size = code_file.stat().st_size
            print(f"  ✅ Found .code file: {code_file} ({size:,} bytes)")
            exefs_candidates.append(code_file)
        
        # Look for directories that might contain ExeFS
        for subdir in location.iterdir():
            if subdir.is_dir() and any(keyword in subdir.name.lower() 
                                     for keyword in ['exefs', 'exe', 'code']):
                print(f"  📁 Potential ExeFS directory: {subdir}")
                files_in_dir = list(subdir.iterdir())
                for f in files_in_dir[:5]:
                    if f.is_file():
                        print(f"    📄 {f.name}")
    print()
    
    # Look for RomFS
    print("📁 ROMFS ANALYSIS:")
    romfs_locations = [Path("romfs"), Path("files/romfs"), Path("dump/romfs")]
    
    for location in romfs_locations:
        if location.exists():
            rtz_files = list(location.rglob("*.rtz"))
            bin_files = list(location.rglob("*.bin"))
            print(f"  ✅ RomFS found at: {location}")
            print(f"    📦 {len(rtz_files)} RTZ files")
            print(f"    📦 {len(bin_files)} BIN files")
            
            # Check for specific files we know about
            important_files = ["title/ci.rtz", "title/ti.rtz"]
            for imp_file in important_files:
                full_path = location / imp_file
                if full_path.exists():
                    print(f"    ✅ {imp_file}")
                else:
                    print(f"    ❌ {imp_file}")
        else:
            print(f"  ❌ Not found: {location}")
    print()
    
    # Summary and recommendations
    print("=" * 60)
    print("   ANALYSIS SUMMARY")
    print("=" * 60)
    
    if code_candidates:
        print("✅ CODE.BIN STATUS: Found existing files")
        print("   Recommendation: Validate these files")
        for candidate in code_candidates:
            print(f"   - {candidate}")
    elif exefs_candidates:
        print("⚠️ CODE.BIN STATUS: Found .code files that need renaming")
        print("   Recommendation: Copy .code file to files/code.bin")
        for candidate in exefs_candidates:
            print(f"   - Copy {candidate} → files/code.bin")
    else:
        print("❌ CODE.BIN STATUS: Need to extract from ROM")
        print("   Recommendation: Use Citra to dump ExeFS")
    
    print()
    
    # Check if user put RomFS files in wrong location
    if code_bin_folder.exists() and code_bin_folder.is_dir():
        files_in_code_folder = list(code_bin_folder.iterdir())
        rtz_in_code_folder = [f for f in files_in_code_folder if f.suffix == '.rtz']
        
        if rtz_in_code_folder:
            print("🔄 FOLDER CONFUSION DETECTED:")
            print(f"   You have {len(rtz_in_code_folder)} RTZ files in 'code.bin/' folder")
            print("   These are RomFS files, not the code.bin executable we need!")
            print()
            print("   RECOMMENDED FIXES:")
            print(f"   1. Move code.bin/ folder contents to romfs/")
            print(f"   2. Remove empty code.bin/ folder")
            print(f"   3. Extract actual code.bin executable from ROM using Citra")
    
    return code_candidates, exefs_candidates

def generate_fix_script(code_candidates, exefs_candidates):
    """Generate commands to fix the file structure"""
    print("=" * 60)
    print("   RECOMMENDED TERMINAL COMMANDS")
    print("=" * 60)
    
    # Create proper directory structure
    print("# 1. Create proper directory structure")
    print("mkdir -p files")
    print("mkdir -p romfs")
    print()
    
    # Fix RomFS location if needed
    code_bin_folder = Path("code.bin")
    if code_bin_folder.exists() and code_bin_folder.is_dir():
        print("# 2. Move RomFS files to correct location")
        print("mv code.bin/* romfs/")
        print("rmdir code.bin")
        print()
    
    # Handle code.bin extraction
    if exefs_candidates:
        print("# 3. Copy .code file to correct location")
        best_candidate = exefs_candidates[0]  # Use first found
        print(f"cp '{best_candidate}' files/code.bin")
    elif not code_candidates:
        print("# 3. Extract code.bin using Citra")
        print("# In Citra:")
        print("#   - Right-click game → 'Dump ExeFS'")
        print("#   - Find .code file in dump directory")
        print("#   - Copy to files/code.bin")
    
    print()
    print("# 4. Validate extraction")
    print("python3 validate_extraction.py")
    print()
    print("# 5. If validation passes, test injection")
    print("python3 scripts/inject_character_selection_test.py")

def main():
    print("Scanning project directory for CF Vanguard files...")
    print(f"Current directory: {Path.cwd()}")
    print()
    
    code_candidates, exefs_candidates = scan_directory_structure()
    generate_fix_script(code_candidates, exefs_candidates)

if __name__ == "__main__":
    main()