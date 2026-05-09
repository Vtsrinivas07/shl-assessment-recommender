# Implementation Plan: SHL Assessment Recommender

## Overview

This implementation plan breaks down the SHL Assessment Recommender into discrete coding tasks. The system is a stateless conversational API built with FastAPI that uses semantic search (FAISS + Sentence Transformers) and LLM-powered conversation management (Groq API with Llama 3.3 70B) to recommend SHL Individual Test Solutions based on natural language queries.

The implementation follows a bottom-up approach: data layer (scraping and indexing) → core components (schemas, retriever, LLM client) → business logic (agent) → API layer (FastAPI endpoints) → testing and deployment.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create project directory structure with folders: `app/`, `data/`, `tests/`, `docs/`
  - Create `requirements.txt` with pinned dependencies: fastapi, uvicorn, pydantic, sentence-transformers, faiss-cpu, pandas, beautifulsoup4, requests, groq, python-dotenv, pytest, httpx
  - Create `.env.example` template with GROQ_API_KEY placeholder
  - Create `.gitignore` for Python projects (exclude `.env`, `__pycache__/`, `*.pyc`, `data/`, `.pytest_cache/`)
  - _Requirements: 22.1, 22.2, 22.3, 18.2_

- [x] 2. Implement catalog scraper
  - [x] 2.1 Create `app/scraper.py` with CatalogScraper class
    - Implement scraping logic for https://www.shl.com/solutions/products/product-catalog/
    - Extract fields: name, url, description, test_type, duration, remote_testing_support, job_levels, languages
    - Handle pagination to retrieve all products
    - Implement retry logic with exponential backoff (3 retries)
    - Validate all URLs belong to shl.com domain
    - Save results to `data/shl_catalog.csv`
    - Log total number of products extracted
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 2.2 Write unit tests for catalog scraper
    - Test URL validation logic
    - Test CSV output format
    - Test retry mechanism with mocked failures
    - Test pagination handling
    - _Requirements: 5.4, 5.6, 19.1_

- [x] 3. Implement semantic index builder
  - [x] 3.1 Create `app/index_builder.py` with IndexBuilder class
    - Load catalog data from `data/shl_catalog.csv`
    - Create text chunks combining name, description, test_type, and metadata
    - Generate embeddings using sentence-transformers `all-MiniLM-L6-v2` model
    - Create FAISS index from embeddings
    - Save FAISS index to `data/faiss.index`
    - Save metadata mapping to `data/metadata.pkl`
    - Raise descriptive error when CSV is missing or empty
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [ ]* 3.2 Write unit tests for index builder
    - Test embedding generation
    - Test FAISS index creation
    - Test metadata serialization
    - Test error handling for missing CSV
    - _Requirements: 6.7, 19.1_

- [ ] 4. Checkpoint - Verify data pipeline
  - Run scraper and index builder to generate `data/shl_catalog.csv`, `data/faiss.index`, and `data/metadata.pkl`
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement core API schemas
  - [x] 5.1 Create `app/schemas.py` with Pydantic models
    - Define `Message` model with role (Literal["user", "assistant"]) and content (str) fields
    - Define `ChatRequest` model with messages (List[Message]) field
    - Define `Recommendation` model with name, url, test_type fields
    - Define `ChatResponse` model with reply, recommendations (List[Recommendation]), end_of_conversation fields
    - Define `HealthResponse` model with status field
    - Add validation for non-empty content
    - Add validation for alternating roles
    - Add validation that last message is from user
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4_

  - [ ]* 5.2 Write unit tests for schemas
    - Test valid message arrays
    - Test rejection of invalid roles
    - Test rejection of empty content
    - Test validation of conversation alternation
    - Test validation of last message role
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 19.2_

- [x] 6. Implement configuration management
  - [x] 6.1 Create `app/config.py` with configuration loading
    - Load GROQ_API_KEY from environment variables using python-dotenv
    - Define configuration constants: model name, temperature, retrieval parameters (k=20)
    - Validate required configuration on module import
    - Raise descriptive error when GROQ_API_KEY is missing
    - _Requirements: 18.1, 18.3, 18.4, 8.2, 8.3_

  - [ ]* 6.2 Write unit tests for configuration
    - Test successful loading with valid environment
    - Test error when GROQ_API_KEY is missing
    - Test default values for optional parameters
    - _Requirements: 8.3, 18.4, 19.1_

- [x] 7. Implement semantic retriever
  - [x] 7.1 Create `app/retriever.py` with SemanticRetriever class
    - Load FAISS index and metadata on initialization
    - Implement `retrieve(query: str, k: int, filters: dict)` method
    - Generate query embedding using same sentence-transformers model
    - Perform FAISS similarity search
    - Apply metadata filtering by test_type, job_level, language
    - Deduplicate results by assessment name
    - Return results ranked by similarity score in descending order
    - Return empty list when no results match
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [x] 7.2 Implement `retrieve_by_names(names: List[str])` method
    - Search metadata for assessments matching given names
    - Return full assessment objects with all catalog fields
    - _Requirements: 12.2, 7.4_

  - [ ]* 7.3 Write unit tests for retriever
    - Test retrieval with various queries
    - Test metadata filtering
    - Test deduplication logic
    - Test empty result handling
    - Test retrieve_by_names method
    - _Requirements: 7.1, 7.2, 7.3, 7.6, 19.1_

- [x] 8. Implement LLM client
  - [x] 8.1 Create `app/llm_client.py` with LLMClient class
    - Initialize Groq client with API key from config
    - Implement `generate(system_prompt: str, messages: List[dict])` method
    - Use llama-3.3-70b-versatile model
    - Set temperature to 0.1
    - Return generated text response
    - Raise exception with error details on API failure
    - _Requirements: 8.1, 8.2, 8.4, 8.5, 8.6, 8.7_

  - [ ]* 8.2 Write unit tests for LLM client
    - Test successful generation with mocked API
    - Test error handling for API failures
    - Test correct model and temperature parameters
    - _Requirements: 8.7, 19.1_

- [ ] 9. Checkpoint - Verify core components
  - Test retriever with sample queries
  - Test LLM client with sample prompts
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement prompt templates
  - [x] 10.1 Create `app/prompts.py` with prompt templates
    - Define system prompt for conversational agent with scope, grounding rules, and response format
    - Define clarification prompt template
    - Define recommendation prompt template
    - Define comparison prompt template
    - Define refusal prompt template
    - Include instructions for prompt injection resistance
    - Include instructions for URL validation
    - _Requirements: 9.1, 10.4, 12.3, 13.1, 13.2, 14.1, 14.2, 15.1_

  - [ ]* 10.2 Write unit tests for prompt templates
    - Test prompt formatting with various inputs
    - Test that prompts include grounding instructions
    - Test that prompts include refusal instructions
    - _Requirements: 10.6, 13.1, 14.3, 19.1_

- [x] 11. Implement conversational agent
  - [x] 11.1 Create `app/agent.py` with ConversationalAgent class
    - Initialize with retriever and LLM client
    - Implement `process_conversation(messages: List[Message])` method
    - Implement intent detection logic (off-topic, clarification, recommendation, comparison, refinement)
    - _Requirements: 9.1, 10.1, 11.1, 12.1, 13.1_

  - [x] 11.2 Implement off-topic request handling
    - Detect off-topic requests before retrieval
    - Return polite refusal with scope explanation
    - Return empty recommendations array
    - Set end_of_conversation to true
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 11.3 Implement clarification flow
    - Detect vague queries lacking specificity
    - Retrieve candidate assessments (k=20)
    - Generate clarifying question using LLM with catalog context
    - Return empty recommendations array
    - Set end_of_conversation to false
    - Track clarification count (max 2 per conversation)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 11.4 Implement recommendation flow
    - Retrieve candidate assessments with filters (k=20)
    - Implement hybrid re-ranking combining semantic similarity and keyword overlap
    - Select top 1-10 most relevant assessments
    - Generate response text using LLM
    - Validate all URLs belong to shl.com domain
    - Return recommendation objects with name, url, test_type
    - Set end_of_conversation to false
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 15.1, 15.2, 15.3_

  - [x] 11.5 Implement refinement flow
    - Detect refinement intent from constraint phrases
    - Extract filters from user message (duration, remote testing, language)
    - Retrieve new candidates with updated filters
    - Return updated recommendations
    - Acknowledge refinement in reply text
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 11.6 Implement comparison flow
    - Detect comparison intent
    - Extract assessment names from user message
    - Retrieve catalog details using retrieve_by_names
    - Generate comparison highlighting differences
    - Handle missing assessments gracefully
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 11.7 Implement conversation completion logic
    - Track conversation turn count
    - Set end_of_conversation to true after recommendations are provided and refined
    - Set end_of_conversation to true when user expresses satisfaction
    - Aim for completion within 8 turns
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 11.8 Implement URL validation and logging
    - Validate all recommendation URLs against shl.com domain
    - Exclude invalid URLs from recommendations
    - Log warnings for invalid URLs
    - Never generate or hallucinate URLs
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [ ]* 11.9 Write unit tests for agent
    - Test off-topic request refusal
    - Test clarification generation
    - Test recommendation generation
    - Test refinement handling
    - Test comparison generation
    - Test URL validation
    - Test conversation completion logic
    - Test prompt injection resistance
    - _Requirements: 19.3, 19.4, 19.5, 19.6, 19.7, 19.8_

- [ ] 12. Checkpoint - Verify agent logic
  - Test agent with various conversation scenarios
  - Verify grounding and URL validation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement FastAPI application
  - [x] 13.1 Create `app/main.py` with FastAPI application
    - Initialize FastAPI app with title and description
    - Configure CORS middleware for all origins, POST/GET methods, standard headers
    - Initialize retriever and agent on startup
    - Handle initialization errors gracefully
    - _Requirements: 1.1, 24.1, 24.2, 24.3, 24.4, 17.1_

  - [x] 13.2 Implement GET /health endpoint
    - Return HTTP 200 status code
    - Return JSON with status: "ok"
    - Respond within 1 second
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 13.3 Implement POST /chat endpoint
    - Accept ChatRequest with message array
    - Validate request schema using Pydantic
    - Process conversation using agent
    - Return ChatResponse with reply, recommendations, end_of_conversation
    - Respond within 30 seconds
    - Return HTTP 422 for validation errors
    - Return HTTP 500 for internal errors with descriptive messages
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 13.4 Implement error handling
    - Handle missing FAISS index with HTTP 500
    - Handle LLM API failures with fallback response
    - Handle empty retrieval results gracefully
    - Log all errors with context
    - Avoid exposing internal details in error messages
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [x] 13.5 Implement structured logging
    - Log all incoming requests with timestamp and endpoint
    - Log retrieval results with query and candidate count
    - Log LLM generation with token counts
    - Log errors with full stack traces
    - Use structured logging format
    - Avoid logging sensitive information
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6_

  - [ ]* 13.6 Write integration tests for API endpoints
    - Test health endpoint returns correct status
    - Test chat endpoint with valid requests
    - Test chat endpoint validation errors
    - Test chat endpoint with various conversation scenarios
    - Test error handling for missing index
    - Test CORS headers
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6_

- [ ] 14. Checkpoint - Verify API functionality
  - Start FastAPI server locally
  - Test health endpoint with curl
  - Test chat endpoint with sample conversations
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Create documentation
  - [x] 15.1 Create `README.md` with comprehensive documentation
    - Add project overview and features
    - Add setup instructions (clone, install dependencies, configure .env)
    - Add data pipeline instructions (run scraper, build index)
    - Add API usage examples with curl commands for /health and /chat
    - Add deployment instructions for local and Render
    - Add troubleshooting section
    - _Requirements: 21.1, 21.5, 21.6_

  - [x] 15.2 Create `docs/approach.md` with technical documentation
    - Document architecture and design decisions
    - Explain retrieval design (semantic search, hybrid ranking)
    - Explain prompt engineering approach
    - Document evaluation metrics (Recall@10, Precision@10, groundedness, schema compliance, conversation turns, refusal correctness)
    - Document failed experiments and lessons learned
    - _Requirements: 21.2, 21.3, 21.4_

- [x] 16. Implement evaluation utilities
  - [x] 16.1 Create `app/evaluation.py` with evaluation functions
    - Implement Recall@10 calculation
    - Implement Precision@10 calculation
    - Implement groundedness measurement (percentage of recommendations in retrieved evidence)
    - Implement schema compliance validation
    - Implement conversation turn tracking
    - Implement refusal correctness measurement
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6_

  - [ ]* 16.2 Write unit tests for evaluation utilities
    - Test metric calculations with sample data
    - Test edge cases (empty results, perfect scores)
    - _Requirements: 19.1, 19.8_

- [x] 17. Create deployment configuration
  - [x] 17.1 Create `Dockerfile` for containerized deployment
    - Use Python 3.11 base image
    - Copy requirements.txt and install dependencies
    - Copy application code
    - Expose application port (8000)
    - Set CMD to run uvicorn server
    - _Requirements: 20.1, 20.2, 20.3, 20.4_

  - [x] 17.2 Create `render.yaml` for Render platform deployment
    - Configure web service with appropriate start command
    - Set environment variables
    - Configure health check endpoint
    - Ensure compatibility with Render free tier
    - _Requirements: 20.5, 20.6, 20.7_

  - [ ]* 17.3 Write deployment verification tests
    - Test Docker build succeeds
    - Test container starts successfully
    - Test health endpoint accessible in container
    - _Requirements: 20.1, 19.1_

- [ ] 18. Final checkpoint - Complete system verification
  - Run complete test suite and verify 80% code coverage
  - Test end-to-end conversation flows
  - Verify all requirements are met
  - Test deployment configuration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- The implementation uses Python with FastAPI, FAISS, Sentence Transformers, and Groq API
- Data pipeline (scraping and indexing) must be run before API can function
- All recommendations must be grounded in retrieved catalog evidence
- URL validation is critical for security and trust
