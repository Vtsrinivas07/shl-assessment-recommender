# Troubleshooting Guide

## Common Issues and Solutions

### 1. Torch/Transformers Compatibility Error

**Error:**
```
AttributeError: module 'torch.utils._pytree' has no attribute 'register_pytree_node'
```

**Solution:**
The torch version is incompatible. Reinstall with the correct version:

```powershell
pip uninstall torch -y
pip install torch==2.2.0
```

Or run the full reinstall:
```powershell
pip install -r requirements.txt --force-reinstall
```

### 2. Dependency Conflicts

**Error:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages...
```

**Solution:**
These warnings are usually safe to ignore if the core packages (fastapi, torch, sentence-transformers) work. If you want a clean environment:

```powershell
# Create a new virtual environment
python -m venv venv_clean
venv_clean\Scripts\activate
pip install -r requirements.txt
```

### 3. GROQ_API_KEY Missing

**Error:**
```
ValueError: GROQ_API_KEY is required
```

**Solution:**
1. Get a free API key from https://console.groq.com/
2. Edit `.env` file and add:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

### 4. FAISS Index Not Found

**Error:**
```
FileNotFoundError: FAISS index not found at data/faiss.index
```

**Solution:**
Build the index from the sample data:

```powershell
python -m app.index_builder
```

If you want to scrape fresh data:
```powershell
python -m app.scraper
python -m app.index_builder
```

### 5. Scraper Timeout/Interruption

**Error:**
```
KeyboardInterrupt or timeout during scraping
```

**Solution:**
The scraper was interrupted. You have two options:

**Option A: Use sample data (fastest)**
```powershell
# Sample data is already in data/shl_catalog.csv
python -m app.index_builder
```

**Option B: Re-run scraper**
```powershell
python -m app.scraper
```

### 6. PowerShell curl Issues

**Error:**
```
A parameter cannot be found that matches parameter name 'X'
```

**Solution:**
PowerShell's `curl` is an alias for `Invoke-WebRequest` which has different syntax. Use:

```powershell
# Health check
Invoke-RestMethod -Uri http://localhost:8000/health

# Chat request
$body = @{
    messages = @(
        @{
            role = "user"
            content = "I need to hire a Java developer"
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri http://localhost:8000/chat -Method Post -Body $body -ContentType "application/json"
```

Or use the provided test script:
```powershell
.\test_api.ps1
```

### 7. Port Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
Another process is using port 8000. Either:

**Option A: Kill the process**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Option B: Use a different port**
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 8. Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**
Make sure you're running from the project root directory:

```powershell
cd D:\SHL
python run.py
```

### 9. Slow First Request

**Issue:**
First API request takes 10-20 seconds.

**Explanation:**
This is normal! The first request loads:
- FAISS index (2-3 seconds)
- Sentence transformer model (5-10 seconds)
- LLM connection (1-2 seconds)

Subsequent requests are much faster (2-5 seconds).

### 10. Empty Recommendations

**Issue:**
API returns empty recommendations array.

**Possible Causes:**

1. **Clarification needed** - Query is too vague
   - Solution: Provide more specific details

2. **Off-topic request** - Query is not about assessments
   - Solution: Ask about hiring/assessment needs

3. **No matching assessments** - Very specific constraints
   - Solution: Broaden the search criteria

### 11. BeautifulSoup Deprecation Warnings

**Warning:**
```
DeprecationWarning: The 'text' argument to find()-type methods is deprecated
```

**Solution:**
These warnings are harmless and have been fixed in the latest code. If you still see them, update the scraper:

The code now uses `string=` instead of `text=` parameter.

## Quick Fixes

### Complete Reset

If nothing works, try a complete reset:

```powershell
# 1. Clean up
Remove-Item -Recurse -Force venv, data\*.index, data\*.pkl

# 2. Fresh install
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. Setup
Copy-Item .env.example .env
# Edit .env and add GROQ_API_KEY

# 4. Build index
python -m app.index_builder

# 5. Run
python run.py
```

### Verify Installation

Check that everything is installed correctly:

```powershell
# Check Python version (should be 3.11+)
python --version

# Check key packages
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import torch; print('Torch:', torch.__version__)"
python -c "import sentence_transformers; print('Sentence Transformers: OK')"
python -c "import faiss; print('FAISS: OK')"
python -c "import groq; print('Groq: OK')"
```

## Getting Help

If you're still stuck:

1. **Check the logs** - Look for error messages in the console
2. **Verify environment** - Make sure `.env` has GROQ_API_KEY
3. **Check data files** - Ensure `data/shl_catalog.csv` exists
4. **Test components** - Run individual modules to isolate the issue

### Test Individual Components

```powershell
# Test index builder
python -m app.index_builder

# Test retriever
python -c "from app.retriever import SemanticRetriever; r = SemanticRetriever(); print('Retriever OK')"

# Test LLM client (requires GROQ_API_KEY)
python -c "from app.llm_client import LLMClient; c = LLMClient(); print('LLM Client OK')"
```

## Performance Tips

1. **Use sample data** - Faster than scraping (already provided)
2. **Keep index loaded** - Don't restart the server unnecessarily
3. **Use lower k** - Set `RETRIEVAL_K=10` in `.env` for faster retrieval
4. **Monitor memory** - FAISS index uses ~500MB RAM

## Windows-Specific Issues

### Long Path Names

If you get path-too-long errors:

```powershell
# Enable long paths in Windows
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Execution Policy

If scripts won't run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Still Having Issues?

1. Check README.md for setup instructions
2. Review docs/approach.md for technical details
3. Look at the code comments for implementation details
4. Ensure all prerequisites are met (Python 3.11+, Groq API key)
