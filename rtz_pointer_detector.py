#!/usr/bin/env python3
"""
RTZ REFINED TEXT DETECTOR - PHASE 5.1.1
========================================
CF VANGUARD STRIDE TO VICTORY - FANMADE TRANSLATION PROJECT

Improved version that filters out file metadata and focuses on actual game text
Addresses the metadata detection issue found in Phase 5.1 initial results
"""

import gzip
import struct
import re
from pathlib import Path
from typing import List, Dict, Optional
import csv

class RTZRefinedDetector:
    def __init__(self):
        self.debug_mode = True
        self.metadata_filters = [
            # File path patterns
            r'[a-zA-Z0-9_/\\]+\.(rtz|h|cpp|c|txt|bin)',
            r'script[/\\]',
            r'core[/\\]',
            r'fight[/\\]',
            r'\.\/script',
            r'<built-in>',
            
            # Common metadata patterns
            r'^[a-zA-Z0-9_/\\\.]+$',  # Pure ASCII paths
            r'#include',
            r'typedef',
            r'struct',
            r'class',
            
            # Encoding artifacts that look like Japanese but aren't
            r'^[⽣楦桧⽴捳楲瑰猯湥彤潣浭湥⹴瑲୳戼極楬⵴湩᜾뎂菣뎃菣ꦃ苣뎃ᐾ⼮捳楲瑰振牯⽥潣敲栮⸎猯牣灩⽴敧⹮ᕨ]+',
        ]
        
    def decompress_rtz(self, rtz_path: Path) -> Optional[bytes]:
        """Decompress RTZ file using proven method"""
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
            if self.debug_mode:
                print(f"❌ Decompression failed for {rtz_path.name}: {e}")
            return None
    
    def is_metadata_text(self, text: str) -> bool:
        """Check if text appears to be file metadata rather than game content"""
        
        # Filter out obvious metadata patterns
        for pattern in self.metadata_filters:
            if re.search(pattern, text):
                return True
                
        # Check for high ratio of ASCII to Japanese (likely metadata)
        ascii_chars = len(re.findall(r'[a-zA-Z0-9_./\\]', text))
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))
        
        if ascii_chars > japanese_chars * 3:  # Mostly ASCII = likely metadata
            return True
            
        # Check for specific metadata indicators
        metadata_indicators = [
            'script', 'core', 'header', 'include', 'build', 'compile',
            '.h', '.c', '.cpp', '.rtz', 'built-in', 'typedef'
        ]
        
        text_lower = text.lower()
        metadata_count = sum(1 for indicator in metadata_indicators if indicator in text_lower)
        
        if metadata_count > 2:  # Multiple metadata indicators
            return True
            
        return False
    
    def is_genuine_japanese_text(self, text: str) -> bool:
        """Check if text contains genuine Japanese content suitable for translation"""
        
        # Must contain actual Japanese characters
        japanese_chars = re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text)
        if len(japanese_chars) < 2:
            return False
            
        # Look for common Japanese game text patterns
        game_text_patterns = [
            r'[\u3042-\u3096]',  # Hiragana
            r'[\u30a2-\u30f6]',  # Katakana
            r'[\u4e00-\u9faf]',  # Kanji
            r'[。、！？]',        # Japanese punctuation
        ]
        
        pattern_matches = 0
        for pattern in game_text_patterns:
            if re.search(pattern, text):
                pattern_matches += 1
                
        if pattern_matches < 2:  # Need multiple Japanese elements
            return False
            
        # Check for reasonable text length
        if len(text.strip()) < 3 or len(text.strip()) > 200:
            return False
            
        # Look for game-specific vocabulary (bonus points)
        game_keywords = [
            'カード', 'デッキ', 'バトル', 'ファイト', 'ユニット', 'プレイヤー',
            'ターン', 'ドロー', 'アタック', 'ガード', 'ダメージ', 'パワー',
            'クリティカル', 'トリガー', 'ヴァンガード', 'リアガード',
            'ライド', 'コール', 'スタンド', 'レスト', 'チューン'
        ]
        
        confidence_bonus = 0
        for keyword in game_keywords:
            if keyword in text:
                confidence_bonus += 0.2
                
        return True
    
    def find_text_at_rtz_end(self, data: bytes, rtz_path: Path) -> List[Dict]:
        """
        Look for text at the end of RTZ files, which is more likely to be game content
        Based on project knowledge that text is often stored at file endings
        """
        patterns = []
        
        # Focus on the last 25% of the file where game text is more likely
        start_offset = len(data) * 3 // 4
        search_data = data[start_offset:]
        
        # Look for UTF-16LE aligned text
        pos = 0
        while pos < len(search_data) - 10:
            # Try different text lengths
            for text_length in [10, 20, 30, 50, 100]:
                if pos + text_length * 2 > len(search_data):
                    continue
                    
                try:
                    text_bytes = search_data[pos:pos + text_length * 2]
                    
                    # Ensure even byte alignment for UTF-16LE
                    if len(text_bytes) % 2 != 0:
                        text_bytes = text_bytes[:-1]
                        
                    decoded_text = text_bytes.decode('utf-16le', errors='ignore')
                    
                    # Skip if it's metadata
                    if self.is_metadata_text(decoded_text):
                        continue
                        
                    # Check if it's genuine Japanese text
                    if self.is_genuine_japanese_text(decoded_text):
                        patterns.append({
                            'file': str(rtz_path),
                            'offset': start_offset + pos,
                            'text_length': text_length,
                            'decoded_text': decoded_text.strip(),
                            'confidence': self.calculate_game_text_confidence(decoded_text),
                            'source_section': 'file_end'
                        })
                        
                        if self.debug_mode:
                            print(f"✅ Game text at 0x{start_offset + pos:X}: '{decoded_text[:30]}{'...' if len(decoded_text) > 30 else ''}'")
                        
                        break  # Found text at this position, move on
                        
                except UnicodeDecodeError:
                    continue
                    
            pos += 2  # Move by 2 bytes (UTF-16LE alignment)
            
        return patterns
    
    def find_structured_text_patterns(self, data: bytes, rtz_path: Path) -> List[Dict]:
        """
        Look for structured text patterns that might indicate game content
        Focus on patterns that are less likely to be metadata
        """
        patterns = []
        
        # Look for the terminator pattern first to find structured data sections
        terminator = b'\x00\xFF\xFF\xFF\xFF'
        terminator_positions = []
        
        pos = 0
        while pos < len(data):
            pos = data.find(terminator, pos)
            if pos == -1:
                break
            terminator_positions.append(pos)
            pos += len(terminator)
            
        # Search around terminator positions for text
        for term_pos in terminator_positions:
            # Look before terminator (structured data section)
            search_start = max(0, term_pos - 1000)
            search_end = term_pos
            section_data = data[search_start:search_end]
            
            # Look for text patterns in this section
            section_patterns = self.find_text_in_section(section_data, search_start, rtz_path, 'before_terminator')
            patterns.extend(section_patterns)
            
        return patterns
    
    def find_text_in_section(self, section_data: bytes, base_offset: int, rtz_path: Path, section_type: str) -> List[Dict]:
        """Find text within a specific data section"""
        patterns = []
        
        # Look for 5-byte prefixes followed by text
        pos = 0
        while pos < len(section_data) - 10:
            if pos + 5 > len(section_data):
                break
                
            # Extract potential 5-byte prefix
            prefix = section_data[pos:pos+5]
            char_count = prefix[4]
            
            # Reasonable character count check
            if char_count == 0 or char_count > 100:
                pos += 1
                continue
                
            text_start = pos + 5
            text_end = text_start + (char_count * 2)  # UTF-16LE
            
            if text_end > len(section_data):
                pos += 1
                continue
                
            try:
                text_bytes = section_data[text_start:text_end]
                decoded_text = text_bytes.decode('utf-16le')
                
                # Apply our refined filters
                if self.is_metadata_text(decoded_text):
                    pos += 1
                    continue
                    
                if self.is_genuine_japanese_text(decoded_text):
                    patterns.append({
                        'file': str(rtz_path),
                        'offset': base_offset + pos,
                        'text_offset': base_offset + text_start,
                        'char_count': char_count,
                        'decoded_text': decoded_text.strip(),
                        'confidence': self.calculate_game_text_confidence(decoded_text),
                        'source_section': section_type,
                        'prefix_hex': prefix.hex()
                    })
                    
                    if self.debug_mode:
                        print(f"✅ Structured text at 0x{base_offset + pos:X}: '{decoded_text[:30]}{'...' if len(decoded_text) > 30 else ''}'")
                        
            except UnicodeDecodeError:
                pass
                
            pos += 1
            
        return patterns
    
    def calculate_game_text_confidence(self, text: str) -> float:
        """Calculate confidence that this is actual game text"""
        confidence = 0.0
        
        # Base confidence for containing Japanese
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))
        if japanese_chars > 0:
            confidence += 0.4
            
        # Bonus for game-specific vocabulary
        game_keywords = [
            'カード', 'デッキ', 'バトル', 'ファイト', 'ユニット', 'プレイヤー',
            'ターン', 'ドロー', 'アタック', 'ガード', 'ダメージ', 'パワー',
            'ヴァンガード', 'チュートリアル', 'スキル', 'アビリティ'
        ]
        
        for keyword in game_keywords:
            if keyword in text:
                confidence += 0.15
                
        # Bonus for proper Japanese text structure
        if re.search(r'[\u3042-\u3096][\u4e00-\u9faf]', text):  # Hiragana + Kanji
            confidence += 0.1
            
        if re.search(r'[。、！？]', text):  # Japanese punctuation
            confidence += 0.1
            
        # Penalty for ASCII content (likely metadata)
        ascii_ratio = len(re.findall(r'[a-zA-Z0-9]', text)) / len(text) if text else 0
        if ascii_ratio > 0.5:
            confidence -= 0.3
            
        return min(1.0, max(0.0, confidence))
    
    def scan_rtz_refined(self, rtz_path: Path) -> Dict:
        """Refined RTZ scanning focused on game content"""
        
        if self.debug_mode:
            print(f"\n🔍 REFINED SCAN: {rtz_path.name}")
            print("-" * (16 + len(rtz_path.name)))
            
        result = {
            'file': str(rtz_path),
            'success': False,
            'game_text_patterns': [],
            'error': None
        }
        
        try:
            # Decompress
            data = self.decompress_rtz(rtz_path)
            if data is None:
                result['error'] = "Decompression failed"
                return result
                
            result['success'] = True
            
            # Method 1: Look for text at file end (most promising)
            end_patterns = self.find_text_at_rtz_end(data, rtz_path)
            result['game_text_patterns'].extend(end_patterns)
            
            # Method 2: Look for structured text patterns
            structured_patterns = self.find_structured_text_patterns(data, rtz_path)
            result['game_text_patterns'].extend(structured_patterns)
            
            # Remove duplicates and sort by confidence
            seen_texts = set()
            unique_patterns = []
            for pattern in result['game_text_patterns']:
                text_key = pattern['decoded_text']
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    unique_patterns.append(pattern)
                    
            result['game_text_patterns'] = sorted(unique_patterns, 
                                                key=lambda x: x['confidence'], 
                                                reverse=True)
            
            if self.debug_mode:
                print(f"📊 Found {len(result['game_text_patterns'])} potential game text entries")
                
        except Exception as e:
            result['error'] = str(e)
            if self.debug_mode:
                print(f"❌ Error: {e}")
                
        return result
    
    def scan_priority_files(self, romfs_path: Path, max_files: int = 10):
        """Scan high-priority files for actual game text"""
        
        print("🔍 PHASE 5.1.1 - REFINED RTZ TEXT DETECTION")
        print("=" * 50)
        print("Filtering out metadata, focusing on game content")
        print("=" * 50)
        
        if not romfs_path.exists():
            print(f"❌ Directory not found: {romfs_path}")
            return []
            
        # Prioritize tutorial and UI files
        priority_patterns = ['tuto', 'tutorial', 'title', 'menu', 'ui', 'fe', 'char', 'dialog']
        
        all_rtz_files = list(romfs_path.rglob("*.rtz"))
        
        # Sort by priority
        priority_files = []
        for pattern in priority_patterns:
            matching_files = [f for f in all_rtz_files if pattern in f.name.lower()]
            priority_files.extend(matching_files[:3])  # Top 3 per category
            
        # Remove duplicates while preserving order
        seen = set()
        unique_priority_files = []
        for f in priority_files:
            if f not in seen:
                seen.add(f)
                unique_priority_files.append(f)
                
        files_to_scan = unique_priority_files[:max_files]
        
        print(f"🎯 Scanning {len(files_to_scan)} high-priority files:")
        for f in files_to_scan:
            print(f"   📁 {f.name}")
        print()
        
        results = []
        total_game_text = 0
        
        for i, rtz_file in enumerate(files_to_scan, 1):
            print(f"[{i}/{len(files_to_scan)}] Processing {rtz_file.name}")
            result = self.scan_rtz_refined(rtz_file)
            results.append(result)
            
            if result['success']:
                game_text_count = len(result['game_text_patterns'])
                total_game_text += game_text_count
                print(f"   ✅ Found {game_text_count} game text entries")
                
                # Show best examples
                high_conf = [p for p in result['game_text_patterns'] if p['confidence'] > 0.6]
                for pattern in high_conf[:2]:
                    print(f"   🎮 '{pattern['decoded_text'][:40]}...' (conf: {pattern['confidence']:.2f})")
            else:
                print(f"   ❌ Failed: {result['error']}")
                
        print(f"\n📊 REFINED DETECTION SUMMARY:")
        print(f"   🎮 Total game text found: {total_game_text}")
        print(f"   🎯 Files with game text: {sum(1 for r in results if r['game_text_patterns'])}")
        
        if total_game_text > 0:
            # Save refined results
            self.save_refined_results(results)
            print(f"   💾 Results saved to files/rtz_game_text_refined.csv")
        else:
            print(f"   🤔 No clear game text found - may need further refinement")
            
        return results
    
    def save_refined_results(self, results: List[Dict]):
        """Save refined game text results"""
        csv_path = Path("files/rtz_game_text_refined.csv")
        
        rows = []
        for result in results:
            if not result['success']:
                continue
                
            for pattern in result['game_text_patterns']:
                rows.append({
                    'file': pattern['file'],
                    'offset': f"0x{pattern['offset']:X}",
                    'japanese_text': pattern['decoded_text'],
                    'english_text': '',  # For translation
                    'confidence': f"{pattern['confidence']:.2f}",
                    'source_section': pattern['source_section'],
                    'priority': 'HIGH' if pattern['confidence'] > 0.7 else 'MEDIUM' if pattern['confidence'] > 0.5 else 'LOW'
                })
                
        if rows:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)


def main():
    """Phase 5.1.1 - Refined RTZ text detection"""
    detector = RTZRefinedDetector()
    
    romfs_path = Path("romfs")
    detector.scan_priority_files(romfs_path, max_files=10)


if __name__ == "__main__":
    main()