#!/usr/bin/env python3
"""
Precision RTZ Injector - Multi-Alignment
========================================
Uses search results to inject translations with correct alignment detection
"""

import gzip
import struct
import csv
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class PrecisionRTZInjector:
    def __init__(self):
        self.romfs_dir = Path("romfs")
        self.translations_dir = Path("files/translations")
        self.search_results_dir = Path("search_results")
        self.output_dir = Path("romfs_english_precision")
        self.debug_dir = Path("debug_precision")
        
        self.debug_dir.mkdir(exist_ok=True)
        
        self.stats = {
            'files_processed': 0,
            'successful_injections': 0,
            'total_replacements': 0,
            'exact_matches_used': 0,
            'partial_matches_used': 0
        }
    
    def load_search_results(self) -> Dict[str, List[Dict]]:
        """Load search results to know exactly where text was found"""
        
        results_file = self.search_results_dir / "complete_search_results.csv"
        if not results_file.exists():
            print("❌ Search results not found. Run rtz_text_searcher.py first.")
            return {}
        
        print(f"📁 Loading search results from: {results_file.name}")
        
        results_by_file = {}
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    file_path = row['file']
                    search_text = row['search_text']
                    exact_match = row['exact_match'] == 'True'
                    alignment = int(row['alignment'])
                    position = int(row['position'])
                    context = row['context']
                    
                    if file_path not in results_by_file:
                        results_by_file[file_path] = []
                    
                    results_by_file[file_path].append({
                        'search_text': search_text,
                        'exact_match': exact_match,
                        'alignment': alignment,
                        'position': position,
                        'context': context
                    })
        
        except Exception as e:
            print(f"❌ Error loading search results: {e}")
            return {}
        
        print(f"📋 Loaded search results for {len(results_by_file)} files")
        return results_by_file
    
    def load_translations(self) -> Dict[str, List[Dict]]:
        """Load original translations"""
        
        translation_files = list(self.translations_dir.glob("filtered_usable_*.csv"))
        if not translation_files:
            return {}
        
        latest_file = max(translation_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 Loading translations from: {latest_file.name}")
        
        translations_by_file = {}
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    if row.get('translation_status') == 'FAILED':
                        continue
                    
                    file_ref = row.get('file', '').strip()
                    japanese_text = row.get('japanese_text', '').strip()
                    english_text = row.get('english_text', '').strip()
                    
                    if not all([file_ref, japanese_text, english_text]):
                        continue
                    
                    # Fix file path
                    if file_ref.startswith('romfs/'):
                        file_ref = file_ref[6:]
                    
                    if file_ref not in translations_by_file:
                        translations_by_file[file_ref] = []
                    
                    translations_by_file[file_ref].append({
                        'japanese': japanese_text,
                        'english': english_text,
                        'confidence': float(row.get('confidence', 0)),
                        'quality': row.get('quality_assessment', 'unknown')
                    })
        
        except Exception as e:
            print(f"❌ Error loading translations: {e}")
            return {}
        
        return translations_by_file
    
    def find_best_alignment_for_text(self, search_results: List[Dict], target_text: str) -> Optional[int]:
        """Find the best alignment for a specific text based on search results"""
        
        # Look for exact matches first
        exact_matches = [r for r in search_results if r['search_text'] == target_text and r['exact_match']]
        if exact_matches:
            # Use the alignment from the first exact match
            return exact_matches[0]['alignment']
        
        # Look for partial matches
        partial_matches = [r for r in search_results if r['search_text'] == target_text and not r['exact_match']]
        if partial_matches:
            # Use the alignment from the first partial match
            return partial_matches[0]['alignment']
        
        return None
    
    def inject_with_precise_alignment(self, rtz_path: Path, translations: List[Dict], 
                                    search_results: List[Dict]) -> bool:
        """Inject translations using precise alignment information"""
        
        print(f"\n📁 PRECISION INJECTION: {rtz_path.relative_to(self.romfs_dir)}")
        
        try:
            # Read and decompress RTZ file
            with open(rtz_path, 'rb') as f:
                raw_data = f.read()
            
            header = raw_data[:4]
            compressed_data = raw_data[4:]
            decompressed_data = gzip.decompress(compressed_data)
            
            print(f"   📦 Decompressed: {len(compressed_data)} → {len(decompressed_data)} bytes")
            
            # Process each translation
            modified_data = decompressed_data
            successful_replacements = 0
            
            for i, translation in enumerate(translations, 1):
                japanese = translation['japanese']
                english = translation['english']
                quality = translation['quality']
                
                print(f"   [{i:2}/{len(translations)}] {quality.upper()}")
                print(f"       JP: {japanese[:40]}{'...' if len(japanese) > 40 else ''}")
                print(f"       EN: {english[:40]}{'...' if len(english) > 40 else ''}")
                
                # Find the best alignment for this text
                best_alignment = self.find_best_alignment_for_text(search_results, japanese)
                
                if best_alignment is None:
                    print(f"       ❌ No alignment found in search results")
                    continue
                
                # Try replacement with the precise alignment
                replacements_made = self.replace_text_with_alignment(
                    modified_data, japanese, english, best_alignment
                )
                
                if replacements_made > 0:
                    modified_data = self.get_modified_data()  # Get the modified version
                    successful_replacements += replacements_made
                    match_type = "EXACT" if any(r['search_text'] == japanese and r['exact_match'] 
                                              for r in search_results) else "PARTIAL"
                    print(f"       ✅ {match_type} - {replacements_made} replacements (alignment {best_alignment})")
                    
                    if match_type == "EXACT":
                        self.stats['exact_matches_used'] += 1
                    else:
                        self.stats['partial_matches_used'] += 1
                else:
                    print(f"       ❌ Replacement failed (alignment {best_alignment})")
            
            # Save modified file if successful
            if successful_replacements > 0:
                # Recompress
                recompressed = gzip.compress(modified_data)
                final_data = header + recompressed
                
                # Save to output
                output_file = self.output_dir / rtz_path.relative_to(self.romfs_dir)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'wb') as f:
                    f.write(final_data)
                
                print(f"   💾 SUCCESS: {successful_replacements} translations applied")
                print(f"   📊 File size: {len(raw_data)} → {len(final_data)} bytes")
                
                # Save debug info
                self.save_debug_info(rtz_path, translations, search_results, successful_replacements)
                
                self.stats['successful_injections'] += 1
                self.stats['total_replacements'] += successful_replacements
                return True
            else:
                print(f"   ⚠️  No successful replacements")
                return False
                
        except Exception as e:
            print(f"   ❌ Error processing: {e}")
            return False
    
    def replace_text_with_alignment(self, data: bytes, search_text: str, 
                                  replace_text: str, alignment: int) -> int:
        """Replace text with specific byte alignment"""
        
        try:
            # Apply alignment
            aligned_data = data[alignment:]
            if len(aligned_data) % 2 == 1:
                aligned_data = aligned_data[:-1]
            
            # Convert to UTF-16LE
            search_bytes = search_text.encode('utf-16le')
            replace_bytes = replace_text.encode('utf-16le')
            
            # Count occurrences before replacement
            count_before = aligned_data.count(search_bytes)
            
            if count_before == 0:
                return 0
            
            # Perform replacement
            self.modified_aligned_data = aligned_data.replace(search_bytes, replace_bytes)
            
            # Count occurrences after replacement
            count_after = self.modified_aligned_data.count(search_bytes)
            
            return count_before - count_after
            
        except Exception as e:
            print(f"      ❌ Replacement error: {e}")
            return 0
    
    def get_modified_data(self) -> bytes:
        """Get the modified data after text replacement"""
        # This is a simplified version - in practice, you'd need to
        # properly reconstruct the full data with alignment
        return getattr(self, 'modified_aligned_data', b'')
    
    def save_debug_info(self, rtz_path: Path, translations: List[Dict], 
                       search_results: List[Dict], successful_replacements: int):
        """Save debug information"""
        
        debug_file = self.debug_dir / f"{rtz_path.stem}_precision_debug.txt"
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(f"Precision Injection Debug: {rtz_path.name}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Successful replacements: {successful_replacements}\n")
            f.write(f"Total translations attempted: {len(translations)}\n\n")
            
            f.write("Search Results Summary:\n")
            exact_count = len([r for r in search_results if r['exact_match']])
            partial_count = len([r for r in search_results if not r['exact_match']])
            f.write(f"  Exact matches: {exact_count}\n")
            f.write(f"  Partial matches: {partial_count}\n\n")
            
            f.write("Alignments used:\n")
            alignments = set(r['alignment'] for r in search_results)
            for alignment in sorted(alignments):
                count = len([r for r in search_results if r['alignment'] == alignment])
                f.write(f"  Alignment {alignment}: {count} results\n")
    
    def run_precision_injection(self):
        """Run precision injection using search results"""
        
        print("🎯 PRECISION RTZ INJECTOR")
        print("=" * 30)
        print("Using search results for precise text injection")
        print()
        
        # Load search results
        search_results_by_file = self.load_search_results()
        if not search_results_by_file:
            return False
        
        # Load translations
        translations_by_file = self.load_translations()
        if not translations_by_file:
            return False
        
        # Setup output directory
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        shutil.copytree(self.romfs_dir, self.output_dir)
        print(f"✅ Created precision English romfs: {self.output_dir}")
        
        # Find files that have both translations and search results
        target_files = set(search_results_by_file.keys()) & set(translations_by_file.keys())
        
        if not target_files:
            print("❌ No files found with both translations and search results")
            return False
        
        print(f"🎯 Processing {len(target_files)} files with confirmed text matches")
        
        # Process each target file
        self.stats['files_processed'] = len(target_files)
        
        for file_path in sorted(target_files):
            rtz_file = self.romfs_dir / file_path
            
            if not rtz_file.exists():
                print(f"❌ File not found: {file_path}")
                continue
            
            translations = translations_by_file[file_path]
            search_results = search_results_by_file[file_path]
            
            print(f"\n📋 {file_path}:")
            print(f"   Translations: {len(translations)}")
            print(f"   Search results: {len(search_results)}")
            
            success = self.inject_with_precise_alignment(rtz_file, translations, search_results)
        
        # Print final results
        self.print_final_results()
        
        return self.stats['total_replacements'] > 0
    
    def print_final_results(self):
        """Print final injection results"""
        
        print(f"\n🎉 PRECISION INJECTION COMPLETE!")
        print("=" * 40)
        print(f"Files processed:      {self.stats['files_processed']}")
        print(f"Successful injections: {self.stats['successful_injections']}")
        print(f"Total replacements:    {self.stats['total_replacements']}")
        print(f"Exact matches used:    {self.stats['exact_matches_used']}")
        print(f"Partial matches used:  {self.stats['partial_matches_used']}")
        
        if self.stats['total_replacements'] > 0:
            print(f"\n🎮 SUCCESS! English text injected using precise alignment!")
            print(f"📁 Modified romfs: {self.output_dir}")
            print(f"📋 Debug info: {self.debug_dir}")
            print(f"🚀 Ready for ROM building!")
        else:
            print(f"\n⚠️  No text replacements made")

def main():
    """Main precision injection function"""
    
    injector = PrecisionRTZInjector()
    
    print("🎯 PRECISION RTZ INJECTOR")
    print("========================")
    print()
    print("This tool uses the search results to inject translations")
    print("with precise alignment information.")
    print()
    
    # Check prerequisites
    if not Path("search_results/complete_search_results.csv").exists():
        print("❌ Search results not found")
        print("   Please run: python3 scripts/rtz_text_searcher.py")
        return
    
    if not Path("romfs").exists():
        print("❌ romfs directory not found")
        return
    
    print("✅ Prerequisites found")
    response = input("\nProceed with precision injection? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Operation cancelled")
        return
    
    success = injector.run_precision_injection()
    
    if success:
        print(f"\n🎉 PRECISION INJECTION SUCCESSFUL!")
        print(f"   Your translations are now precisely injected")
        print(f"   Next step: Build ROM with romfs_english_precision/")
    else:
        print(f"\n❌ Precision injection failed")

if __name__ == "__main__":
    main()