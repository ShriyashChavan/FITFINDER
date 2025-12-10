# FitFinder (FitFinder - AI Fashion Assistant)


Quickstart

1. Create a Python virtual environment and activate it.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Run the app:

   ```powershell
   python app.py
   ```

The app serves `static/index.html` at `http://localhost:5000/` and exposes API endpoints under `/api/*`.

To push to a remote Git repository, add a remote and run `git push -u origin main` (you can choose another branch name).

Optional: Enabling real AI integration

- Hugging Face Inference API: Set environment variables to enable server-side image generation.
   - `HF_API_TOKEN` — your Hugging Face API token
   - `HF_MODEL` — (optional) model id, e.g. `stabilityai/stable-diffusion-2-1`

When these variables are set the backend will call the Hugging Face Inference API to generate images. If not set, the app runs in demo mode and returns placeholder images.

Example (PowerShell):
```powershell
$env:HF_API_TOKEN = "hf_xxx..."
$env:HF_MODEL = "stabilityai/stable-diffusion-2-1"
python app.py
```
