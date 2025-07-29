#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to validate our character selection translations
"""

import csv
from pathlib import Path

def test_translations():
    """Test our translation CSV file format and content."""
    
    translation_file = Path("../files/character_selection_translated.csv")
    
    if not translation_file.exists():
        print("❌ Translation file not found!")
        return False
    
    print("🔍 Testing translation file...")
    
    try:
        with translation_file.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
        
        print(f"✅ Found {len(rows)} translation entries")
        
        for i, row in enumerate(rows):
            print(f"\n📝 Translation #{i+1}:")
            print(f"   Pointer: {row['pointer_value']}")
            print(f"   Translation: {row['extract']}")
            print(f"   Separators: {row['separators']}")
            
            # Test UTF-16LE encoding
            try:
                utf16_bytes = row['extract'].encode('utf-16le')
                print(f"   UTF-16LE bytes: {len(utf16_bytes)} bytes")
            except Exception as e:
                print(f"   ❌ UTF-16LE encoding error: {e}")
                return False
        
        print(f"\n✅ All translations validated!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading translation file: {e}")
        return False

if __name__ == "__main__":
    print("🎮 CF VANGUARD Translation Test")
    print("=" * 50)
    
    test_translations()
