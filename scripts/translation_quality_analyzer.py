#!/usr/bin/env python3
"""
CF Vanguard Translation Viewer
==============================
View and showcase the best auto-translations
"""

import csv
from pathlib import Path

def show_best_translations():
    """Display the best translations from our filtered datasets"""
    
    print("🎮 CF VANGUARD - BEST AUTO-TRANSLATIONS")
    print("=" * 45)
    
    translations_dir = Path("files/translations")
    
    # Find the latest filtered files
    excellent_files = list(translations_dir.glob("filtered_excellent_*.csv"))
    good_files = list(translations_dir.glob("filtered_good_*.csv"))
    
    if not excellent_files:
        print("❌ No excellent translations found")
        return
    
    latest_excellent = max(excellent_files, key=lambda x: x.stat().st_mtime)
    latest_good = max(good_files, key=lambda x: x.stat().st_mtime) if good_files else None
    
    print(f"📁 Reading from: {latest_excellent.name}")
    print()
    
    # Show excellent translations
    print("🏆 EXCELLENT TRANSLATIONS (Perfect Quality)")
    print("-" * 50)
    
    try:
        with open(latest_excellent, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader, 1):
                jp_text = row.get('japanese_text', '')[:80]
                en_text = row.get('english_text', '')[:80] 
                confidence = row.get('confidence', 'N/A')
                context = row.get('context', 'Unknown')
                
                print(f"{i:2}. Context: {context}")
                print(f"    JP: {jp_text}")
                print(f"    EN: {en_text}")
                print(f"    Confidence: {confidence}")
                print()
                
                if i >= 15:  # Show first 15
                    print(f"    ... and {sum(1 for _ in open(latest_excellent))-1-15} more excellent translations!")
                    break
    except Exception as e:
        print(f"❌ Error reading excellent translations: {e}")
        return
    
    # Show some good translations too
    if latest_good:
        print(f"\n✅ GOOD TRANSLATIONS (High Quality)")
        print("-" * 50)
        
        try:
            with open(latest_good, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader, 1):
                    jp_text = row.get('japanese_text', '')[:80]
                    en_text = row.get('english_text', '')[:80]
                    confidence = row.get('confidence', 'N/A')
                    context = row.get('context', 'Unknown')
                    
                    print(f"{i:2}. Context: {context}")
                    print(f"    JP: {jp_text}")
                    print(f"    EN: {en_text}")
                    print(f"    Confidence: {confidence}")
                    print()
                    
                    if i >= 10:  # Show first 10
                        print(f"    ... and {sum(1 for _ in open(latest_good))-1-10} more good translations!")
                        break
        except Exception as e:
            print(f"❌ Error reading good translations: {e}")
    
    # Show statistics
    print(f"\n📊 TRANSLATION SUMMARY")
    print("=" * 25)
    
    # Count entries in each file
    excellent_count = sum(1 for _ in open(latest_excellent)) - 1 if latest_excellent.exists() else 0
    good_count = sum(1 for _ in open(latest_good)) - 1 if latest_good and latest_good.exists() else 0
    usable_files = list(translations_dir.glob("filtered_usable_*.csv"))
    usable_count = sum(1 for _ in open(max(usable_files, key=lambda x: x.stat().st_mtime))) - 1 if usable_files else 0
    
    print(f"Excellent Quality: {excellent_count}")
    print(f"Good Quality:      {good_count}")
    print(f"Total Usable:      {usable_count}")
    print()
    print(f"🎯 Ready for ROM injection: {usable_count} translations!")
    print(f"🎮 This is enough to translate key game elements!")
    
    # Show what types of content we translated
    print(f"\n🎭 CONTENT TYPES SUCCESSFULLY TRANSLATED:")
    context_counts = {}
    
    try:
        usable_file = max(usable_files, key=lambda x: x.stat().st_mtime)
        with open(usable_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                context = row.get('context', 'Unknown')
                context_counts[context] = context_counts.get(context, 0) + 1
        
        for context, count in sorted(context_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {context}: {count} translations")
            
    except Exception as e:
        print(f"   (Could not analyze content types: {e})")
    
    print(f"\n🚀 NEXT PHASE: RTZ FILE INJECTION")
    print(f"   Use filtered_usable_*.csv for Phase 5.3")
    print(f"   Ready to inject English text into game files!")

if __name__ == "__main__":
    show_best_translations()