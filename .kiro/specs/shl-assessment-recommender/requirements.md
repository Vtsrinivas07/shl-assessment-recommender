# Requirements Document

## Introduction

The SHL Assessment Recommender is a stateless conversational recommendation API that helps hiring managers discover relevant SHL Individual Test Solutions from the SHL product catalog. The system uses natural language conversation to clarify hiring needs, retrieve relevant assessments using semantic search, and provide grounded recommendations with catalog evidence.

## Glossary

- **API**: The FastAPI-based REST service exposing health and chat endpoints
- **Catalog_Scraper**: Component that extracts SHL product data from the official catalog website
- **Index_Builder**: Component that creates embeddings and FAISS index from catalog data
- **Retriever**: Component that performs semantic search over the catalog using embeddings
- **LLM_Client**: Wrapper for Groq API using llama-3.3-70b-versatile model
- **Agent**: Core conversational logic that orchestrates retrieval, ranking, and response generation
- **Conversation_History**: Array of message objects containing role and content
- **Recommendation**: Structured object containing assessment name, URL, and test type
- **Grounded_Response**: Response based solely on retrieved catalog evidence
- **Test_Type**: Single-character code (K=Knowledge, A=Ability, P=Personality, B=Behavioral)
- **Stateless_Operation**: Processing where each request contains complete context without server-side session storage

## Requirements

### Requirement 1: Health Check Endpoint

**User Story:** As a system administrator, I want a health check endpoint, so that I can monitor API availability.

#### Acceptance Criteria

1. WHEN a GET request is sent to /health, THE API SHALL return HTTP 200 status code
2. WHEN a GET request is sent to /health, THE API SHALL return a JSON object with status field set to "ok"
3. THE API SHALL respond to health checks within 1 second

### Requirement 2: Stateless Chat Endpoint

**User Story:** As a client application, I want a stateless chat endpoint, so that I can send conversation history and receive recommendations without managing sessions.

#### Acceptance Criteria

1. WHEN a POST request is sent to /chat with valid message array, THE API SHALL process the complete conversation history
2. THE API SHALL NOT store any conversation state between requests
3. WHEN the message array is empty, THE API SHALL return HTTP 422 validation error
4. WHEN the message array contains invalid role values, THE API SHALL return HTTP 422 validation error
5. THE API SHALL respond to chat requests within 30 seconds
6. WHEN processing fails, THE API SHALL return appropriate HTTP error codes with descriptive messages

### Requirement 3: Request Schema Validation

**User Story:** As an API consumer, I want strict request validation, so that I receive clear feedback on malformed requests.

#### Acceptance Criteria

1. THE API SHALL accept requests with messages array containing objects with role and content fields
2. WHEN role is not "user" or "assistant", THE API SHALL reject the request with validation error
3. WHEN content is empty or missing, THE API SHALL reject the request with validation error
4. THE API SHALL validate that conversation alternates between user and assistant roles
5. THE API SHALL validate that the last message role is "user"

### Requirement 4: Response Schema Compliance

**User Story:** As an API consumer, I want consistent response structure, so that I can reliably parse recommendations.

#### Acceptance Criteria

1. THE API SHALL return responses with reply, recommendations, and end_of_conversation fields
2. WHEN clarifying or refusing, THE API SHALL return empty recommendations array
3. WHEN recommending assessments, THE API SHALL return 1 to 10 recommendation objects
4. THE API SHALL include name, url, and test_type fields in each recommendation object
5. THE API SHALL ensure reply text is JSON-safe without unescaped quotes or newlines
6. THE API SHALL set end_of_conversation to true when conversation should terminate
7. THE API SHALL set end_of_conversation to false when further interaction is expected

### Requirement 5: Catalog Data Scraping

**User Story:** As a system operator, I want to scrape the SHL catalog, so that the system has current product data.

#### Acceptance Criteria

1. THE Catalog_Scraper SHALL extract data from https://www.shl.com/solutions/products/product-catalog/
2. THE Catalog_Scraper SHALL extract name, url, description, test_type, duration, remote_testing_support, job_levels, and languages fields
3. THE Catalog_Scraper SHALL handle pagination to retrieve all available products
4. WHEN a page fails to load, THE Catalog_Scraper SHALL retry up to 3 times with exponential backoff
5. THE Catalog_Scraper SHALL save extracted data to CSV format in data/shl_catalog.csv
6. THE Catalog_Scraper SHALL validate that all extracted URLs belong to shl.com domain
7. WHEN scraping completes, THE Catalog_Scraper SHALL log the total number of products extracted

### Requirement 6: Semantic Index Construction

**User Story:** As a system operator, I want to build a semantic search index, so that the system can retrieve relevant assessments efficiently.

#### Acceptance Criteria

1. THE Index_Builder SHALL load catalog data from data/shl_catalog.csv
2. THE Index_Builder SHALL create text chunks combining name, description, test_type, and metadata for each product
3. THE Index_Builder SHALL generate embeddings using sentence-transformers all-MiniLM-L6-v2 model
4. THE Index_Builder SHALL create a FAISS index from the embeddings
5. THE Index_Builder SHALL save the FAISS index to data/faiss.index
6. THE Index_Builder SHALL save metadata mapping to data/metadata.pkl
7. WHEN the CSV file is missing or empty, THE Index_Builder SHALL raise a descriptive error

### Requirement 7: Semantic Retrieval

**User Story:** As the Agent, I want to retrieve relevant assessments, so that I can provide grounded recommendations.

#### Acceptance Criteria

1. WHEN given a query string, THE Retriever SHALL return top-k most semantically similar assessments
2. THE Retriever SHALL support metadata filtering by test_type, job_level, and language
3. THE Retriever SHALL deduplicate results by assessment name
4. THE Retriever SHALL return assessment objects with all catalog fields
5. THE Retriever SHALL return results ranked by semantic similarity score in descending order
6. WHEN no results match the query, THE Retriever SHALL return an empty list
7. THE Retriever SHALL load the FAISS index and metadata on initialization

### Requirement 8: LLM Integration

**User Story:** As the Agent, I want to generate natural language responses, so that I can communicate with users effectively.

#### Acceptance Criteria

1. THE LLM_Client SHALL use Groq API with llama-3.3-70b-versatile model
2. THE LLM_Client SHALL load GROQ_API_KEY from environment variables
3. WHEN GROQ_API_KEY is missing, THE LLM_Client SHALL raise a configuration error on initialization
4. THE LLM_Client SHALL use temperature 0.1 for deterministic generation
5. THE LLM_Client SHALL accept system prompt and conversation history as input
6. THE LLM_Client SHALL return the generated text response
7. WHEN API request fails, THE LLM_Client SHALL raise an exception with the error details

### Requirement 9: Query Clarification

**User Story:** As a hiring manager, I want the system to ask clarifying questions, so that I receive relevant recommendations.

#### Acceptance Criteria

1. WHEN the user query lacks specificity about role, seniority, or skills, THE Agent SHALL generate a clarifying question
2. WHEN clarifying, THE Agent SHALL return empty recommendations array
3. WHEN clarifying, THE Agent SHALL set end_of_conversation to false
4. THE Agent SHALL avoid asking more than 2 clarifying questions per conversation
5. THE Agent SHALL use retrieved catalog context to inform clarification questions

### Requirement 10: Assessment Recommendation

**User Story:** As a hiring manager, I want to receive relevant assessment recommendations, so that I can evaluate candidates effectively.

#### Acceptance Criteria

1. WHEN the user query is sufficiently specific, THE Agent SHALL retrieve candidate assessments using semantic search
2. THE Agent SHALL re-rank candidates by combining semantic similarity and keyword overlap scores
3. THE Agent SHALL select 1 to 10 most relevant assessments for recommendation
4. THE Agent SHALL generate a concise reply explaining the recommendations
5. THE Agent SHALL return recommendation objects with name, url, and test_type fields
6. THE Agent SHALL ensure all recommended URLs are from the retrieved catalog evidence
7. THE Agent SHALL set end_of_conversation to false to allow refinement

### Requirement 11: Recommendation Refinement

**User Story:** As a hiring manager, I want to refine recommendations based on additional constraints, so that I can narrow down options.

#### Acceptance Criteria

1. WHEN the user adds constraints after receiving recommendations, THE Agent SHALL retrieve new candidates with updated filters
2. THE Agent SHALL detect refinement intent from phrases like "shorter duration", "remote testing", or "specific language"
3. THE Agent SHALL apply metadata filters to the Retriever based on detected constraints
4. THE Agent SHALL return updated recommendations reflecting the new constraints
5. THE Agent SHALL acknowledge the refinement in the reply text

### Requirement 12: Assessment Comparison

**User Story:** As a hiring manager, I want to compare specific assessments, so that I can make informed selection decisions.

#### Acceptance Criteria

1. WHEN the user requests comparison between assessments, THE Agent SHALL detect comparison intent
2. THE Agent SHALL retrieve catalog details for the specified assessments
3. THE Agent SHALL generate a comparison highlighting differences in test_type, duration, job_levels, and languages
4. THE Agent SHALL base comparison solely on retrieved catalog evidence
5. WHEN a requested assessment is not found in the catalog, THE Agent SHALL state that it cannot compare unknown assessments

### Requirement 13: Off-Topic Request Refusal

**User Story:** As a system owner, I want the system to refuse off-topic requests, so that it stays focused on SHL assessments.

#### Acceptance Criteria

1. WHEN the user asks about non-SHL products, THE Agent SHALL politely refuse and explain its scope
2. WHEN the user asks about topics unrelated to hiring or assessments, THE Agent SHALL politely refuse
3. WHEN refusing, THE Agent SHALL return empty recommendations array
4. WHEN refusing, THE Agent SHALL set end_of_conversation to true
5. THE Agent SHALL detect off-topic intent before performing retrieval

### Requirement 14: Prompt Injection Defense

**User Story:** As a system owner, I want the system to resist prompt injection attacks, so that it maintains secure operation.

#### Acceptance Criteria

1. WHEN the user attempts to override system instructions, THE Agent SHALL ignore the injection and respond within scope
2. WHEN the user requests the system prompt or internal instructions, THE Agent SHALL refuse
3. THE Agent SHALL validate that generated responses stay within the SHL assessment domain
4. THE Agent SHALL not execute instructions embedded in user messages that contradict system behavior

### Requirement 15: URL Validation

**User Story:** As a system owner, I want all recommended URLs validated, so that users only receive legitimate SHL links.

#### Acceptance Criteria

1. THE Agent SHALL validate that all recommendation URLs belong to shl.com domain
2. WHEN a retrieved URL does not match shl.com domain, THE Agent SHALL exclude it from recommendations
3. THE Agent SHALL never generate or hallucinate URLs not present in the catalog
4. THE Agent SHALL log warnings when invalid URLs are detected in catalog data

### Requirement 16: Conversation Completion

**User Story:** As a hiring manager, I want conversations to complete efficiently, so that I can get recommendations quickly.

#### Acceptance Criteria

1. THE Agent SHALL aim to complete conversations within 8 turns
2. WHEN recommendations have been provided and refined, THE Agent SHALL set end_of_conversation to true
3. WHEN the user expresses satisfaction, THE Agent SHALL set end_of_conversation to true
4. THE Agent SHALL avoid unnecessary follow-up questions after providing comprehensive recommendations

### Requirement 17: Error Handling and Resilience

**User Story:** As an API consumer, I want graceful error handling, so that failures provide actionable feedback.

#### Acceptance Criteria

1. WHEN the FAISS index is missing, THE API SHALL return HTTP 500 with descriptive error message
2. WHEN the LLM API fails, THE Agent SHALL return a fallback response with retrieved recommendations
3. WHEN retrieval returns no results, THE Agent SHALL inform the user that no matching assessments were found
4. THE API SHALL log all errors with sufficient context for debugging
5. THE API SHALL not expose internal implementation details in error messages

### Requirement 18: Configuration Management

**User Story:** As a system operator, I want environment-based configuration, so that I can deploy across different environments.

#### Acceptance Criteria

1. THE API SHALL load GROQ_API_KEY from environment variables or .env file
2. THE API SHALL provide .env.example template with required variables
3. THE API SHALL validate required configuration on startup
4. WHEN required configuration is missing, THE API SHALL fail startup with clear error message
5. THE API SHALL support configuration of model name, temperature, and retrieval parameters

### Requirement 19: Testing Coverage

**User Story:** As a developer, I want comprehensive tests, so that I can verify system behavior and prevent regressions.

#### Acceptance Criteria

1. THE test suite SHALL include tests for health endpoint returning correct status
2. THE test suite SHALL include tests for schema validation of requests and responses
3. THE test suite SHALL include tests for clarification behavior with vague queries
4. THE test suite SHALL include tests for recommendation generation with specific queries
5. THE test suite SHALL include tests for comparison behavior
6. THE test suite SHALL include tests for refusal of off-topic requests
7. THE test suite SHALL include tests for prompt injection resistance
8. THE test suite SHALL achieve at least 80% code coverage

### Requirement 20: Deployment Configuration

**User Story:** As a system operator, I want deployment automation, so that I can deploy to production environments easily.

#### Acceptance Criteria

1. THE project SHALL include a Dockerfile for containerized deployment
2. THE Dockerfile SHALL use Python 3.11 base image
3. THE Dockerfile SHALL install all dependencies from requirements.txt
4. THE Dockerfile SHALL expose the application port
5. THE project SHALL include render.yaml for Render platform deployment
6. THE render.yaml SHALL configure the web service with appropriate start command
7. THE deployment SHALL be compatible with Render free tier resource limits

### Requirement 21: Documentation

**User Story:** As a developer or evaluator, I want comprehensive documentation, so that I can understand, run, and evaluate the system.

#### Acceptance Criteria

1. THE project SHALL include README.md with setup instructions, API usage examples, and deployment steps
2. THE project SHALL include docs/approach.md explaining architecture, retrieval design, and prompt engineering
3. THE docs/approach.md SHALL document evaluation metrics including Recall@10, groundedness, and schema compliance
4. THE docs/approach.md SHALL document failed experiments and lessons learned
5. THE README.md SHALL include example curl commands for both endpoints
6. THE documentation SHALL explain the scraping and indexing workflow

### Requirement 22: Dependency Management

**User Story:** As a developer, I want pinned dependencies, so that builds are reproducible.

#### Acceptance Criteria

1. THE project SHALL include requirements.txt with all dependencies
2. THE requirements.txt SHALL pin major and minor versions for stability
3. THE requirements.txt SHALL include: fastapi, uvicorn, pydantic, sentence-transformers, faiss-cpu, pandas, beautifulsoup4, requests, groq, python-dotenv, pytest, httpx
4. THE requirements.txt SHALL specify compatible versions that work together

### Requirement 23: Evaluation Metrics

**User Story:** As a system evaluator, I want quantitative metrics, so that I can assess system quality objectively.

#### Acceptance Criteria

1. THE project SHALL include utilities to calculate Recall@10 for retrieval quality
2. THE project SHALL include utilities to calculate Precision@10 for retrieval quality
3. THE project SHALL include utilities to measure groundedness (percentage of recommendations present in retrieved evidence)
4. THE project SHALL include utilities to validate schema compliance across responses
5. THE project SHALL include utilities to measure average conversation turns to completion
6. THE project SHALL include utilities to measure refusal correctness on off-topic queries

### Requirement 24: CORS Configuration

**User Story:** As a frontend developer, I want CORS enabled, so that I can call the API from web applications.

#### Acceptance Criteria

1. THE API SHALL enable CORS middleware
2. THE API SHALL allow all origins for development and testing
3. THE API SHALL allow POST and GET methods
4. THE API SHALL allow standard headers including Content-Type and Authorization

### Requirement 25: Logging and Observability

**User Story:** As a system operator, I want structured logging, so that I can monitor and debug production issues.

#### Acceptance Criteria

1. THE API SHALL log all incoming requests with timestamp and endpoint
2. THE API SHALL log retrieval results with query and number of candidates
3. THE API SHALL log LLM generation with token counts
4. THE API SHALL log errors with full stack traces
5. THE API SHALL use structured logging format for machine parsing
6. THE API SHALL not log sensitive information like API keys

