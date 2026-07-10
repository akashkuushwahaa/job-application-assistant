# Job Application Assistant

An AI agent that compares your resume against a job posting, scores the
match, drafts a tailored cover letter, suggests resume bullet rewrites,
and logs every application to a tracker — with a web UI or CLI.

## Features

- **Match scoring** — 0–100 score with matched/missing skills and seniority fit
- **Cover letter drafting** — grounded only in what's actually in your resume (no invented experience)
- **Resume bullet suggestions** — rephrased to mirror the job posting's language for ATS matching
- **Application tracker** — every run logs to a CSV you can review or export

## Project structure

```
.
├── app.py                        # Streamlit web UI
├── job_application_assistant.py  # CLI version (edit the paths at the bottom to run)
├── requirements.txt
├── .env.example                  # copy to .env and add your key
└── .gitignore
```

## Setup

**1. Clone and enter the repo**
```bash
git clone https://github.com/akashkuushwahaa/job-application-assistant.git
cd job-application-assistant
```

**2. Create a virtual environment (recommended)**
```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

**3. Install dependencies**
```bash
python -m pip install -r requirements.txt
```

**4. Set your OpenAI API key**

Add your real key. Alternatively, set it directly:
```bash
# macOS / Linux
export OPENAI_API_KEY="sk-..."

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
```
You can also just paste the key into the sidebar when the web app is running — it doesn't have to come from an environment variable.

## Running the web app

```bash
python -m streamlit run app.py
```
(Use `python -m streamlit` rather than a bare `streamlit` command if your system can't find the `streamlit` executable on PATH — this routes through the same Python environment you installed it in.)

This opens a browser tab where you can:
1. Upload your resume (PDF, DOCX, or TXT)
2. Paste a job posting
3. Click **Generate application materials**
4. Review the match score, cover letter, and bullet suggestions
5. See every past application in the sidebar tracker, exportable as CSV

## Running the CLI version

Edit the bottom of `job_application_assistant.py`:
```python
result = run(
    resume_path="resume.pdf",
    job_text_or_path="job_posting.txt",
    company="Acme Corp",
    role="Backend Engineer",
)
```
Then run:
```bash
python job_application_assistant.py
```

## How it works

1. **Parsing** — extracts plain text from your resume (PDF/DOCX/TXT) and the job posting
2. **Match analysis** — an LLM call compares both and returns a structured JSON score, matched/missing skills, and seniority fit
3. **Cover letter generation** — a second call drafts a letter, explicitly instructed to use only real experience from your resume — no fabricated metrics or job titles
4. **Bullet suggestions** — rephrases your existing achievements to mirror the job posting's terminology
5. **Tracker logging** — appends the result to `applications_tracker.csv`

## Guardrails built in

- The model is instructed not to invent achievements, metrics, or experience — everything in the cover letter must trace back to your actual resume
- This tool only **drafts** — it never auto-submits applications. You always review and send manually
- Low match scores (<40) trigger a warning so you can decide whether a role is worth pursuing before spending time on it

## Notes

- `applications_tracker.csv` and any resumes/job postings you upload are excluded from version control via `.gitignore` — they're personal data, not code
- The Streamlit sidebar API key field is masked but visible within your own browser session; fine for local use, but don't deploy this publicly without adding proper authentication
- Model defaults to `gpt-4o` in both scripts — swap to `gpt-4o-mini` for cheaper/faster iteration while testing

