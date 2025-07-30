#!/usr/bin/env python3
"""
🛡️ CF VANGUARD TUTORIAL TEXT EXTRACTOR
Extract and analyze Japanese text from tutorial RTZ/BIN files
"""

import os
import re
import struct
from pathlib import Path

def find_japanese_text(data, min_length=4):
    """Find Japanese text in binary data"""
    # Japanese Unicode ranges
    japanese_patterns = [
        # Hiragana: U+3040-U+309F
        r'[\u3040-\u309F]+',
        # Katakana: U+30A0-U+30FF  
        r'[\u30A0-\u30FF]+',
        # Kanji: U+4E00-U+9FAF
        r'[\u4E00-\u9FAF]+',
        # Mixed Japanese
        r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3000-\u303F\uFF00-\uFFEF]+',
    ]
    
    found_text = []
    
    # Try different encodings
    encodings = ['utf-8', 'utf-16le', 'utf-16be', 'shift_jis', 'euc-jp']
    
    for encoding in encodings:
        try:
            # Decode the data
            text = data.decode(encoding, errors='ignore')
            
            # Find Japanese text using patterns
            for pattern in japanese_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) >= min_length:
                        # Get position in original data
                        try:
                            pos = data.find(match.encode(encoding))
                            found_text.append({
                                'text': match,
                                'encoding': encoding,
                                'position': pos,
                                'length': len(match.encode(encoding))
                            })
                        except:
                            continue
                            
        except UnicodeDecodeError:
            continue
    
    # Remove duplicates and sort by position
    unique_text = []
    seen = set()
    for item in found_text:
        key = (item['text'], item['encoding'])
        if key not in seen:
            seen.add(key)
            unique_text.append(item)
    
    return sorted(unique_text, key=lambda x: x['position'])

def analyze_rtz_structure(file_path):
    """Analyze RTZ file structure"""
    print(f"\n🔍 Analyzing RTZ structure: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"📊 File size: {len(data):,} bytes")
    
    # Look for common headers/magic numbers
    header = data[:16]
    print(f"🏷️  Header (hex): {header.hex()}")
    print(f"🏷️  Header (ascii): {header.decode('ascii', errors='ignore')}")
    
    # Check for possible string tables or text sections
    # Look for repeated patterns that might indicate structure
    if len(data) >= 4:
        # Try to read as little-endian 32-bit integers
        try:
            first_int = struct.unpack('<I', data[:4])[0]
            print(f"🔢 First 4 bytes as uint32: {first_int}")
            
            # If it's a reasonable number, might be a count or offset
            if first_int < len(data):
                print(f"   Could be: offset or count ({first_int} < file_size)")
        except:
            pass
    
    return data

def analyze_bin_structure(file_path):
    """Analyze BIN file structure"""
    print(f"\n🔍 Analyzing BIN structure: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"📊 File size: {len(data):,} bytes")
    
    # Look for patterns
    header = data[:32]
    print(f"🏷️  Header (hex): {header.hex()}")
    
    return data

def search_tutorial_files():
    """Search for tutorial files and extract text"""
    print("🛡️ CF VANGUARD TUTORIAL TEXT EXTRACTOR")
    print("=" * 50)
    
    # Look for tutorial files
    tutorial_patterns = [
        "tuto_001.rtz",
        "tuto_001.bin", 
        "**/tuto_001.*",
        "**/fe/**/tuto_001.*"
    ]
    
    found_files = []
    
    # Search current directory and subdirectories
    for pattern in tutorial_patterns:
        for file_path in Path('.').glob(pattern):
            if file_path.is_file():
                found_files.append(file_path)
    
    # Also search in fe directory specifically
    fe_dir = Path('fe')
    if fe_dir.exists():
        print(f"📁 Found 'fe' directory, searching...")
        for file_path in fe_dir.rglob('tuto_001.*'):
            if file_path.is_file():
                found_files.append(file_path)
    
    if not found_files:
        print("❌ No tutorial files found. Please check file paths.")
        print("🔍 Looking for files matching:")
        for pattern in tutorial_patterns:
            print(f"   - {pattern}")
        
        # List what we can find
        print(f"\n📂 Current directory contents:")
        for item in Path('.').iterdir():
            if item.is_dir():
                print(f"   📁 {item.name}/")
            else:
                print(f"   📄 {item.name}")
        return
    
    print(f"✅ Found {len(found_files)} tutorial file(s):")
    for file_path in found_files:
        print(f"   📄 {file_path}")
    
    # Analyze each file
    for file_path in found_files:
        print(f"\n" + "="*60)
        print(f"📖 ANALYZING: {file_path}")
        print("="*60)
        
        if file_path.suffix.lower() == '.rtz':
            data = analyze_rtz_structure(file_path)
        elif file_path.suffix.lower() == '.bin':
            data = analyze_bin_structure(file_path)
        else:
            print(f"🔍 Generic binary analysis for {file_path}")
            with open(file_path, 'rb') as f:
                data = f.read()
            print(f"📊 File size: {len(data):,} bytes")
        
        # Search for Japanese text
        print(f"\n🔤 Searching for Japanese text...")
        japanese_text = find_japanese_text(data)
        
        if japanese_text:
            print(f"✅ Found {len(japanese_text)} Japanese text entries:")
            for i, entry in enumerate(japanese_text[:10]):  # Show first 10
                print(f"   {i+1:2d}. Position 0x{entry['position']:06X} ({entry['encoding']}): {entry['text'][:50]}...")
            
            if len(japanese_text) > 10:
                print(f"   ... and {len(japanese_text) - 10} more entries")
                
            # Save extracted text to file
            output_file = f"{file_path.stem}_extracted_text.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Extracted Japanese text from {file_path}\n")
                f.write("="*50 + "\n\n")
                for i, entry in enumerate(japanese_text):
                    f.write(f"Entry {i+1}:\n")
                    f.write(f"Position: 0x{entry['position']:06X}\n")
                    f.write(f"Encoding: {entry['encoding']}\n")
                    f.write(f"Length: {entry['length']} bytes\n")
                    f.write(f"Text: {entry['text']}\n")
                    f.write("-"*30 + "\n\n")
            
            print(f"💾 Saved extracted text to: {output_file}")
        else:
            print("❌ No Japanese text found in this file")
            
            # Try to find any readable text
            print("🔍 Searching for any readable text...")
            try:
                # Try UTF-8 first
                text = data.decode('utf-8', errors='ignore')
                readable_parts = re.findall(r'[A-Za-z0-9\s]{4,}', text)
                if readable_parts:
                    print(f"📝 Found {len(readable_parts)} readable text segments:")
                    for part in readable_parts[:5]:
                        print(f"   - {part[:30]}...")
            except:
                pass

if __name__ == "__main__":
    search_tutorial_files()