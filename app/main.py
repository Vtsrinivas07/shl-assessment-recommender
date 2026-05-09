"""FastAPI application for SHL Assessment Recommender."""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.schemas import ChatRequest, ChatResponse, HealthResponse
from app.retriever import SemanticRetriever
from app.llm_client import LLMClient
from app.agent import ConversationalAgent
from app.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
retriever = None
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global retriever, agent
    
    # Startup
    logger.info("Starting SHL Assessment Recommender API...")
    
    try:
        # Validate configuration
        config.validate()
        logger.info("✓ Configuration validated")
        
        # Initialize retriever
        logger.info("Initializing semantic retriever...")
        retriever = SemanticRetriever()
        logger.info("✓ Semantic retriever initialized")
        
        # Initialize LLM client
        logger.info("Initializing LLM client...")
        llm_client = LLMClient()
        logger.info("✓ LLM client initialized")
        
        # Initialize agent
        logger.info("Initializing conversational agent...")
        agent = ConversationalAgent(retriever, llm_client)
        logger.info("✓ Conversational agent initialized")
        
        logger.info("🚀 API startup complete!")
        
    except FileNotFoundError as e:
        logger.error(f"❌ Startup failed - Missing data files: {e}")
        logger.error("Please run the scraper and index builder first:")
        logger.error("  1. python -m app.scraper")
        logger.error("  2. python -m app.index_builder")
        raise
    except ValueError as e:
        logger.error(f"❌ Startup failed - Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Startup failed - Unexpected error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down SHL Assessment Recommender API...")


# Create FastAPI app
app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational API for recommending SHL Individual Test Solutions",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    logger.info(f"→ {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"← {request.method} {request.url.path} - {response.status_code} ({duration:.2f}s)")
    
    return response


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with status "ok"
    """
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for conversational recommendations.
    
    Args:
        request: ChatRequest with conversation history
        
    Returns:
        ChatResponse with reply, recommendations, and end_of_conversation flag
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Processing chat request with {len(request.messages)} messages")
        
        # Check if agent is initialized
        if agent is None:
            logger.error("Agent not initialized")
            raise HTTPException(
                status_code=500,
                detail="Service not ready. Please ensure data files are available."
            )
        
        # Process conversation
        start_time = time.time()
        response = agent.process_conversation(request.messages)
        duration = time.time() - start_time
        
        logger.info(f"Generated response with {len(response.recommendations)} recommendations ({duration:.2f}s)")
        
        # Check response time
        if duration > 30:
            logger.warning(f"Response time exceeded 30s: {duration:.2f}s")
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        
        # Return fallback response
        return ChatResponse(
            reply="I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
            recommendations=[],
            end_of_conversation=False
        )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found. Available endpoints: GET /health, POST /chat"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please check logs for details."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
