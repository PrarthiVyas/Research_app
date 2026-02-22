# CrewAI Research Paper Analyzer

A small Flask UI around a CrewAI pipeline that analyzes research PDFs. Upload a PDF and the app runs 4 sequential agents (paper reader, math simplifier, implementation guidance, and summary) and returns a consolidated analysis.

## Project structure

- `app.py` - Flask web UI (upload PDF → runs Crew → shows results)
- `crew_runner.py` - original CLI runner (renamed from the earlier `app.py`)
- `crew/crew_setup.py` - builds the Crew (agents, tasks)
- `agents/` - agent definitions
- `tasks/` - task definitions
- `llm/gemini_llm.py` - LLM configuration (currently set to Azure OpenAI)
- `templates/` - Flask templates (`index.html`, `result.html`, `error.html`)
- `requirements.txt` - Python dependencies
- `venv/` or `crewai-env/` - virtual environment (not checked in)

## Prerequisites

- Recommended: Python 3.11 (CrewAI and some dependencies are not yet stable on 3.13)
- Git (optional)
- A valid LLM API key (Azure OpenAI or Google Gemini). Set as environment variables:
  - For Azure: `AZURE_API_KEY` and configure `llm/gemini_llm.py` if needed
  - For Google Gemini: `GOOGLE_API_KEY` if you switch to Gemini in `llm/gemini_llm.py`

## Quick Windows setup (recommended)

1. Install Python 3.11 from https://www.python.org/downloads/release/python-3119/ and check "Add to PATH".
2. Open PowerShell and create a venv:

```powershell
py -3.11 -m venv venv311
.\venv311\Scripts\activate
```

If `py -3.11` isn't available, install Python 3.11 and restart PowerShell, or use the full path to the Python executable.

3. Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

4. Set your API key(s) in an `.env` file in the project root or export in PowerShell:

```powershell
# .env content
AZURE_API_KEY=your_azure_key_here
# or
GOOGLE_API_KEY=your_google_key_here
```

5. Run the Flask UI (from project root):

```powershell
# If using the venv created above
.\venv311\Scripts\python.exe app.py

# Or, if you already have another venv (like .\venv or .\crewai-env)
.\venv\Scripts\python.exe app.py
# or
.\crewai-env\Scripts\python.exe app.py
```

6. Open the UI at: `http://127.0.0.1:5000`

## Running the CLI runner

If you prefer the original CLI mode (runs on a hardcoded PDF path):

```powershell
# Use the venv python
.\venv311\Scripts\python.exe crew_runner.py
```

## Troubleshooting

- ImportError complaining about `crewai.llms.providers.azure` or similar:
  - Ensure you installed `crewai[azure-ai-inference]` inside the same venv used to run the app:

```powershell
.\venv311\Scripts\pip.exe install "crewai[azure-ai-inference]"
```

- If you get Pydantic / build-time errors or very long freezes while importing `crewai` on Python 3.13, switch to Python 3.11 as shown above.

- If the Flask server starts but you see a long delay after uploading a PDF, that is expected—Crew will make LLM API calls for each agent; ensure your API key has quota and network access.

## Next steps and improvements

- Add asynchronous processing (Celery / background jobs) for long-running analysis and a job status page.
- Support multiple LLM providers or per-agent provider overrides.
- Add richer HTML output formatting (sections collapsed/expanded, downloadable markdown/JSON).

If you want, I can:
- Add an asynchronous job queue so uploads return a job id immediately, and results are accessible later.
- Convert the UI to Streamlit or a single-page React app for better UX.

---

If you want me to proceed with adding async processing or switching the LLM provider to Google Gemini, say which option and I'll implement it next.