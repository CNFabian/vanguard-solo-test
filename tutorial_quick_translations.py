#!/usr/bin/env python3
"""
Quick Tutorial Translations - High Priority Entries
===================================================
Translate the most important tutorial kanji/kana markup patterns
"""

# High-priority kanji/kana translations based on card game terminology
TUTORIAL_TRANSLATIONS = {
    # Game terminology
    "<|色々教|いろいろおし|>": "teach various things",
    "<|下画面|したがめん|>": "bottom screen", 
    "<|退却|たいきゃく|>": "retreat",
    "<|説明|せつめい|>": "explanation",
    "<|攻撃|こうげき|>": "attack",
    "<|防御|ぼうぎょ|>": "defense",
    "<|拡大|かくだい|>": "enlarge",
    "<|一緒|いっしょ|>": "together",
    "<|分身|ぶんしん|>": "clone",
    "<|山札|やまふだ|>": "deck",
    "<|枚数|まいすう|>": "number of cards",
    "<|注意|ちゅうい|>": "attention",
    "<|特別|とくべつ|>": "special",
    "<|最大|さいだい|>": "maximum",
    "<|数字|すうじ|>": "number",
    "<|手札|てふだ|>": "hand",
    "<|場所|ばしょ|>": "location",
    "<|最後|さいご|>": "last",
    "<|有利|ゆうり|>": "advantage",
    "<|画像|がぞう|>": "image",
    
    # Additional common terms (from pattern analysis)
    "<|次|つぎ|>": "next",
    "<|教|おし|>": "teach",
    "<|他|ほか|>": "other",
    "<|置|お|>": "place",
    "<|言|い|>": "say",
    "<|束|た|>": "bundle",
}

def create_translated_csv():
    """Create a translated version of the tutorial CSV"""
    import csv
    
    # Read the original extraction
    input_file = "tutorial_translation_ready.csv"
    output_file = "tutorial_translated_ready.csv"
    
    translated_entries = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for row in reader:
                japanese_text = row['japanese_text']
                
                # Check if we have a direct translation
                if japanese_text in TUTORIAL_TRANSLATIONS:
                    row['english_translation'] = TUTORIAL_TRANSLATIONS[japanese_text]
                    row['notes'] = 'Direct translation - ready for injection'
                elif row['type'] == 'kanji_kana_markup':
                    row['english_translation'] = '[NEEDS TRANSLATION]'
                    row['notes'] = 'High priority kanji/kana markup'
                else:
                    row['english_translation'] = '[NEEDS TRANSLATION]'
                    row['notes'] = 'Context sentence or text segment'
                
                translated_entries.append(row)
        
        # Write translated version
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if translated_entries:
                fieldnames = translated_entries[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                writer.writerows(translated_entries)
        
        print(f"✅ Created translated CSV: {output_file}")
        
        # Count translations
        translated_count = sum(1 for entry in translated_entries 
                             if entry['english_translation'] not in ['', '[NEEDS TRANSLATION]'])
        
        print(f"📊 Translation Status:")
        print(f"   Total entries: {len(translated_entries)}")
        print(f"   Translated: {translated_count}")
        print(f"   Remaining: {len(translated_entries) - translated_count}")
        
        return translated_entries, translated_count
        
    except FileNotFoundError:
        print(f"❌ Could not find {input_file}")
        print("   Please run extract_tutorial_text.py first")
        return [], 0

def create_injection_test_file():
    """Create a small test file with just the translated entries"""
    import csv
    
    # Read translated entries
    try:
        with open("tutorial_translated_ready.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            entries = list(reader)
        
        # Filter to only translated entries
        translated_entries = [entry for entry in entries 
                            if entry['english_translation'] not in ['', '[NEEDS TRANSLATION]']]
        
        # Create injection test file
        test_file = "tutorial_injection_test.csv"
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'offset', 'japanese_text', 'english_translation', 'priority']
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            
            for entry in translated_entries[:10]:  # Top 10 for testing
                writer.writerow({
                    'id': entry['id'],
                    'offset': entry['offset'],
                    'japanese_text': entry['japanese_text'],
                    'english_translation': entry['english_translation'],
                    'priority': entry['priority']
                })
        
        print(f"✅ Created injection test file: {test_file}")
        print(f"   Contains {len(translated_entries[:10])} entries ready for testing")
        
        return translated_entries[:10]
        
    except FileNotFoundError:
        print("❌ Could not find translated CSV file")
        return []

def show_translation_examples():
    """Show examples of the translations"""
    print("\n🎯 TRANSLATION EXAMPLES:")
    print("=" * 50)
    
    examples = [
        ("<|山札|やまふだ|>", "deck", "The deck of cards"),
        ("<|手札|てふだ|>", "hand", "Cards in hand"),
        ("<|攻撃|こうげき|>", "attack", "Attack action"),
        ("<|防御|ぼうぎょ|>", "defense", "Defense action"),
        ("<|説明|せつめい|>", "explanation", "Tutorial explanation"),
    ]
    
    for japanese, english, context in examples:
        print(f"Japanese: {japanese}")
        print(f"English:  {english}")
        print(f"Context:  {context}")
        print()

def main():
    print("🎓 CF VANGUARD TUTORIAL QUICK TRANSLATIONS")
    print("=" * 55)
    
    # Create translated CSV
    entries, translated_count = create_translated_csv()
    
    if translated_count > 0:
        print(f"\n✅ SUCCESS: {translated_count} entries translated!")
        
        # Create injection test file
        test_entries = create_injection_test_file()
        
        # Show examples
        show_translation_examples()
        
        print("🚀 READY FOR INJECTION TESTING!")
        print("=" * 40)
        print("Next steps:")
        print("1. Review tutorial_translated_ready.csv")
        print("2. Test injection with tutorial_injection_test.csv")
        print("3. Use extract_rtz_content.py for injection")
        print("4. Validate translations in-game")
        
        print(f"\n🎮 IMMEDIATE TESTING CANDIDATES:")
        for entry in test_entries[:5]:
            print(f"   {entry['japanese_text']} → {entry['english_translation']}")
    
    else:
        print("❌ No translations created. Check if tutorial_translation_ready.csv exists.")

if __name__ == "__main__":
    main()