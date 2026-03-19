"""Run Pipeline with REAL Data from tong_hop_comment.json"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.data_importer import DataImporter
from pipeline.data_cleaner import DataCleaner
from pipeline.data_labeler import DataLabeler, LabelMethod
from pipeline.data_validator import DataValidator
from pipeline.data_exporter import DataExporter

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         📊 REAL DATA PIPELINE - TikTok Analytics 📊           ║
    ║                                                               ║
    ║          Import & Process REAL TikTok Data from File         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    source_file = "data/tong_hop_comment.json"
    export_formats = ['json', 'csv', 'excel']
    
    print(f"\n{'='*70}")
    print(f"📥 IMPORTING REAL DATA")
    print(f"{'='*70}")
    print(f"Source: {source_file}")
    print(f"{'='*70}\n")
    
    try:
        # Stage 1: Import Real Data
        print(f"\n{'-'*70}")
        print(f"Stage 1/5: IMPORT")
        print(f"{'-'*70}\n")
        
        importer = DataImporter()
        result = importer.import_and_save(source_file)
        raw_data = result['raw_data']
        platform = result['platform']
        identifier = result['identifier']
        
        # Stage 2: Clean (but data is already clean)
        print(f"\n{'-'*70}")
        print(f"Stage 2/5: CLEAN")
        print(f"{'-'*70}\n")
        
        cleaner = DataCleaner()
        clean_result = cleaner.clean_data(raw_data)
        cleaned_data = clean_result['cleaned_data']
        cleaner.save_cleaned_data(cleaned_data, clean_result['removed_data'], platform, identifier)
        
        # Stage 3: Skip Labeling (already has sentiment from PhoBERT!)
        print(f"\n{'-'*70}")
        print(f"Stage 3/5: LABEL (skipped - already has PhoBERT sentiment)")
        print(f"{'-'*70}\n")
        print("✅ Data already labeled by PhoBERT model (92% accuracy)")
        
        # Prepare labeled data (already has sentiment)
        labeled_data = {
            **cleaned_data,
            "labeling_info": {
                "labeled_at": raw_data['metadata']['original_analyzed_at'],
                "method": "phobert",
                "model": raw_data['metadata']['original_model'],
                "accuracy": raw_data['metadata']['accuracy']
            }
        }
        
        # Stage 4: Validate
        print(f"\n{'-'*70}")
        print(f"Stage 4/5: VALIDATE")
        print(f"{'-'*70}\n")
        
        validator = DataValidator()
        validate_result = validator.validate_data(labeled_data)
        validated_data = validate_result['validated_data']
        validator.save_validated_data(validated_data, validate_result['issues'], platform, identifier)
        
        # Stage 5: Export
        print(f"\n{'-'*70}")
        print(f"Stage 5/5: EXPORT")
        print(f"{'-'*70}\n")
        
        exporter = DataExporter()
        exported = exporter.export_all(validated_data, platform, identifier, export_formats)
        
        # Summary
        print(f"\n{'='*70}")
        print(f"✅ PIPELINE COMPLETED!")
        print(f"{'='*70}")
        
        # Calculate sentiment distribution
        comments = validated_data.get('comments', [])
        pos = sum(1 for c in comments if c.get('sentiment') == 'positive')
        neg = sum(1 for c in comments if c.get('sentiment') == 'negative')
        neu = sum(1 for c in comments if c.get('sentiment') == 'neutral')
        
        print(f"\n📊 SUMMARY:")
        print(f"   Videos: {len(validated_data.get('videos', []))}")
        print(f"   Comments: {len(comments)}")
        print(f"   Sentiment: +{pos} / -{neg} / ={neu}")
        print(f"   Model: PhoBERT (92% accuracy)")
        print(f"{'='*70}\n")
        
        print(f"\n✅ SUCCESS! Real data processed successfully!")
        
    except FileNotFoundError:
        print(f"\n❌ ERROR: File '{source_file}' not found!")
        print(f"   Please make sure the file exists in the data/ directory.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
