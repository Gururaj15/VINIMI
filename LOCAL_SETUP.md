# VINIMI Local Setup (frontend + backend)

Follow these steps to run the app locally with a MySQL database.

## Prereqs
- MySQL running locally (default port 3306).
- Python 3.10+ and `pip`.
- Node 18+ and `npm`.

## Database
1) Create the database:
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS vinimi_local DEFAULT CHARACTER SET utf8mb4;"
```
2) Import the schema dump:
```bash
mysql -u root -p vinimi_local < vinimi_live/vinimi_local_schema.sql
```
3) Set your MySQL connection details (preferred) **before starting the backend**:
```bash
export LOCAL_DB_HOST=127.0.0.1
export LOCAL_DB_PORT=3306
export LOCAL_DB_USER=<your_mysql_user>
export LOCAL_DB_PASS=<your_mysql_password>
export LOCAL_DB_NAME=vinimi_local
```
   (If you prefer hard-coding, the defaults live at the top of `vinimi_live/app/db.py`.)

## Backend (FastAPI)
```bash
cd vinimi_live
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# set your DB creds (copy .env.example -> .env and edit)
cp .env.example .env
```
Edit `vinimi_live/.env` to match your MySQL user/password (or export `LOCAL_DB_*` env vars in your shell), then start:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
Notes:
- The backend reads the `LOCAL_DB_*` env vars above.
- Media is served from `http://localhost:8001/media`.

## Frontend (Vite)
```bash
cd vinimi-vision-safety-main
npm install
echo "VITE_API_URL=http://localhost:8001
VITE_LIVE_API_URL=http://localhost:8001" > .env.local
npm run dev -- --host --port 8000
```
Visit `http://localhost:8000` and the app will call the backend at `http://localhost:8001`.
