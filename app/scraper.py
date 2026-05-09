"""Catalog scraper for SHL Individual Test Solutions."""

import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CatalogScraper:
    """Scrapes SHL product catalog and extracts assessment information."""
    
    BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    def __init__(self):
        """Initialize the catalog scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate that URL belongs to shl.com domain.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return 'shl.com' in parsed.netloc.lower()
        except Exception:
            return False
    
    def _fetch_page(self, url: str, retry_count: int = 0) -> Optional[BeautifulSoup]:
        """
        Fetch a page with retry logic and exponential backoff.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            BeautifulSoup object or None if all retries failed
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except requests.RequestException as e:
            if retry_count < self.MAX_RETRIES:
                wait_time = self.RETRY_DELAY * (2 ** retry_count)
                logger.warning(
                    f"Failed to fetch {url} (attempt {retry_count + 1}/{self.MAX_RETRIES}). "
                    f"Retrying in {wait_time}s... Error: {e}"
                )
                time.sleep(wait_time)
                return self._fetch_page(url, retry_count + 1)
            else:
                logger.error(f"Failed to fetch {url} after {self.MAX_RETRIES} retries: {e}")
                return None
    
    def _extract_product_info(self, product_element) -> Optional[Dict[str, str]]:
        """
        Extract product information from a product element.
        
        Args:
            product_element: BeautifulSoup element containing product data
            
        Returns:
            Dictionary with product information or None if extraction fails
        """
        try:
            # Extract name
            name_elem = product_element.find(['h2', 'h3', 'h4'], class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
            if not name_elem:
                name_elem = product_element.find(['h2', 'h3', 'h4'])
            name = name_elem.get_text(strip=True) if name_elem else "Unknown"
            
            # Extract URL
            link_elem = product_element.find('a', href=True)
            url = urljoin(self.BASE_URL, link_elem['href']) if link_elem else ""
            
            # Validate URL
            if url and not self._validate_url(url):
                logger.warning(f"Invalid URL detected (not shl.com): {url}")
                return None
            
            # Extract description
            desc_elem = product_element.find(['p', 'div'], class_=lambda x: x and ('description' in x.lower() or 'summary' in x.lower()))
            if not desc_elem:
                desc_elem = product_element.find('p')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract test type (K=Knowledge, A=Ability, P=Personality, B=Behavioral)
            test_type = "K"  # Default
            test_type_elem = product_element.find(string=lambda t: t and any(x in t.lower() for x in ['knowledge', 'ability', 'personality', 'behavioral']))
            if test_type_elem:
                text = test_type_elem.lower()
                if 'ability' in text:
                    test_type = "A"
                elif 'personality' in text:
                    test_type = "P"
                elif 'behavioral' in text:
                    test_type = "B"
            
            # Extract duration
            duration_elem = product_element.find(string=lambda t: t and ('min' in t.lower() or 'hour' in t.lower()))
            duration = duration_elem.strip() if duration_elem else "Not specified"
            
            # Extract remote testing support
            remote_elem = product_element.find(string=lambda t: t and 'remote' in t.lower())
            remote_testing_support = "Yes" if remote_elem else "Not specified"
            
            # Extract job levels
            job_levels_elem = product_element.find(string=lambda t: t and any(x in t.lower() for x in ['entry', 'mid', 'senior', 'executive']))
            job_levels = job_levels_elem.strip() if job_levels_elem else "All levels"
            
            # Extract languages
            languages_elem = product_element.find(string=lambda t: t and 'language' in t.lower())
            languages = languages_elem.strip() if languages_elem else "English"
            
            return {
                'name': name,
                'url': url,
                'description': description,
                'test_type': test_type,
                'duration': duration,
                'remote_testing_support': remote_testing_support,
                'job_levels': job_levels,
                'languages': languages
            }
        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
            return None
    
    def scrape_catalog(self, output_path: str = "data/shl_catalog.csv") -> int:
        """
        Scrape the SHL product catalog and save to CSV.
        
        Args:
            output_path: Path to save the CSV file
            
        Returns:
            Number of products extracted
        """
        logger.info(f"Starting catalog scrape from {self.BASE_URL}")
        products = []
        
        # Fetch main catalog page
        soup = self._fetch_page(self.BASE_URL)
        if not soup:
            logger.error("Failed to fetch main catalog page")
            return 0
        
        # Find all product elements
        # Try multiple selectors as the actual structure may vary
        product_elements = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower() or 'card' in x.lower()))
        
        if not product_elements:
            # Fallback: try to find any links that might be products
            logger.warning("No product elements found with standard selectors, trying fallback")
            product_elements = soup.find_all('a', href=lambda x: x and '/product/' in x.lower())
        
        logger.info(f"Found {len(product_elements)} potential product elements")
        
        # Extract information from each product
        for idx, element in enumerate(product_elements, 1):
            product_info = self._extract_product_info(element)
            if product_info and product_info['url']:
                products.append(product_info)
                logger.debug(f"Extracted product {idx}: {product_info['name']}")
        
        # Handle pagination (if exists)
        page_num = 2
        while True:
            next_page_url = f"{self.BASE_URL}?page={page_num}"
            soup = self._fetch_page(next_page_url)
            
            if not soup:
                break
            
            page_products = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower()))
            
            if not page_products:
                logger.info(f"No more products found on page {page_num}, stopping pagination")
                break
            
            logger.info(f"Processing page {page_num} with {len(page_products)} products")
            
            for element in page_products:
                product_info = self._extract_product_info(element)
                if product_info and product_info['url']:
                    products.append(product_info)
            
            page_num += 1
            time.sleep(1)  # Be respectful to the server
        
        # Save to CSV
        if products:
            df = pd.DataFrame(products)
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"Successfully scraped {len(products)} products and saved to {output_path}")
        else:
            logger.warning("No products were extracted")
        
        return len(products)


def main():
    """Main function to run the scraper."""
    scraper = CatalogScraper()
    count = scraper.scrape_catalog()
    print(f"Scraping complete. Total products extracted: {count}")


if __name__ == "__main__":
    main()
