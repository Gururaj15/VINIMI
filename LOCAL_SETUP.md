# VINIMI Local Development Setup Guide

## 1. Overview

**VINIMI** is an AI-powered workplace safety monitoring system consisting of:

- **Backend**: FastAPI server for real-time face detection, recognition, and safety violations
- **Frontend**: Vite + React + Tailwind CSS web dashboard for monitoring and alerts
- **Database**: MySQL 8.x for worker data, embeddings, violations, and logs

### Repository Layout

```
VINIMI/
├── vinimi_live/                      # Backend (FastAPI)
│   ├── app/
│   │   ├── main.py                   # FastAPI entry point
│   │   ├── config.py                 # Configuration (env vars)
│   │   ├── db.py                     # Database connection
│   │   ├── detection.py              # YOLO + face detection
│   │   ├── alerts.py                 # SMS/alert logic
│   │   ├── face_gallery.py           # Face embedding operations
│   │   └── live.html                 # Live monitoring template
│   ├── requirements.txt              # Python dependencies
│   ├── vinimi_local_schema.sql       # MySQL schema + seed data
│   ├── embeddings_with_vectors.csv   # Precomputed face embeddings (optional)
│   └── vinimi_live_still.py          # Standalone detection script
│
├── vinimi-vision-safety-main/        # Frontend (Vite/React)
│   ├── package.json                  # Node dependencies
│   ├── vite.config.ts                # Vite configuration
│   ├── tailwind.config.ts            # Tailwind CSS config
│   ├── src/
│   │   ├── App.tsx                   # Main React component
│   │   ├── pages/                    # Page components
│   │   └── components/               # Reusable components
│   └── .env.example                  # Environment template
│
└── README.md                         # Project overview

```

---

## 2. Prerequisites

Before starting, ensure you have the following installed:

- **Git** – version control
- **Node.js LTS** (≥ 18) + npm – frontend package manager
- **Python 3.10+** (recommend 3.11) – backend runtime
- **MySQL 8.x server** – database
- **Homebrew** (macOS only) – package manager

### macOS: Quick Install

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install git node python mysql
brew services start mysql
```

### Optional Dependencies

- **ffmpeg** – for video processing (`brew install ffmpeg`)
- **tf-keras** – if DeepFace complains about missing backend (`pip install tf-keras`)

---

## 3. Clone the Repository

```bash
git clone https://github.com/vinimifall2025-ops/VINIMI.git
cd VINIMI
```

---

## 4. Database Setup (MySQL)

Choose **Option A (CLI)** or **Option B (Workbench)** below.

### Option A — Command Line

#### 1. Start MySQL service (if not running)

**macOS (Homebrew):**
```bash
brew services start mysql
```

**Linux (systemd):**
```bash
sudo systemctl start mysql
```

**Windows (cmd as Administrator):**
```cmd
net start MySQL80
```

#### 2. Create the database

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS vinimi_local CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

When prompted, enter your MySQL root password.

#### 3. Import schema and seed data

```bash
mysql -u root -p vinimi_local < vinimi_live/vinimi_local_schema.sql
```

#### 4. Verify the import

```bash
mysql -u root -p vinimi_local -e "SHOW TABLES; SELECT COUNT(*) as worker_count FROM worker; SELECT COUNT(*) as embedding_count FROM embeddings;"
```

You should see tables like `worker`, `embeddings`, `violations`, and seed data counts.

---

### Option B — MySQL Workbench (GUI)

1. **Open MySQL Workbench** and connect to your local MySQL server.

2. **Create the schema:**
   - Go to **File** → **New Query Tab**
   - Copy and run:
     ```sql
     CREATE DATABASE IF NOT EXISTS vinimi_local CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
     USE vinimi_local;
     ```

3. **Import the schema:**
   - Go to **Server** → **Data Import**
   - Select **"Import from Self-Contained File"**
   - Choose `vinimi_live/vinimi_local_schema.sql`
   - Set **Default Target Schema** to `vinimi_local`
   - Click **Start Import**

4. **Verify:**
   - In a new query tab, run:
     ```sql
     USE vinimi_local;
     SHOW TABLES;
     SELECT COUNT(*) as worker_count FROM worker;
     SELECT COUNT(*) as embedding_count FROM embeddings;
     ```

---

## 5. Backend Setup (FastAPI)

### 1. Navigate to backend directory

```bash
cd vinimi_live
```

### 2. Create and activate virtual environment

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Upgrade pip and install dependencies

```bash
pip install -U pip wheel setuptools
pip install -r requirements.txt
```

### 4. Create environment configuration

Create a file named `.env` in the `vinimi_live/` directory:

```bash
cat > .env << 'EOF'
# Database configuration
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=3306
LOCAL_DB_USER=root
LOCAL_DB_PASSWORD=your_mysql_root_password
LOCAL_DB_NAME=vinimi_local

# File paths
EMBEDDINGS_CSV=./embeddings_with_vectors.csv
EMBEDDINGS_NPY=./embeddings_matrix.npy
FACE_IMAGE_DIR=./worker_images
YOLO_MODEL_PATH=./best.pt
LOGS_PATH=./logs/live_events.log

# API configuration
FRONTEND_ORIGIN=http://localhost:8080
MEDIA_BASE_URL=http://localhost:8001/media

# Face recognition
FACE_SIM_THRESHOLD=0.5

# Twilio alerts (optional; leave empty if SMS alerts not needed)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
ALERTS_SMS_ENABLED=false
ALERTS_COOLDOWN_MINUTES=15
EOF
```

**Important:** Replace `your_mysql_root_password` with your actual MySQL root password.

### 5. Run the backend

```bash
uvicorn app.main:app --reload --port 8001
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Application startup complete
```

### 6. Test the backend

Open in your browser or use curl:
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{"status": "ok"}
```

---

## 6. Frontend Setup (Vite/React)

### 1. Navigate to frontend directory

In a **new terminal** (keep the backend running), navigate to the frontend:

```bash
cd ../vinimi-vision-safety-main
```

### 2. Install dependencies

```bash
npm install
```

### 3. Create environment configuration

Create a file named `.env.local`:

```bash
cat > .env.local << 'EOF'
VITE_LIVE_API_URL=http://localhost:8001
EOF
```

### 4. Run the development server

```bash
npm run dev
```

You should see:
```
  VITE v... dev server running at:

  ➜  Local:   http://localhost:8080/
  ➜  press h + enter to show help
```

### 5. Open the app

Open your browser to **http://localhost:8080**

---

## 7. Using the Application

### Navigation

- **Home** – Product overview and features
- **Live Monitoring** – Real-time camera feed with face detection overlay
- **Workers** – View all workers in the database
- **Worker Detail** – See a specific worker's profile, embeddings, and violation history
- **Violations** – Browse all recorded safety violations
- **Recent Alerts** – View recently triggered alerts
- **Account** – User profile and settings

### Common Workflows

#### Register a New Worker

1. Navigate to **Live Monitoring** or **Workers** page
2. When an unknown face is detected, a registration prompt appears
3. Fill in:
   - Name
   - Employee ID
   - Department
   - Contact info
4. Click **Submit** – the face embedding is captured and stored

#### View Worker Details

1. Go to **Workers** page
2. Click on a worker's name or card
3. See:
   - Profile photo
   - Face embeddings
   - Violation history
   - Last detection timestamp

#### Monitor Live Feed

1. Navigate to **Live Monitoring**
2. Grant camera permissions if prompted
3. Watch the real-time overlay:
   - Green bounding boxes = recognized workers
   - Red bounding boxes = unknown faces / potential violations
   - Helmet detection status displayed

#### Download Logs

- Logs are written to `LOGS_PATH` on the backend
- Available through the UI if the log-download endpoint is implemented

---

## 8. Common Issues & Fixes

### CORS / 403 Forbidden Error

**Symptom:** Frontend can't reach backend; browser console shows CORS error.

**Fix:**
1. Verify `FRONTEND_ORIGIN` in `vinimi_live/.env` matches your frontend URL:
   ```env
   FRONTEND_ORIGIN=http://localhost:8080
   ```
2. Restart the backend:
   ```bash
   # Stop current process (Ctrl+C) and re-run
   uvicorn app.main:app --reload --port 8001
   ```

---

### MySQL Connection Refused

**Symptom:** Backend crashes with `Connection refused` or `Can't connect to MySQL server`.

**Fix:**
1. Verify MySQL is running:
   ```bash
   mysql -u root -p -e "SELECT 1;"
   ```
   Should return `1`.

2. Check credentials in `vinimi_live/.env`:
   ```env
   LOCAL_DB_HOST=localhost
   LOCAL_DB_PORT=3306
   LOCAL_DB_USER=root
   LOCAL_DB_PASSWORD=your_password
   LOCAL_DB_NAME=vinimi_local
   ```

3. Confirm the database and tables exist:
   ```bash
   mysql -u root -p vinimi_local -e "SHOW TABLES;"
   ```

4. If the database doesn't exist, re-import the schema (see Section 4).

---

### DeepFace tf_keras Import Error

**Symptom:** `ModuleNotFoundError: No module named 'tf_keras'`

**Fix:**
```bash
pip install tf-keras
```

Or use OpenCV backend (if supported by your DeepFace version):
```python
# In detection.py, adjust:
# detector_backend="opencv"
```

---

### OpenCV Import Error on M-series Macs

**Symptom:** `ImportError: No module named 'cv2'` or segmentation fault.

**Fix:**
1. Ensure you're using Python 3.10 or 3.11 (not 3.9):
   ```bash
   python3 --version
   ```

2. Reinstall OpenCV:
   ```bash
   pip uninstall opencv-python opencv-python-headless
   pip install opencv-python
   ```

3. If still failing, reinstall Xcode command-line tools:
   ```bash
   xcode-select --install
   ```

---

### Port Already in Use

**Symptom:** `Address already in use` when starting backend or frontend.

**Fix:**

**Backend (change port):**
```bash
uvicorn app.main:app --reload --port 8002
# Then update frontend .env:
# VITE_LIVE_API_URL=http://localhost:8002
```

**Frontend (change port):**
```bash
npm run dev -- --port 8081
```

---

### Node Dependencies Cache Issue

**Symptom:** `npm install` fails or modules missing after git pull.

**Fix:**
```bash
rm -rf node_modules package-lock.json
npm install
```

---

### Python Virtual Environment Issues

**Symptom:** Packages not found after activating `.venv`.

**Fix:**
```bash
# Recreate the virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -U pip wheel setuptools
pip install -r requirements.txt
```

---

## 9. Next Steps

- **Read the Wiki** for detailed architecture and API documentation: [VINIMI Wiki](https://github.com/vinimifall2025-ops/VINIMI/wiki)
- **Report Issues** on [GitHub Issues](https://github.com/vinimifall2025-ops/VINIMI/issues)
- **Contribute** – see [CONTRIBUTING.md](CONTRIBUTING.md) (if present)

---

## 10. Support & Contact

For questions or issues:
1. Check the [FAQ on the Wiki](https://github.com/vinimifall2025-ops/VINIMI/wiki)
2. Open a GitHub Issue with:
   - Your OS and Python/Node versions
   - Steps to reproduce
   - Error message (full stack trace)
3. Contact the team via Slack or email

---

**Happy coding!** 🚀
