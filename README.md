# CodeAlpha FAQ Chatbot

An authenticated Cloudify FAQ chatbot. Gemini creates 3072-dimensional embeddings, Qdrant Cloud retrieves the shared FAQ knowledge records, and Groq produces cited answers that are checked against retrieved evidence. PostgreSQL stores users and private conversation history. FAQ vectors are global and never scoped to a user.

## Architecture

```text
faqs.json -> Gemini gemini-embedding-001 -> dedicated Qdrant Cloud collection
Question -> Gemini query embedding -> top 5 cosine retrieval (threshold .50)
         -> Groq structured JSON -> citation validation -> Groq evidence check
         -> PostgreSQL conversation/messages -> React chat with FAQ sources
```

The project uses a modular FastAPI and React/Vite layout adapted to FAQ records and user-owned conversations. It does not upload or process PDFs.

## Requirements

- Python 3.11 or newer
- Node.js 22 and npm
- PostgreSQL 15+
- Qdrant Cloud cluster credentials
- Gemini API key and Groq API key

## Windows PowerShell setup

From the project root:

```powershell
python --version
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If `python` is not recognized, install Python 3.11+ and enable “Add Python to PATH”, open a new PowerShell session, and retry. If the `py` launcher is installed, `py -3.11 -m venv .venv` also works.

Set the variables below in `.env`. Create a separate PostgreSQL database named `codealpha_faq_db`; do not use Study-Buddy's database. Reuse the Qdrant Cloud cluster but set the collection to `codealpha_faq_knowledge_base`. Generate a JWT secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

| Variable | Purpose |
|---|---|
| `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Signed bearer tokens and expiry |
| `DATABASE_URL` | Dedicated PostgreSQL connection (`postgresql+psycopg://...`) |
| `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION_NAME` | Qdrant Cloud and isolated FAQ collection |
| `GEMINI_API_KEY`, `GEMINI_EMBEDDING_MODEL`, `GEMINI_EMBEDDING_DIMENSIONS` | Gemini model `gemini-embedding-001`, 3072 dimensions |
| `GROQ_API_KEY`, `GROQ_MODEL` | Groq generation; default model `openai/gpt-oss-120b` |
| `RETRIEVAL_TOP_K`, `RETRIEVAL_SCORE_THRESHOLD` | Defaults 5 and 0.50; cosine score higher is better |
| `CORS_ALLOWED_ORIGINS`, `BACKEND_API_URL`, `VITE_API_BASE_URL` | Browser and development routing |

## Migrations and FAQ ingestion

With PostgreSQL running and `DATABASE_URL` set:

```powershell
python -m alembic upgrade head
python -m app.ingest
```

Ingestion uses deterministic FAQ IDs, upserts records, and removes stale points only from the dedicated collection. It never deletes or recreates Study-Buddy's collection. Optional `category` metadata is retained only if present in the FAQ JSON. For future schema changes:

```powershell
python -m alembic revision --autogenerate -m "describe change"
python -m alembic upgrade head
```

## Run locally

Terminal 1, backend:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2, frontend:

```powershell
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`. API docs: `http://127.0.0.1:8000/docs`; readiness: `GET /api/health`. Build the frontend using `npm run build`; FastAPI serves `dist/` when present.

## API

- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `POST /api/conversations`, `GET /api/conversations`, `GET /api/conversations/{id}`, `DELETE /api/conversations/{id}`
- `POST /api/conversations/{id}/chat` with `{"message":"How do I create an account?"}`
- `GET /api/health`

Protected routes require `Authorization: Bearer <access_token>`. Chat returns `answer`, `conversation_id`, and FAQ sources with IDs, original questions, and retrieval scores. Conversation access always checks ownership; citations are persisted with assistant messages.

## Tests and Docker

```powershell
python -m pytest -q
npm run build
docker build -t codealpha-faq .
docker run --env-file .env -p 8000:8000 codealpha-faq
```

Tests mock Gemini, Qdrant, and Groq. The container applies migrations at startup and expects external PostgreSQL and Qdrant Cloud services; it contains no credentials.

## Security and troubleshooting

- Keep `.env`, API keys, JWT secrets, local database files, `node_modules/`, and `dist/` out of GitHub.
- For chat service errors, inspect Gemini, Qdrant, and Groq configuration and backend logs.
- The Qdrant collection must use a dense 3072-dimensional cosine vector. The service validates this and stops if it differs.
- Tune the 0.50 similarity threshold against the FAQ dataset if relevant questions are rejected.
- PostgreSQL must be reachable before migrations and database endpoints work.
- Do not point this app to Study-Buddy's PostgreSQL database or PDF vector collection.
