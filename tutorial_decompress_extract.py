#!/usr/bin/env python3
"""
🛡️ CF VANGUARD TUTORIAL RTZ DECOMPRESSOR
Decompress RTZ files and extract readable Japanese text
"""

import os
import re
import gzip
import struct
from pathlib import Path

def decompress_rtz(file_path):
    """Decompress RTZ file (gzip compressed)"""
    print(f"🗜️  Decompressing RTZ file: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Check if it's gzip compressed
    if data[:2] == b'\x1f\x8b':
        print("✅ Detected gzip compression")
        try:
            # Skip the first 4 bytes (seems to be a header) and decompress the rest
            compressed_data = data[4:]
            decompressed = gzip.decompress(compressed_data)
            print(f"📊 Decompressed: {len(data)} → {len(decompressed)} bytes")
            return decompressed
        except Exception as e:
            print(f"❌ Decompression failed: {e}")
            return None
    else:
        print("ℹ️  File doesn't appear to be gzip compressed")
        return data

def find_clean_japanese_text(data):
    """Find clean Japanese text with proper position tracking"""
    found_text = []
    
    # Try different encodings
    encodings_to_try = [
        ('utf-8', 'UTF-8'),
        ('utf-16le', 'UTF-16 Little Endian'), 
        ('utf-16be', 'UTF-16 Big Endian'),
        ('shift_jis', 'Shift-JIS')
    ]
    
    for encoding, encoding_name in encodings_to_try:
        try:
            # Decode the entire data
            text = data.decode(encoding, errors='ignore')
            
            # Find Japanese text patterns
            japanese_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+'
            
            for match in re.finditer(japanese_pattern, text):
                japanese_text = match.group()
                if len(japanese_text) >= 2:  # Minimum 2 characters
                    # Calculate byte position in original data
                    char_pos = match.start()
                    try:
                        byte_pos = len(text[:char_pos].encode(encoding))
                        if byte_pos < len(data):  # Valid position
                            found_text.append({
                                'text': japanese_text,
                                'position': byte_pos,
                                'encoding': encoding_name,
                                'char_position': char_pos
                            })
                    except:
                        continue
                        
        except Exception as e:
            continue
    
    # Remove duplicates and sort by position
    unique_text = []
    seen_texts = set()
    
    for item in found_text:
        if item['text'] not in seen_texts:
            seen_texts.add(item['text'])
            unique_text.append(item)
    
    return sorted(unique_text, key=lambda x: x['position'])

def analyze_bin_file(file_path):
    """Analyze BIN file structure and extract text"""
    print(f"\n🔍 Analyzing BIN file: {file_path}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"📊 File size: {len(data):,} bytes")
    
    # Look at the header
    header = data[:64]
    print(f"🏷️  Header (hex): {header.hex()[:64]}...")
    
    # Try to find readable ASCII strings first
    ascii_text = data.decode('ascii', errors='ignore')
    print(f"🔤 Header as ASCII: {ascii_text[:64]}...")
    
    # Look for Japanese text
    japanese_text = find_clean_japanese_text(data)
    
    if japanese_text:
        print(f"✅ Found {len(japanese_text)} Japanese text entries:")
        return japanese_text
    else:
        print("❌ No Japanese text found")
        return []

def extract_tutorial_text():
    """Main function to extract tutorial text"""
    print("🛡️ CF VANGUARD TUTORIAL TEXT EXTRACTOR V2")
    print("=" * 55)
    
    # Focus on one clean version
    tutorial_files = [
        "romfs/fe/tuto_001.rtz",
        "romfs/fe/tuto_001.bin"
    ]
    
    all_extracted_text = []
    
    for file_path in tutorial_files:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            continue
            
        print(f"\n" + "="*60)
        print(f"📖 PROCESSING: {file_path}")
        print("="*60)
        
        if file_path.endswith('.rtz'):
            # Decompress and analyze RTZ
            decompressed_data = decompress_rtz(file_path)
            if decompressed_data:
                # Save decompressed data for inspection
                decompressed_file = f"{Path(file_path).stem}_decompressed.bin"
                with open(decompressed_file, 'wb') as f:
                    f.write(decompressed_data)
                print(f"💾 Saved decompressed data to: {decompressed_file}")
                
                # Extract text from decompressed data
                japanese_text = find_clean_japanese_text(decompressed_data)
                
                if japanese_text:
                    print(f"✅ Found {len(japanese_text)} Japanese text entries in RTZ:")
                    for i, entry in enumerate(japanese_text[:10]):
                        print(f"   {i+1:2d}. 0x{entry['position']:04X}: {entry['text']}")
                    all_extracted_text.extend(japanese_text)
                else:
                    print("❌ No clean Japanese text found in decompressed RTZ")
        
        elif file_path.endswith('.bin'):
            # Analyze BIN file directly
            japanese_text = analyze_bin_file(file_path)
            if japanese_text:
                print(f"✅ Found {len(japanese_text)} Japanese text entries in BIN:")
                for i, entry in enumerate(japanese_text[:10]):
                    print(f"   {i+1:2d}. 0x{entry['position']:04X}: {entry['text']}")
                all_extracted_text.extend(japanese_text)
    
    # Save all extracted text
    if all_extracted_text:
        output_file = "tutorial_japanese_text.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("🛡️ CF VANGUARD TUTORIAL JAPANESE TEXT\n")
            f.write("=" * 50 + "\n\n")
            
            for i, entry in enumerate(all_extracted_text):
                f.write(f"Entry {i+1}:\n")
                f.write(f"Position: 0x{entry['position']:06X}\n")
                f.write(f"Encoding: {entry['encoding']}\n")
                f.write(f"Text: {entry['text']}\n")
                f.write("-" * 30 + "\n\n")
        
        print(f"\n💾 Saved all extracted text to: {output_file}")
        
        # Show the most promising entries
        print(f"\n🌟 MOST PROMISING TEXT ENTRIES:")
        print("-" * 40)
        
        # Filter for longer, more meaningful text
        meaningful_text = [t for t in all_extracted_text if len(t['text']) >= 3]
        
        for i, entry in enumerate(meaningful_text[:15]):  # Show top 15
            print(f"{i+1:2d}. [{entry['encoding']}] {entry['text']}")
        
    else:
        print("\n❌ No Japanese text could be extracted from any file")

if __name__ == "__main__":
    extract_tutorial_text()