# EquipmentIQ Render Deployment Guide

This guide covers deploying both EquipmentIQ Streamlit apps to Render.

## Overview

Two separate services:
1. **equipmentiq-main** — Query interface (ui/app.py)
2. **equipmentiq-eval** — Evaluation dashboard (ui/eval_dashboard.py)

## Prerequisites

- Render account (https://render.com)
- GitHub repository with EquipmentIQ code
- API keys:
  - `ANTHROPIC_API_KEY` (Claude LLM)
  - `OPENAI_API_KEY` (text-embedding-3-small)
  - `LANGCHAIN_API_KEY` (LangSmith tracing)

## Deployment Steps

### 1. Push Code to GitHub

Ensure all files are committed and pushed:
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

Required files in repo:
- `render.yaml` — Infrastructure-as-code definition
- `requirements.txt` — Python dependencies
- `runtime.txt` — Python version
- `.env.example` — Environment variable documentation
- `ui/app.py` — Main dashboard
- `ui/eval_dashboard.py` — Evaluation dashboard
- `config.yaml` — Configuration (will be read at runtime)
- All source modules (`agents/`, `orchestrator/`, `ingestion/`, `evaluation/`, `feedback/`, `prompts/`)

### 2. Create Render Account & Dashboard

1. Sign up at https://render.com
2. Connect your GitHub repository
3. Go to Dashboard → Create → Web Service

### 3. Deploy via render.yaml (Recommended)

**Option A: Using Render Dashboard UI**

1. Go to Render Dashboard
2. Click **New +** → **Web Service**
3. Select your GitHub repository
4. In the "Create Web Service" form:
   - **Name**: `equipmentiq-main`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0`
5. Add environment variables (marked as "Secret" for API keys):
   - `ANTHROPIC_API_KEY` (secret)
   - `OPENAI_API_KEY` (secret)
   - `LANGCHAIN_API_KEY` (secret)
   - `LANGCHAIN_TRACING_V2=true`
   - `LANGCHAIN_PROJECT=equipmentiq`
   - `STREAMLIT_SERVER_HEADLESS=true`
   - `STREAMLIT_SERVER_FILEWATCHERTYPE=none`
6. Click **Deploy Web Service**

**Repeat for Evaluation Dashboard:**
1. New Web Service
2. Name: `equipmentiq-eval`
3. Same commands but using `ui/eval_dashboard.py`

**Option B: Using render.yaml (Infrastructure as Code)**

1. Go to Render Dashboard → **Settings** → **Connect Repository**
2. Click **Create from render.yaml**
3. Select your branch and repository
4. Render will automatically create both services defined in `render.yaml`

### 4. Configure Environment Variables

In Render Dashboard:
1. Go to each service (equipmentiq-main, equipmentiq-eval)
2. Click **Environment**
3. Add the required secrets:

| Variable | Type | Value |
|----------|------|-------|
| `ANTHROPIC_API_KEY` | Secret | Your Anthropic API key |
| `OPENAI_API_KEY` | Secret | Your OpenAI API key |
| `LANGCHAIN_API_KEY` | Secret | Your LangSmith API key |
| `LANGCHAIN_TRACING_V2` | Published | `true` |
| `LANGCHAIN_PROJECT` | Published | `equipmentiq` |
| `STREAMLIT_SERVER_HEADLESS` | Published | `true` |
| `STREAMLIT_SERVER_FILEWATCHERTYPE` | Published | `none` |
| `PYTHONUNBUFFERED` | Published | `1` |

### 5. Verify Deployment

After deployment:

1. **Main App** (Query Interface)
   - URL: `https://equipmentiq-main.onrender.com`
   - Test: Submit a sample query (e.g., "What is SPN-CR-001?")
   - Expected: Answer with citations and routing display

2. **Eval Dashboard** (Metrics)
   - URL: `https://equipmentiq-eval.onrender.com`
   - Test: View metrics and recent feedback
   - Expected: Metrics display with all collected data

### 6. Monitor Logs

In Render Dashboard:
1. Select service (equipmentiq-main or equipmentiq-eval)
2. Click **Logs** to view real-time output
3. Check for errors (API key issues, module import failures)
4. Look for successful startup: `"You can now view your Streamlit app in your browser"`

## Troubleshooting

### Issue: Import Errors on Startup

**Error**: `ModuleNotFoundError: No module named 'orchestrator'`

**Solution**: Ensure `sys.path` includes parent directory
- Check `ui/app.py` and `ui/eval_dashboard.py` have:
  ```python
  import sys
  from pathlib import Path
  parent_dir = str(Path(__file__).parent.parent)
  if parent_dir not in sys.path:
      sys.path.insert(0, parent_dir)
  ```

### Issue: API Key Not Found

**Error**: `AuthenticationError: No API key provided`

**Solution**:
1. Verify environment variable is set in Render Dashboard
2. Check variable name matches exactly (case-sensitive)
3. Ensure "Secret" variables are not set as "Published"
4. Restart service after adding keys

### Issue: Streamlit Connection Timeout

**Error**: `StreamlitAPIException: Connection timeout`

**Solution**:
1. Set `STREAMLIT_SERVER_HEADLESS=true`
2. Set `STREAMLIT_SERVER_FILEWATCHERTYPE=none`
3. Disable CSRF protection: `--server.enableXsrfProtection=false`

### Issue: Database Not Found

**Error**: `No such file or directory: 'chroma_db'`

**Solution**:
- ChromaDB collections are rebuilt on first startup (collections auto-initialize)
- First app load will take ~30-60 seconds as data ingests
- Check logs for "Ingesting..." messages
- Service will be available once ingestion completes

### Issue: Slow Startup (>1 minute)

**Expected behavior on Render free tier:**
- Cold starts: 1-2 minutes (Python environment setup + dependencies)
- Collections auto-initialized on first startup: +30-60 seconds
- Warm restarts: ~10 seconds

### Issue: Service Keeps Crashing

**Check:**
1. **Logs** for actual error messages
2. **Memory usage** (free tier = 512 MB RAM; embeddings + ChromaDB ~300 MB)
3. **Disk space** (data/error_docs/ = ~3 MB; chroma_db/ grows to ~50 MB)
4. Consider upgrading to **Starter plan** (2 GB RAM) for production

## Scaling Considerations

### For Production

1. **Upgrade from Free Tier**
   - Free: Auto-spins down after 15 min inactivity
   - Starter: Always on, 2 GB RAM, better for concurrent users
   - Standard: 4 GB RAM, recommended for heavy load

2. **Database Persistence**
   - Current: ChromaDB in-memory (rebuilt on startup)
   - Recommended: Use Render PostgreSQL add-on for persistent feedback.db
   - Update `feedback/feedback_store.py` to use PostgreSQL connection string

3. **Caching Strategy**
   - Add Redis for embedding cache (reduces OpenAI API calls)
   - Cache intent classification results (5 min TTL)
   - Cache retrieval results (10 min TTL)

4. **Monitoring**
   - LangSmith tracing (already configured) provides full visibility
   - Set up alerts in Render for high memory/CPU
   - Monitor API quota usage (Anthropic, OpenAI)

## Cost Estimation

### Current Setup (Free Tier)

| Component | Cost |
|-----------|------|
| equipmentiq-main (web service) | $0 (auto-sleeps) |
| equipmentiq-eval (web service) | $0 (auto-sleeps) |
| Storage (code + chroma_db) | $0 (included) |
| **Total** | **~$0/month** |

### Recommended Upgrade (Starter Plan)

| Component | Cost/Month |
|-----------|-----------|
| equipmentiq-main (Starter web) | $7 |
| equipmentiq-eval (Starter web) | $7 |
| PostgreSQL add-on (feedback store) | $15 |
| **Total** | **~$29/month** |

## Post-Deployment Checklist

- [ ] Both services are showing "Live" in Render Dashboard
- [ ] Main app loads at `https://equipmentiq-main.onrender.com`
- [ ] Eval dashboard loads at `https://equipmentiq-eval.onrender.com`
- [ ] Sample query returns answer with citations
- [ ] LangSmith tracing shows logged queries
- [ ] No errors in service logs for 5+ minutes
- [ ] API keys are set as "Secret" (not visible in logs)
- [ ] Redis/PostgreSQL add-ons configured (if using Starter+)

## Rollback

If deployment fails:
1. Render Dashboard → Service → **Settings** → **Suspend**
2. Fix code locally and push to GitHub
3. Render will auto-redeploy on push (if auto-deploy enabled)
4. Or manually click **Redeploy** button in Dashboard

## Support

For Render-specific issues:
- Render Docs: https://render.com/docs
- Status: https://status.render.com

For EquipmentIQ issues:
- Check `CLAUDE.md` for architecture overview
- Review logs for specific error messages
- Ensure all API keys are valid and quota available
