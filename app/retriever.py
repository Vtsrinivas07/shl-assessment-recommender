"""Semantic retriever for SHL assessment catalog."""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from app.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticRetriever:
    """Retrieves relevant assessments using semantic search."""
    
    def __init__(
        self,
        index_path: str = None,
        metadata_path: str = None,
        model_name: str = None
    ):
        """
        Initialize the semantic retriever.
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata pickle file
            model_name: Name of the sentence-transformers model
        """
        self.index_path = index_path or str(config.FAISS_INDEX)
        self.metadata_path = metadata_path or str(config.METADATA_PKL)
        self.model_name = model_name or config.EMBEDDING_MODEL
        
        logger.info(f"Loading semantic retriever...")
        logger.info(f"Index path: {self.index_path}")
        logger.info(f"Metadata path: {self.metadata_path}")
        
        # Load FAISS index
        if not Path(self.index_path).exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self.index_path}. "
                "Please run the index builder first."
            )
        
        self.index = faiss.read_index(self.index_path)
        logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        
        # Load metadata
        if not Path(self.metadata_path).exists():
            raise FileNotFoundError(
                f"Metadata not found at {self.metadata_path}. "
                "Please run the index builder first."
            )
        
        with open(self.metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        logger.info(f"Loaded metadata with {len(self.metadata)} entries")
        
        # Load embedding model
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Semantic retriever initialized successfully")
    
    def _apply_filters(
        self,
        candidates: List[Dict],
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Apply metadata filters to candidate results.
        
        Args:
            candidates: List of candidate assessment dictionaries
            filters: Dictionary of filter criteria
            
        Returns:
            Filtered list of candidates
        """
        if not filters:
            return candidates
        
        filtered = []
        for candidate in candidates:
            include = True
            
            # Filter by test_type
            if 'test_type' in filters:
                if candidate.get('test_type', '').upper() != filters['test_type'].upper():
                    include = False
            
            # Filter by job_level (partial match)
            if 'job_level' in filters and include:
                job_levels = candidate.get('job_levels', '').lower()
                filter_level = filters['job_level'].lower()
                if filter_level not in job_levels and job_levels != 'all levels':
                    include = False
            
            # Filter by language (partial match)
            if 'language' in filters and include:
                languages = candidate.get('languages', '').lower()
                filter_lang = filters['language'].lower()
                if filter_lang not in languages:
                    include = False
            
            # Filter by remote testing support
            if 'remote_testing' in filters and include:
                remote = candidate.get('remote_testing_support', '').lower()
                if filters['remote_testing'].lower() == 'yes' and remote != 'yes':
                    include = False
            
            if include:
                filtered.append(candidate)
        
        return filtered
    
    def _deduplicate(self, candidates: List[Dict]) -> List[Dict]:
        """
        Deduplicate candidates by assessment name.
        
        Args:
            candidates: List of candidate assessment dictionaries
            
        Returns:
            Deduplicated list of candidates
        """
        seen_names = set()
        deduplicated = []
        
        for candidate in candidates:
            name = candidate.get('name', '').strip()
            if name and name not in seen_names:
                seen_names.add(name)
                deduplicated.append(candidate)
        
        return deduplicated
    
    def retrieve(
        self,
        query: str,
        k: int = None,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Retrieve top-k most relevant assessments for a query.
        
        Args:
            query: Search query string
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of assessment dictionaries with similarity scores
        """
        if k is None:
            k = config.RETRIEVAL_K
        
        logger.info(f"Retrieving top-{k} results for query: {query[:100]}...")
        
        # Generate query embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Search FAISS index
        # Request more results than needed to account for filtering and deduplication
        search_k = min(k * 3, self.index.ntotal)
        scores, indices = self.index.search(query_embedding.astype('float32'), search_k)
        
        # Collect candidates with scores
        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                candidate = self.metadata[idx].copy()
                candidate['similarity_score'] = float(score)
                candidates.append(candidate)
        
        logger.info(f"Found {len(candidates)} initial candidates")
        
        # Apply filters
        if filters:
            candidates = self._apply_filters(candidates, filters)
            logger.info(f"After filtering: {len(candidates)} candidates")
        
        # Deduplicate
        candidates = self._deduplicate(candidates)
        logger.info(f"After deduplication: {len(candidates)} candidates")
        
        # Sort by similarity score (descending) and limit to k
        candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
        results = candidates[:k]
        
        logger.info(f"Returning {len(results)} results")
        
        return results
    
    def retrieve_by_names(self, names: List[str]) -> List[Dict]:
        """
        Retrieve assessments by their names.
        
        Args:
            names: List of assessment names to retrieve
            
        Returns:
            List of assessment dictionaries
        """
        logger.info(f"Retrieving assessments by names: {names}")
        
        # Normalize names for comparison
        normalized_names = [name.strip().lower() for name in names]
        
        results = []
        for item in self.metadata:
            item_name = item.get('name', '').strip().lower()
            if item_name in normalized_names:
                results.append(item.copy())
        
        logger.info(f"Found {len(results)} assessments matching the names")
        
        return results
