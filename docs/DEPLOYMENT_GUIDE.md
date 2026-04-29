# How to Deploy Abstract Enclave Assessment Live on the Web

This guide covers **3 options** from easiest to most powerful. Pick the one that fits your needs.

---

## Option A: Vercel (Frontend) + Render (Backend) — ⭐ Recommended, 100% Free

This is the **easiest** approach. Both platforms have generous free tiers. No credit card required.

### Step 1: Push Code to GitHub

```bash
# From d:\het\SELF\RP\FINAL
git init
git add .
git commit -m "Initial commit: Abstract Enclave Assessment"

# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/abstract-enclave.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy Backend on Render (Free)

1. Go to [render.com](https://render.com) → Sign up with GitHub
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `enclave-api` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn src.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

5. Add **Environment Variables** (click "Environment" tab):

| Key | Value |
|-----|-------|
| `GOOGLE_API_KEY` | *(your Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com/apikey))* |
| `CORS_ORIGINS` | `https://YOUR-APP.vercel.app` *(fill after Step 3)* |

6. Click **"Create Web Service"** → Wait 2–3 minutes for deploy
7. Copy your backend URL: `https://enclave-api.onrender.com`

---

### Step 3: Deploy Frontend on Vercel (Free)

1. Go to [vercel.com](https://vercel.com) → Sign up with GitHub
2. Click **"Add New Project"** → Import your GitHub repo
3. Configure:

| Setting | Value |
|---------|-------|
| **Framework Preset** | `Next.js` (auto-detected) |
| **Root Directory** | `frontend` |

4. Add **Environment Variable** (expand "Environment Variables"):

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://enclave-api.onrender.com` *(your Render URL from Step 2)* |

5. Click **"Deploy"** → Wait 1–2 minutes
6. Your app is live at: `https://your-project.vercel.app` 🎉

---

### Step 4: Update CORS on Render

Go back to Render → your `enclave-api` service → Environment → update:

| Key | Value |
|-----|-------|
| `CORS_ORIGINS` | `https://your-project.vercel.app` |

Click **"Save Changes"** → Render auto-redeploys.

---

### Step 5: Get a Gemini API Key (Free)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key
4. Paste it as `GOOGLE_API_KEY` in Render environment variables

> Without this key, the AI companion will use rule-based fallback responses (still works, just less dynamic).

---

### ✅ You're Live!

| Component | URL |
|-----------|-----|
| Frontend | `https://your-project.vercel.app` |
| Backend | `https://enclave-api.onrender.com` |
| Health Check | `https://enclave-api.onrender.com/api/v1/external/health` |
| API Docs | `https://enclave-api.onrender.com/docs` |

> **Note**: Render free tier sleeps after 15 min of inactivity. First request after sleep takes ~30s. This is normal.

---
---

## Option B: Railway — Single Platform (Free Trial, then $5/mo)

Railway deploys both frontend and backend from one dashboard.

### Step 1: Push to GitHub (same as Option A Step 1)

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app) → Sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub Repo"**
3. Select your repo

#### Deploy Backend:
4. Click **"Add a Service"** → **"GitHub Repo"** → select same repo
5. Configure:

| Setting | Value |
|---------|-------|
| **Root Directory** | `/backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn src.main:app --host 0.0.0.0 --port $PORT` |

6. Add Variables: `GOOGLE_API_KEY`, `CORS_ORIGINS`
7. Click **"Generate Domain"** to get a public URL

#### Deploy Frontend:
8. Click **"Add a Service"** → **"GitHub Repo"** again
9. Configure:

| Setting | Value |
|---------|-------|
| **Root Directory** | `/frontend` |
| **Build Command** | `npm install && npm run build` |
| **Start Command** | `npm start` |

10. Add Variable: `NEXT_PUBLIC_API_URL` = backend Railway URL
11. Click **"Generate Domain"**

---
---

## Option C: VPS with Docker — Full Control ($4-6/mo)

Use your existing `docker-compose.yml` on a cloud server. Best for production.

### Step 1: Get a VPS

| Provider | Plan | Price |
|----------|------|-------|
| [DigitalOcean](https://digitalocean.com) | Basic Droplet | $4/mo |
| [Hetzner](https://hetzner.com) | CX22 | €4/mo |
| [AWS Lightsail](https://aws.amazon.com/lightsail/) | 512MB | $3.50/mo |

Choose **Ubuntu 22.04**, minimum **1 GB RAM**.

### Step 2: SSH into Server & Install Docker

```bash
ssh root@YOUR_SERVER_IP

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt install docker-compose-plugin -y
```

### Step 3: Clone & Deploy

```bash
git clone https://github.com/YOUR_USERNAME/abstract-enclave.git
cd abstract-enclave

# Create .env file
cat > .env << 'EOF'
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://YOUR_SERVER_IP,https://yourdomain.com
EOF

# Launch everything
docker compose up -d
```

### Step 4: Access Your App

Open browser: `http://YOUR_SERVER_IP` → your app is live!

### Step 5: Add a Domain + HTTPS (Optional)

```bash
# Point your domain DNS A record to YOUR_SERVER_IP, then:
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com
```

---
---

## Quick Comparison

| | Vercel + Render | Railway | VPS + Docker |
|---|---|---|---|
| **Cost** | Free forever | Free trial → $5/mo | $4-6/mo |
| **Setup Time** | ~10 min | ~10 min | ~30 min |
| **Difficulty** | Easy | Easy | Moderate |
| **Cold Start** | 30s (Render free) | None | None |
| **Custom Domain** | ✅ Both platforms | ✅ | ✅ (manual) |
| **HTTPS** | ✅ Automatic | ✅ Automatic | Manual (Certbot) |
| **Database** | ❌ (in-memory) | ✅ Add PostgreSQL | ✅ Included |
| **Scaling** | Auto (Vercel) | Manual | Manual |
| **Best For** | Demo / Portfolio | Small production | Full production |

---

## Troubleshooting

### "CORS error" in browser console
→ Make sure `CORS_ORIGINS` on the backend includes your exact frontend URL (with `https://`, no trailing slash).

### "Module not found" on Render
→ Make sure **Root Directory** is set to `backend`, not the project root.

### Frontend shows interactions but no AI companion responses
→ Either `GOOGLE_API_KEY` is missing/invalid, or Gemini free tier rate limit hit. The app still works with rule-based fallbacks.

### Render takes 30s to respond
→ Normal for free tier. Upgrade to $7/mo "Starter" plan for always-on.

### "502 Bad Gateway" on initial load
→ Backend is still starting. Wait 30-60 seconds and refresh.
