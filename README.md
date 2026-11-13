# AI SIT Helpdesk Ticket Triage System

[![CI/CD](https://github.com/mbszmn/INF1103-Team-6/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/mbszmn/INF1103-Team-6/actions/workflows/ci-cd.yml)

INF1103 Team 6. A terminal app where SIT students and staff log IT problems. Every ticket goes
through Gemini, then the business rules, then gets saved. If the AI is not available the ticket is
still saved with general troubleshooting steps and flagged for manual review.

## Run it on your laptop

You need Python 3.12 or newer.

```powershell
pip install -r requirements.txt
python main.py
```

To use the AI, make a file called `.env` next to `main.py` with your key. Never commit this file.

```
GEMINI_API_KEY=your-key-here
```

Without a key the app still works, it just uses the offline steps for every ticket.

## Run the tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

This runs every test file in `test_scripts`, including each manager's own tests. No API key or
internet is needed, the AI is replaced by a fake one in the tests. Other checks the pipeline runs:

```powershell
python -m pytest --cov     # tests plus coverage, fails under 90%
ruff check .               # lint
mypy .                     # type check of the app code
```

## Run it with Docker

Docker Desktop has to be running. Commands are for PowerShell, run from this folder.

```powershell
docker build -t inf1103-team6-helpdesk .
docker run -it --rm --env-file .env -v helpdesk-data:/app/data inf1103-team6-helpdesk
```

Leave out `--env-file .env` to run without the AI. Tickets are kept in the `helpdesk-data` volume,
so they are still there next time.

Run the tests inside a container:

```powershell
docker build --target test -t inf1103-team6-helpdesk-tests .
docker run --rm inf1103-team6-helpdesk-tests
```

Or the same two things with Docker Compose:

```powershell
docker compose run --rm app
docker compose run --rm tests
```

Or run the image the pipeline publishes, no build needed:

```powershell
docker run -it --rm --env-file .env -v helpdesk-data:/app/data ghcr.io/mbszmn/inf1103-team-6:latest
```

## Settings

| Variable | What it does | Default |
|---|---|---|
| `GEMINI_API_KEY` | Gemini key for the AI manager | none, app runs in offline mode |
| `HELPDESK_DATA_DIR` | Folder for `tickets.json` and the exports | `data` next to `main.py` |
| `APP_VERSION` | Version shown when the app starts, set by the pipeline | `dev` |

## CI/CD pipeline

The workflow is `.github/workflows/ci-cd.yml`. It runs on every pull request and every push to `main`.

| Job | What it checks |
|---|---|
| Lint and type check | `ruff check` and `mypy` |
| Tests | every test file with coverage on Python 3.12 and 3.13, results table and reports saved as artifacts |
| Docker | builds the test image and runs all tests inside it, builds the app image and checks it starts with no API key |
| Publish | only after a push to `main` or a version tag: pushes the app image to GitHub Container Registry |
| Verify | pulls the exact image that was pushed and runs the same start up check |
| Release | only for a version tag: makes a GitHub release with the test and coverage reports attached |

To make a release, tag a commit on `main` and push the tag:

```powershell
git tag v2.0.0
git push origin v2.0.0
```

The image then gets the tags `latest`, `2.0.0`, `2.0` and the short commit id.

## Where things are

| Folder or file | Part |
|---|---|
| `main.py` | builds all the objects and starts the app |
| `helpdesk_app.py` | the menu, sends each ticket through the four managers |
| `managers/io_manager.py`, `ticket/` | IO manager: input, checks on the input, menus |
| `managers/ai_manager.py` | AI manager: prompt, Gemini call, retries, offline reply |
| `managers/logic_manager.py` | logic manager: category, security, priority and manual review rules |
| `managers/data_manager.py`, `storage/`, `filters/`, `exporters/` | data manager: saving, loading, searching and exporting tickets |
| `models/` | the `Ticket` and `StatusChange` classes |
| `views/` | turns tickets into text for the screen |
| `errors/` | the app's own error types |
| `test_scripts/` | all the automated tests |
| `data/tickets.json` | saved tickets |

Menu option 8 filters tickets by status, priority, category and a search word. Option 6 writes
`data/tickets.csv` for Excel and `data/ticket_summary.txt` with counts and the urgent tickets.
