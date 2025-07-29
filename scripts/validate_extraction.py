#!/usr/bin/env python3
"""
Validate CF Vanguard extraction files for Phase 4 injection testing
"""

from pathlib import Path
import csv

def check_file_exists(path, description, required_size=None):
    """Check if file exists and has expected size"""
    if not path.exists():
        print(f"❌ Missing: {description} ({path})")
        return False
    
    size = path.stat().st_size
    print(f"✅ Found: {description} ({size:,} bytes)")
    
    if required_size and size != required_size:
        print(f"   ⚠️ Size mismatch: expected {required_size:,} bytes")
        return False
    
    return True

def validate_translation_csv(csv_path):
    """Validate translation CSV format"""
    if not csv_path.exists():
        print(f"❌ Translation CSV not found: {csv_path}")
        return False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
        
        print(f"✅ Translation CSV loaded: {len(rows)} translations")
        
        # Check required columns
        required_cols = ['pointer_offsets', 'pointer_value', 'separators', 'extract']
        for col in required_cols:
            if col not in reader.fieldnames:
                print(f"❌ Missing column: {col}")
                return False
        
        # Validate each row
        for i, row in enumerate(rows):
            try:
                # Test UTF-16LE encoding
                text = row['extract'].replace('†', '\n')
                utf16_bytes = text.encode('utf-16le')
                print(f"   Row {i+1}: {len(utf16_bytes)} UTF-16LE bytes - ✅")
            except Exception as e:
                print(f"   Row {i+1}: Encoding error - ❌ {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ CSV validation error: {e}")
        return False

def main():
    print("=" * 60)
    print("   CF VANGUARD EXTRACTION VALIDATION")
    print("=" * 60)
    
    # Check project structure
    files_dir = Path("files")
    scripts_dir = Path("scripts")
    
    if not files_dir.exists():
        print("❌ files/ directory not found")
        return False
    
    if not scripts_dir.exists():
        print("❌ scripts/ directory not found") 
        return False
    
    print("✅ Project structure validated")
    print()
    
    # Check source ROM
    print("📦 CHECKING SOURCE FILES:")
    rom_exists = check_file_exists(Path("cf_vanguard.3ds"), "Source ROM", 536870912)
    print()
    
    # Check extracted files
    print("🔧 CHECKING EXTRACTED FILES:")
    code_exists = check_file_exists(files_dir / "code.bin", "code.bin")
    exheader_exists = check_file_exists(files_dir / "exheader.bin", "exheader.bin")
    padded_exists = check_file_exists(files_dir / "full_padded.bin", "full_padded.bin")
    print()
    
    # Check translation files
    print("📝 CHECKING TRANSLATION FILES:")
    trans_basic = check_file_exists(files_dir / "character_selection_translated.csv", 
                                   "Character selection translations")
    if trans_basic:
        validate_translation_csv(files_dir / "character_selection_translated.csv")
    
    original_strings = check_file_exists(files_dir / "reduced" / "extracted_strings.csv",
                                       "Original extracted strings")
    pointers = check_file_exists(files_dir / "reduced" / "rodata_pointers.csv",
                                "Memory pointers")
    print()
    
    # Check scripts
    print("🐍 CHECKING SCRIPTS:")
    injection_script = check_file_exists(scripts_dir / "inject_character_selection_test.py",
                                       "Injection test script")
    pad_script = check_file_exists(scripts_dir / "pad_data.py", "Data padding script")
    patch_script = check_file_exists(scripts_dir / "patch_exheader.py", "ExHeader patch script")
    print()
    
    # Check romfs
    print("📁 CHECKING ROMFS:")
    romfs_dir = Path("romfs")
    if romfs_dir.exists():
        rtz_files = list(romfs_dir.rglob("*.rtz"))
        print(f"✅ RomFS extracted: {len(rtz_files)} RTZ files found")
    else:
        print("❌ RomFS not extracted")
    print()
    
    # Overall status
    print("=" * 60)
    print("   PHASE 4 READINESS ASSESSMENT")
    print("=" * 60)
    
    ready_for_injection = (code_exists and trans_basic and injection_script)
    ready_for_building = (ready_for_injection and exheader_exists and patch_script)
    
    if ready_for_injection:
        print("✅ READY FOR INJECTION TESTING!")
        print("   Next step: python3 scripts/inject_character_selection_test.py")
    else:
        print("⏳ INJECTION TESTING BLOCKED")
        if not code_exists:
            print("   Need: Extract code.bin from ROM")
        if not trans_basic:
            print("   Need: Character selection translations")
        if not injection_script:
            print("   Need: Injection test script")
    
    print()
    
    if ready_for_building:
        print("✅ READY FOR ROM BUILDING!")
        print("   All required files present for full ROM assembly")
    else:
        print("⏳ ROM BUILDING PREPARATION NEEDED")
        if not padded_exists:
            print("   Need: Create full_padded.bin")
        if not exheader_exists:
            print("   Need: Extract exheader.bin")
    
    print()
    print("🎯 IMMEDIATE PRIORITIES:")
    if not code_exists:
        print("1. Extract code.bin using Citra dump or extraction script")
    elif not padded_exists:
        print("1. Create full_padded.bin using pad_data.py")
    elif ready_for_injection:
        print("1. Run injection test with 4 character selection translations")
    else:
        print("1. Check file extraction status above")

if __name__ == "__main__":
    main()