#!/usr/bin/env python3
"""
CF VANGUARD LIBRETRANSLATE BATCH TRANSLATOR
===========================================
Phase 5.2.1 - Auto-Translation Implementation

Translates extracted Japanese text using Docker LibreTranslate API
Preserves formatting codes and game-specific terminology
"""

import requests
import json
import csv
import re
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuration
LIBRETRANSLATE_URL = "http://localhost:5001/translate"
INPUT_CSV = Path("files/rtz_game_text_refined.csv")
OUTPUT_DIR = Path("files/translations")
MIN_CONFIDENCE = 0.7  # Only translate high-quality entries
BATCH_SIZE = 50  # Number of entries per batch
DELAY_BETWEEN_REQUESTS = 0.1  # Seconds between API calls

# Vanguard game terminology dictionary
VANGUARD_TERMINOLOGY = {
    'ヴァンガード': 'Vanguard',
    'アタック': 'Attack', 
    'ガード': 'Guard',
    'パワー': 'Power',
    'ノーガード': 'No Guard',
    'カード': 'Card',
    'デッキ': 'Deck',
    'ダメージ': 'Damage',
    'ターン': 'Turn',
    'ライド': 'Ride',
    'コール': 'Call',
    'リアガード': 'Rearguard',
    'スペリオルライド': 'Superior Ride',
    'ドライブチェック': 'Drive Check',
    'トリガー': 'Trigger',
    'クリティカル': 'Critical',
    'フロント': 'Front',
    'ヒール': 'Heal',
    'スタンド': 'Stand',
    'ドロー': 'Draw'
}

class VanguardTranslator:
    def __init__(self):
        self.session = requests.Session()
        self.translation_stats = {
            'total_processed': 0,
            'successful_translations': 0,
            'failed_translations': 0,
            'formatting_preserved': 0,
            'api_errors': 0
        }
        
    def test_libretranslate_connection(self) -> bool:
        """Test if LibreTranslate is running and accessible"""
        try:
            test_data = {
                "q": "テスト",
                "source": "ja", 
                "target": "en"
            }
            response = self.session.post(LIBRETRANSLATE_URL, json=test_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'translatedText' in result:
                    print(f"✅ LibreTranslate connection successful!")
                    print(f"   Test translation: テスト → {result['translatedText']}")
                    return True
            
            print(f"❌ LibreTranslate response error: {response.status_code}")
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"❌ LibreTranslate connection failed: {e}")
            print(f"   Make sure Docker container is running:")
            print(f"   docker run -ti --rm -p 5000:5000 libretranslate/libretranslate")
            return False
    
    def extract_formatting_codes(self, text: str) -> Tuple[str, List[Tuple[str, int]]]:
        """Extract formatting codes for preservation during translation"""
        
        # Find kanji reading aids: <|kanji|reading|>
        kanji_pattern = r'<\|([^|]+)\|([^|]+)\|>'
        kanji_codes = []
        for match in re.finditer(kanji_pattern, text):
            kanji_codes.append((match.group(0), match.start()))
        
        # Find color codes: {$336600} and {$}
        color_pattern = r'\{\$[^}]*\}'
        color_codes = []
        for match in re.finditer(color_pattern, text):
            color_codes.append((match.group(0), match.start()))
        
        # Replace codes with placeholders
        clean_text = text
        placeholder_map = []
        
        # Replace kanji codes with placeholders
        for i, (code, pos) in enumerate(kanji_codes):
            placeholder = f"__KANJI_{i}__"
            clean_text = clean_text.replace(code, placeholder, 1)
            placeholder_map.append((placeholder, code))
        
        # Replace color codes with placeholders
        for i, (code, pos) in enumerate(color_codes):
            placeholder = f"__COLOR_{i}__"
            clean_text = clean_text.replace(code, placeholder, 1)
            placeholder_map.append((placeholder, code))
        
        return clean_text, placeholder_map
    
    def restore_formatting_codes(self, translated_text: str, placeholder_map: List[Tuple[str, str]]) -> str:
        """Restore formatting codes after translation"""
        
        restored_text = translated_text
        
        for placeholder, original_code in placeholder_map:
            # Try exact placeholder match first
            if placeholder in restored_text:
                restored_text = restored_text.replace(placeholder, original_code)
            else:
                # Placeholder might have been translated/modified
                # Try to find similar patterns and restore
                if "__KANJI_" in placeholder:
                    # Look for variations like "KANJI_0" or translated versions
                    kanji_num = placeholder.split("_")[2].replace("__", "")
                    possible_variations = [
                        f"KANJI_{kanji_num}",
                        f"kanji_{kanji_num}",
                        f"Kanji {kanji_num}",
                        f"kanji {kanji_num}"
                    ]
                    for variation in possible_variations:
                        if variation in restored_text:
                            restored_text = restored_text.replace(variation, original_code)
                            break
                
                elif "__COLOR_" in placeholder:
                    # Similar for color codes
                    color_num = placeholder.split("_")[2].replace("__", "")
                    possible_variations = [
                        f"COLOR_{color_num}",
                        f"color_{color_num}",
                        f"Color {color_num}",
                        f"color {color_num}"
                    ]
                    for variation in possible_variations:
                        if variation in restored_text:
                            restored_text = restored_text.replace(variation, original_code)
                            break
        
        return restored_text
    
    def apply_vanguard_terminology(self, text: str) -> str:
        """Apply Vanguard-specific terminology corrections"""
        
        corrected_text = text
        
        for japanese_term, english_term in VANGUARD_TERMINOLOGY.items():
            # Replace if the Japanese term somehow survived translation
            corrected_text = corrected_text.replace(japanese_term, english_term)
            
            # Also fix common mistranslations
            common_mistranslations = {
                'vanguard': 'Vanguard',
                'attack': 'Attack',
                'guard': 'Guard',
                'power': 'Power',
                'no guard': 'No Guard',
                'card': 'Card',
                'deck': 'Deck',
                'damage': 'Damage',
                'turn': 'Turn'
            }
            
            for wrong, correct in common_mistranslations.items():
                corrected_text = corrected_text.replace(wrong, correct)
        
        return corrected_text
    
    def translate_text(self, japanese_text: str) -> Optional[str]:
        """Translate single text entry with formatting preservation"""
        
        try:
            # Extract formatting codes
            clean_text, placeholder_map = self.extract_formatting_codes(japanese_text)
            
            # Prepare translation request
            translation_data = {
                "q": clean_text,
                "source": "ja",
                "target": "en"
            }
            
            # Send to LibreTranslate
            response = self.session.post(LIBRETRANSLATE_URL, json=translation_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if 'translatedText' in result:
                    translated = result['translatedText']
                    
                    # Restore formatting codes
                    restored = self.restore_formatting_codes(translated, placeholder_map)
                    
                    # Apply Vanguard terminology
                    final_translation = self.apply_vanguard_terminology(restored)
                    
                    # Update stats
                    self.translation_stats['successful_translations'] += 1
                    if placeholder_map and all(code in final_translation for _, code in placeholder_map):
                        self.translation_stats['formatting_preserved'] += 1
                    
                    return final_translation
                else:
                    print(f"❌ No translation in response: {result}")
                    
            else:
                print(f"❌ API error {response.status_code}: {response.text}")
                self.translation_stats['api_errors'] += 1
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            self.translation_stats['api_errors'] += 1
        except Exception as e:
            print(f"❌ Translation error: {e}")
            
        self.translation_stats['failed_translations'] += 1
        return None
    
    def load_translation_candidates(self) -> List[Dict]:
        """Load high-quality translation candidates from CSV"""
        
        if not INPUT_CSV.exists():
            print(f"❌ Input file not found: {INPUT_CSV}")
            return []
        
        candidates = []
        
        try:
            with open(INPUT_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        confidence = float(row.get('confidence', 0))
                        priority = row.get('priority', '').upper()
                        
                        # Filter for high-quality entries
                        if confidence >= MIN_CONFIDENCE or priority == 'HIGH':
                            candidates.append({
                                'file': row.get('file', ''),
                                'japanese_text': row.get('japanese_text', '').strip(),
                                'confidence': confidence,
                                'priority': priority,
                                'context': row.get('context', ''),
                                'difficulty': row.get('difficulty', ''),
                                'original_row': row
                            })
                            
                    except (ValueError, TypeError):
                        # Skip rows with invalid confidence scores
                        continue
        
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
        
        # Sort by priority and confidence
        candidates.sort(key=lambda x: (
            0 if x['priority'] == 'HIGH' else 1,  # HIGH priority first
            -x['confidence']  # Higher confidence first
        ))
        
        print(f"📋 Loaded {len(candidates)} high-quality translation candidates")
        print(f"   Confidence >= {MIN_CONFIDENCE}: {len([c for c in candidates if c['confidence'] >= MIN_CONFIDENCE])}")
        print(f"   HIGH priority: {len([c for c in candidates if c['priority'] == 'HIGH'])}")
        
        return candidates
    
    def batch_translate(self, max_entries: Optional[int] = None) -> str:
        """Perform batch translation of all candidates"""
        
        print("🚀 STARTING LIBRETRANSLATE BATCH TRANSLATION")
        print("=" * 50)
        
        # Test connection first
        if not self.test_libretranslate_connection():
            return ""
        
        # Load candidates
        candidates = self.load_translation_candidates()
        if not candidates:
            print("❌ No translation candidates found")
            return ""
        
        # Limit if specified
        if max_entries:
            candidates = candidates[:max_entries]
            print(f"🎯 Processing first {len(candidates)} entries")
        
        # Prepare output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"auto_translated_batch_{timestamp}.csv"
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Start translation
        translated_entries = []
        
        print(f"\n⚙ Starting translation of {len(candidates)} entries...")
        print(f"   Output file: {output_file.name}")
        print(f"   Batch size: {BATCH_SIZE}")
        
        for i, candidate in enumerate(candidates, 1):
            japanese_text = candidate['japanese_text']
            
            if not japanese_text:
                continue
            
            print(f"\n[{i:3}/{len(candidates)}] Translating...")
            print(f"   JP: {japanese_text[:60]}{'...' if len(japanese_text) > 60 else ''}")
            
            # Translate
            english_text = self.translate_text(japanese_text)
            
            if english_text:
                print(f"   EN: {english_text[:60]}{'...' if len(english_text) > 60 else ''}")
                print(f"   ✅ Success")
            else:
                english_text = ""  # Empty for failed translations
                print(f"   ❌ Failed")
            
            # Create output entry
            output_entry = candidate['original_row'].copy()
            output_entry['english_text'] = english_text
            output_entry['translation_status'] = 'COMPLETED' if english_text else 'FAILED'
            output_entry['translation_timestamp'] = datetime.now().isoformat()
            
            translated_entries.append(output_entry)
            self.translation_stats['total_processed'] += 1
            
            # Rate limiting
            if i % BATCH_SIZE == 0:
                print(f"\n⏸ Batch {i//BATCH_SIZE} complete, pausing briefly...")
                time.sleep(1)
            else:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Save results
        self.save_translations(translated_entries, output_file)
        
        # Print final stats
        self.print_translation_stats()
        
        return str(output_file)
    
    def save_translations(self, translations: List[Dict], output_file: Path):
        """Save translations to CSV file"""
        
        if not translations:
            print("❌ No translations to save")
            return
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = list(translations[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(translations)
            
            print(f"\n💾 Translations saved: {output_file}")
            print(f"   {len(translations)} entries written")
            
        except Exception as e:
            print(f"❌ Error saving translations: {e}")
    
    def print_translation_stats(self):
        """Print translation statistics"""
        
        stats = self.translation_stats
        total = stats['total_processed']
        
        print(f"\n📊 TRANSLATION STATISTICS")
        print("=" * 30)
        print(f"Total processed:      {total}")
        print(f"Successful:          {stats['successful_translations']} ({stats['successful_translations']/max(total,1)*100:.1f}%)")
        print(f"Failed:              {stats['failed_translations']} ({stats['failed_translations']/max(total,1)*100:.1f}%)")
        print(f"Formatting preserved: {stats['formatting_preserved']}")
        print(f"API errors:          {stats['api_errors']}")
        
        success_rate = stats['successful_translations'] / max(total, 1) * 100
        if success_rate >= 80:
            print(f"\n🎉 Excellent success rate: {success_rate:.1f}%")
        elif success_rate >= 60:
            print(f"\n✅ Good success rate: {success_rate:.1f}%")
        else:
            print(f"\n⚠ Low success rate: {success_rate:.1f}% - Check LibreTranslate connection")

def main():
    """Main execution function"""
    
    print("🎮 CF VANGUARD LIBRETRANSLATE BATCH TRANSLATOR")
    print("=" * 50)
    print("Phase 5.2.1 - Auto-Translation Implementation")
    print()
    
    # Check for required files
    if not INPUT_CSV.exists():
        print(f"❌ Required file not found: {INPUT_CSV}")
        print(f"   Please ensure RTZ text extraction has been completed")
        return
    
    translator = VanguardTranslator()
    
    # Interactive mode
    while True:
        print("\n🎯 TRANSLATION OPTIONS:")
        print("1. Test LibreTranslate connection")
        print("2. Translate small test batch (10 entries)")
        print("3. Translate medium batch (50 entries)")
        print("4. Translate all high-quality entries")
        print("5. Custom batch size")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            translator.test_libretranslate_connection()
        
        elif choice == '2':
            print("\n🧪 Translating test batch...")
            result_file = translator.batch_translate(max_entries=10)
            if result_file:
                print(f"✅ Test batch complete: {Path(result_file).name}")
        
        elif choice == '3':
            print("\n⚙ Translating medium batch...")
            result_file = translator.batch_translate(max_entries=50)
            if result_file:
                print(f"✅ Medium batch complete: {Path(result_file).name}")
        
        elif choice == '4':
            print("\n🚀 Translating ALL high-quality entries...")
            confirm = input("This will process ~434 entries. Continue? (y/N): ").strip().lower()
            if confirm == 'y':
                result_file = translator.batch_translate()
                if result_file:
                    print(f"🎉 Full batch complete: {Path(result_file).name}")
        
        elif choice == '5':
            try:
                count = int(input("Enter number of entries to translate: "))
                if count > 0:
                    result_file = translator.batch_translate(max_entries=count)
                    if result_file:
                        print(f"✅ Custom batch complete: {Path(result_file).name}")
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()