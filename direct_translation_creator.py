#!/usr/bin/env python3
"""
Direct translation creator - bypass file format issues
Creates character selection translations directly from known working data
"""

import csv
from pathlib import Path

def create_direct_translations():
    """Create translations directly using our known working data"""
    
    # Known working translations from our previous analysis
    # These are the 7 strings with valid pointers from find_valid_character_strings.py
    translations = [
        {
            'pointer_offsets': '0x8D3F50',
            'pointer_value': '0x00949ED8',
            'separators': '00 00',
            'extract': 'You can change your character\'s appearance, name, and nickname',
            'original_japanese': '<|主人公|しゅじんこう|>の<|容姿|ようし|>や<|名前|なまえ|>、ニックネームを†<|変更|へんこう|>することができます',
            'context': 'Character customization main description',
            'priority': 1
        },
        {
            'pointer_offsets': '0x8D3F60',
            'pointer_value': '0x00949E70',
            'separators': '00 00 00 00',
            'extract': 'You can change StreetPass communication settings',
            'original_japanese': 'すれちがい<|通信|つうしん|>の<|設定|せってい|>を†<|変更|へんこう|>することができます',
            'context': 'Communication settings menu',
            'priority': 2
        },
        {
            'pointer_offsets': '0x8D3F48',
            'pointer_value': '0x00949B78',
            'separators': '00 00',
            'extract': 'This is the title displayed in communication fights.†Set your favorite title.',
            'original_japanese': '<|通信|つうしん|>ファイトで<|表示|ひょうじ|>する<|称号|しょうごう|>です。†お<|気|き|>に<|入|い|>りの<|称号|しょうごう|>を<|設定|せってい|>しましょう。',
            'context': 'Title/badge selection help text',
            'priority': 3
        },
        {
            'pointer_offsets': '0x8D3F40',
            'pointer_value': '0x00949C34',
            'separators': '00 00',
            'extract': 'This is the message displayed in communication fights.†Set a message for your opponent.',
            'original_japanese': '<|通信|つうしん|>ファイトで<|表示|ひょうじ|>するメッセージです。†<|相手|あいて|>へのメッセージを<|設定|せってい|>しましょう。',
            'context': 'Message customization help text',
            'priority': 4
        },
        {
            'pointer_offsets': '0x8D3F28',
            'pointer_value': '0x00949DC8',
            'separators': '00 00',
            'extract': 'You can check win rates and information for characters†and other players you\'ve faced in events',
            'original_japanese': 'イベントで<|対戦|たいせん|>したキャラクターや<|他|ほか|>の†プレイヤーとの<|勝率|しょうりつ|>や<|情報|じょうほう|>を<|確認|かくにん|>できます',
            'context': 'Player statistics help text',
            'priority': 5
        },
        {
            'pointer_offsets': '0x8D3F58',
            'pointer_value': '0x0094A21C',
            'separators': '00 00',
            'extract': 'You can fight characters from events and†other players through communication',
            'original_japanese': 'イベントで<|対戦|たいせん|>したキャラクターや†<|通信|つうしん|>で<|他|ほか|>のプレイヤーとファイトできます',
            'context': 'Multiplayer options help text',
            'priority': 6
        },
        {
            'pointer_offsets': '0x8D3F10',
            'pointer_value': '0x00949F5C',
            'separators': '00 00',
            'extract': 'Press the START button during the tutorial†to exit at any time',
            'original_japanese': 'チュートリアル<|中|ちゅう|>に<|START|スタート|>ボタンを<|押|お|>すと†<|途中|とちゅう|>で<|終了|しゅうりょう|>することができます',
            'context': 'Tutorial exit instructions',
            'priority': 7
        }
    ]
    
    print("=" * 60)
    print("   CREATING DIRECT CHARACTER TRANSLATIONS")
    print("=" * 60)
    
    # Validate all translations
    print("🔍 VALIDATING TRANSLATIONS:")
    all_valid = True
    for i, trans in enumerate(translations, 1):
        try:
            text = trans['extract'].replace('†', '\n')
            utf16_bytes = text.encode('utf-16le')
            print(f"   ✅ Translation {i}: {len(utf16_bytes)} UTF-16LE bytes")
        except Exception as e:
            print(f"   ❌ Translation {i}: Encoding error - {e}")
            all_valid = False
    
    if not all_valid:
        print("❌ Some translations have encoding issues")
        return False
    
    # Save complete translation set
    output_csv = Path("files/character_selection_complete.csv")
    fieldnames = list(translations[0].keys())
    
    with output_csv.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(translations)
    
    print(f"\n📁 Complete translation set saved: {output_csv}")
    print(f"📊 Total translations: {len(translations)}")
    
    # Show translation summary
    print(f"\n🎯 TRANSLATION SUMMARY:")
    for trans in translations:
        print(f"   {trans['priority']}. {trans['context']}")
        print(f"      Pointer: {trans['pointer_offsets']}")
        print(f"      English: {trans['extract'][:50]}...")
        print()
    
    return output_csv

def create_injection_script():
    """Create the injection script"""
    injection_code = '''#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

BASE_ADDR = 0x0100000
INPUT_BIN = Path("files/full_padded.bin")
TRANSLATION_CSV = Path("files/character_selection_complete.csv")
OUTPUT_BIN = Path("files/full_patched_complete.bin")

try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

def parse_separators(sep_field: str) -> bytes:
    if sep_field.strip() == "(aucun)":
        return b""
    parts = sep_field.split()
    return bytes(int(p, 16) for p in parts)

def main():
    print("=" * 60)
    print("   COMPLETE CHARACTER TRANSLATION INJECTION")
    print("=" * 60)
    
    if not INPUT_BIN.exists():
        print(f"❌ Input file not found: {INPUT_BIN}")
        return False
    
    if not TRANSLATION_CSV.exists():
        print(f"❌ Translation file not found: {TRANSLATION_CSV}")
        return False
    
    data = bytearray(INPUT_BIN.read_bytes())
    orig_len = len(data)
    print(f"⚙ Loaded binary: {orig_len:,} bytes")
    
    with TRANSLATION_CSV.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        translations = list(reader)
    
    print(f"📝 Loaded {len(translations)} translations")
    
    cursor = orig_len
    successful_injections = 0
    
    for trans in translations:
        priority = trans.get('priority', '?')
        print(f"\\n🔧 Processing translation {priority}/7:")
        print(f"   Context: {trans.get('context', 'Unknown')}")
        
        txt = trans['extract'].replace('†', '\\n')
        utf16_bytes = txt.encode('utf-16le')
        sep_bytes = parse_separators(trans['separators'])
        block = utf16_bytes + sep_bytes
        
        new_file_off = cursor
        new_addr = BASE_ADDR + new_file_off
        
        # Update pointer
        addr_virt = int(trans['pointer_offsets'], 16)
        off = addr_virt - BASE_ADDR
        
        if 0 <= off < len(data) - 4:
            data[off:off + 4] = new_addr.to_bytes(4, 'little')
            data.extend(block)
            cursor += len(block)
            successful_injections += 1
            
            print(f"   ✅ Updated pointer @ {hex(addr_virt)} → {hex(new_addr)}")
            print(f"   📍 Added {len(block)} bytes")
        else:
            print(f"   ❌ Invalid pointer: {hex(addr_virt)}")
    
    OUTPUT_BIN.write_bytes(data)
    
    print(f"\\n" + "=" * 60)
    print(f"✅ SUCCESS: {successful_injections}/{len(translations)} translations injected")
    print(f"📁 Output: {OUTPUT_BIN}")
    print(f"📊 Added: {len(data) - orig_len:,} bytes")
    
    return successful_injections == len(translations)

if __name__ == "__main__":
    main()
'''
    
    script_path = Path("inject_character_selection_complete.py")
    script_path.write_text(injection_code)
    print(f"📁 Created injection script: {script_path}")
    return script_path

def main():
    print("🎯 Creating complete character translation set (direct approach)")
    
    # Create translations
    result = create_direct_translations()
    
    if result:
        # Create injection script
        injection_script = create_injection_script()
        
        print(f"\n✅ READY FOR INJECTION!")
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. python3 inject_character_selection_complete.py")
        print(f"2. ./phase_4_3_rom_building.sh")
        print(f"3. Test ROM in Citra")
        print(f"\n🎮 Expected: 7/7 character translations (100% success)")
    else:
        print(f"\n❌ Failed to create translations")

if __name__ == "__main__":
    main()