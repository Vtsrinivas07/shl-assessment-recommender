"""Index builder for semantic search over SHL catalog."""

import logging
import pickle
from pathlib import Path
from typing import List, Dict
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndexBuilder:
    """Builds FAISS index and metadata for semantic search."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the index builder.
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def _create_text_chunk(self, row: pd.Series) -> str:
        """
        Create a text chunk from catalog row combining relevant fields.
        
        Args:
            row: Pandas Series containing product data
            
        Returns:
            Combined text chunk for embedding
        """
        parts = []
        
        # Add name (most important)
        if pd.notna(row.get('name')):
            parts.append(f"Assessment: {row['name']}")
        
        # Add description
        if pd.notna(row.get('description')) and row['description']:
            parts.append(f"Description: {row['description']}")
        
        # Add test type
        test_type_map = {
            'K': 'Knowledge Test',
            'A': 'Ability Test',
            'P': 'Personality Test',
            'B': 'Behavioral Test'
        }
        if pd.notna(row.get('test_type')):
            test_type_full = test_type_map.get(row['test_type'], row['test_type'])
            parts.append(f"Type: {test_type_full}")
        
        # Add job levels
        if pd.notna(row.get('job_levels')) and row['job_levels'] != 'All levels':
            parts.append(f"Job Levels: {row['job_levels']}")
        
        # Add duration
        if pd.notna(row.get('duration')) and row['duration'] != 'Not specified':
            parts.append(f"Duration: {row['duration']}")
        
        # Add remote testing support
        if pd.notna(row.get('remote_testing_support')) and row['remote_testing_support'] == 'Yes':
            parts.append("Supports remote testing")
        
        # Add languages
        if pd.notna(row.get('languages')) and row['languages'] != 'English':
            parts.append(f"Languages: {row['languages']}")
        
        return ". ".join(parts)
    
    def build_index(
        self,
        csv_path: str = "data/shl_catalog.csv",
        index_path: str = "data/faiss.index",
        metadata_path: str = "data/metadata.pkl"
    ) -> None:
        """
        Build FAISS index and save metadata.
        
        Args:
            csv_path: Path to the catalog CSV file
            index_path: Path to save the FAISS index
            metadata_path: Path to save the metadata pickle file
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV file is empty
        """
        # Validate CSV exists
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"Catalog CSV not found at {csv_path}. Please run the scraper first.")
        
        # Load catalog data
        logger.info(f"Loading catalog data from {csv_path}")
        df = pd.read_csv(csv_path)
        
        if df.empty:
            raise ValueError(f"Catalog CSV at {csv_path} is empty. Please run the scraper first.")
        
        logger.info(f"Loaded {len(df)} products from catalog")
        
        # Create text chunks
        logger.info("Creating text chunks for embedding...")
        text_chunks = []
        metadata = []
        
        for idx, row in df.iterrows():
            text_chunk = self._create_text_chunk(row)
            text_chunks.append(text_chunk)
            
            # Store metadata for each product
            metadata.append({
                'id': idx,
                'name': row.get('name', ''),
                'url': row.get('url', ''),
                'description': row.get('description', ''),
                'test_type': row.get('test_type', ''),
                'duration': row.get('duration', ''),
                'remote_testing_support': row.get('remote_testing_support', ''),
                'job_levels': row.get('job_levels', ''),
                'languages': row.get('languages', ''),
                'text_chunk': text_chunk
            })
        
        logger.info(f"Created {len(text_chunks)} text chunks")
        
        # Generate embeddings
        logger.info("Generating embeddings (this may take a few minutes)...")
        embeddings = self.model.encode(
            text_chunks,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        
        # Create FAISS index
        logger.info("Creating FAISS index...")
        index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for normalized vectors = cosine similarity
        index.add(embeddings.astype('float32'))
        
        logger.info(f"FAISS index created with {index.ntotal} vectors")
        
        # Save FAISS index
        index_file = Path(index_path)
        index_file.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(index_file))
        logger.info(f"FAISS index saved to {index_path}")
        
        # Save metadata
        metadata_file = Path(metadata_path)
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        logger.info(f"Metadata saved to {metadata_path}")
        
        logger.info("Index building complete!")
    
    def verify_index(
        self,
        index_path: str = "data/faiss.index",
        metadata_path: str = "data/metadata.pkl"
    ) -> None:
        """
        Verify that index and metadata were created correctly.
        
        Args:
            index_path: Path to the FAISS index
            metadata_path: Path to the metadata pickle file
        """
        # Load index
        index = faiss.read_index(index_path)
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors")
        
        # Load metadata
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        logger.info(f"Loaded metadata with {len(metadata)} entries")
        
        # Verify counts match
        if index.ntotal != len(metadata):
            logger.warning(f"Mismatch: index has {index.ntotal} vectors but metadata has {len(metadata)} entries")
        else:
            logger.info("✓ Index and metadata counts match")
        
        # Show sample
        if metadata:
            logger.info(f"Sample product: {metadata[0]['name']}")


def main():
    """Main function to build the index."""
    builder = IndexBuilder()
    
    try:
        builder.build_index()
        builder.verify_index()
        print("\n✓ Index building successful!")
    except Exception as e:
        print(f"\n✗ Index building failed: {e}")
        raise


if __name__ == "__main__":
    main()
