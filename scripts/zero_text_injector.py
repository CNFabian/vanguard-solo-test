#!/usr/bin/env python3
"""
ZERO TEXT TEST INJECTOR - PHASE 5.3.1 DEBUG
Replace ALL text in RTZ files with "0" to test injection mechanism
"""

import struct
import gzip
import shutil
from pathlib import Path
import re
from typing import List, Dict, Optional

class ZeroTextInjector:
    def __init__(self):
        self.romfs_dir = Path("romfs")
        self.output_dir = Path("romfs_zero_test")
        self.debug_dir = Path("debug_zero_test")
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.debug_dir.mkdir(exist_ok=True)
        
        self.stats = {
            'files_processed': 0,
            'files_modified': 0, 
            'text_replacements': 0,
            'errors': 0
        }
    
    def decompress_rtz(self, rtz_path: Path) -> Optional[bytes]:
        """Decompress RTZ file"""
        try:
            data = rtz_path.read_bytes()
            if len(data) < 4:
                return None
                
            size = struct.unpack('<I', data[:4])[0]
            if not (100 < size < 10000000):
                return None
                
            gzip_data = data[4:]
            if not gzip_data.startswith(b'\x1f\x8b'):
                return None
                
            decompressed = gzip.decompress(gzip_data)
            return decompressed
            
        except Exception as e:
            print(f"❌ Decompression failed for {rtz_path.name}: {e}")
            return None
    
    def compress_rtz(self, data: bytes) -> bytes:
        """Compress data back to RTZ format"""
        try:
            # Compress the data
            compressed = gzip.compress(data, compresslevel=6)
            
            # Add size header
            size_header = struct.pack('<I', len(data))
            
            return size_header + compressed
            
        except Exception as e:
            print(f"❌ Compression failed: {e}")
            return None
    
    def replace_all_text_with_zero(self, data: bytes) -> tuple[bytes, int]:
        """Replace ALL text in the data with '0'"""
        replacements = 0
        modified_data = bytearray(data)
        
        # Strategy 1: Replace UTF-16LE text patterns
        replacements += self.replace_utf16_text(modified_data, '0')
        
        # Strategy 2: Replace UTF-8 text patterns  
        replacements += self.replace_utf8_text(modified_data, '0')
        
        # Strategy 3: Replace Shift-JIS text patterns
        replacements += self.replace_shift_jis_text(modified_data, '0')
        
        return bytes(modified_data), replacements
    
    def replace_utf16_text(self, data: bytearray, replacement: str) -> int:
        """Replace UTF-16LE text with replacement string"""
        replacements = 0
        replacement_bytes = replacement.encode('utf-16le')
        
        # Look for Japanese/English text patterns in UTF-16LE
        i = 0
        while i < len(data) - 6:  # Need at least 6 bytes for meaningful text
            try:
                # Try to decode a chunk as UTF-16LE
                chunk_size = min(200, len(data) - i)  # Max 200 bytes
                if chunk_size % 2 == 1:
                    chunk_size -= 1
                
                chunk = data[i:i + chunk_size]
                
                try:
                    decoded = chunk.decode('utf-16le', errors='strict')
                except:
                    i += 2  # Move by 2 bytes for UTF-16 alignment
                    continue
                
                # Check if this looks like meaningful text
                if self.is_meaningful_text(decoded):
                    # Find the actual text boundaries
                    text_start, text_end = self.find_text_boundaries(data, i, chunk_size)
                    
                    if text_end > text_start:
                        # Calculate replacement size
                        original_text_size = text_end - text_start
                        
                        # Replace with "0" but preserve original byte length if possible
                        zero_repeated = '0' * (original_text_size // 2)  # UTF-16LE is 2 bytes per char
                        if len(zero_repeated) == 0:
                            zero_repeated = '0'
                        
                        zero_bytes = zero_repeated.encode('utf-16le')
                        
                        # Pad or truncate to match original size
                        if len(zero_bytes) < original_text_size:
                            zero_bytes += b'\x00' * (original_text_size - len(zero_bytes))
                        elif len(zero_bytes) > original_text_size:
                            zero_bytes = zero_bytes[:original_text_size]
                        
                        # Replace the text
                        data[text_start:text_end] = zero_bytes[:original_text_size]
                        replacements += 1
                        
                        # Skip past this replacement
                        i = text_end
                        continue
                
                i += 2  # Move by 2 bytes for UTF-16 alignment
                
            except:
                i += 1
        
        return replacements
    
    def replace_utf8_text(self, data: bytearray, replacement: str) -> int:
        """Replace UTF-8 text with replacement string"""
        replacements = 0
        
        # Look for UTF-8 patterns
        i = 0
        while i < len(data) - 3:
            try:
                # Try to find UTF-8 text
                chunk_size = min(100, len(data) - i)
                chunk = data[i:i + chunk_size]
                
                try:
                    decoded = chunk.decode('utf-8', errors='strict')
                except:
                    i += 1
                    continue
                
                if self.is_meaningful_text(decoded):
                    # Find null terminator or end of meaningful text
                    text_end = i
                    while text_end < len(data) and data[text_end] != 0:
                        text_end += 1
                    
                    text_length = text_end - i
                    if text_length > 3:  # Only replace meaningful chunks
                        replacement_bytes = replacement.encode('utf-8')
                        
                        # Pad to original length
                        if len(replacement_bytes) < text_length:
                            replacement_bytes += b'\x00' * (text_length - len(replacement_bytes))
                        
                        data[i:i + text_length] = replacement_bytes[:text_length]
                        replacements += 1
                        i += text_length
                        continue
                
                i += 1
                
            except:
                i += 1
        
        return replacements
    
    def replace_shift_jis_text(self, data: bytearray, replacement: str) -> int:
        """Replace Shift-JIS text with replacement string"""
        replacements = 0
        
        # Look for Shift-JIS patterns (common in Japanese games)
        # This is more complex but let's try a simple approach
        
        # Look for common Shift-JIS byte patterns
        japanese_patterns = [
            b'\x82\xa0',  # あ in Shift-JIS
            b'\x82\xa2',  # い in Shift-JIS
            b'\x83J',     # カ in Shift-JIS
            b'\x83^\x83\x93',  # タン in Shift-JIS
        ]
        
        for pattern in japanese_patterns:
            pos = 0
            while pos < len(data):
                pos = data.find(pattern, pos)
                if pos == -1:
                    break
                
                # Replace this character with '0' in Shift-JIS
                zero_sjis = '0'.encode('shift_jis')
                data[pos:pos + len(pattern)] = zero_sjis + b'\x00' * (len(pattern) - len(zero_sjis))
                replacements += 1
                pos += len(pattern)
        
        return replacements
    
    def is_meaningful_text(self, text: str) -> bool:
        """Check if decoded text looks meaningful"""
        if len(text) < 3:
            return False
        
        # Must contain readable characters
        readable_chars = re.findall(r'[a-zA-Z\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf0-9]', text)
        if len(readable_chars) < 2:
            return False
        
        # Avoid binary garbage
        control_chars = len(re.findall(r'[\x00-\x08\x0E-\x1F\x7F-\x9F]', text))
        if control_chars > len(text) * 0.3:  # Too many control characters
            return False
        
        # Look for Japanese or English content
        has_japanese = bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))
        has_english = bool(re.search(r'[a-zA-Z]', text))
        
        return has_japanese or has_english
    
    def find_text_boundaries(self, data: bytearray, start: int, max_size: int) -> tuple[int, int]:
        """Find the actual start and end of a text string"""
        
        # Start from the given position and find the real text start
        text_start = start
        
        # Find text end (look for null terminator or end of meaningful content)
        text_end = start
        consecutive_nulls = 0
        
        while text_end < min(len(data), start + max_size):
            if data[text_end] == 0:
                consecutive_nulls += 1
                if consecutive_nulls >= 4:  # Multiple nulls = end of text
                    break
            else:
                consecutive_nulls = 0
            
            text_end += 1
        
        # Ensure even length for UTF-16
        if (text_end - text_start) % 2 == 1:
            text_end -= 1
        
        return text_start, text_end
    
    def process_rtz_file(self, rtz_path: Path) -> bool:
        """Process a single RTZ file and replace all text with '0'"""
        
        relative_path = rtz_path.relative_to(self.romfs_dir)
        output_path = self.output_dir / relative_path
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to decompress and modify
        data = self.decompress_rtz(rtz_path)
        if data is None:
            # Not an RTZ file or decompression failed, just copy
            shutil.copy2(rtz_path, output_path)
            return False
        
        print(f"📝 Processing: {relative_path}")
        
        # Replace all text with "0"
        modified_data, replacements = self.replace_all_text_with_zero(data)
        
        if replacements > 0:
            print(f"   ✅ Made {replacements} text replacements")
            
            # Compress back to RTZ format
            compressed_data = self.compress_rtz(modified_data)
            if compressed_data:
                output_path.write_bytes(compressed_data)
                self.stats['files_modified'] += 1
                self.stats['text_replacements'] += replacements
                return True
            else:
                print(f"   ❌ Failed to compress modified data")
                shutil.copy2(rtz_path, output_path)
                return False
        else:
            print(f"   ⚪ No text found to replace")
            shutil.copy2(rtz_path, output_path)
            return False
    
    def process_all_rtz_files(self):
        """Process all RTZ files in the romfs directory"""
        
        print("🔄 ZERO TEXT INJECTION - COMPLETE REPLACEMENT")
        print("=" * 50)
        print("Replacing ALL text in ALL RTZ files with '0'")
        print("This will help verify if RTZ injection works at all")
        print()
        
        # Find all RTZ files
        rtz_files = list(self.romfs_dir.rglob("*.rtz"))
        
        if not rtz_files:
            print("❌ No RTZ files found in romfs directory")
            return False
        
        print(f"📁 Found {len(rtz_files)} RTZ files to process")
        print()
        
        # Process each file
        for rtz_file in rtz_files:
            self.stats['files_processed'] += 1
            try:
                self.process_rtz_file(rtz_file)
            except Exception as e:
                print(f"❌ Error processing {rtz_file.name}: {e}")
                self.stats['errors'] += 1
        
        # Copy all non-RTZ files
        print(f"\n📋 Copying non-RTZ files...")
        self.copy_non_rtz_files()
        
        # Show results
        print(f"\n🎉 ZERO TEXT INJECTION COMPLETE!")
        print(f"   📁 Files processed: {self.stats['files_processed']}")
        print(f"   ✅ Files modified: {self.stats['files_modified']}")
        print(f"   🔄 Text replacements: {self.stats['text_replacements']}")
        print(f"   ❌ Errors: {self.stats['errors']}")
        
        if self.stats['files_modified'] > 0:
            print(f"\n🚀 READY FOR ZERO TEST ROM BUILD!")
            print(f"   Modified romfs: {self.output_dir}")
            print(f"   Next: Build ROM and test in Citra")
            print(f"   Expected: ALL text should show as '0' if injection works")
        else:
            print(f"\n⚠️  No files were modified - check RTZ file format")
        
        return self.stats['files_modified'] > 0
    
    def copy_non_rtz_files(self):
        """Copy all non-RTZ files to maintain romfs structure"""
        
        for item in self.romfs_dir.rglob("*"):
            if item.is_file() and not item.name.endswith('.rtz'):
                relative_path = item.relative_to(self.romfs_dir)
                output_path = self.output_dir / relative_path
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, output_path)

def main():
    """Main zero text injection"""
    
    injector = ZeroTextInjector()
    
    print("🎯 ZERO TEXT TEST - PHASE 5.3.1 DEBUG")
    print("=" * 40)
    print()
    print("This will replace ALL text in the game with '0'")
    print("If you see '0' everywhere in-game, injection works!")
    print("If you still see Japanese, there's a fundamental issue.")
    print()
    
    if not Path("romfs").exists():
        print("❌ romfs directory not found")
        print("Please ensure you have extracted the original ROM first")
        return
    
    response = input("Proceed with zero text injection? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Injection cancelled")
        return
    
    success = injector.process_all_rtz_files()
    
    if success:
        print(f"\n🎮 NEXT STEPS:")
        print(f"1. Build ROM: ./build_english_rom.sh (modify to use romfs_zero_test)")
        print(f"2. Test in Citra")
        print(f"3. If you see '0' everywhere = SUCCESS! RTZ injection works")
        print(f"4. If still Japanese text = Need to debug injection method")
    else:
        print(f"\n❌ Zero text injection failed")

if __name__ == "__main__":
    main()