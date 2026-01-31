# Deploy Medical Paper Summarizer

Deploy this app as a live website in a few minutes.

## Option 1: Render (Recommended)

[Render](https://render.com) offers a free tier and one-click deploy.

### Steps

1. **Push your code** to GitHub (or connect your repo).

2. **Create a new Web Service** on [Render Dashboard](https://dashboard.render.com).

3. **Connect your repository** and configure:
   - **Build Command:** (leave empty – uses Dockerfile)
   - **Start Command:** (leave empty – uses Dockerfile CMD)
   - **Runtime:** Docker

4. **Add Environment Variables** in Render:
   - `ANTHROPIC_API_KEY` – Your Anthropic API key (or)
   - `OPENAI_API_KEY` – Your OpenAI API key
   
   You need at least one. The app prefers Claude (Anthropic) and falls back to GPT-4 (OpenAI).

5. **Deploy.** Render will build from the Dockerfile and start the app.

6. Your site will be live at `https://your-app-name.onrender.com`

### Blueprint (Alternative)

If your repo has a `render.yaml` at the root:

1. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
2. Connect your repo.
3. Render will detect `render.yaml` and create the service.
4. Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the service's Environment tab.

---

## Option 2: Railway

[Railway](https://railway.app) also supports Docker and has a simple flow.

1. Install the [Railway CLI](https://docs.railway.app/develop/cli) or use the web UI.
2. Create a new project and connect your repo.
3. Railway auto-detects the Dockerfile.
4. Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in Variables.
5. Deploy.

---

## Option 3: Fly.io

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/).
2. Run `fly launch` in the project directory.
3. Add secrets: `fly secrets set ANTHROPIC_API_KEY=your_key`
4. Deploy: `fly deploy`

---

## Option 4: Run Locally (Production-like)

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
export ANTHROPIC_API_KEY=your_key   # or OPENAI_API_KEY

# Run
python web_server.py
```

Open http://localhost:8000

---

## Important Notes

- **Request timeout:** Summarization can take 1–2 minutes. Render's free tier allows long requests; some platforms may need timeout adjustments.
- **API keys:** Never commit `.env` or API keys. Use your platform's environment variable settings.
- **PDF size:** Large PDFs (e.g. 50+ pages) may hit memory limits on free tiers.
