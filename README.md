# SHL Assessment Recommender

A stateless conversational recommendation API that helps hiring managers find relevant SHL Individual Test Solutions from the SHL product catalog using natural language queries.

## Features

- 🤖 **Conversational AI**: Natural language interaction powered by Groq's Llama 3.3 70B
- 🔍 **Semantic Search**: FAISS-based vector search with sentence transformers
- 🎯 **Hybrid Ranking**: Combines semantic similarity with keyword matching
- 🛡️ **Security**: Prompt injection resistance and URL validation
- 📊 **Grounded Responses**: All recommendations backed by catalog evidence
- ⚡ **Fast**: Sub-30 second response times
- 🔄 **Stateless**: No server-side session management

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /chat
       ▼
┌─────────────────────────────────────┐
│         FastAPI Application         │
├─────────────────────────────────────┤
│  ┌──────────────────────────────┐  │
│  │   Conversational Agent       │  │
│  │  - Intent Detection          │  │
│  │  - Clarification Logic       │  │
│  │  - Recommendation Flow       │  │
│  └────┬──────────────────┬──────┘  │
│       │                  │          │
│  ┌────▼────────┐   ┌────▼──────┐  │
│  │  Retriever  │   │ LLM Client│  │
│  │   (FAISS)   │   │  (Groq)   │  │
│  └─────────────┘   └───────────┘  │
└─────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- Groq API key ([Get one here](https://console.groq.com/))

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd shl-assessment-recommender
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_api_key_here
```

## Data Pipeline Setup

Before running the API, you need to scrape the SHL catalog and build the search index.

### Step 1: Scrape the Catalog

```bash
python -m app.scraper
```

This will:
- Scrape https://www.shl.com/solutions/products/product-catalog/
- Extract assessment details (name, URL, description, test type, etc.)
- Save results to `data/shl_catalog.csv`
- Handle pagination and retries automatically

### Step 2: Build the Search Index

```bash
python -m app.index_builder
```

This will:
- Load the catalog CSV
- Generate embeddings using sentence-transformers
- Create a FAISS index for semantic search
- Save index to `data/faiss.index` and metadata to `data/metadata.pkl`

## Running the API

### Local Development

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the run script
python run.py
```

The API will be available at `http://localhost:8000`

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok"
}
```

### Chat Endpoint

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "I need to hire a senior Java developer"
      }
    ]
  }'
```

Response:
```json
{
  "reply": "Based on your need for a senior Java developer, here are 5 relevant assessments...",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/solutions/products/java-8/",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

### Multi-Turn Conversation

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "I need to hire a developer"
      },
      {
        "role": "assistant",
        "content": "What programming language or technology stack are you looking for?"
      },
      {
        "role": "user",
        "content": "Python, mid-level"
      }
    ]
  }'
```

## Request Schema

### ChatRequest

```json
{
  "messages": [
    {
      "role": "user" | "assistant",
      "content": "string (non-empty)"
    }
  ]
}
```

**Validation Rules:**
- Messages array must not be empty
- Roles must alternate between "user" and "assistant"
- Last message must be from "user"
- Content must not be empty

### ChatResponse

```json
{
  "reply": "string",
  "recommendations": [
    {
      "name": "string",
      "url": "string (shl.com domain)",
      "test_type": "K" | "A" | "P" | "B"
    }
  ],
  "end_of_conversation": boolean
}
```

**Test Types:**
- `K` = Knowledge Test
- `A` = Ability Test
- `P` = Personality Test
- `B` = Behavioral Test

**Recommendations:**
- Empty array when clarifying or refusing
- 1-10 items when recommending

## Conversation Flows

### 1. Clarification Flow

When the query is vague:

```
User: "I need a test"
Assistant: "What type of role are you hiring for?"
User: "Software engineer"
Assistant: [provides recommendations]
```

### 2. Recommendation Flow

When the query is specific:

```
User: "I need to assess a senior Python developer"
Assistant: [provides 5-10 relevant assessments]
```

### 3. Refinement Flow

When adding constraints:

```
User: "Show me shorter assessments"
Assistant: [provides filtered recommendations]
```

### 4. Comparison Flow

When comparing assessments:

```
User: "Compare Java 8 and Python 3"
Assistant: [provides detailed comparison]
```

### 5. Refusal Flow

When request is off-topic:

```
User: "What's the weather?"
Assistant: "I can only help with SHL assessment recommendations..."
```

## Docker Deployment

### Build Image

```bash
docker build -t shl-recommender .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_api_key \
  -v $(pwd)/data:/app/data \
  shl-recommender
```

## Render Deployment

### Prerequisites

1. Push code to GitHub
2. Create Render account
3. Add `GROQ_API_KEY` to Render environment variables

### Deploy

1. Connect your GitHub repository to Render
2. Render will automatically detect `render.yaml`
3. Set environment variables in Render dashboard
4. Deploy!

The `render.yaml` configuration handles:
- Web service setup
- Build commands
- Start command
- Health check endpoint

## Configuration

Environment variables (`.env` file):

```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional (with defaults)
MODEL_NAME=llama-3.3-70b-versatile
TEMPERATURE=0.1
RETRIEVAL_K=20
```

## Project Structure

```
shl-assessment-recommender/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── schemas.py           # Pydantic models
│   ├── config.py            # Configuration management
│   ├── prompts.py           # Prompt templates
│   ├── scraper.py           # Catalog scraper
│   ├── index_builder.py     # FAISS index builder
│   ├── retriever.py         # Semantic retriever
│   ├── llm_client.py        # Groq API wrapper
│   └── agent.py             # Conversational agent
├── data/
│   ├── shl_catalog.csv      # Scraped catalog (generated)
│   ├── faiss.index          # FAISS index (generated)
│   └── metadata.pkl         # Metadata store (generated)
├── tests/
│   └── test_api.py          # API tests
├── docs/
│   └── approach.md          # Technical documentation
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── render.yaml              # Render deployment config
├── README.md                # This file
└── run.py                   # Development server script
```

## Troubleshooting

### "FAISS index not found"

Run the data pipeline:
```bash
python -m app.scraper
python -m app.index_builder
```

### "GROQ_API_KEY is required"

Add your API key to `.env`:
```bash
GROQ_API_KEY=your_actual_api_key
```

### "No assessments found"

The scraper may have failed. Check:
1. Internet connection
2. SHL website availability
3. Scraper logs for errors

Re-run the scraper:
```bash
python -m app.scraper
```

### Slow Response Times

- Check Groq API status
- Reduce `RETRIEVAL_K` in config
- Ensure FAISS index is properly loaded

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## Performance

- **Response Time**: < 30 seconds (typically 2-5 seconds)
- **Conversation Length**: Typically completes in 3-8 turns
- **Retrieval**: Top-20 candidates retrieved in < 100ms
- **LLM Generation**: 750+ tokens/second with Groq

## Security

- ✅ Prompt injection resistance
- ✅ URL validation (shl.com only)
- ✅ Input validation with Pydantic
- ✅ No code execution from user input
- ✅ CORS configured for production
- ✅ No sensitive data logging

## License

This project is created for the SHL AI Intern take-home assignment.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs for error details
3. Ensure all setup steps were completed
4. Verify environment variables are set correctly

## Acknowledgments

- **SHL** for the product catalog
- **Groq** for fast LLM inference
- **Sentence Transformers** for embeddings
- **FAISS** for efficient similarity search
