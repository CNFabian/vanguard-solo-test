#!/usr/bin/env python3
"""
TUTORIAL TEXT EXTRACTOR - tuto_001.rtz
======================================
Extract clean, translatable Japanese text from the tutorial file
Based on successful pattern detection
"""

import gzip
import struct
import re
from pathlib import Path

def decompress_rtz(rtz_path: Path) -> bytes:
    """Decompress RTZ file"""
    data = rtz_path.read_bytes()
    
    if len(data) >= 4:
        try:
            size = struct.unpack('<I', data[:4])[0]
            if 100 < size < 10000000:
                gzip_data = data[4:]
                if gzip_data.startswith(b'\x1f\x8b'):
                    return gzip.decompress(gzip_data)
        except:
            pass
    
    return data

def extract_clean_japanese_text(data: bytes) -> list:
    """Extract clean Japanese text patterns for translation"""
    
    findings = []
    
    # Pattern 1: Find kanji/kana markup patterns like <|漢字|かな|>
    # Convert to UTF-16LE encoded pattern
    pattern_start = '<|'.encode('utf-16le')
    pattern_middle = '|'.encode('utf-16le')
    pattern_end = '|>'.encode('utf-16le')
    
    # Search for the pattern manually
    pos = 0
    while pos < len(data) - 20:
        start_pos = data.find(pattern_start, pos)
        if start_pos == -1:
            break
        
        # Look for the complete pattern
        middle_pos = data.find(pattern_middle, start_pos + len(pattern_start))
        if middle_pos == -1:
            pos = start_pos + len(pattern_start)
            continue
        
        end_pos = data.find(pattern_end, middle_pos + len(pattern_middle))
        if end_pos == -1:
            pos = middle_pos + len(pattern_middle)
            continue
        
        # Extract the complete pattern
        pattern_data = data[start_pos:end_pos + len(pattern_end)]
        try:
            text = pattern_data.decode('utf-16le')
            if len(text) > 5:
                findings.append({
                    'offset': start_pos,
                    'type': 'kanji_kana_markup',
                    'text': text,
                    'priority': 'HIGH'
                })
        except:
            pass
        
        pos = end_pos + len(pattern_end)
    
    # Pattern 2: Find Japanese sentences with proper context
    # Look for areas around the markup patterns to get full sentences
    pos = 0
    while pos < len(data) - 20:
        start_pos = data.find(pattern_start, pos)
        if start_pos == -1:
            break
        
        start_context = max(0, start_pos - 200)
        end_context = min(len(data), start_pos + 400)
        
        # Make sure we're aligned to UTF-16LE boundaries
        if start_context % 2 != 0:
            start_context -= 1
        if (end_context - start_context) % 2 != 0:
            end_context -= 1
        
        context_data = data[start_context:end_context]
        
        try:
            context_text = context_data.decode('utf-16le', errors='ignore')
            
            # Split by common sentence terminators
            sentences = re.split(r'[。？！\.\?\!]', context_text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                # Look for sentences with Japanese characters and reasonable length
                if (len(sentence) >= 10 and 
                    re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', sentence) and
                    len(sentence) <= 200):
                    
                    findings.append({
                        'offset': start_context,
                        'type': 'japanese_sentence',
                        'text': sentence.strip(),
                        'priority': 'MEDIUM'
                    })
        except:
            pass
        
        pos = start_pos + 20
    
    # Pattern 3: Find standalone Japanese text segments
    # Look for UTF-16LE strings that contain substantial Japanese text
    pos = 0
    while pos < len(data) - 20:
        try:
            # Try different lengths
            for length in [20, 50, 100, 150]:
                if pos + length * 2 > len(data):
                    continue
                
                chunk = data[pos:pos + length * 2]
                try:
                    decoded = chunk.decode('utf-16le')
                    
                    # Check for Japanese content
                    japanese_match = re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+', decoded)
                    if japanese_match:
                        # Extract just the Japanese part and some context
                        japanese_text = japanese_match.group()
                        
                        # Look for fuller context around the Japanese text
                        start_pos = max(0, decoded.find(japanese_text) - 10)
                        end_pos = min(len(decoded), decoded.find(japanese_text) + len(japanese_text) + 10)
                        context = decoded[start_pos:end_pos].strip()
                        
                        if len(context) >= 5 and len(japanese_text) >= 3:
                            findings.append({
                                'offset': pos,
                                'type': 'japanese_text',
                                'text': context,
                                'japanese_part': japanese_text,
                                'priority': 'LOW'
                            })
                        
                        pos += length * 2
                        break
                except UnicodeDecodeError:
                    continue
            else:
                pos += 2
        except:
            pos += 2
    
    # Remove duplicates and sort by priority and length
    unique_findings = []
    seen_texts = set()
    
    for finding in findings:
        text_key = finding['text'].replace(' ', '').replace('\x00', '')
        if text_key not in seen_texts and len(text_key) >= 5:
            seen_texts.add(text_key)
            unique_findings.append(finding)
    
    # Sort by priority and length
    priority_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    unique_findings.sort(key=lambda x: (priority_order[x['priority']], len(x['text'])), reverse=True)
    
    return unique_findings

def create_translation_csv(findings: list, output_file: str):
    """Create a CSV file ready for translation"""
    
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['id', 'offset', 'type', 'priority', 'japanese_text', 'english_translation', 'notes'])
        
        for i, finding in enumerate(findings, 1):
            writer.writerow([
                f"TUTO_{i:03d}",
                f"0x{finding['offset']:04X}",
                finding['type'],
                finding['priority'],
                finding['text'],
                '',  # Empty translation field
                ''   # Empty notes field
            ])

def main():
    print("🎓 CF VANGUARD TUTORIAL TEXT EXTRACTOR")
    print("=" * 50)
    
    tutorial_file = Path("romfs/fe/tuto_001.rtz")
    
    if not tutorial_file.exists():
        print(f"❌ Tutorial file not found: {tutorial_file}")
        return
    
    print(f"📂 Processing: {tutorial_file}")
    
    # Decompress the file
    data = decompress_rtz(tutorial_file)
    print(f"📊 Decompressed size: {len(data):,} bytes")
    
    # Extract Japanese text
    findings = extract_clean_japanese_text(data)
    print(f"✅ Found {len(findings)} translatable text entries")
    
    # Show summary by type and priority
    by_type = {}
    by_priority = {}
    
    for finding in findings:
        t = finding['type']
        p = finding['priority']
        by_type[t] = by_type.get(t, 0) + 1
        by_priority[p] = by_priority.get(p, 0) + 1
    
    print(f"\n📊 BREAKDOWN BY TYPE:")
    for text_type, count in by_type.items():
        print(f"   {text_type}: {count} entries")
    
    print(f"\n📊 BREAKDOWN BY PRIORITY:")
    for priority, count in by_priority.items():
        print(f"   {priority}: {count} entries")
    
    # Show best examples
    print(f"\n🌟 TOP 20 TRANSLATION CANDIDATES:")
    print("-" * 80)
    print(f"{'ID':<8} {'Type':<20} {'Pri':<4} {'Text':<50}")
    print("-" * 80)
    
    for i, finding in enumerate(findings[:20], 1):
        text_preview = finding['text'][:47] + "..." if len(finding['text']) > 50 else finding['text']
        print(f"TUTO_{i:03d} {finding['type']:<20} {finding['priority']:<4} {text_preview}")
    
    # Create translation-ready CSV
    csv_output = "tutorial_translation_ready.csv"
    create_translation_csv(findings, csv_output)
    print(f"\n💾 Created translation CSV: {csv_output}")
    
    # Create detailed text file
    txt_output = "tutorial_japanese_extracted.txt"
    with open(txt_output, 'w', encoding='utf-8') as f:
        f.write("CF VANGUARD TUTORIAL JAPANESE TEXT EXTRACTION\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"File: {tutorial_file}\n")
        f.write(f"Total entries: {len(findings)}\n\n")
        
        for i, finding in enumerate(findings, 1):
            f.write(f"ENTRY {i:03d}:\n")
            f.write(f"  ID: TUTO_{i:03d}\n")
            f.write(f"  Offset: 0x{finding['offset']:04X}\n")
            f.write(f"  Type: {finding['type']}\n")
            f.write(f"  Priority: {finding['priority']}\n")
            f.write(f"  Japanese Text: {finding['text']}\n")
            if 'japanese_part' in finding:
                f.write(f"  Japanese Part: {finding['japanese_part']}\n")
            f.write(f"  Translation: [TO BE TRANSLATED]\n")
            f.write("\n")
    
    print(f"💾 Created detailed text file: {txt_output}")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Review {csv_output} and add English translations")
    print(f"2. Focus on HIGH and MEDIUM priority entries first")
    print(f"3. Test injection with a few translated entries")
    print(f"4. Use extract_rtz_content.py for more detailed extraction")
    
    # Show specific high-priority examples for immediate translation
    high_priority = [f for f in findings if f['priority'] == 'HIGH']
    if high_priority:
        print(f"\n🔥 HIGH PRIORITY ENTRIES FOR IMMEDIATE TRANSLATION:")
        print("-" * 60)
        for i, finding in enumerate(high_priority[:5], 1):
            print(f"{i}. {finding['text']}")
            print(f"   → [TRANSLATE THIS TEXT]\n")

if __name__ == "__main__":
    main()