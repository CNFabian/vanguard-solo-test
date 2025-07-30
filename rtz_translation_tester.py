#!/usr/bin/env python3
"""
RTZ TRANSLATION TESTER - PHASE 5.2 PREPARATION
===============================================
CF VANGUARD STRIDE TO VICTORY - FANMADE TRANSLATION PROJECT

Extracts the cleanest Japanese text for translation testing
Prepares injection pipeline for RTZ files
"""

import csv
import re
from pathlib import Path
from typing import List, Dict

class RTZTranslationTester:
    def __init__(self):
        self.csv_path = Path("files/rtz_game_text_refined.csv")
        self.output_path = Path("files")
        
    def extract_clean_japanese_entries(self) -> List[Dict]:
        """Extract the cleanest Japanese text entries for translation"""
        
        print("🔍 EXTRACTING CLEAN JAPANESE TEXT FOR TRANSLATION")
        print("=" * 50)
        
        if not self.csv_path.exists():
            print(f"❌ CSV file not found: {self.csv_path}")
            return []
            
        clean_entries = []
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            entries = list(reader)
            
        print(f"📊 Total entries in CSV: {len(entries)}")
        
        for entry in entries:
            text = entry['japanese_text']
            confidence = float(entry['confidence'])
            
            # Quality filters for translation candidates
            if self.is_translation_ready(text, confidence):
                clean_entries.append({
                    'file': entry['file'],
                    'offset': entry['offset'],
                    'japanese_text': text,
                    'confidence': confidence,
                    'priority': entry['priority'],
                    'translation_quality': self.assess_translation_quality(text)
                })
                
        # Sort by translation quality
        clean_entries.sort(key=lambda x: (x['translation_quality'], x['confidence']), reverse=True)
        
        print(f"✅ Clean translation candidates: {len(clean_entries)}")
        return clean_entries
    
    def is_translation_ready(self, text: str, confidence: float) -> bool:
        """Check if text is ready for translation"""
        
        # Must have high confidence
        if confidence < 0.7:
            return False
            
        # Must contain readable Japanese
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))
        if japanese_chars < 2:
            return False
            
        # Must not be too corrupted
        weird_chars = len(re.findall(r'[￿\uffff\x00-\x1f]', text))
        if weird_chars > japanese_chars:
            return False
            
        # Reasonable length
        if len(text.strip()) < 2 or len(text.strip()) > 100:
            return False
            
        return True
    
    def assess_translation_quality(self, text: str) -> float:
        """Assess how suitable text is for translation (0-1 score)"""
        score = 0.0
        
        # Base score for Japanese content
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))
        if japanese_chars > 0:
            score += 0.3
            
        # Bonus for complete words/phrases
        if re.search(r'[\u3040-\u309f]{2,}', text):  # Hiragana sequences
            score += 0.2
            
        if re.search(r'[\u30a0-\u30ff]{2,}', text):  # Katakana sequences
            score += 0.2
            
        if re.search(r'[\u4e00-\u9faf]+', text):  # Kanji
            score += 0.2
            
        # Bonus for punctuation (complete sentences)
        if re.search(r'[。！？]', text):
            score += 0.2
            
        # Penalty for corruption indicators
        corruption_indicators = ['￿', '㸀', '籓', '蔰', '地', '縰']
        corruption_count = sum(text.count(indicator) for indicator in corruption_indicators)
        if corruption_count > 0:
            score -= 0.3
            
        # Penalty for too many symbols
        symbol_ratio = len(re.findall(r'[<>|]', text)) / len(text) if text else 0
        if symbol_ratio > 0.3:
            score -= 0.2
            
        return max(0.0, min(1.0, score))
    
    def create_translation_test_set(self, clean_entries: List[Dict], max_entries: int = 10):
        """Create a small test set for initial translation work"""
        
        print(f"\n🎯 CREATING TRANSLATION TEST SET")
        print("=" * 35)
        
        if not clean_entries:
            print("❌ No clean entries available for test set")
            return
            
        # Take the best entries
        test_entries = clean_entries[:max_entries]
        
        print(f"📋 Selected {len(test_entries)} entries for translation testing:")
        print()
        
        for i, entry in enumerate(test_entries, 1):
            print(f"{i:2d}. Quality: {entry['translation_quality']:.2f} | Conf: {entry['confidence']:.2f}")
            print(f"    Japanese: {entry['japanese_text']}")
            print(f"    File: {Path(entry['file']).name}")
            print(f"    English: [TO BE TRANSLATED]")
            print()
            
        # Save test set to CSV
        test_csv_path = self.output_path / "rtz_translation_test_set.csv"
        
        with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'file', 'offset', 'japanese_text', 'english_text', 
                         'confidence', 'translation_quality', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, entry in enumerate(test_entries, 1):
                writer.writerow({
                    'id': f'RTZ_TEST_{i:02d}',
                    'file': entry['file'],
                    'offset': entry['offset'],
                    'japanese_text': entry['japanese_text'],
                    'english_text': '',  # To be filled
                    'confidence': entry['confidence'],
                    'translation_quality': entry['translation_quality'],
                    'notes': ''
                })
                
        print(f"💾 Test set saved to: {test_csv_path}")
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Manually translate the Japanese text in {test_csv_path.name}")
        print(f"2. Focus on entries with highest translation_quality scores")
        print(f"3. Test RTZ injection with 2-3 completed translations")
        print(f"4. Validate English text display in-game")
        
        return test_csv_path
    
    def show_translation_examples(self, clean_entries: List[Dict]):
        """Show specific examples of what we found"""
        
        print(f"\n🌟 TRANSLATION EXAMPLES")
        print("=" * 25)
        
        # Show different types of text we found
        categories = {
            'High Quality': [e for e in clean_entries if e['translation_quality'] > 0.8],
            'Medium Quality': [e for e in clean_entries if 0.5 < e['translation_quality'] <= 0.8],
            'Needs Cleanup': [e for e in clean_entries if e['translation_quality'] <= 0.5]
        }
        
        for category, entries in categories.items():
            if not entries:
                continue
                
            print(f"\n📂 {category} ({len(entries)} entries):")
            for entry in entries[:3]:  # Show top 3 per category
                print(f"   • '{entry['japanese_text']}'")
                print(f"     Quality: {entry['translation_quality']:.2f}, Conf: {entry['confidence']:.2f}")
                
        # Show some specific good examples for manual translation
        if categories['High Quality']:
            print(f"\n🎯 RECOMMENDED FOR IMMEDIATE TRANSLATION:")
            for entry in categories['High Quality'][:5]:
                print(f"   Japanese: {entry['japanese_text']}")
                print(f"   Suggested English: [Please translate this]")
                print()
    
    def run_analysis(self):
        """Run complete analysis and create translation test set"""
        
        print("🚀 RTZ TRANSLATION TESTER - PHASE 5.2 PREPARATION")
        print("=" * 55)
        
        # Extract clean entries
        clean_entries = self.extract_clean_japanese_entries()
        
        if not clean_entries:
            print("❌ No suitable entries found for translation")
            return
            
        # Show examples
        self.show_translation_examples(clean_entries)
        
        # Create test set
        test_csv_path = self.create_translation_test_set(clean_entries)
        
        print(f"\n🏆 PHASE 5.1.1 → 5.2 TRANSITION COMPLETE!")
        print(f"✅ Found {len(clean_entries)} translation-ready entries")
        print(f"✅ Created test set with highest quality candidates")
        print(f"✅ Ready for translation and injection testing")
        print(f"\n📋 YOUR HOMEWORK:")
        print(f"1. Open {test_csv_path} and add English translations")
        print(f"2. Start with the highest quality entries first")
        print(f"3. Come back to test RTZ injection pipeline")


def main():
    """Run RTZ translation analysis"""
    tester = RTZTranslationTester()  
    tester.run_analysis()


if __name__ == "__main__":
    main()