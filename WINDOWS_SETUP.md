# Windows Setup Guide

Quick setup guide for Windows users.

## Prerequisites

- Python 3.11+ ([Download](https://www.python.org/downloads/))
- Groq API key ([Get free key](https://console.groq.com/))

## Quick Setup (5 minutes)

### Option 1: Automated Setup (Recommended)

```powershell
# Run the setup script
.\setup.ps1
```

This will:
1. Check Python version
2. Install all dependencies
3. Create .env file
4. Build the search index

Then:
1. Edit `.env` and add your `GROQ_API_KEY`
2. Run: `python run.py`

### Option 2: Manual Setup

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
Copy-Item .env.example .env
# Edit .env and add your GROQ_API_KEY

# 3. Build index (uses sample data)
python -m app.index_builder

# 4. Run the API
python run.py
```

## Testing the API

### Option 1: Use Test Script (Recommended)

```powershell
# Make sure API is running first (python run.py)
# Then in another terminal:
.\test_api.ps1
```

### Option 2: Manual Testing

```powershell
# Health check
Invoke-RestMethod -Uri http://localhost:8000/health

# Chat request
$body = @{
    messages = @(
        @{
            role = "user"
            content = "I need to hire a senior Java developer"
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri http://localhost:8000/chat -Method Post -Body $body -ContentType "application/json"
```

### Option 3: Browser

Open http://localhost:8000/docs for interactive API documentation.

## Common Windows Issues

### Issue: "pip is not recognized"

**Solution:**
```powershell
python -m pip install -r requirements.txt
```

### Issue: "Scripts cannot be executed"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: PowerShell curl doesn't work

**Solution:**
PowerShell's `curl` is different. Use `Invoke-RestMethod` instead (see examples above) or use the test script.

### Issue: Torch compatibility error

**Solution:**
```powershell
pip uninstall torch -y
pip install torch==2.2.0
```

## Project Structure

```
D:\SHL\
├── app\              # Application code
├── data\             # Data files (CSV, index)
├── tests\            # Test files
├── docs\             # Documentation
├── .env              # Your configuration (add GROQ_API_KEY here)
├── run.py            # Start the API
├── setup.ps1         # Setup script
└── test_api.ps1      # Test script
```

## Next Steps

1. **Add your API key** to `.env`
2. **Run the API**: `python run.py`
3. **Test it**: `.\test_api.ps1`
4. **Read the docs**: See README.md for full documentation

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions to common issues.

## Quick Commands Reference

```powershell
# Start API
python run.py

# Run tests
.\test_api.ps1

# Build index
python -m app.index_builder

# Scrape fresh data (optional)
python -m app.scraper

# Run pytest
pytest tests\ -v

# Check health
Invoke-RestMethod http://localhost:8000/health
```

## Getting Help

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [README.md](README.md)
3. Look at [docs/approach.md](docs/approach.md)

## Sample Data

The project includes sample data in `data/shl_catalog.csv` with 20 assessments. This is enough to test the API without scraping.

To use fresh data from the SHL website:
```powershell
python -m app.scraper
python -m app.index_builder
```

## Performance Notes

- **First request**: 10-20 seconds (loading models)
- **Subsequent requests**: 2-5 seconds
- **Memory usage**: ~1GB RAM
- **Disk space**: ~500MB (models + dependencies)

Happy coding! 🚀
