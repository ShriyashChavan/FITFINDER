# FitFinder (FitFinder - AI Fashion Assistant)

Simple Flask backend that serves static front-end files from the `static/` directory.

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
