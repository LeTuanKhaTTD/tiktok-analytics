"""Run Pipeline với Apify Profile Data - Video Stats đầy đủ"""
import sys
from pathlib import Path

# Import các modules pipeline
from pipeline.apify_importer import ApifyProfileImporter
from pipeline.data_cleaner import DataCleaner
from pipeline.data_validator import DataValidator
from pipeline.data_exporter import DataExporter

def print_header():
    """Print pipeline header"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         📊 APIFY DATA PIPELINE - TikTok Analytics 📊          ║
    ║                                                               ║
    ║          Import & Process Apify Profile Data (Full Stats)    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
""")

def main():
    print_header()
    
    # File input
    apify_file = "dataset_tiktok-scraper_2026-03-06_08-07-00-276.json"
    
    print("=" * 70)
    print("📥 IMPORTING APIFY PROFILE DATA")
    print("=" * 70)
    print(f"Source: {apify_file}")
    print("=" * 70)
    print()
    
    # Stage 1: IMPORT from Apify
    print("-" * 70)
    print("Stage 1/4: IMPORT")
    print("-" * 70)
    print()
    
    importer = ApifyProfileImporter(output_dir="data/raw")
    result = importer.import_and_save(apify_file)
    
    raw_data = result['raw_data']
    platform = result['platform']
    identifier = result['identifier']
    
    # Stage 2: CLEAN
    print()
    print("-" * 70)
    print("Stage 2/4: CLEAN")
    print("-" * 70)
    print()
    
    cleaner = DataCleaner(
        output_cleaned_dir="data/cleaned",
        output_removed_dir="data/removed"
    )
    clean_result = cleaner.clean_data(raw_data)
    cleaned_data = clean_result['cleaned_data']
    removed_data = clean_result['removed_data']
    cleaner.save_cleaned_data(cleaned_data, removed_data, platform, identifier)
    
    # Stage 3: VALIDATE
    print()
    print("-" * 70)
    print("Stage 3/4: VALIDATE")
    print("-" * 70)
    print()
    
    validator = DataValidator(output_validated_dir="data/validated")
    validate_result = validator.validate_data(cleaned_data)
    validated_data = validate_result['validated_data']
    issues = validate_result['issues']
    validator.save_validated_data(validated_data, issues, platform, identifier)
    
    # Stage 4: EXPORT
    print()
    print("-" * 70)
    print("Stage 4/4: EXPORT")
    print("-" * 70)
    print()
    
    exporter = DataExporter(output_dir="data/export")
    exported_files = exporter.export_all(
        validated_data, 
        platform, 
        identifier,
        formats=['json', 'csv', 'excel']
    )
    
    # Summary
    print()
    print("=" * 70)
    print("✅ PIPELINE COMPLETED!")
    print("=" * 70)
    print()
    print("📊 SUMMARY:")
    print(f"   Videos: {len(validated_data.get('videos', []))}")
    print(f"   Total Plays: {raw_data['user'].get('total_plays', 0):,}")
    print(f"   Total Likes: {raw_data['user'].get('total_likes', 0):,}")
    print(f"   Total Comments: {raw_data['user'].get('total_comments', 0):,}")
    print(f"   Total Shares: {raw_data['user'].get('total_shares', 0):,}")
    print("=" * 70)
    print()
    print()
    print("✅ SUCCESS! Apify profile data processed successfully!")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
