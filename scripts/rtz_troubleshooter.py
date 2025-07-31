#!/usr/bin/env python3
"""
RTZ File Troubleshooter
=======================
Diagnose why RTZ files aren't being found for injection
"""

import csv
from pathlib import Path
from collections import defaultdict

def find_rtz_files():
    """Find all RTZ files in the romfs directory"""
    
    romfs_dir = Path("romfs")
    if not romfs_dir.exists():
        print("❌ romfs directory not found!")
        return []
    
    # Find all RTZ files
    rtz_files = list(romfs_dir.rglob("*.rtz"))
    
    print(f"📁 ROMFS RTZ FILE ANALYSIS")
    print("=" * 30)
    print(f"Total RTZ files found: {len(rtz_files)}")
    
    # Group by directory
    by_directory = defaultdict(list)
    for rtz_file in rtz_files:
        relative_path = rtz_file.relative_to(romfs_dir)
        directory = str(relative_path.parent)
        by_directory[directory].append(relative_path.name)
    
    # Show directory structure
    for directory, files in sorted(by_directory.items()):
        print(f"\n📂 {directory}/")
        for file in sorted(files)[:10]:  # Show first 10
            print(f"   {file}")
        if len(files) > 10:
            print(f"   ... and {len(files) - 10} more files")
    
    return rtz_files

def check_translation_file_references():
    """Check what RTZ files are referenced in translation file"""
    
    translation_files = list(Path("files/translations").glob("filtered_usable_*.csv"))
    if not translation_files:
        print("❌ No usable translation files found")
        return {}
    
    latest_file = max(translation_files, key=lambda x: x.stat().st_mtime)
    print(f"\n📋 TRANSLATION FILE ANALYSIS")
    print("=" * 35)
    print(f"File: {latest_file.name}")
    
    file_references = defaultdict(int)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                file_ref = row.get('file', '').strip()
                if file_ref:
                    file_references[file_ref] += 1
        
        print(f"\nReferenced RTZ files:")
        for file_ref, count in sorted(file_references.items()):
            print(f"   {file_ref} ({count} translations)")
            
            # Check if file actually exists
            actual_path = Path("romfs") / file_ref
            if actual_path.exists():
                print(f"      ✅ File exists")
            else:
                print(f"      ❌ File NOT found")
                
                # Try to find similar files
                file_name = Path(file_ref).name
                similar_files = list(Path("romfs").rglob(file_name))
                if similar_files:
                    print(f"      💡 Similar files found:")
                    for similar in similar_files[:3]:
                        rel_path = similar.relative_to(Path("romfs"))
                        print(f"         {rel_path}")
    
    except Exception as e:
        print(f"❌ Error reading translation file: {e}")
    
    return file_references

def find_actual_tutorial_files():
    """Find tutorial-related RTZ files that actually exist"""
    
    romfs_dir = Path("romfs")
    if not romfs_dir.exists():
        return []
    
    print(f"\n🎯 SEARCHING FOR TUTORIAL FILES")
    print("=" * 35)
    
    # Search for tutorial-related files
    tutorial_patterns = ["tuto", "tutorial", "help", "guide"]
    tutorial_files = []
    
    for pattern in tutorial_patterns:
        matches = list(romfs_dir.rglob(f"*{pattern}*"))
        for match in matches:
            if match.suffix.lower() == '.rtz':
                tutorial_files.append(match)
    
    if tutorial_files:
        print("Found tutorial-related RTZ files:")
        for tuto_file in sorted(tutorial_files):
            rel_path = tuto_file.relative_to(romfs_dir)
            size = tuto_file.stat().st_size
            print(f"   {rel_path} ({size:,} bytes)")
    else:
        print("❌ No tutorial RTZ files found with common patterns")
    
    return tutorial_files

def suggest_fixes():
    """Suggest ways to fix the RTZ injection issues"""
    
    print(f"\n🔧 SUGGESTED FIXES")
    print("=" * 20)
    
    print("1. UPDATE FILE PATHS IN TRANSLATION DATA:")
    print("   The translation file references paths that don't exist")
    print("   We need to map to actual RTZ file paths")
    
    print("\n2. SEARCH FOR TEXT IN EXISTING RTZ FILES:")
    print("   Instead of relying on file paths, search for the")
    print("   Japanese text across all RTZ files")
    
    print("\n3. VALIDATE RTZ EXTRACTION:")
    print("   Ensure the romfs extraction captured all files correctly")
    
    print("\n4. MANUAL RTZ FILE MAPPING:")
    print("   Create a mapping between expected and actual file paths")

def create_rtz_file_mapper():
    """Create a script to map translation files to actual RTZ files"""
    
    mapper_script = '''#!/usr/bin/env python3
"""
RTZ File Mapper
===============
Maps translation file references to actual RTZ files
"""

import csv
from pathlib import Path

def map_translation_files():
    """Map translation file references to actual RTZ files"""
    
    # Load translation data
    translation_files = list(Path("files/translations").glob("filtered_usable_*.csv"))
    if not translation_files:
        print("❌ No translation files found")
        return
    
    latest_file = max(translation_files, key=lambda x: x.stat().st_mtime)
    
    # Get all actual RTZ files
    romfs_dir = Path("romfs")
    actual_rtz_files = list(romfs_dir.rglob("*.rtz"))
    
    print(f"🔍 Mapping {latest_file.name} to actual RTZ files...")
    print(f"   Found {len(actual_rtz_files)} actual RTZ files")
    
    # Read translations and try to map files
    with open(latest_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        translations = list(reader)
    
    # Group by referenced file
    by_file = {}
    for trans in translations:
        file_ref = trans.get('file', '').strip()
        if file_ref:
            if file_ref not in by_file:
                by_file[file_ref] = []
            by_file[file_ref].append(trans)
    
    print(f"\\nFile mapping results:")
    for file_ref, trans_list in by_file.items():
        print(f"\\n📁 {file_ref} ({len(trans_list)} translations)")
        
        # Try to find actual file
        actual_path = Path("romfs") / file_ref
        if actual_path.exists():
            print(f"   ✅ Found: {actual_path}")
        else:
            # Try to find by filename only
            filename = Path(file_ref).name
            matches = [f for f in actual_rtz_files if f.name == filename]
            if matches:
                print(f"   💡 Possible matches:")
                for match in matches[:3]:
                    rel_path = match.relative_to(romfs_dir)
                    print(f"      {rel_path}")
            else:
                print(f"   ❌ No matches found for {filename}")

if __name__ == "__main__":
    map_translation_files()
'''
    
    mapper_file = Path("scripts/rtz_file_mapper.py")
    mapper_file.write_text(mapper_script)
    print(f"\n💾 Created RTZ file mapper: {mapper_file}")
    print(f"   Run with: python3 {mapper_file}")

def main():
    """Run complete RTZ troubleshooting"""
    
    print("🔍 RTZ INJECTION TROUBLESHOOTER")
    print("=" * 35)
    
    # Find actual RTZ files
    actual_rtz_files = find_rtz_files()
    
    # Check translation file references
    referenced_files = check_translation_file_references()
    
    # Find tutorial files
    tutorial_files = find_actual_tutorial_files()
    
    # Suggest fixes
    suggest_fixes()
    
    # Create mapper script
    create_rtz_file_mapper()
    
    print(f"\n📊 SUMMARY")
    print("=" * 10)
    print(f"Actual RTZ files: {len(actual_rtz_files)}")
    print(f"Referenced in translations: {len(referenced_files)}")
    print(f"Tutorial files found: {len(tutorial_files)}")
    
    if actual_rtz_files and not referenced_files:
        print(f"\n💡 RECOMMENDATION:")
        print(f"   The RTZ files exist but file paths in translations are wrong")
        print(f"   Run: python3 scripts/rtz_file_mapper.py")
        print(f"   This will help map correct file paths")

if __name__ == "__main__":
    main()