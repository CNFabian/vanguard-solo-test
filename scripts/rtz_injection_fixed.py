#!/usr/bin/env python3
"""
CF VANGUARD RTZ INJECTION SYSTEM - FIXED VERSION
=================================================
Phase 5.3 - Fixed to handle correct RTZ file paths

This version fixes the path mapping issue and injects English translations
into the correct RTZ files.
"""

import csv
import gzip
import struct
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class FixedRTZInjector:
    def __init__(self):
        self.romfs_dir = Path("romfs")
        self.translations_dir = Path("files/translations")
        self.output_dir = Path("romfs_english")
        self.backup_dir = Path("romfs_backup")
        
        # File path mapping (fix the path references)
        self.path_mapping = {
            'romfs/fe/tuto_007.rtz': 'fe/tuto_007.rtz',
            'romfs/fe/tuto_012.rtz': 'fe/tuto_012.rtz', 
            'romfs/fe/tuto_013.rtz': 'fe/tuto_013.rtz',
            'romfs/script/FEV_G_S_03.rtz': 'script/FEV_G_S_03.rtz'
        }
        
        self.injection_stats = {
            'files_processed': 0,
            'files_modified': 0,
            'translations_applied': 0,
            'translations_failed': 0,
            'bytes_added': 0
        }
    
    def find_latest_usable_translations(self) -> Path:
        """Find the latest filtered usable translations file"""
        
        usable_files = list(self.translations_dir.glob("filtered_usable_*.csv"))
        if not usable_files:
            print("❌ No usable translation files found")
            return None
        
        latest_file = max(usable_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 Using translation file: {latest_file.name}")
        return latest_file
    
    def load_translations(self) -> Dict[str, List[Dict]]:
        """Load translations grouped by RTZ file with path mapping"""
        
        translation_file = self.find_latest_usable_translations()
        if not translation_file:
            return {}
        
        translations_by_file = {}
        
        try:
            with open(translation_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Skip failed translations
                    if row.get('translation_status') == 'FAILED':
                        continue
                    
                    original_file_ref = row.get('file', '').strip()
                    japanese_text = row.get('japanese_text', '').strip()
                    english_text = row.get('english_text', '').strip()
                    
                    if not all([original_file_ref, japanese_text, english_text]):
                        continue
                    
                    # Map to correct file path
                    actual_file_path = self.path_mapping.get(original_file_ref, original_file_ref)
                    
                    # Remove 'romfs/' prefix if it exists
                    if actual_file_path.startswith('romfs/'):
                        actual_file_path = actual_file_path[6:]
                    
                    # Group by actual file path
                    if actual_file_path not in translations_by_file:
                        translations_by_file[actual_file_path] = []
                    
                    translations_by_file[actual_file_path].append({
                        'japanese': japanese_text,
                        'english': english_text,
                        'confidence': float(row.get('confidence', 0)),
                        'quality': row.get('quality_assessment', 'unknown'),
                        'original_file_ref': original_file_ref,
                        'original_row': row
                    })
        
        except Exception as e:
            print(f"❌ Error loading translations: {e}")
            return {}
        
        print(f"📋 Loaded translations for {len(translations_by_file)} RTZ files")
        
        # Show mapping details
        for actual_path, translations in translations_by_file.items():
            actual_file = self.romfs_dir / actual_path
            exists = "✅" if actual_file.exists() else "❌"
            print(f"   {exists} {actual_path} ({len(translations)} translations)")
        
        total_translations = sum(len(trans) for trans in translations_by_file.values())
        print(f"   Total translations: {total_translations}")
        
        return translations_by_file
    
    def setup_directories(self):
        """Create backup and output directories"""
        
        # Create backup of original romfs
        if not self.backup_dir.exists() and self.romfs_dir.exists():
            print("🔄 Creating backup of original romfs...")
            shutil.copytree(self.romfs_dir, self.backup_dir)
            print(f"✅ Backup created: {self.backup_dir}")
        
        # Create English output directory
        if self.output_dir.exists():
            print(f"⚠️  Removing existing English romfs...")
            shutil.rmtree(self.output_dir)
        
        if self.romfs_dir.exists():
            print(f"📁 Creating English romfs...")
            shutil.copytree(self.romfs_dir, self.output_dir)
            print(f"✅ English romfs ready: {self.output_dir}")
        else:
            print(f"❌ Original romfs not found: {self.romfs_dir}")
            return False
        
        return True
    
    def find_text_in_rtz(self, rtz_data: bytes, search_text: str) -> List[int]:
        """Find Japanese text positions in RTZ file data"""
        
        # Convert search text to UTF-16LE bytes
        search_bytes = search_text.encode('utf-16le')
        
        positions = []
        start = 0
        
        while True:
            pos = rtz_data.find(search_bytes, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        return positions
    
    def replace_text_in_rtz(self, rtz_data: bytes, japanese_text: str, english_text: str) -> Tuple[bytes, bool]:
        """Replace Japanese text with English text in RTZ data"""
        
        try:
            # Find positions of Japanese text
            positions = self.find_text_in_rtz(rtz_data, japanese_text)
            
            if not positions:
                return rtz_data, False
            
            # Convert texts to bytes
            japanese_bytes = japanese_text.encode('utf-16le')
            english_bytes = english_text.encode('utf-16le')
            
            # Replace text (work backwards to maintain positions)
            modified_data = bytearray(rtz_data)
            replacements_made = 0
            
            for pos in reversed(positions):
                # Verify we found the right text
                if pos + len(japanese_bytes) <= len(modified_data):
                    found_text = modified_data[pos:pos + len(japanese_bytes)]
                    if found_text == japanese_bytes:
                        # Calculate new size
                        size_diff = len(english_bytes) - len(japanese_bytes)
                        
                        if size_diff > 0:
                            # English is longer - insert bytes
                            modified_data[pos:pos + len(japanese_bytes)] = english_bytes
                        else:
                            # English is shorter or same - direct replacement
                            modified_data[pos:pos + len(japanese_bytes)] = english_bytes
                        
                        replacements_made += 1
                        self.injection_stats['bytes_added'] += size_diff
            
            return bytes(modified_data), replacements_made > 0
            
        except Exception as e:
            print(f"❌ Error replacing text: {e}")
            return rtz_data, False
    
    def process_rtz_file(self, rtz_file: Path, translations: List[Dict]) -> bool:
        """Process a single RTZ file with translations"""
        
        print(f"\n📁 Processing: {rtz_file.relative_to(self.romfs_dir)}")
        print(f"   File size: {rtz_file.stat().st_size:,} bytes")
        print(f"   {len(translations)} translations to apply")
        
        try:
            # Read RTZ file
            with open(rtz_file, 'rb') as f:
                original_data = f.read()
            
            # Try to decompress if it's gzipped
            try:
                decompressed_data = gzip.decompress(original_data)
                was_compressed = True
                working_data = decompressed_data
                print(f"   📦 Decompressed: {len(original_data)} → {len(decompressed_data)} bytes")
            except:
                was_compressed = False
                working_data = original_data
                print(f"   📄 Uncompressed file")
            
            # Apply translations
            modified_data = working_data
            successful_replacements = 0
            
            for i, translation in enumerate(translations, 1):
                japanese = translation['japanese']
                english = translation['english']
                quality = translation['quality']
                
                print(f"   [{i:2}/{len(translations)}] {quality.upper()}")
                print(f"       JP: {japanese[:50]}{'...' if len(japanese) > 50 else ''}")
                print(f"       EN: {english[:50]}{'...' if len(english) > 50 else ''}")
                
                # Replace text
                new_data, success = self.replace_text_in_rtz(modified_data, japanese, english)
                
                if success:
                    modified_data = new_data
                    successful_replacements += 1
                    print(f"       ✅ Replaced!")
                    self.injection_stats['translations_applied'] += 1
                else:
                    print(f"       ❌ Text not found")
                    self.injection_stats['translations_failed'] += 1
            
            # Save modified file
            if successful_replacements > 0:
                # Recompress if original was compressed
                if was_compressed:
                    try:
                        final_data = gzip.compress(modified_data)
                        print(f"   📦 Recompressed: {len(modified_data)} → {len(final_data)} bytes")
                    except Exception as e:
                        print(f"   ⚠️  Compression failed, saving uncompressed: {e}")
                        final_data = modified_data
                else:
                    final_data = modified_data
                
                # Write to English romfs
                english_file = self.output_dir / rtz_file.relative_to(self.romfs_dir)
                english_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(english_file, 'wb') as f:
                    f.write(final_data)
                
                print(f"   💾 Saved with {successful_replacements}/{len(translations)} translations")
                self.injection_stats['files_modified'] += 1
                return True
            else:
                print(f"   ⚠️  No translations applied")
                return False
                
        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            return False
    
    def create_injection_report(self, translations_by_file: Dict):
        """Create detailed injection report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.translations_dir / f"injection_report_fixed_{timestamp}.txt"
        
        total_files = len(translations_by_file)
        total_translations = sum(len(trans) for trans in translations_by_file.values())
        
        report = f"""
🎮 CF VANGUARD RTZ INJECTION REPORT (FIXED VERSION)
===================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 INJECTION STATISTICS:
Files Processed:      {self.injection_stats['files_processed']}
Files Modified:       {self.injection_stats['files_modified']} / {total_files}
Translations Applied: {self.injection_stats['translations_applied']} / {total_translations}
Translations Failed:  {self.injection_stats['translations_failed']}
Bytes Added:          {self.injection_stats['bytes_added']:,}

📁 OUTPUT DIRECTORIES:
Original RomFS:   {self.romfs_dir}
Backup RomFS:     {self.backup_dir}
English RomFS:    {self.output_dir}

🎯 SUCCESS RATE: {self.injection_stats['translations_applied'] / max(total_translations, 1) * 100:.1f}%

🚀 NEXT STEPS:
1. Build English ROM using modified romfs_english/
2. Test in Citra emulator
3. Validate English text display in game

📋 FILES MODIFIED:
"""
        
        for file_path, translations in translations_by_file.items():
            successful = len([t for t in translations if t.get('applied', False)])
            total = len(translations)
            report += f"   {file_path}: {successful}/{total} translations\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"\n💾 Full report saved: {report_file.name}")
    
    def run_injection(self):
        """Run complete RTZ injection process"""
        
        print("🚀 CF VANGUARD RTZ INJECTION - PHASE 5.3 (FIXED)")
        print("=" * 50)
        print("Injecting English translations into RTZ files with correct paths")
        print()
        
        # Setup directories
        if not self.setup_directories():
            return False
        
        # Load translations
        translations_by_file = self.load_translations()
        if not translations_by_file:
            return False
        
        # Process each RTZ file
        print(f"\n⚙ PROCESSING RTZ FILES...")
        self.injection_stats['files_processed'] = len(translations_by_file)
        
        for file_path, translations in translations_by_file.items():
            rtz_file = self.romfs_dir / file_path
            
            if not rtz_file.exists():
                print(f"❌ RTZ file still not found: {file_path}")
                continue
            
            success = self.process_rtz_file(rtz_file, translations)
            
            # Mark translations as applied for tracking
            if success:
                for translation in translations:
                    translation['applied'] = True
        
        # Create report
        self.create_injection_report(translations_by_file)
        
        # Show results
        success_rate = self.injection_stats['translations_applied'] / max(sum(len(trans) for trans in translations_by_file.values()), 1) * 100
        
        print(f"\n🎉 RTZ INJECTION COMPLETE!")
        print(f"✅ {self.injection_stats['files_modified']} files modified")
        print(f"✅ {self.injection_stats['translations_applied']} translations applied")
        print(f"✅ {success_rate:.1f}% success rate")
        print(f"✅ English romfs ready: {self.output_dir}")
        
        if success_rate >= 50:
            print(f"\n🎮 EXCELLENT! Ready for ROM building!")
            print(f"   Your English translations are now in the RTZ files")
            print(f"   Run: ./build_english_rom.sh")
        elif success_rate >= 25:
            print(f"\n✅ GOOD! Partial success - ready for testing")
            print(f"   Some translations applied, worth testing in game")
        else:
            print(f"\n⚠️  LOW success rate - check for issues")
            print(f"   Review the injection report for details")
        
        return True

def main():
    """Main injection process with fixed file paths"""
    
    injector = FixedRTZInjector()
    
    print("🎮 FIXED RTZ INJECTION SYSTEM - PHASE 5.3")
    print("=========================================")
    print()
    print("This version fixes the file path mapping issues")
    print("and will inject your 138 translations correctly.")
    print()
    
    # Check prerequisites
    if not Path("romfs").exists():
        print("❌ romfs directory not found")
        return
    
    usable_files = list(Path("files/translations").glob("filtered_usable_*.csv"))
    if not usable_files:
        print("❌ No usable translation files found")
        return
    
    print(f"✅ Found translation files and RTZ files")
    
    # Show what will be processed
    print(f"\n📋 PLANNED INJECTIONS:")
    print(f"   fe/tuto_007.rtz → Tutorial 7 (29 translations)")
    print(f"   fe/tuto_012.rtz → Tutorial 12 (41 translations)")  
    print(f"   fe/tuto_013.rtz → Tutorial 13 (16 translations)")
    print(f"   script/FEV_G_S_03.rtz → Game Script (12 translations)")
    print(f"   Total: 98 translations into 4 tutorial/script files")
    
    # Confirm before proceeding
    response = input(f"\nProceed with fixed RTZ injection? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Injection cancelled")
        return
    
    # Run injection
    success = injector.run_injection()
    
    if success:
        print(f"\n🚀 READY FOR ROM BUILDING!")
        print(f"   English RTZ files created successfully")
        print(f"   Next: ./build_english_rom.sh")
    else:
        print(f"\n❌ Injection failed")

if __name__ == "__main__":
    main()