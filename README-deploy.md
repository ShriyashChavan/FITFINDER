# Deploying FITFINDER (Railway / Heroku)

This file describes quick steps to deploy the Flask backend to Railway or Heroku (both can deploy from a GitHub repo and provide a public URL).

Prerequisites
- A GitHub repository (this project is already pushed to `origin/main`).
- An account on Railway (https://railway.app) or Heroku (https://heroku.com).
- `requirements.txt` present (this repo includes `requirements.txt` and `gunicorn`).

Railway (quickest)
1. Sign in to Railway and choose "New Project" → "Deploy from GitHub".
2. Authorize Railway to access your GitHub account and select the `FITFINDER` repository.
3. For build settings Railway will detect `requirements.txt` and install dependencies.
4. Set the start command to (Railway typically sets this automatically from `Procfile`):
   ```
   python app.py
   ```
   or rely on `Procfile` (preferred):
   ```
   web: gunicorn -w 2 -b 0.0.0.0:$PORT app:app
   ```
5. Add environment variables in Railway dashboard if needed:
   - `HF_API_TOKEN` (optional) — your Hugging Face token
   - `HF_MODEL` (optional) — model id (default: `stabilityai/stable-diffusion-2-1`)
6. Deploy and open the provided URL.

Heroku (alternative)
1. Install the Heroku CLI and login: `heroku login`.
2. Create an app on the Heroku dashboard or via CLI: `heroku create your-app-name`.
3. Connect GitHub repo in the Heroku dashboard (Deploy → GitHub) and enable automatic deploys.
4. Set config vars (`HF_API_TOKEN`, `HF_MODEL`) in the Heroku dashboard (Settings → Config Vars).
5. Heroku will use the `Procfile` to run the app with `gunicorn`.

Local run & testing
1. Activate the venv and install requirements:
   ```powershell
   . .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Start locally:
   ```powershell
   python d:\ssr\app.py
   ```
3. Health check:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:5000/api/health -Method Get
   ```

Security notes
- Do not publish your `HF_API_TOKEN` publicly — store it as an environment variable in the host (Railway/Heroku).
- For production, consider running behind HTTPS and a proper WSGI server; `gunicorn` is suitable for many cases.

If you want, I can also add a GitHub Actions workflow or a `Dockerfile` to support other hosts — tell me which host you prefer and I will prepare the files.
