#!/usr/bin/env python3
"""
CF Vanguard Safe String Replacement Test
Replaces existing Japanese strings with English ones in-place
Much safer than appending new strings and updating pointers
"""

from pathlib import Path
import struct

# Configuration
INPUT_BIN = Path("files/full_padded.bin")
OUTPUT_BIN = Path("files/full_safe_test.bin")

# Simple test replacements - find Japanese strings and replace with English
TEST_REPLACEMENTS = [
    {
        'search_japanese': 'ゲームの環境設定を行います',  # "Configure game environment"
        'replace_english': 'Configure game settings',
        'description': 'Game settings menu text'
    },
    {
        'search_japanese': 'デッキの作成や編集をします', # "Create and edit decks"
        'replace_english': 'Create and edit decks',
        'description': 'Deck customization text'
    },
    {
        'search_japanese': 'ファイトの遊び方を確認します', # "Check how to play Fight"
        'replace_english': 'Check how to play Fight',
        'description': 'Tutorial/help text'
    }
]

def find_utf16_string(data, search_text):
    """Find UTF-16LE encoded string in binary data"""
    search_bytes = search_text.encode('utf-16le')
    offset = data.find(search_bytes)
    return offset if offset != -1 else None

def replace_utf16_string(data, offset, original_text, new_text):
    """Replace UTF-16LE string at specific offset, padding if necessary"""
    original_bytes = original_text.encode('utf-16le')
    new_bytes = new_text.encode('utf-16le')
    
    # Pad or truncate to same length
    if len(new_bytes) < len(original_bytes):
        # Pad with spaces and null terminator
        padding_needed = len(original_bytes) - len(new_bytes)
        new_bytes += ' '.encode('utf-16le') * (padding_needed // 2)
    elif len(new_bytes) > len(original_bytes):
        # Truncate to fit
        new_bytes = new_bytes[:len(original_bytes)]
    
    return new_bytes

def main():
    print("🛡️ CF VANGUARD SAFE STRING REPLACEMENT TEST")
    print("=" * 50)
    
    # Load binary
    data = bytearray(INPUT_BIN.read_bytes())
    print(f"📁 Loaded binary: {len(data):,} bytes")
    
    replacements_made = 0
    
    for i, replacement in enumerate(TEST_REPLACEMENTS, 1):
        print(f"\n🔍 Test {i}: {replacement['description']}")
        
        # Find Japanese string
        offset = find_utf16_string(data, replacement['search_japanese'])
        
        if offset is not None:
            print(f"   ✅ Found Japanese text at offset {hex(offset)}")
            print(f"   📝 Original: '{replacement['search_japanese']}'")
            print(f"   🔄 Replacing with: '{replacement['replace_english']}'")
            
            # Replace the string
            new_bytes = replace_utf16_string(
                data, offset, 
                replacement['search_japanese'], 
                replacement['replace_english']
            )
            
            # Update the binary
            original_length = len(replacement['search_japanese'].encode('utf-16le'))
            data[offset:offset + original_length] = new_bytes
            
            print(f"   ✅ Replacement successful!")
            replacements_made += 1
            
        else:
            print(f"   ❌ Japanese text not found in binary")
    
    if replacements_made > 0:
        # Save the modified binary
        OUTPUT_BIN.write_bytes(data)
        
        print(f"\n🎉 SAFE REPLACEMENT TEST COMPLETE!")
        print(f"=" * 50)
        print(f"📁 Output: {OUTPUT_BIN}")
        print(f"📊 Size: {len(data):,} bytes (unchanged)")
        print(f"✅ Replacements made: {replacements_made}/{len(TEST_REPLACEMENTS)}")
        print(f"\n🎯 ADVANTAGES OF THIS METHOD:")
        print(f"- ✅ No memory layout changes")
        print(f"- ✅ No pointer updates needed")
        print(f"- ✅ Same file size (very stable)")
        print(f"- ✅ Easy to test and validate")
        
        print(f"\n🔧 TO BUILD TEST ROM:")
        print(f"1. Copy exheader: cp files/exheader.bin files/exheader_safe.bin")
        print(f"2. Build ROM:")
        print(f"   ./tools/makerom -f cci -o cf_vanguard_safe_test.3ds \\")
        print(f"       -rsf files/cf_vanguard.rsf \\")
        print(f"       -code {OUTPUT_BIN} \\")
        print(f"       -exheader files/exheader_safe.bin \\")
        print(f"       -romfs romfs.bin")
        
        print(f"\n🎮 TESTING:")
        print(f"Look for these English translations in the game:")
        for repl in TEST_REPLACEMENTS:
            if find_utf16_string(data, repl['search_japanese']) or True:  # Show all for reference
                print(f"   - '{repl['replace_english']}' ({repl['description']})")
    
    else:
        print(f"\n❌ No replacements could be made.")
        print(f"The Japanese strings might not exist in the binary as expected.")
        
        print(f"\n🔍 DEBUGGING:")
        print(f"Try searching for shorter Japanese text snippets or")
        print(f"check if the strings are stored in RTZ files instead.")

if __name__ == "__main__":
    main()