#!/usr/bin/env python3
"""
RTZ Text Searcher - Find Correct Files
======================================
Searches ALL RTZ files to find where the translation text actually exists
"""

import gzip
import struct
import csv
from pathlib import Path
from typing import Dict, List, Set
import concurrent.futures
from collections import defaultdict

class RTZTextSearcher:
    def __init__(self):
        self.romfs_dir = Path("romfs")
        self.translations_dir = Path("files/translations")
        self.results_dir = Path("search_results")
        self.results_dir.mkdir(exist_ok=True)
        
        self.search_results = defaultdict(list)
        self.files_processed = 0
        
    def decompress_rtz(self, rtz_path: Path) -> tuple:
        """Decompress RTZ file and return decompressed data"""
        try:
            with open(rtz_path, 'rb') as f:
                raw_data = f.read()
            
            if len(raw_data) < 8:
                return None, "File too small"
            
            # Try decompression from offset 4 (after header)
            try:
                compressed_data = raw_data[4:]
                decompressed = gzip.decompress(compressed_data)
                return decompressed, None
            except Exception as e:
                return None, f"Decompression failed: {e}"
                
        except Exception as e:
            return None, f"Read error: {e}"
    
    def search_text_in_data(self, data: bytes, search_texts: List[str], file_path: Path) -> List[Dict]:
        """Search for Japanese text in decompressed data with different alignments"""
        
        found_matches = []
        
        # Try different byte alignments for UTF-16LE
        for alignment in range(min(16, len(data))):
            try:
                aligned_data = data[alignment:]
                if len(aligned_data) % 2 == 1:
                    aligned_data = aligned_data[:-1]
                
                if len(aligned_data) < 2:
                    continue
                
                # Decode as UTF-16LE
                try:
                    text_content = aligned_data.decode('utf-16le', errors='ignore')
                except:
                    continue
                
                # Search for each target text
                for search_text in search_texts:
                    if search_text in text_content:
                        # Find the exact position
                        pos = text_content.find(search_text)
                        
                        # Get surrounding context (50 chars before and after)
                        start = max(0, pos - 50)
                        end = min(len(text_content), pos + len(search_text) + 50)
                        context = text_content[start:end]
                        
                        found_matches.append({
                            'file': str(file_path.relative_to(self.romfs_dir)),
                            'search_text': search_text,
                            'alignment': alignment,
                            'position': pos,
                            'context': context,
                            'exact_match': True
                        })
                
                # Also search for partial matches (first 5 characters)
                for search_text in search_texts:
                    if len(search_text) >= 5:
                        partial = search_text[:5]
                        if partial in text_content and search_text not in text_content:
                            pos = text_content.find(partial)
                            start = max(0, pos - 30)
                            end = min(len(text_content), pos + 30)
                            context = text_content[start:end]
                            
                            found_matches.append({
                                'file': str(file_path.relative_to(self.romfs_dir)),
                                'search_text': search_text,
                                'partial_match': partial,
                                'alignment': alignment,
                                'position': pos,
                                'context': context,
                                'exact_match': False
                            })
                            
            except Exception:
                continue
        
        return found_matches
    
    def search_single_rtz_file(self, rtz_path: Path, search_texts: List[str]) -> List[Dict]:
        """Search for text in a single RTZ file"""
        
        # Decompress the file
        decompressed_data, error = self.decompress_rtz(rtz_path)
        
        if error:
            return []
        
        # Search for text
        matches = self.search_text_in_data(decompressed_data, search_texts, rtz_path)
        
        return matches
    
    def load_translation_texts(self) -> List[str]:
        """Load all Japanese texts from translation files"""
        
        translation_files = list(self.translations_dir.glob("filtered_usable_*.csv"))
        if not translation_files:
            return []
        
        latest_file = max(translation_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 Loading search texts from: {latest_file.name}")
        
        search_texts = set()
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    japanese_text = row.get('japanese_text', '').strip()
                    if japanese_text and len(japanese_text) >= 3:
                        search_texts.add(japanese_text)
        
        except Exception as e:
            print(f"❌ Error loading translations: {e}")
            return []
        
        search_list = list(search_texts)
        print(f"📋 Loaded {len(search_list)} unique Japanese texts to search for")
        
        # Show some examples
        print(f"📝 Sample texts:")
        for i, text in enumerate(search_list[:5]):
            print(f"   {i+1}. {text}")
        
        return search_list
    
    def search_all_rtz_files(self, max_workers: int = 4):
        """Search all RTZ files for the translation texts"""
        
        print("🔍 RTZ TEXT SEARCHER - FIND CORRECT FILES")
        print("=" * 45)
        
        # Load texts to search for
        search_texts = self.load_translation_texts()
        if not search_texts:
            print("❌ No texts to search for")
            return
        
        # Find all RTZ files
        rtz_files = list(self.romfs_dir.rglob("*.rtz"))
        print(f"📁 Found {len(rtz_files)} RTZ files to search")
        
        # Search files in parallel
        print(f"⚙ Searching files with {max_workers} workers...")
        
        all_matches = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all search tasks
            future_to_file = {
                executor.submit(self.search_single_rtz_file, rtz_file, search_texts): rtz_file 
                for rtz_file in rtz_files
            }
            
            # Process completed tasks
            for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
                rtz_file = future_to_file[future]
                
                try:
                    matches = future.result()
                    if matches:
                        all_matches.extend(matches)
                        print(f"   [{i:3}/{len(rtz_files)}] ✅ {rtz_file.name}: {len(matches)} matches")
                    else:
                        print(f"   [{i:3}/{len(rtz_files)}] ❌ {rtz_file.name}: no matches")
                        
                except Exception as e:
                    print(f"   [{i:3}/{len(rtz_files)}] ❌ {rtz_file.name}: error - {e}")
        
        # Analyze results
        self.analyze_search_results(all_matches, search_texts)
        
        return all_matches
    
    def analyze_search_results(self, all_matches: List[Dict], search_texts: List[str]):
        """Analyze and report search results"""
        
        print(f"\n📊 SEARCH RESULTS ANALYSIS")
        print("=" * 30)
        
        if not all_matches:
            print("❌ No matches found in any RTZ files!")
            print("\n🤔 POSSIBLE REASONS:")
            print("1. Text might be in a different encoding")
            print("2. Text might be split across multiple lines")
            print("3. Text might have been modified during extraction")
            print("4. Text might be in compressed archives within RTZ files")
            return
        
        # Group by file
        matches_by_file = defaultdict(list)
        matches_by_text = defaultdict(list)
        
        for match in all_matches:
            matches_by_file[match['file']].append(match)
            matches_by_text[match['search_text']].append(match)
        
        print(f"✅ Found {len(all_matches)} total matches")
        print(f"📁 Matches in {len(matches_by_file)} RTZ files")
        print(f"📝 {len(matches_by_text)} different texts found")
        
        # Show files with most matches
        print(f"\n🏆 FILES WITH MOST MATCHES:")
        sorted_files = sorted(matches_by_file.items(), key=lambda x: len(x[1]), reverse=True)
        
        for i, (file_path, matches) in enumerate(sorted_files[:10], 1):
            exact_matches = len([m for m in matches if m['exact_match']])
            partial_matches = len([m for m in matches if not m['exact_match']])
            print(f"   {i:2}. {file_path}")
            print(f"       Exact: {exact_matches}, Partial: {partial_matches}")
        
        # Show most found texts
        print(f"\n🎯 MOST FOUND TEXTS:")
        sorted_texts = sorted(matches_by_text.items(), key=lambda x: len(x[1]), reverse=True)
        
        for i, (text, matches) in enumerate(sorted_texts[:10], 1):
            files_with_text = set(m['file'] for m in matches)
            print(f"   {i:2}. '{text[:30]}{'...' if len(text) > 30 else ''}'")
            print(f"       Found in {len(files_with_text)} files")
        
        # Save detailed results
        self.save_detailed_results(all_matches, matches_by_file, matches_by_text)
        
        # Suggest next steps
        print(f"\n🚀 NEXT STEPS:")
        if sorted_files:
            top_file = sorted_files[0][0]
            top_matches = len(sorted_files[0][1])
            print(f"1. Focus injection on: {top_file} ({top_matches} matches)")
            print(f"2. Update translation file paths to point to correct files")
            print(f"3. Re-run injection with corrected file paths")
        
        print(f"4. Check detailed results in: {self.results_dir}")
    
    def save_detailed_results(self, all_matches: List[Dict], matches_by_file: Dict, matches_by_text: Dict):
        """Save detailed search results to files"""
        
        # Save complete results
        results_file = self.results_dir / "complete_search_results.csv"
        
        with open(results_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['file', 'search_text', 'exact_match', 'alignment', 'position', 'context']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for match in all_matches:
                writer.writerow({
                    'file': match['file'],
                    'search_text': match['search_text'],
                    'exact_match': match['exact_match'],
                    'alignment': match['alignment'],
                    'position': match['position'],
                    'context': match['context'][:100]  # Limit context length
                })
        
        print(f"💾 Complete results saved: {results_file}")
        
        # Save file summary
        summary_file = self.results_dir / "file_summary.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("RTZ Text Search Summary\n")
            f.write("=====================\n\n")
            
            f.write("Files with matches:\n")
            sorted_files = sorted(matches_by_file.items(), key=lambda x: len(x[1]), reverse=True)
            
            for file_path, matches in sorted_files:
                exact_count = len([m for m in matches if m['exact_match']])
                partial_count = len([m for m in matches if not m['exact_match']])
                f.write(f"{file_path}: {exact_count} exact, {partial_count} partial\n")
            
            f.write(f"\nTotal matches: {len(all_matches)}\n")
            f.write(f"Files with matches: {len(matches_by_file)}\n")
        
        print(f"📋 Summary saved: {summary_file}")

def main():
    """Main search function"""
    
    searcher = RTZTextSearcher()
    
    print("🔍 RTZ TEXT SEARCHER")
    print("===================")
    print()
    print("This tool searches ALL RTZ files to find where")
    print("your translation texts actually exist.")
    print()
    
    if not Path("romfs").exists():
        print("❌ romfs directory not found")
        return
    
    translation_files = list(Path("files/translations").glob("filtered_usable_*.csv"))
    if not translation_files:
        print("❌ No translation files found")
        return
    
    print("✅ Prerequisites found")
    
    # Ask for search parameters
    max_workers = 4
    try:
        user_workers = input(f"Number of parallel workers (1-8, default {max_workers}): ").strip()
        if user_workers:
            max_workers = max(1, min(8, int(user_workers)))
    except:
        pass
    
    print(f"⚙ Using {max_workers} parallel workers")
    
    response = input(f"\nStart searching all RTZ files? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Search cancelled")
        return
    
    # Run the search
    matches = searcher.search_all_rtz_files(max_workers)
    
    if matches:
        print(f"\n🎉 SEARCH COMPLETE!")
        print(f"   Found translation texts in RTZ files")
        print(f"   Check results in search_results/ directory")
    else:
        print(f"\n❌ SEARCH FAILED")
        print(f"   No translation texts found in any RTZ files")
        print(f"   This suggests a mismatch between extraction and files")

if __name__ == "__main__":
    main()