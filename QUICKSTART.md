# Quick Start Guide

Get the SHL Assessment Recommender running in 5 minutes!

## Prerequisites

- Python 3.11+
- Groq API key ([Get one free here](https://console.groq.com/))

## Step 1: Install (2 minutes)

```bash
# Clone and navigate
cd shl-assessment-recommender

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure (30 seconds)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_api_key_here
```

## Step 3: Prepare Data (2 minutes)

```bash
# Scrape the SHL catalog
python -m app.scraper

# Build the search index
python -m app.index_builder
```

## Step 4: Run (30 seconds)

```bash
# Start the API
python run.py
```

The API is now running at `http://localhost:8000`

## Step 5: Test

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Request
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"I need to hire a senior Java developer\"}]}"
```

### Interactive Documentation
Open your browser: http://localhost:8000/docs

## What's Next?

- Read [README.md](README.md) for detailed documentation
- Read [docs/approach.md](docs/approach.md) for technical details
- Run tests: `pytest tests/ -v`
- Deploy to Render (see README.md)

## Troubleshooting

**"FAISS index not found"**
→ Run: `python -m app.scraper` then `python -m app.index_builder`

**"GROQ_API_KEY is required"**
→ Add your API key to the `.env` file

**Slow responses**
→ Normal for first request (model loading). Subsequent requests are faster.

## Example Conversation

```bash
# First message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"I need a developer"}]}'

# Response: "What programming language or technology stack are you looking for?"

# Second message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[
    {"role":"user","content":"I need a developer"},
    {"role":"assistant","content":"What programming language or technology stack are you looking for?"},
    {"role":"user","content":"Python, mid-level"}
  ]}'

# Response: [5-10 Python assessment recommendations]
```

## Project Structure

```
shl-assessment-recommender/
├── app/                 # Application code
├── data/                # Generated data files
├── tests/               # Test files
├── docs/                # Documentation
├── scripts/             # Helper scripts
├── requirements.txt     # Dependencies
├── .env                 # Your configuration
└── run.py              # Start script
```

## Key Files

- `app/main.py` - FastAPI application
- `app/agent.py` - Conversational logic
- `app/retriever.py` - Semantic search
- `app/scraper.py` - Catalog scraper
- `app/index_builder.py` - Index builder

## Support

For detailed information, see:
- [README.md](README.md) - Complete documentation
- [docs/approach.md](docs/approach.md) - Technical approach
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview

Happy coding! 🚀
