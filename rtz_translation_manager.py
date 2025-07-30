#!/usr/bin/env python3
"""
RTZ TRANSLATION MANAGER - GOOGLE SHEETS INTEGRATION
====================================================
CF VANGUARD STRIDE TO VICTORY - FANMADE TRANSLATION PROJECT

Easy translation workflow:
1. Export clean text to Google Sheets format
2. Edit translations in spreadsheet
3. Import completed translations back to project
4. Generate injection-ready files
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import datetime

class RTZTranslationManager:
    def __init__(self):
        self.project_root = Path(".")
        self.files_dir = Path("files")
        self.translations_dir = self.files_dir / "translations"
        self.translations_dir.mkdir(exist_ok=True)
        
        # Translation status tracking
        self.status_file = self.translations_dir / "translation_status.json"
        
    def export_for_google_sheets(self, max_entries: int = 50) -> str:
        """
        Export clean Japanese text to Google Sheets-friendly CSV format
        Includes context, priorities, and easy editing columns
        """
        print("📊 EXPORTING TEXT FOR GOOGLE SHEETS TRANSLATION")
        print("=" * 50)
        
        # Load the refined RTZ text
        rtz_csv = self.files_dir / "rtz_game_text_refined.csv"
        if not rtz_csv.exists():
            print(f"❌ Source file not found: {rtz_csv}")
            return ""
        
        # Read and filter entries
        with open(rtz_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            entries = list(reader)
        
        # Sort by quality and confidence
        quality_entries = []
        for entry in entries:
            if self.is_good_for_translation(entry['japanese_text'], float(entry['confidence'])):
                quality_entries.append({
                    'file': Path(entry['file']).name,
                    'japanese_text': self.clean_japanese_text(entry['japanese_text']),
                    'confidence': float(entry['confidence']),
                    'priority': entry['priority'],
                    'translation_difficulty': self.assess_difficulty(entry['japanese_text']),
                    'game_context': self.identify_context(entry['japanese_text'], entry['file']),
                    'offset': entry['offset']
                })
        
        # Sort by priority and difficulty
        quality_entries.sort(key=lambda x: (
            x['priority'] == 'HIGH',
            x['confidence'],
            -x['translation_difficulty']
        ), reverse=True)
        
        # Take top entries
        export_entries = quality_entries[:max_entries]
        
        # Create Google Sheets friendly export
        export_file = self.translations_dir / f"vanguard_translation_batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        
        with open(export_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'ID', 'File', 'Game_Context', 'Priority', 'Difficulty',
                'Japanese_Text', 'English_Translation', 'Translation_Notes',
                'Status', 'Confidence', 'Offset'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, entry in enumerate(export_entries, 1):
                writer.writerow({
                    'ID': f'VG_T_{i:03d}',
                    'File': entry['file'],
                    'Game_Context': entry['game_context'],
                    'Priority': entry['priority'],
                    'Difficulty': self.difficulty_to_text(entry['translation_difficulty']),
                    'Japanese_Text': entry['japanese_text'],
                    'English_Translation': '',  # To be filled
                    'Translation_Notes': '',    # For translator notes
                    'Status': 'PENDING',
                    'Confidence': f"{entry['confidence']:.2f}",
                    'Offset': entry['offset']
                })
        
        print(f"✅ Exported {len(export_entries)} entries to: {export_file}")
        print(f"📋 GOOGLE SHEETS WORKFLOW:")
        print(f"   1. Upload {export_file.name} to Google Sheets")
        print(f"   2. Share sheet for collaborative translation")
        print(f"   3. Fill 'English_Translation' column")
        print(f"   4. Add notes in 'Translation_Notes' column")
        print(f"   5. Set 'Status' to COMPLETED when done")
        print(f"   6. Download as CSV and import back")
        
        # Create translation guide
        self.create_translation_guide()
        
        return str(export_file)
    
    def clean_japanese_text(self, text: str) -> str:
        """Clean up Japanese text for easier translation"""
        # Remove obvious corruption while preserving game formatting
        text = re.sub(r'[␀㌀㘀紀꼀옰ꌰꬰ鈰ର篿圀昰缰洰델Ỷ]+', '', text)
        text = re.sub(r'[\uffff\x00-\x1f]+', '', text)
        
        # Clean up but preserve important formatting
        text = text.strip()
        
        # Remove trailing corruption indicators
        corruption_endings = ['쓁', '鶀', '￿']
        for ending in corruption_endings:
            if text.endswith(ending):
                text = text.rstrip(ending)
        
        return text
    
    def is_good_for_translation(self, text: str, confidence: float) -> bool:
        """Check if text is suitable for translation workflow"""
        # Must have reasonable confidence
        if confidence < 0.75:
            return False
            
        # Clean the text first
        clean_text = self.clean_japanese_text(text)
        
        # Must have actual Japanese content
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', clean_text))
        if japanese_chars < 2:
            return False
            
        # Must not be too corrupted
        if len(clean_text.strip()) < 3:
            return False
            
        # Must not be mostly symbols
        symbol_ratio = len(re.findall(r'[<>|{}\$\d]', clean_text)) / len(clean_text) if clean_text else 0
        if symbol_ratio > 0.7:
            return False
            
        return True
    
    def assess_difficulty(self, text: str) -> float:
        """Assess translation difficulty (0.0 = easy, 1.0 = hard)"""
        difficulty = 0.0
        
        # Base difficulty
        difficulty += 0.2
        
        # Longer text is harder
        if len(text) > 50:
            difficulty += 0.2
        elif len(text) > 100:
            difficulty += 0.4
            
        # Complex formatting increases difficulty
        if '<|' in text and '|>' in text:
            difficulty += 0.1  # Kanji reading aids
        if '{$' in text:
            difficulty += 0.1  # Color formatting
        if text.count('\n') > 1:
            difficulty += 0.2  # Multi-line
            
        # Game-specific terms reduce difficulty (more predictable)
        game_terms = ['ヴァンガード', 'アタック', 'ガード', 'パワー', 'カード']
        for term in game_terms:
            if term in text:
                difficulty -= 0.1
                
        return max(0.0, min(1.0, difficulty))
    
    def difficulty_to_text(self, difficulty: float) -> str:
        """Convert difficulty score to readable text"""
        if difficulty < 0.3:
            return "EASY"
        elif difficulty < 0.6:
            return "MEDIUM"
        else:
            return "HARD"
    
    def identify_context(self, text: str, file_path: str) -> str:
        """Identify the game context for better translation"""
        file_name = Path(file_path).name.lower()
        
        # File-based context
        if 'tuto' in file_name:
            return "TUTORIAL"
        elif 'title' in file_name:
            return "TITLE_SCREEN"
        elif 'menu' in file_name:
            return "MENU"
        elif 'char' in file_name:
            return "CHARACTER"
        elif 'fight' in file_name or 'battle' in file_name:
            return "BATTLE"
        elif 'card' in file_name:
            return "CARD_INFO"
        
        # Content-based context
        if 'アタック' in text and 'ガード' in text:
            return "COMBAT_TUTORIAL"
        elif 'ヴァンガード' in text:
            return "VANGUARD_MECHANICS"
        elif 'カード' in text:
            return "CARD_GAME"
        elif '？' in text or '！' in text:
            return "DIALOG"
        
        return "GENERAL"
    
    def create_translation_guide(self):
        """Create a translation guide for Google Sheets users"""
        guide_file = self.translations_dir / "TRANSLATION_GUIDE.md"
        
        guide_content = """# 🎮 CF VANGUARD TRANSLATION GUIDE

## 📋 HOW TO USE GOOGLE SHEETS FOR TRANSLATION

### STEP 1: Setup
1. Upload the CSV file to Google Sheets
2. Share with translation team members
3. Use different colors for different translators

### STEP 2: Translation Rules
- **Preserve formatting**: Keep `<|kanji|reading|>` exactly as is
- **Keep color codes**: Maintain `{$336600}` format
- **Preserve line breaks**: Use Ctrl+Enter in cells for line breaks
- **Stay concise**: Game text should be short and clear

### STEP 3: Key Terms Dictionary
| Japanese | English | Context |
|----------|---------|---------|
| ヴァンガード | Vanguard | Core card type |
| アタック | Attack | Combat action |
| ガード | Guard | Defense action |
| パワー | Power | Card statistic |
| ノーガード | No Guard | Cannot defend |
| カード | Card | Game piece |
| デッキ | Deck | Card collection |
| ターン | Turn | Game phase |

### STEP 4: Context Guidelines
- **TUTORIAL**: Clear, instructional language
- **DIALOG**: Natural conversation style
- **COMBAT**: Action-oriented, concise
- **MENU**: Short button labels
- **CARD_INFO**: Technical descriptions

### STEP 5: Quality Check
- Read translation aloud - does it sound natural?
- Does it fit the game context?
- Is it clear to a new player?
- Are game terms consistent?

### STEP 6: Status Tracking
- Set Status to 'IN_PROGRESS' when starting
- Set Status to 'COMPLETED' when finished
- Set Status to 'NEEDS_REVIEW' if unsure
- Add notes for complex translations

## 🎯 PRIORITY ORDER
1. HIGH priority entries first
2. EASY difficulty before HARD
3. TUTORIAL context is most important
4. DIALOG second priority

## ❓ HELP
If stuck on a translation:
1. Add note in Translation_Notes column
2. Mark Status as 'NEEDS_REVIEW'
3. Continue with other entries
"""
        
        guide_file.write_text(guide_content, encoding='utf-8')
        print(f"📖 Translation guide created: {guide_file}")
    
    def import_from_google_sheets(self, csv_file_path: str) -> Dict:
        """
        Import completed translations from Google Sheets CSV
        Process and prepare for RTZ injection
        """
        print("📥 IMPORTING TRANSLATIONS FROM GOOGLE SHEETS")
        print("=" * 45)
        
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            print(f"❌ Import file not found: {csv_path}")
            return {}
        
        # Read completed translations
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported_entries = list(reader)
        
        # Process translations
        completed_translations = []
        pending_translations = []
        
        for entry in imported_entries:
            if entry['Status'] == 'COMPLETED' and entry['English_Translation'].strip():
                completed_translations.append({
                    'id': entry['ID'],
                    'file': entry['File'],
                    'japanese_text': entry['Japanese_Text'],
                    'english_text': entry['English_Translation'].strip(),
                    'context': entry['Game_Context'],
                    'notes': entry['Translation_Notes'],
                    'offset': entry['Offset'],
                    'confidence': float(entry['Confidence'])
                })
            else:
                pending_translations.append(entry)
        
        print(f"✅ Completed translations: {len(completed_translations)}")
        print(f"⏳ Pending translations: {len(pending_translations)}")
        
        if completed_translations:
            # Save completed translations for injection
            injection_file = self.translations_dir / f"injection_ready_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json"
            
            with open(injection_file, 'w', encoding='utf-8') as f:
                json.dump(completed_translations, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Injection-ready file saved: {injection_file}")
            
            # Show preview of translations
            self.preview_translations(completed_translations[:5])
            
            # Create RTZ injection script
            self.create_injection_script(str(injection_file))
        
        return {
            'completed': len(completed_translations),
            'pending': len(pending_translations),
            'injection_file': str(injection_file) if completed_translations else None
        }
    
    def preview_translations(self, translations: List[Dict]):
        """Show preview of completed translations"""
        print(f"\n🌟 TRANSLATION PREVIEW:")
        print("-" * 60)
        
        for i, trans in enumerate(translations, 1):
            print(f"{i}. Context: {trans['context']}")
            print(f"   Japanese: {trans['japanese_text']}")
            print(f"   English:  {trans['english_text']}")
            if trans['notes']:
                print(f"   Notes:    {trans['notes']}")
            print()
    
    def create_injection_script(self, injection_file: str):
        """Create RTZ injection script for completed translations"""
        script_content = f'''#!/usr/bin/env python3
"""
AUTO-GENERATED RTZ INJECTION SCRIPT
===================================
Generated from Google Sheets translations
Injection file: {Path(injection_file).name}
"""

import json
import gzip
import struct
from pathlib import Path

def inject_translations():
    """Inject completed translations into RTZ files"""
    
    print("🚀 INJECTING TRANSLATIONS INTO RTZ FILES")
    print("=" * 40)
    
    # Load translations
    with open("{injection_file}", 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    print(f"📋 Loading {{len(translations)}} translations...")
    
    # Group by file for efficient processing
    by_file = {{}}
    for trans in translations:
        file_path = Path("romfs") / trans['file']
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(trans)
    
    print(f"🎯 Processing {{len(by_file)}} RTZ files...")
    
    for rtz_file, file_translations in by_file.items():
        print(f"\\n📁 Processing: {{rtz_file.name}}")
        print(f"   {{len(file_translations)}} translations to inject")
        
        # TODO: Implement RTZ injection logic
        # This will be completed in Phase 5.3
        
        for trans in file_translations:
            print(f"   • {{trans['japanese_text'][:30]}}... → {{trans['english_text'][:30]}}...")
    
    print(f"\\n✅ Translation injection prepared!")
    print(f"🔧 RTZ injection logic will be implemented in Phase 5.3")

if __name__ == "__main__":
    inject_translations()
'''
        
        script_file = self.translations_dir / "inject_completed_translations.py"
        script_file.write_text(script_content)
        script_file.chmod(0o755)
        
        print(f"🔧 Injection script created: {script_file}")
    
    def show_translation_status(self):
        """Show current translation project status"""
        print("📊 CF VANGUARD TRANSLATION PROJECT STATUS")
        print("=" * 45)
        
        # Check available files
        rtz_csv = self.files_dir / "rtz_game_text_refined.csv"
        if rtz_csv.exists():
            with open(rtz_csv, 'r', encoding='utf-8') as f:
                total_entries = len(list(csv.DictReader(f)))
            print(f"📝 Total extracted entries: {total_entries}")
        
        # Check exports
        exports = list(self.translations_dir.glob("vanguard_translation_batch_*.csv"))
        print(f"📤 Translation batches exported: {len(exports)}")
        
        # Check completions
        injections = list(self.translations_dir.glob("injection_ready_*.json"))
        print(f"✅ Completed translation sets: {len(injections)}")
        
        if exports:
            print(f"\\n📋 LATEST EXPORT:")
            latest_export = max(exports, key=lambda x: x.stat().st_mtime)
            print(f"   File: {latest_export.name}")
            print(f"   Created: {datetime.datetime.fromtimestamp(latest_export.stat().st_mtime)}")
        
        if injections:
            print(f"\\n🎯 LATEST COMPLETED TRANSLATIONS:")
            latest_injection = max(injections, key=lambda x: x.stat().st_mtime)
            with open(latest_injection, 'r', encoding='utf-8') as f:
                completed = len(json.load(f))
            print(f"   File: {latest_injection.name}")
            print(f"   Translations: {completed}")
    
    def run_interactive_menu(self):
        """Interactive menu for translation management"""
        while True:
            print("\\n" + "=" * 50)
            print("🎮 CF VANGUARD TRANSLATION MANAGER")
            print("=" * 50)
            print("1. Export text for Google Sheets translation")
            print("2. Import completed translations from Google Sheets")
            print("3. Show translation project status")
            print("4. Create custom export (specify count)")
            print("5. Exit")
            print()
            
            choice = input("Select option (1-5): ").strip()
            
            if choice == '1':
                export_file = self.export_for_google_sheets()
                input(f"\\n✅ Export complete! Press Enter to continue...")
                
            elif choice == '2':
                csv_file = input("Enter path to Google Sheets CSV file: ").strip()
                if csv_file:
                    self.import_from_google_sheets(csv_file)
                input("\\nPress Enter to continue...")
                
            elif choice == '3':
                self.show_translation_status()
                input("\\nPress Enter to continue...")
                
            elif choice == '4':
                try:
                    count = int(input("How many entries to export? (default 50): ").strip() or "50")
                    self.export_for_google_sheets(count)
                except ValueError:
                    print("❌ Invalid number")
                input("\\nPress Enter to continue...")
                
            elif choice == '5':
                print("👋 Happy translating!")
                break
                
            else:
                print("❌ Invalid choice")


def main():
    """Run the translation manager"""
    manager = RTZTranslationManager()
    manager.run_interactive_menu()


if __name__ == "__main__":
    main()