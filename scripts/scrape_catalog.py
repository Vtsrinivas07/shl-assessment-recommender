"""Script to scrape the SHL product catalog."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scraper import CatalogScraper


def main():
    """Run the catalog scraper."""
    print("="*60)
    print("SHL CATALOG SCRAPER")
    print("="*60)
    print()
    
    scraper = CatalogScraper()
    
    try:
        count = scraper.scrape_catalog()
        
        print()
        print("="*60)
        print(f"✓ SUCCESS: Scraped {count} products")
        print("="*60)
        print()
        print("Next step: Run the index builder")
        print("  python scripts/build_index.py")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("="*60)
        print(f"✗ ERROR: {e}")
        print("="*60)
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
