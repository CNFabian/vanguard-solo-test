#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

# Character selection related keywords
CHARACTER_KEYWORDS = [
    # Japanese keywords
    '選', '選択', '選ぶ', 'キャラ', 'アバター', '名前', '男', '女',
    '主人公', '容姿', 'ニックネーム', '設定', '変更', 'プレイヤー',
    '称号', '外見', '姿', 'カスタム', '作成', '編集',
    
    # UI/Navigation keywords  
    '確認', '決定', '戻る', 'キャンセル', 'OK', 'はい', 'いいえ',
    'スタート', '開始', '終了', 'メニュー', '画面'
]

def filter_character_strings():
    input_file = Path("files/original/extracted_strings.csv")
    output_file = Path("files/character_selection_strings.csv")
    
    print(f"Reading from: {input_file}")
    print(f"Output to: {output_file}")
    
    character_strings = []
    
    with input_file.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            extract = row.get('extract', '')
            
            # Check for character selection keywords
            has_keyword = any(keyword in extract for keyword in CHARACTER_KEYWORDS)
            
            if has_keyword:
                # Add relevance score
                keyword_count = sum(1 for keyword in CHARACTER_KEYWORDS if keyword in extract)
                row['relevance_score'] = keyword_count
                row['matched_keywords'] = ', '.join([k for k in CHARACTER_KEYWORDS if k in extract])
                character_strings.append(row)
    
    # Sort by relevance score (highest first)
    character_strings.sort(key=lambda x: int(x['relevance_score']), reverse=True)
    
    # Write filtered results
    if character_strings:
        fieldnames = list(character_strings[0].keys())
        with output_file.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(character_strings)
    
    print(f"Found {len(character_strings)} character selection related strings")
    
    # Show top 10 most relevant
    print("\nTop 10 most relevant strings:")
    for i, string in enumerate(character_strings[:10]):
        print(f"{i+1}. [{string['relevance_score']}] {string['extract'][:80]}...")
        print(f"   Keywords: {string['matched_keywords']}")
        print(f"   Pointer: {string['pointer_value']}\n")

if __name__ == "__main__":
    filter_character_strings()