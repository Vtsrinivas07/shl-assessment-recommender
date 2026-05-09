"""Script to build the FAISS index from scraped catalog."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.index_builder import IndexBuilder


def main():
    """Run the index builder."""
    print("="*60)
    print("FAISS INDEX BUILDER")
    print("="*60)
    print()
    
    builder = IndexBuilder()
    
    try:
        builder.build_index()
        builder.verify_index()
        
        print()
        print("="*60)
        print("✓ SUCCESS: Index built and verified")
        print("="*60)
        print()
        print("Next step: Start the API server")
        print("  python run.py")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("="*60)
        print(f"✗ ERROR: {e}")
        print("="*60)
        print()
        print("Make sure you've run the scraper first:")
        print("  python scripts/scrape_catalog.py")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
