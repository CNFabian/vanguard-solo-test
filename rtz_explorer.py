#!/usr/bin/env python3
"""
RTZ FILE EXPLORER - Find the best RTZ files for translation
===========================================================
Scans all RTZ files to identify which contain the most translatable text
"""

import gzip
import struct
from pathlib import Path
import re
from collections import defaultdict

def analyze_rtz_file(rtz_path: Path) -> dict:
    """Analyze a single RTZ file for translation potential"""
    result = {
        'path': str(rtz_path),
        'size': rtz_path.stat().st_size,
        'compressed': False,
        'decompressed_size': 0,
        'japanese_text_count': 0,
        'total_text_length': 0,
        'contains_ui_keywords': False,
        'priority_score': 0,
        'sample_text': [],
        'error': None
    }
    
    try:
        data = rtz_path.read_bytes()
        
        # Try to decompress
        decompressed_data = None
        
        # Method 1: Direct gzip
        if data.startswith(b'\x1f\x8b'):
            try:
                decompressed_data = gzip.decompress(data)
                result['compressed'] = True
            except:
                pass
        
        # Method 2: RTZ format (4-byte size + gzip)
        if decompressed_data is None and len(data) >= 4:
            try:
                size = struct.unpack('<I', data[:4])[0]
                if 100 < size < 10000000:  # Reasonable range
                    gzip_data = data[4:]
                    if gzip_data.startswith(b'\x1f\x8b'):
                        decompressed_data = gzip.decompress(gzip_data)
                        result['compressed'] = True
                        if len(decompressed_data) != size:
                            result['error'] = f"Size mismatch: header={size}, actual={len(decompressed_data)}"
            except Exception as e:
                result['error'] = f"RTZ decompression failed: {e}"
        
        # Use raw data if decompression failed
        if decompressed_data is None:
            decompressed_data = data
        
        result['decompressed_size'] = len(decompressed_data)
        
        # Analyze for Japanese text
        japanese_pattern = re.compile(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+')
        
        # Try UTF-16LE decoding in chunks
        pos = 0
        while pos < len(decompressed_data) - 4:
            try:
                # Try to decode chunks as UTF-16LE
                chunk_size = min(200, len(decompressed_data) - pos)
                for end_pos in range(pos + 4, pos + chunk_size, 2):
                    try:
                        decoded = decompressed_data[pos:end_pos].decode('utf-16le')
                        
                        # Look for Japanese characters
                        japanese_matches = japanese_pattern.findall(decoded)
                        if japanese_matches:
                            for match in japanese_matches:
                                if len(match) >= 2:  # Meaningful text
                                    result['japanese_text_count'] += 1
                                    result['total_text_length'] += len(match)
                                    if len(result['sample_text']) < 5:
                                        result['sample_text'].append(match[:50])
                        
                        pos = end_pos
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    pos += 2
            except:
                pos += 1
        
        # Check for UI-related keywords in the path
        ui_keywords = [
            'title', 'menu', 'ui', 'fe', 'frontend', 'button', 'dialog',
            'tutorial', 'tuto', 'help', 'guide', 'option', 'setting',
            'character', 'select', 'create', 'deck', 'card', 'fight'
        ]
        
        path_lower = str(rtz_path).lower()
        result['contains_ui_keywords'] = any(keyword in path_lower for keyword in ui_keywords)
        
        # Calculate priority score
        score = 0
        score += result['japanese_text_count'] * 2  # Text quantity
        score += min(result['total_text_length'] // 10, 50)  # Text length (capped)
        if result['contains_ui_keywords']:
            score += 20  # UI relevance bonus
        if 'title' in path_lower or 'fe' in path_lower:
            score += 10  # High priority directories
        if result['decompressed_size'] > 1000:
            score += 5  # Substantial file size
        
        result['priority_score'] = score
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    print("🔍 RTZ FILE EXPLORER - CF VANGUARD TRANSLATION TARGET FINDER")
    print("=" * 70)
    
    romfs_path = Path("romfs")
    if not romfs_path.exists():
        print("❌ romfs/ directory not found. Please extract RomFS first.")
        return
    
    # Find all RTZ files
    rtz_files = list(romfs_path.rglob("*.rtz"))
    print(f"📦 Found {len(rtz_files)} RTZ files to analyze")
    print()
    
    if not rtz_files:
        print("❌ No RTZ files found in romfs/ directory")
        return
    
    # Analyze each file
    results = []
    for i, rtz_file in enumerate(rtz_files, 1):
        print(f"⚙️  Analyzing {i}/{len(rtz_files)}: {rtz_file.name}...", end='\r')
        result = analyze_rtz_file(rtz_file)
        results.append(result)
    
    print()  # Clear the progress line
    
    # Sort by priority score
    results.sort(key=lambda x: x['priority_score'], reverse=True)
    
    # Display top candidates
    print("🎯 TOP 20 TRANSLATION CANDIDATES:")
    print("=" * 70)
    print(f"{'Rank':<4} {'File':<30} {'Score':<6} {'JP Text':<8} {'UI':<3} {'Size':<8}")
    print("-" * 70)
    
    for i, result in enumerate(results[:20], 1):
        path_parts = Path(result['path']).parts
        display_path = '/'.join(path_parts[-2:]) if len(path_parts) >= 2 else path_parts[-1]
        
        ui_mark = "✅" if result['contains_ui_keywords'] else "❌"
        size_str = f"{result['decompressed_size']:,}" if result['decompressed_size'] else "N/A"
        
        print(f"{i:<4} {display_path:<30} {result['priority_score']:<6} "
              f"{result['japanese_text_count']:<8} {ui_mark:<3} {size_str:<8}")
        
        # Show sample text for top 10
        if i <= 10 and result['sample_text']:
            for sample in result['sample_text'][:2]:
                print(f"     📝 {sample}")
    
    print()
    
    # Category breakdown
    print("📊 CATEGORY BREAKDOWN:")
    print("=" * 30)
    
    categories = defaultdict(list)
    for result in results:
        path_parts = Path(result['path']).parts
        if len(path_parts) >= 2:
            category = path_parts[-2]  # Parent directory
            categories[category].append(result)
    
    for category, files in sorted(categories.items()):
        total_score = sum(f['priority_score'] for f in files)
        total_text = sum(f['japanese_text_count'] for f in files)
        avg_score = total_score / len(files) if files else 0
        
        print(f"{category:<15}: {len(files):3d} files, {total_text:4d} texts, avg score {avg_score:.1f}")
    
    print()
    
    # Specific recommendations
    print("🎯 TRANSLATION STRATEGY RECOMMENDATIONS:")
    print("=" * 45)
    
    top_files = results[:5]
    ui_files = [r for r in results if r['contains_ui_keywords']][:10]
    
    print("🥇 HIGH PRIORITY FILES (Start Here):")
    for result in top_files:
        if result['japanese_text_count'] > 0:
            print(f"   • {result['path']}")
            print(f"     {result['japanese_text_count']} texts, score {result['priority_score']}")
    
    print("\n🎮 UI-FOCUSED FILES (Character Selection, Menus):")
    for result in ui_files[:5]:
        if result['japanese_text_count'] > 0:
            print(f"   • {result['path']}")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Extract and translate top 3 files using extract_rtz_content.py")
    print("   2. Focus on fe/ (frontend) and title/ directories first")
    print("   3. Use decompress_rtz.py to examine file contents manually")
    print("   4. Test translations in-game to validate approach")

if __name__ == "__main__":
    main()