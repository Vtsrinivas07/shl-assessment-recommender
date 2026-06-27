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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
retriever = None
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global retriever, agent

    logger.info("Starting SHL Assessment Recommender API...")

    try:
        config.validate()
        logger.info("✓ Configuration validated")

        logger.info("Initializing semantic retriever...")
        retriever = SemanticRetriever()
        logger.info("✓ Semantic retriever initialized")

        logger.info("Initializing LLM client...")
        llm_client = LLMClient()
        logger.info("✓ LLM client initialized")

        logger.info("Initializing conversational agent...")
        agent = ConversationalAgent(retriever, llm_client)
        logger.info("✓ Conversational agent initialized")

        logger.info("🚀 API startup complete!")

    except FileNotFoundError as e:
        logger.error(f"Missing data files: {e}")
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    logger.info("Shutting down SHL Assessment Recommender API...")


app = FastAPI(
    title="SHL Assessment Recommender API",
    description="Conversational API for recommending SHL assessments",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    logger.info(f"→ {request.method} {request.url.path}")

    response = await call_next(request)

    logger.info(
        f"← {request.method} {request.url.path} - {response.status_code} ({time.time()-start:.2f}s)"
    )

    return response


# -------------------------------
# ROOT ENDPOINT
# -------------------------------
@app.get("/")
async def root():
    return {
        "message": "🚀 SHL Assessment Recommender API is running!",
        "version": "1.0.0",
        "status": "healthy",
        "documentation": "/docs",
        "health": "/health",
        "chat_endpoint": "/chat",
    }


# -------------------------------
# HEALTH CHECK
# -------------------------------
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")


# -------------------------------
# CHAT ENDPOINT
# -------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(
            f"Processing request with {len(request.messages)} messages"
        )

        if agent is None:
            raise HTTPException(
                status_code=500,
                detail="Service not initialized.",
            )

        start = time.time()

        response = agent.process_conversation(request.messages)

        logger.info(
            f"Generated {len(response.recommendations)} recommendations in {time.time()-start:.2f}s"
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(e)

        return ChatResponse(
            reply="I'm sorry, an internal error occurred. Please try again.",
            recommendations=[],
            end_of_conversation=False,
        )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "message": "Endpoint not found.",
            "available_endpoints": {
                "/": "API Home",
                "/docs": "Swagger UI",
                "/redoc": "ReDoc",
                "/health": "Health Check",
                "/chat": "POST Chat API",
            },
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.exception(exc)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error"
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
