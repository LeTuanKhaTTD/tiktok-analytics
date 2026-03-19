"""
Run Pipeline - Main Entry Point
================================

File này để run data pipeline từ command line hoặc code

Usage:
    # Run full pipeline
    python run_pipeline.py --platform tiktok --id travinhuniversity --videos 30
    
    # Or from code
    python run_pipeline.py

Author: Data Pipeline Team
Created: 2026-03-06
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipeline import DataPipeline


def main():
    """
    Main entry point
    
    Vibe: CLI interface cho users
    - Simple và intuitive
    - Clear help messages
    - Sensible defaults
    """
    parser = argparse.ArgumentParser(
        description='🚀 Data Pipeline - Thu thập và phân tích dữ liệu TikTok/YouTube',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # TikTok analysis
  python run_pipeline.py --platform tiktok --id travinhuniversity --videos 30
  
  # YouTube analysis
  python run_pipeline.py --platform youtube --id UCaxnllxL894OHbc_6VQcGmA --videos 50
  
  # Hybrid labeling (auto + manual review)
  python run_pipeline.py --platform tiktok --id travinhuniversity --label hybrid
  
  # Export specific formats only
  python run_pipeline.py --platform tiktok --id travinhuniversity --formats json csv
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--platform',
        type=str,
        required=True,
        choices=['tiktok', 'youtube'],
        help='Platform: tiktok hoặc youtube'
    )
    
    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help='Username (TikTok) hoặc Channel ID (YouTube)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--videos',
        type=int,
        default=30,
        help='Số lượng videos tối đa (default: 30)'
    )
    
    parser.add_argument(
        '--label',
        type=str,
        default='auto',
        choices=['auto', 'manual', 'hybrid'],
        help='Phương pháp labeling (default: auto)'
    )
    
    parser.add_argument(
        '--formats',
        nargs='+',
        default=['json', 'csv', 'excel', 'parquet'],
        choices=['json', 'csv', 'excel', 'parquet'],
        help='Export formats (default: all)'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        default=0.7,
        help='Confidence threshold (default: 0.7)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Data directory (default: data/)'
    )
    
    parser.add_argument(
        '--no-vietnamese',
        action='store_true',
        help='Không dùng Vietnamese model (dùng VADER cho English)'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                   📊 DATA PIPELINE v1.0 📊                    ║
    ║                                                               ║
    ║          Professional Data Processing for TikTok/YouTube     ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize pipeline
    pipeline = DataPipeline(
        data_dir=args.data_dir,
        confidence_threshold=args.confidence,
        use_vietnamese=not args.no_vietnamese
    )
    
    # Run pipeline
    results = pipeline.run(
        platform=args.platform,
        identifier=args.id,
        max_videos=args.videos,
        labeling_method=args.label,
        export_formats=args.formats
    )
    
    # Exit with appropriate code
    if results["success"]:
        print(f"\n✅ SUCCESS! Pipeline completed in {results['duration_seconds']:.1f}s")
        sys.exit(0)
    else:
        print(f"\n❌ FAILED! Error: {results['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
