#!/usr/bin/env python3
"""
RTZ JAPANESE TEXT PATTERN FINDER
================================
Specialized tool to find readable Japanese text patterns in RTZ files
Based on successful code.bin extraction patterns
"""

import gzip
import struct
import re
from pathlib import Path

def decompress_rtz(rtz_path: Path) -> bytes:
    """Decompress RTZ file using the proven method"""
    data = rtz_path.read_bytes()
    
    # RTZ format: 4-byte size + gzip data
    if len(data) >= 4:
        try:
            size = struct.unpack('<I', data[:4])[0]
            if 100 < size < 10000000:
                gzip_data = data[4:]
                if gzip_data.startswith(b'\x1f\x8b'):
                    decompressed = gzip.decompress(gzip_data)
                    return decompressed
        except Exception as e:
            print(f"⚠️  RTZ decompression failed: {e}")
    
    return data

def find_japanese_patterns(data: bytes) -> list:
    """Find Japanese text patterns similar to code.bin format"""
    patterns = []
    
    # Pattern 1: Look for kanji/kana format like <|漢字|かな|>
    kanji_kana_pattern = re.compile(rb'<\|[^\|]+\|[^\|]+\|>')
    
    for match in kanji_kana_pattern.finditer(data):
        try:
            text = match.group().decode('utf-8', errors='ignore')
            if len(text) > 5:  # Meaningful length
                patterns.append({
                    'offset': match.start(),
                    'pattern': 'kanji_kana',
                    'text': text,
                    'raw_bytes': match.group()
                })
        except:
            pass
    
    # Pattern 2: Look for UTF-16LE Japanese strings
    pos = 0
    while pos < len(data) - 6:
        try:
            # Try decoding 2-byte aligned chunks
            for length in [10, 20, 50, 100, 200]:
                if pos + length * 2 > len(data):
                    continue
                
                try:
                    chunk = data[pos:pos + length * 2]
                    decoded = chunk.decode('utf-16le')
                    
                    # Check for Japanese characters
                    if re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', decoded):
                        # Check for reasonable text (not too many control chars)
                        printable = ''.join(c for c in decoded if c.isprintable())
                        if len(printable) >= 4 and len(printable) >= len(decoded) * 0.7:
                            patterns.append({
                                'offset': pos,
                                'pattern': 'utf16le_japanese',
                                'text': printable.strip(),
                                'raw_bytes': chunk
                            })
                            pos += length * 2
                            break
                except UnicodeDecodeError:
                    continue
            else:
                pos += 2
        except:
            pos += 1
    
    # Pattern 3: Look for Shift-JIS Japanese strings
    pos = 0
    while pos < len(data) - 6:
        try:
            for length in [10, 20, 50, 100]:
                if pos + length > len(data):
                    continue
                
                try:
                    chunk = data[pos:pos + length]
                    decoded = chunk.decode('shift-jis')
                    
                    # Check for Japanese characters
                    if re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', decoded):
                        printable = ''.join(c for c in decoded if c.isprintable())
                        if len(printable) >= 4:
                            patterns.append({
                                'offset': pos,
                                'pattern': 'shift_jis_japanese',
                                'text': printable.strip(),
                                'raw_bytes': chunk
                            })
                            pos += length
                            break
                except UnicodeDecodeError:
                    continue
            else:
                pos += 1
        except:
            pos += 1
    
    # Pattern 4: Look for string references (like in code.bin)
    # Search for patterns that might indicate string data sections
    string_sections = []
    
    # Look for UTF-16 null terminators
    null_pattern = rb'\x00\x00'
    for match in re.finditer(null_pattern, data):
        # Try to find string before the null terminator
        start_pos = max(0, match.start() - 200)
        section = data[start_pos:match.start()]
        
        try:
            # Try UTF-16LE
            if len(section) % 2 == 0:
                decoded = section.decode('utf-16le', errors='ignore')
                # Find last meaningful substring
                lines = decoded.split('\x00')
                for line in reversed(lines):
                    if line.strip() and re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', line):
                        patterns.append({
                            'offset': match.start() - len(line.encode('utf-16le')),
                            'pattern': 'null_terminated_utf16',
                            'text': line.strip(),
                            'raw_bytes': line.encode('utf-16le')
                        })
                        break
        except:
            pass
    
    return patterns

def analyze_high_priority_files():
    """Analyze the top RTZ files identified by the explorer"""
    
    high_priority_files = [
        # UI-focused files (most likely to contain menu text)
        "romfs/system/option.rtz",
        "romfs/system/tuto.rtz", 
        "romfs/system/setting_list.rtz",
        "romfs/fight/fight_result.rtz",
        
        # Title screen files
        "romfs/title/ci.rtz",
        "romfs/title/ti.rtz",
        
        # Frontend files  
        "romfs/fe/tuto_001.rtz",
        "romfs/fe/menu_main.rtz",
        
        # High-scoring files
        "romfs/system/shop.rtz",
        "romfs/system/collection.rtz",
    ]
    
    print("🎯 ANALYZING HIGH PRIORITY RTZ FILES FOR JAPANESE TEXT")
    print("=" * 60)
    
    all_findings = []
    
    for file_path_str in high_priority_files:
        file_path = Path(file_path_str)
        
        if not file_path.exists():
            print(f"⚠️  Not found: {file_path}")
            continue
        
        print(f"\n📂 ANALYZING: {file_path}")
        print("-" * 40)
        
        try:
            # Decompress the file
            data = decompress_rtz(file_path)
            print(f"📊 Decompressed size: {len(data):,} bytes")
            
            # Find Japanese patterns
            patterns = find_japanese_patterns(data)
            
            if patterns:
                print(f"✅ Found {len(patterns)} Japanese text patterns")
                
                # Group by pattern type
                by_pattern = {}
                for p in patterns:
                    pattern_type = p['pattern']
                    if pattern_type not in by_pattern:
                        by_pattern[pattern_type] = []
                    by_pattern[pattern_type].append(p)
                
                # Show summary by pattern type
                for pattern_type, items in by_pattern.items():
                    print(f"   {pattern_type}: {len(items)} entries")
                
                # Show best examples
                print("\n🌟 BEST TEXT EXAMPLES:")
                sorted_patterns = sorted(patterns, key=lambda x: len(x['text']), reverse=True)
                for i, pattern in enumerate(sorted_patterns[:5], 1):
                    print(f"   {i}. [{pattern['pattern']}] @0x{pattern['offset']:04X}")
                    print(f"      Text: {pattern['text'][:80]}{'...' if len(pattern['text']) > 80 else ''}")
                
                all_findings.extend(patterns)
                
                # Save detailed results for this file
                output_file = f"{file_path.stem}_japanese_patterns.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Japanese Text Patterns from {file_path}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for pattern in sorted_patterns:
                        f.write(f"Offset: 0x{pattern['offset']:04X}\n")
                        f.write(f"Pattern: {pattern['pattern']}\n")
                        f.write(f"Text: {pattern['text']}\n")
                        f.write(f"Raw bytes: {pattern['raw_bytes'].hex()}\n")
                        f.write("\n")
                
                print(f"💾 Detailed results saved to: {output_file}")
                
            else:
                print("❌ No readable Japanese text patterns found")
                
                # Show hex dump for debugging
                print("\n🔍 HEX DUMP (first 160 bytes):")
                for i in range(0, min(160, len(data)), 16):
                    hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
                    ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
                    print(f"   {i:04x}: {hex_part:<48} {ascii_part}")
        
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    # Overall summary
    print(f"\n" + "=" * 60)
    print("🎯 OVERALL ANALYSIS SUMMARY")
    print("=" * 60)
    
    if all_findings:
        print(f"✅ Total Japanese text patterns found: {len(all_findings)}")
        
        # Group by pattern type
        pattern_counts = {}
        for finding in all_findings:
            pattern_type = finding['pattern']
            pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1
        
        print("\n📊 PATTERN TYPE BREAKDOWN:")
        for pattern_type, count in sorted(pattern_counts.items()):
            print(f"   {pattern_type}: {count} entries")
        
        # Show overall best examples
        print(f"\n🏆 OVERALL BEST TEXT EXAMPLES:")
        best_overall = sorted(all_findings, key=lambda x: len(x['text']), reverse=True)[:10]
        for i, pattern in enumerate(best_overall, 1):
            source_file = "unknown"  # We'd need to track this
            print(f"   {i:2d}. {pattern['text'][:60]}{'...' if len(pattern['text']) > 60 else ''}")
        
        print(f"\n💡 RECOMMENDED NEXT STEPS:")
        print(f"   1. Focus on files with 'kanji_kana' patterns (most similar to code.bin)")
        print(f"   2. Extract strings from files with most 'utf16le_japanese' patterns")
        print(f"   3. Use extract_rtz_content.py on promising files")
        print(f"   4. Test translation injection on highest-quality patterns")
        
    else:
        print("❌ No readable Japanese text found in any high-priority files")
        print("\n🤔 POSSIBLE EXPLANATIONS:")
        print("   • Text might be stored in a different encoding")
        print("   • Files might use a custom compression/encryption")
        print("   • Text might be split across multiple files")
        print("   • Script references might point to external string tables")

if __name__ == "__main__":
    analyze_high_priority_files()