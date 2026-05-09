# Quick Deployment Guide for Render

## Step 1: Prepare Git Repository

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Complete SHL Assessment Recommender implementation"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., "shl-assessment-recommender")
3. **Do NOT initialize with README** (you already have one)
4. Copy the repository URL

## Step 3: Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/shl-assessment-recommender.git

# Push
git branch -M main
git push -u origin main
```

## Step 4: Deploy to Render

1. Go to https://render.com/
2. Sign up or log in (can use GitHub account)
3. Click **"New +"** → **"Web Service"**
4. Click **"Connect a repository"**
5. Authorize Render to access your GitHub
6. Select your `shl-assessment-recommender` repository
7. Render will auto-detect `render.yaml` configuration

## Step 5: Configure Environment Variables

In the Render dashboard:
1. Scroll to **"Environment Variables"**
2. Add your variable:
   - **Key**: `GROQ_API_KEY`
   - **Value**: `your_actual_groq_api_key`
3. The other variables are already set in `render.yaml`

## Step 6: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
   - Render will install dependencies
   - Run the scraper
   - Build the FAISS index
   - Start the API
3. Once deployed, you'll get a URL like: `https://shl-assessment-recommender.onrender.com`

## Step 7: Test Your Deployment

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Chat test
curl -X POST https://your-app-name.onrender.com/chat \
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

## Step 8: Get Your Public URLs

Your submission URLs will be:
- **Health Check**: `https://your-app-name.onrender.com/health`
- **Chat Endpoint**: `https://your-app-name.onrender.com/chat`
- **API Docs**: `https://your-app-name.onrender.com/docs`

## Troubleshooting

### Build Fails

**Issue**: Scraper or index builder fails during build

**Solution**: 
- Check Render build logs
- Ensure `data/` directory is created
- May need to add sample data instead of scraping during build

### API Returns 500 Error

**Issue**: GROQ_API_KEY not set correctly

**Solution**:
- Go to Render dashboard → Environment Variables
- Verify `GROQ_API_KEY` is set
- Click "Manual Deploy" to redeploy

### Cold Start is Slow

**Issue**: First request after inactivity takes 30-60 seconds

**Solution**: This is expected on Render's free tier. Mention this in your submission.

## Alternative: Deploy with Sample Data

If scraping during build is unreliable, you can use the sample data you already have:

1. Ensure `data/shl_catalog.csv`, `data/faiss.index`, and `data/metadata.pkl` exist
2. Commit them to git:
   ```bash
   git add data/
   git commit -m "Add pre-built index for deployment"
   git push
   ```
3. Update `render.yaml` to skip scraping:
   ```yaml
   buildCommand: pip install -r requirements.txt
   ```
4. Redeploy on Render

## Cost

Render's free tier includes:
- ✅ 750 hours/month (enough for this assignment)
- ✅ Automatic HTTPS
- ✅ Custom domains
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ 512 MB RAM (should be sufficient)

## Next Steps

Once deployed:
1. ✅ Test both endpoints
2. ✅ Copy the public URL
3. ✅ Use it in your submission form
4. ✅ Mention cold-start behavior in submission
