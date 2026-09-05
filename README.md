# Job Application Workspace

A personal, local-first workspace for comparing a resume with a job posting,
creating truthful application drafts, preparing for interviews, and tracking
the application over time.

The AI output is decision support, not an objective ATS result. Every generated
claim should be reviewed before it is used.

## Features

- Evidence-led fit estimate with matched skills, gaps, seniority fit, and a
  requirement-by-requirement explanation
- Cover letter grounded only in resume content
- Resume bullet rewrites linked to their original resume evidence
- Interview questions with role-specific preparation guidance
- Editable artifacts saved to SQLite locally, or hosted Postgres when deployed
- Cover letter downloads as TXT or formatted DOCX
- Searchable application library, status history, filters, and CSV export
- Automatic one-time migration from the legacy `applications_tracker.csv`
- Streamlit web interface and command-line interface

## Architecture

```text
.
├── core.py                       # Parsing, OpenAI call, persistence, exports
├── app.py                        # Streamlit workspace
├── job_application_assistant.py  # CLI
├── check_database.py             # One-off database connectivity check
├── tests/                        # Unit and integration-style tests
├── pyproject.toml                # pytest and Ruff configuration
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

The resume is processed in memory and is not written to the database. The
database stores job metadata, generated materials, the selected model, token
usage, and status history.

## Setup

Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then set your OpenAI API key:

```dotenv
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
DATABASE_FILE=job_applications.db
```

Storage is chosen by `DATABASE_URL`. Leave it unset and the app uses the local
SQLite file above. Set it to a Postgres connection string and the app uses that
instead, which is what a hosted deployment needs:

```dotenv
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

After setting it, confirm the connection works before relying on it:

```bash
python check_database.py
```

The Streamlit app never copies a server-configured key into the browser. When
no environment key exists, a key can be entered for the current local browser
session.

## Run the web app

```bash
python -m streamlit run app.py
```

Use **New analysis** to prepare an application. Use **Applications** to search,
change statuses, reopen saved materials, inspect status history, and export CSV.

## Run the CLI

Analyze and save an application:

```bash
python job_application_assistant.py \
  --resume resume.pdf \
  --job job-posting.txt \
  --company "Acme Corp" \
  --role "Backend Engineer" \
  --job-url "https://example.com/jobs/123" \
  --source "Referral" \
  --location "Remote"
```

Manage saved applications:

```bash
python job_application_assistant.py --show-tracker
python job_application_assistant.py --show APPLICATION_ID
python job_application_assistant.py --set-status APPLICATION_ID applied
python job_application_assistant.py --set-status APPLICATION_ID interviewing \
  --status-note "Technical interview scheduled"
```

## Privacy and safety

- Resume and job text are sent to OpenAI only after explicit confirmation in
  the web app.
- Responses API storage is disabled for generation requests. Provider-level
  retention policies may still apply to API traffic.
- Resume text is not persisted locally; a filename and content hash are stored
  to identify which version was used.
- `.env`, SQLite files, CSV data, resumes, and generated document files are
  excluded from Git.
- CSV export protects spreadsheet users from formula-injection prefixes.
- Uploaded file size, PDF page count, extracted text, URLs, model names, and
  structured model output are validated.

This remains a personal-use application. Do not deploy it as a public,
multi-user service without authentication, per-user database isolation,
encrypted file storage, quotas, and a deployment-specific privacy policy.

## Data migration

On the first database operation, rows from `applications_tracker.csv` are
imported into SQLite and marked as migrated. The original CSV is left untouched.
This one-time import runs for the local SQLite file only; a Postgres database
starts empty. Move existing rows across by exporting CSV from the local app and
re-entering them, or by copying the `applications` table directly.

## Deployment (Streamlit Community Cloud)

The app runs on Streamlit Community Cloud, with two things to get right.

**Use Postgres, not SQLite.** The Community Cloud filesystem is wiped on every
restart and redeploy, so a SQLite file would silently lose every saved
application. Create a free Postgres database (Neon or Supabase both work), then
add its connection string as a secret.

**Deployment steps**

1. Push this repository to GitHub.
2. At [share.streamlit.io](https://share.streamlit.io), create an app pointing
   at this repo, branch `main`, main file `app.py`.
3. Under *Advanced settings*, choose Python 3.13. Newer versions are not
   supported by Community Cloud.
4. Under *Advanced settings > Secrets*, add:

   ```toml
   OPENAI_API_KEY = "sk-your-key-here"
   OPENAI_MODEL = "gpt-4o"
   DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
   ```

5. Deploy, then open the app and generate one application to confirm the
   database is being written to.

**Cost and access.** When `OPENAI_API_KEY` is set on the server, the sidebar key
field disappears and every visitor generates applications on that key. A
Community Cloud URL is public by default, so either restrict viewers in the app
settings or leave `OPENAI_API_KEY` unset, which makes each visitor supply their
own key.

## Development

Install development tools and run checks:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
# or: python -m pytest
python -m ruff check .
```

Tests use temporary databases and mocked AI responses; they do not call the
live OpenAI API.
