# ocr-llm-mvp

MVP: OCR -> Text Cleaning -> LLM Analysis -> Structured JSON Output

Project overview documentation lives in [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md).
Technical documentation for the current codebase lives in [`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md).

## Streamlit App

Run locally:

```bash
pip install -r requirements.txt
streamlit run app/user_interface.py
```

The app can load documentation from either:

- the latest local `outputs/**/final_summary.md` file
- an uploaded `.md` or `.txt` summary file in the sidebar

The chat UI supports both typed questions and voice questions recorded from your microphone. Voice queries are transcribed and then answered against the same loaded documentation.

## Push To GitHub

1. Create a new GitHub repository.
2. From this project root, run:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

Do not commit `.env`. It is already ignored by `.gitignore`.

## Deploy On Streamlit Community Cloud

1. Push the project to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app from your GitHub repository.
4. Set the main file path to:

```text
app/user_interface.py
```

5. In the app settings, add this secret:

```toml
GEMINI_API_KEY = "your_api_key_here"
```

6. Deploy the app.

After deployment, upload a generated summary file in the sidebar if the cloud app does not have a local `outputs/` directory.
