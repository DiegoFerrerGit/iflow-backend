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

The project ships with a `.env.local` file containing sensible defaults for local development.
No changes are needed to get started; just make sure `.env.local` exists in the project root.

For production, set real values via environment variables (they override the file).

### 5. Run the API

```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

### 6. Connect MongoDB Compass

Open MongoDB Compass and connect to:

```
mongodb://localhost:27017
```

After the API starts, you will see the `iflow_dev` database with `users` and `user_sessions` collections.

## Authentication Flow

Authentication is fully cookie-based. The browser/client does not need to store or attach tokens manually.

1. **Login** (`POST /api/auth/google`) sets two HttpOnly cookies: `access_token` and `refresh_token`.
2. **Protected endpoints** (e.g. `GET /api/profile`) authenticate automatically via the `access_token` cookie.
3. **Refresh** (`POST /api/auth/refresh`) rotates both cookies transparently.
4. **Logout** (`POST /api/auth/logout`) revokes the session and clears both cookies.

An `Authorization: Bearer <token>` header is also accepted as fallback for development tools, but cookies take priority.

## API Endpoints

### Health Check

```
GET /api/health
```

**Response:**

```json
{ "status": "ok" }
```

### Beta Signup (allowlist enrollment)

The API runs in closed-beta mode by default (`ALLOWLIST_ENABLED=true`).
Only emails registered in the allowlist can log in with Google.

```
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@gmail.com",
  "signup_secret": "<BETA_SIGNUP_SECRET from .env.local>"
}
```

**Response:**

```json
{ "ok": true }
```

After signing up, the user can log in via the Google endpoint below.

To disable the allowlist and allow any Google email (open mode), set `ALLOWLIST_ENABLED=false` in your env vars.

### Google Login

```
POST /api/auth/google
Content-Type: application/json

{
  "id_token": "<google-id-token-from-frontend>"
}
```

**Response:**

```json
{ "ok": true }
```

Sets HttpOnly cookies: `access_token` and `refresh_token`.

### Refresh Token

```
POST /api/auth/refresh
```

The `refresh_token` cookie is sent automatically by the browser.

**Response:**

```json
{ "ok": true }
```

Both cookies are rotated automatically.

### Logout

```
POST /api/auth/logout
```

**Response:**

```json
{ "ok": true }
```

Revokes the session and clears both cookies.

### Get Profile (protected)

```
GET /api/profile
```

Authenticated via the `access_token` cookie (sent automatically by the browser).

**Response:**

```json
{
  "user": {
    "id": "665f...",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "avatar_url": "https://..."
  },
  "preferences": {
    "display_currency": "USD"
  },
  "exchange_rate": {
    "reference_date": "2026-03-05",
    "usd_to_ars_rate": 1450
  }
}
```

## Testing with Postman

Postman must be configured to preserve cookies across requests.

1. **Health**: `GET http://localhost:8000/api/health` -- no headers needed.
2. **Signup**: `POST http://localhost:8000/api/auth/signup` with JSON body `{ "email": "you@gmail.com", "signup_secret": "<BETA_SIGNUP_SECRET>" }`.
3. **Login**: `POST http://localhost:8000/api/auth/google` with JSON body `{ "id_token": "..." }`. Cookies are set automatically.
4. **Profile**: `GET http://localhost:8000/api/profile` -- Postman sends the `access_token` cookie automatically.
5. **Refresh**: `POST http://localhost:8000/api/auth/refresh` -- Postman sends the `refresh_token` cookie; both cookies are renewed.
6. **Logout**: `POST http://localhost:8000/api/auth/logout` -- both cookies are cleared.

## Running Tests

```bash
# Make sure MongoDB is running first
pytest tests/ -v
```

## Project Structure

```
src/
  main.py                          Application entry point
  core/
    config.py                      Settings via pydantic-settings
    db.py                          Motor client, connection, indexes
    log.py                         Logging configuration
    errors.py                      HTTP error helpers
    dependencies.py                FastAPI dependencies (auth guard)
    security/
      jwt.py                       Access token create / verify
      refresh_tokens.py            Refresh token generation
      hashing.py                   SHA-256 token hashing
      cookies.py                   HttpOnly cookie helpers
      objectid.py                  Pydantic v2 ObjectId type
  modules/
    auth/
      router.py                    Auth endpoints
      schemas.py                   Request / response models
      service.py                   Auth use-cases
      repository.py                MongoDB queries (users + sessions)
      allowlist_service.py         Signup + allowlist enforcement
      allowlist_repository.py      MongoDB queries (allowed_emails)
    profile/
      router.py                    Profile endpoint
      schemas.py                   Profile response models
      service.py                   Profile use-case
      repository.py                MongoDB queries (user lookup)
  shared/
    schemas.py                     Shared models (future)
    utils.py                       Shared utilities (future)
tests/
  test_health.py                   Health endpoint integration test
```
