# Vercel Deployment Guide

This guide covers deploying both frontend and backend to Vercel.

## Prerequisites

- GitHub account
- Vercel account (sign up at https://vercel.com)
- Supabase account (for PostgreSQL database)
- Google Cloud Project (for Gemini API and TTS)
- Stripe Account (for payments)

## Step 1: Prepare Backend for Vercel

### Create Vercel Serverless API

Create `backend/api/index.py`:

```python
from server import app

# Vercel serverless function handler
handler = app
```

### Update Backend Structure

The backend will run as Vercel Serverless Functions. Update `vercel.json` in the root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    },
    {
      "src": "backend/api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ],
  "env": {
    "GEMINI_API_KEY": "@gemini_api_key",
    "STRIPE_SECRET_KEY": "@stripe_secret_key",
    "DATABASE_URL": "@database_url"
  }
}
```

### Create `backend/requirements.txt` (already exists)

Ensure all dependencies are listed.

### Create `backend/vercel.json`

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

## Step 2: Setup Supabase Database

1. Go to https://supabase.com
2. Create a new project
3. Go to **Settings** → **Database**
4. Copy the **Connection String** (URI format)
5. It will look like: `postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres`

## Step 3: Deploy to Vercel

### Option A: Using Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from root directory
cd /Users/waleedjawaid/Documents/Agentic
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? gemini-agent (or your choice)
# - Directory? ./
# - Override settings? No
```

### Option B: Using Vercel Dashboard

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `./`
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`

## Step 4: Configure Environment Variables

In Vercel Dashboard → Settings → Environment Variables, add:

### Backend Variables

| Variable | Value | Type |
|----------|-------|------|
| `DATABASE_URL` | Your Supabase connection string | Secret |
| `GEMINI_API_KEY` | Your Google Gemini API key | Secret |
| `STRIPE_SECRET_KEY` | Your Stripe secret key | Secret |
| `STRIPE_WEBHOOK_SECRET` | Your Stripe webhook secret | Secret |
| `REDIS_URL` | Optional: Redis connection string | Secret |

### Frontend Variables

| Variable | Value | Type |
|----------|-------|------|
| `VITE_API_BASE_URL` | Your Vercel backend URL | Plain Text |

Example: `https://your-project.vercel.app/api`

## Step 5: Update Frontend Config

Update `frontend/src/config.js`:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                     'https://your-project.vercel.app/api';

export const API_URL = API_BASE_URL;
export default API_URL;
```

## Step 6: Database Migration

After deployment, run migrations:

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres"

# Run the schema
\i backend/schema.sql

# Or copy-paste the SQL from schema.sql
```

## Step 7: Verify Deployment

1. Visit your Vercel URL: `https://your-project.vercel.app`
2. Test chat functionality
3. Check browser console for errors
4. Test different agents
5. Try Voice Mode

## Troubleshooting

### Build Fails

**Issue**: Python dependencies fail to install

**Solution**: Ensure `backend/requirements.txt` is correct and uses compatible versions:
```
fastapi
uvicorn
google-generativeai
python-dotenv
pydantic
sqlalchemy
psycopg2-binary
python-multipart
stripe
```

### Database Connection Error

**Issue**: Cannot connect to Supabase

**Solution**: 
1. Check `DATABASE_URL` format
2. Ensure Supabase project is active
3. Check IP allowlist in Supabase (allow all: `0.0.0.0/0`)

### API Routes Not Working

**Issue**: `/api/*` routes return 404

**Solution**: 
1. Check `vercel.json` routes configuration
2. Ensure `backend/api/index.py` exists
3. Redeploy with `vercel --prod`

### CORS Errors

**Issue**: Frontend can't call backend API

**Solution**: Backend already has CORS configured in `server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

For production, update to:
```python
allow_origins=["https://your-project.vercel.app"]
```

## Alternative: Separate Deployments

If you prefer to deploy frontend and backend separately:

### Frontend Only (Vercel)

```bash
cd frontend
vercel

# Set environment variable:
# VITE_API_BASE_URL=https://your-backend.vercel.app
```

### Backend Only (Vercel)

```bash
cd backend
vercel

# Set all backend environment variables
```

Then update frontend config to point to backend URL.

## Production Checklist

- [ ] Database migrated to Supabase
- [ ] All environment variables set in Vercel
- [ ] CORS configured for production domain
- [ ] Stripe webhook configured
- [ ] Google Cloud TTS credentials configured
- [ ] Test all features in production
- [ ] Monitor Vercel logs for errors
- [ ] Set up custom domain (optional)

## Monitoring

### Vercel Logs

```bash
# View real-time logs
vercel logs your-project.vercel.app

# Or check in Vercel Dashboard → Deployments → Logs
```

### Database Monitoring

Use Supabase Dashboard to monitor:
- Active connections
- Query performance
- Database size

## Updating Deployment

```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push

# Vercel will auto-deploy on push
# Or manually deploy:
vercel --prod
```

## Custom Domain (Optional)

1. Go to Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update CORS and environment variables

---

**Quick Deploy Command**:
```bash
cd /Users/waleedjawaid/Documents/Agentic
vercel --prod
```

Your app will be live at: `https://your-project.vercel.app` 🚀
