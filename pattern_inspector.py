#!/usr/bin/env python3
"""
JAPANESE PATTERN INSPECTOR
==========================
Examine the specific Japanese pattern found in tuto_001.rtz
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

def analyze_specific_pattern():
    """Look for the specific pattern we found: <|次|つぎ|>に、ジ"""
    
    target_file = Path("romfs/fe/tuto_001.rtz")
    if not target_file.exists():
        print(f"❌ File not found: {target_file}")
        return
    
    print("🔍 ANALYZING SPECIFIC JAPANESE PATTERN")
    print("=" * 40)
    print(f"Target pattern: <|次|つぎ|>に、ジ")
    print(f"File: {target_file}")
    print()
    
    # Decompress the file
    data = decompress_rtz(target_file)
    print(f"📊 Decompressed size: {len(data):,} bytes")
    
    # Search for the specific pattern components
    patterns_to_find = [
        # The exact pattern we saw
        "<|次|つぎ|>",
        "次",  # The kanji alone
        "つぎ",  # The kana alone
        "に、ジ",  # The continuation
        
        # Related patterns
        "<|",  # Start of kanji/kana markup
        "|>",  # End of kanji/kana markup
    ]
    
    print("🔍 SEARCHING FOR PATTERN COMPONENTS:")
    print("-" * 40)
    
    findings = {}
    
    for pattern in patterns_to_find:
        print(f"\n🎯 Searching for: '{pattern}'")
        
        # Try different encodings
        encodings_to_try = [
            ('utf-8', pattern.encode('utf-8')),
            ('utf-16le', pattern.encode('utf-16le')),
            ('utf-16be', pattern.encode('utf-16be')),
            ('shift-jis', pattern.encode('shift-jis')),
        ]
        
        pattern_findings = []
        
        for encoding_name, encoded_pattern in encodings_to_try:
            try:
                positions = []
                pos = 0
                while pos < len(data):
                    pos = data.find(encoded_pattern, pos)
                    if pos == -1:
                        break
                    positions.append(pos)
                    pos += len(encoded_pattern)
                
                if positions:
                    print(f"   ✅ {encoding_name}: {len(positions)} occurrences")
                    for i, pos in enumerate(positions[:3]):  # Show first 3
                        print(f"      Position {i+1}: 0x{pos:04X}")
                        
                        # Show context around the match
                        start = max(0, pos - 20)
                        end = min(len(data), pos + len(encoded_pattern) + 20)
                        context = data[start:end]
                        
                        print(f"      Context (hex): {context.hex()}")
                        
                        # Try to decode context in the same encoding
                        try:
                            if encoding_name == 'utf-16le':
                                # Align to 2-byte boundary
                                if start % 2 != 0:
                                    start -= 1
                                if len(context) % 2 != 0:
                                    context = context[:-1]
                                
                            decoded_context = context.decode(encoding_name, errors='ignore')
                            readable_context = ''.join(c if c.isprintable() else '.' for c in decoded_context)
                            print(f"      Context (text): {readable_context}")
                            
                        except:
                            print(f"      Context (text): [decode failed]")
                        
                        print()
                    
                    pattern_findings.append({
                        'encoding': encoding_name,
                        'positions': positions,
                        'encoded_bytes': encoded_pattern
                    })
                else:
                    print(f"   ❌ {encoding_name}: not found")
                    
            except UnicodeEncodeError:
                print(f"   ⚠️  {encoding_name}: encoding not possible")
        
        findings[pattern] = pattern_findings
    
    # Look for potential string sections around the found patterns
    print("\n" + "=" * 40)
    print("🎯 ANALYZING STRING SECTIONS")
    print("=" * 40)
    
    # Find areas with high density of Japanese-like patterns
    japanese_bytes = []
    
    # UTF-16LE Japanese character ranges
    for char_code in range(0x3040, 0x309F):  # Hiragana
        japanese_bytes.extend([char_code & 0xFF, (char_code >> 8) & 0xFF])
    for char_code in range(0x30A0, 0x30FF):  # Katakana  
        japanese_bytes.extend([char_code & 0xFF, (char_code >> 8) & 0xFF])
    for char_code in range(0x4E00, 0x9FAF, 100):  # Kanji (sample)
        japanese_bytes.extend([char_code & 0xFF, (char_code >> 8) & 0xFF])
    
    # Find sections with high concentration of these bytes
    window_size = 100
    best_sections = []
    
    for i in range(0, len(data) - window_size, 20):
        window = data[i:i + window_size]
        japanese_byte_count = sum(1 for b in window if b in japanese_bytes)
        density = japanese_byte_count / window_size
        
        if density > 0.1:  # At least 10% Japanese-like bytes
            best_sections.append((i, density))
    
    # Sort by density and show top sections
    best_sections.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Found {len(best_sections)} sections with high Japanese byte density")
    
    for i, (offset, density) in enumerate(best_sections[:5], 1):
        print(f"\n📍 Section {i}: Offset 0x{offset:04X}, Density {density:.2%}")
        
        section_data = data[offset:offset + window_size]
        
        # Try UTF-16LE decoding
        try:
            if offset % 2 != 0:
                # Align to 2-byte boundary
                section_data = data[offset-1:offset-1 + window_size]
                offset -= 1
            
            if len(section_data) % 2 != 0:
                section_data = section_data[:-1]
            
            decoded = section_data.decode('utf-16le', errors='ignore')
            readable = ''.join(c if c.isprintable() else '.' for c in decoded)
            
            print(f"   UTF-16LE: {readable[:80]}{'...' if len(readable) > 80 else ''}")
            
            # Look for Japanese characters specifically
            japanese_chars = re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+', decoded)
            if japanese_chars:
                print(f"   Japanese found: {japanese_chars[:3]}")
            
        except Exception as e:
            print(f"   UTF-16LE decode failed: {e}")
        
        # Show hex dump
        hex_dump = ' '.join(f'{b:02x}' for b in section_data[:32])
        print(f"   Hex: {hex_dump}...")

if __name__ == "__main__":
    analyze_specific_pattern()