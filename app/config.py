"""Configuration management for the SHL Assessment Recommender API."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # LLM Configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    # Retrieval Configuration
    RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "20"))
    MAX_RECOMMENDATIONS: int = 10
    MIN_RECOMMENDATIONS: int = 1
    
    # Data Paths
    DATA_DIR: Path = Path("data")
    CATALOG_CSV: Path = DATA_DIR / "shl_catalog.csv"
    FAISS_INDEX: Path = DATA_DIR / "faiss.index"
    METADATA_PKL: Path = DATA_DIR / "metadata.pkl"
    
    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Conversation Configuration
    MAX_CLARIFICATIONS: int = 2
    MAX_CONVERSATION_TURNS: int = 8
    
    # URL Validation
    VALID_DOMAIN: str = "shl.com"
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration.
        
        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is required. Please set it in your .env file or environment variables. "
                "You can get an API key from https://console.groq.com/"
            )
        
        # Validate temperature range
        if not 0.0 <= cls.TEMPERATURE <= 2.0:
            raise ValueError(f"TEMPERATURE must be between 0.0 and 2.0, got {cls.TEMPERATURE}")
        
        # Validate retrieval k
        if cls.RETRIEVAL_K < 1:
            raise ValueError(f"RETRIEVAL_K must be at least 1, got {cls.RETRIEVAL_K}")


# Validate configuration on module import
try:
    Config.validate()
except ValueError as e:
    # Don't fail on import, but log the error
    # This allows the module to be imported for testing
    import logging
    logging.warning(f"Configuration validation failed: {e}")


# Export config instance
config = Config()
