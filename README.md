# Enhance Digital Freelancer Profiling Management System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-ready-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

**Tags:** #django #python #freelancer-platform #capstone-project

Capstone Freelancer Profiling App is a full-stack Django platform used to curate
freelancer profiles, promote events, and coordinate support interactions between
talent and administrators.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Architecture & Tech Stack](#architecture--tech-stack)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Quick Start](#quick-start)
7. [Configuration](#configuration)
8. [Managing Data](#managing-data)
9. [Running & Developer Tasks](#running--developer-tasks)
10. [Usage](#usage)
11. [User-Generated Media](#user-generated-media)
12. [Social Login Setup](#social-login-setup)
13. [Troubleshooting & Support](#troubleshooting--support)

---

## Overview

The application centralizes portfolio content and program communications for
freelancers. Students or alumni can maintain a living résumé, upload project
artifacts, RSVP for events, and receive announcements, while administrators gain
tools for analytics, ticket triage, and content management.

## Key Features

- **Freelancer Profiles** – Capture affiliations, experiences, skills, and
  language proficiencies with rich profile pages.
- **Resume & Project Management** – Upload résumés, certificates, and portfolio
  projects directly within the platform.
- **Event Management & RSVP** – Explore upcoming events, respond with RSVP
  statuses, and check in with QR codes.
- **Announcements Feed** – Publish timely news and updates to the entire
  community.
- **Support Ticketing** – Submit issues or questions and receive notifications
  when staff respond.
- **Administrative Dashboard** – Visualize analytics, oversee content, and
  moderate community activity.

## Architecture & Tech Stack

- **Backend:** Django 4.x, Django REST Framework, PostgreSQL (SQLite supported
  for local development).
- **Frontend:** Django templates with Tailwind CSS utilities.
- **Authentication:** Django Allauth with optional Google OAuth integration.
- **Asynchronous tasks:** Celery + Redis (optional for background processing).
- **Containerization:** Docker support via `render.yaml` deployment recipe.

## Project Structure

```text
capstone-app-profile/
├── profileapp/           # Django project source
├── profileapp/fixtures/  # Seed data for local testing
├── statics/              # Global static assets (collected at build time)
├── requirements.txt      # Python dependencies
├── render.yaml           # Render deployment configuration
└── README.md             # This document
```

> The repository ships with a `.env.example` template and excludes generated
> media, compiled artifacts, and environment-specific files from version control.

## Prerequisites

- Python **3.11** (use `python3.11` or `py` depending on your OS).
- Pip package manager (paired with the selected Python interpreter).
- PostgreSQL 14+ (recommended) or SQLite for local experimentation.
- Node.js & npm (optional) when extending Tailwind or frontend build tooling.

## Quick Start

> 💡 **Tip:** Substitute `python`/`pip` for `py`/`pip3.11` if those commands are
> unavailable on your system.

1. **Clone the repository**
   ```bash
   git clone https://github.com/Seanneskie/capstone-app-profile-public.git
   cd capstone-app-profile
   ```
2. **Create and activate a virtual environment**
   ```bash
   python -m venv env
   # Windows (Command Prompt)
   env\Scripts\activate.bat
   # Windows (PowerShell)
   env\Scripts\activate.ps1
   # macOS / Linux
   source env/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Enter the Django project directory**
   ```bash
   cd profileapp
   ```
5. **Bootstrap environment variables**
   ```bash
   cp .env.example .env
   ```
6. **Run migrations**
   ```bash
   python manage.py migrate
   ```
   Load sample content (optional):
   ```bash
   bash load_data.sh       # from the profileapp/ directory
   # or run individual fixtures:
   python manage.py loaddata fixtures/profiling_data.json
   python manage.py loaddata fixtures/events_data.json
   python manage.py loaddata fixtures/geolocations_data.json
   ```
7. **Create an admin user**
   ```bash
   python manage.py createsuperuser
   ```
8. **Start the development server**
   ```bash
   python manage.py runserver
   ```
9. **Explore the app**
   - User portal: <http://127.0.0.1:8000/>
   - Admin portal: <http://127.0.0.1:8000/admin>

## Configuration

Populate the `.env` file with secure values:

- `SECRET_KEY` – Django cryptographic key.
- Database: `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
  `DB_PORT`.
- Email: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`,
  `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`.

The example file targets PostgreSQL. To use SQLite locally, set
`DB_ENGINE=django.db.backends.sqlite3` and point `DB_NAME` to a writable path
such as `BASE_DIR / "db.sqlite3"`.

## Managing Data

- **Migrations** – `python manage.py migrate`
- **Fixtures** – `bash load_data.sh` (from `profileapp/`) or run the individual
  fixture files noted above.
- **Createsuperuser** – `python manage.py createsuperuser`

The `profileapp/fixtures/` directory contains curated sample data to quickly
populate a demo environment. Avoid committing real user data to Git history.

## Running & Developer Tasks

| Task                          | Command                                      |
| ----------------------------- | -------------------------------------------- |
| Start development server      | `python manage.py runserver`                 |
| Collect static files          | `python manage.py collectstatic`             |
| Run unit tests                | `python manage.py test`                      |
| Lint with Ruff (if enabled)   | `ruff check .`                               |
| Format with Black (if enabled)| `black .`                                    |

> Configure pre-commit hooks or CI workflows to keep code quality consistent
> across contributions.

## Usage

1. **Launch the development server**
   ```bash
   python manage.py runserver
   ```
2. **Sign in or create a freelancer account** from the landing page at
   <http://127.0.0.1:8000/>. Administrators can authenticate via the admin
   portal at <http://127.0.0.1:8000/admin>.
3. **Complete your profile** by adding background information, skills, and
   uploading résumés, certificates, or portfolio projects.
4. **Explore events and announcements** to RSVP for upcoming sessions and stay
   informed about community updates.
5. **Submit support tickets** whenever you have questions or encounter issues;
   you will receive notifications as staff members respond.


## User-Generated Media

Create directories for uploaded assets before launching the server:

```bash
mkdir -p profileapp/media/{profile,projects,resumes}
```

- `profileapp/media/` stays untracked (`.gitignore`) so user uploads do not leak
  into source control.
- If historical commits contain media, scrub them with
  `git filter-repo --path profileapp/media --invert-paths` or an equivalent
  rewrite.
- For demos, rely on fixtures (`profileapp/fixtures/`) or scripted generators
  rather than bundling binary assets.

## Social Login Setup

OAuth client IDs and secrets must **never** be stored in fixtures or committed
to version control. Provision credentials via your OAuth provider (e.g., Google
Cloud Console) and expose them as environment variables.

1. **Export credentials** so they are available when Django starts:
   ```bash
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```
   Align the redirect URI with your deployment, e.g.
   `https://<your-domain>/accounts/google/login/callback/`.
2. **Register the social application** in Django:
   - **Admin UI** – Navigate to `/admin`, open **Social applications**, create a
     Google entry, paste the client ID and secret, and attach the desired
     **Site**.
   - **Management shell** – With environment variables exported, run:
     ```bash
     python manage.py shell <<'PY'
     from allauth.socialaccount.models import SocialApp
     from django.contrib.sites.models import Site
     import os

     site = Site.objects.get_current()
     app, _ = SocialApp.objects.get_or_create(provider='google', name='Google OAuth')
     app.client_id = os.environ['GOOGLE_CLIENT_ID']
     app.secret = os.environ['GOOGLE_CLIENT_SECRET']
     app.save()
     app.sites.set([site])
     PY
     ```
   Adjust provider names and redirect URIs for any additional OAuth providers.

Keep secrets in a managed vault or environment configuration service and rotate
them whenever exposure is suspected.

## Troubleshooting & Support

- **Virtual environment issues** – Delete the `env/` folder and recreate it to
  clear conflicting dependencies.
- **Database connection errors** – Confirm credentials and network access, or
  fallback to SQLite during development.
- **Static files missing** – Run `python manage.py collectstatic` when deploying
  to production-like environments.
- **Need help?** – Open a GitHub issue or reach out to the project maintainer
  with reproduction steps and logs.

---

Happy building! 🎉
