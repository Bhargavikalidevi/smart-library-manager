# Smart Library Manager

A beginner-friendly Library Management System built with Python, Flask, SQLAlchemy, HTML, and CSS. It supports book inventory, member registration, issuing/returning books, overdue tracking, and fine calculation.

## Features
- Dashboard with book, member, and loan counts
- Add, search, and delete books
- Register members
- Issue available books with a 14-day loan period
- Return books and calculate overdue fines at ₹5/day
- Overdue report
- SQLite by default; PostgreSQL supported through `DATABASE_URL`

## Requirements
- Python 3.10+
- pip

## Run locally (Windows / macOS / Linux)

```bash
git clone https://github.com/YOUR-USERNAME/smart-library-manager.git
cd smart-library-manager

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python app.py
```

On Windows PowerShell, copy the environment template with:
```powershell
Copy-Item .env.example .env
```

Open http://127.0.0.1:5000

The app creates its local SQLite database automatically on first run. For PostgreSQL, set `DATABASE_URL` in `.env` to a valid SQLAlchemy PostgreSQL URL.

## Push to GitHub

Create an empty repository named `smart-library-manager` on GitHub, then run:

```bash
git init
git add .
git commit -m "Build Smart Library Manager"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/smart-library-manager.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

## Important
This is a learning/demo project. Before deploying publicly, add authentication and authorization, CSRF protection, database migrations, stronger validation, and production server configuration. Do not commit `.env` or real credentials.
