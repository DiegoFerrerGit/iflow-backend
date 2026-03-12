# iflow-api

Backend API for iflow, built with FastAPI, Motor (async MongoDB), and Clean Architecture.

## Prerequisites

- **Python 3.12** (installed via Homebrew, not the macOS system Python)
- Docker (for local MongoDB)
- [MongoDB Compass](https://www.mongodb.com/products/compass) (optional, for visual DB inspection)

## Local Development Setup (macOS)

### 1. Install Python 3.12 via Homebrew

The macOS system Python (3.9.x) is **not supported**. Install Python 3.12 with Homebrew:

```bash
brew install python@3.12
```

Verify the installation:

```bash
python3.12 --version
```

You should see `Python 3.12.x`.

### 2. Start MongoDB via Docker

```bash
docker run -d --name iflow-mongo -p 27017:27017 mongo:7
```

Verify it is running:

```bash
docker ps | grep iflow-mongo
```

### 3. Create a virtual environment and install dependencies

Always use `python3.12` explicitly to create the virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To confirm the venv is using the correct version:

```bash
python --version
```

It must show `Python 3.12.x`.

### 4. Configure environment variables

The app requires these variables (no defaults). If missing, it fails to start:

- `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_ACCESS_SECRET`, `JWT_REFRESH_SECRET`, `GOOGLE_OAUTH_CLIENT_ID`, `FRONTEND_ORIGIN`

- **Local:** Copy `.env.example` to `.env.local` and fill in values. `.env.local` is gitignored.
- **Production (e.g. Render):** Set all variables as environment variables in the dashboard. Do not use .env files.
- **Test prod config locally:** `ENV_FILE=.env.prod uvicorn src.main:app ...`

### 5. Run the API

```bash
# 1. Activate the virtual environment
source .venv/bin/activate

# 2. If port 8000 is already in use, kill the process
lsof -ti:8000 | xargs kill -9

# 3. Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

### 6. Connect MongoDB Compass

Open MongoDB Compass and connect to:

```
mongodb://localhost:27017
```

After the API starts, you will see the `iflow_dev` database with `users` and `user_sessions` collections.



## Running Tests

```bash
# Make sure MongoDB is running first
pytest tests/ -v
```
