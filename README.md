# Cloudify FAQ Chatbot — Retrieval-Augmented Generation

A web-based FAQ assistant that retrieves relevant entries from a Cloudify knowledge base with semantic vector search, then uses a language model to generate a grounded answer. The project uses **Gemini Embeddings**, **Qdrant**, **Groq**, and **FastAPI**.

## How the RAG pipeline works

1. **Knowledge ingestion:** FAQ question-and-answer pairs are loaded from `faqs.json`.
2. **Embedding generation:** Gemini's `gemini-embedding-001` model converts each FAQ entry into a 768-dimensional vector. The question and answer are embedded together so retrieval can use both.
3. **Vector storage:** Vectors and their original FAQ text are stored in a Qdrant collection with source metadata.
4. **Query embedding:** A user's question is embedded with the retrieval-query task type.
5. **Semantic retrieval:** Qdrant returns the top matching FAQ entries using cosine similarity and a configurable score threshold.
6. **Grounded generation:** The retrieved entries are added to a constrained prompt and sent to Groq. The model is instructed to answer only from the supplied context.
7. **Source display:** The API returns the generated answer and the retrieved FAQ questions with similarity scores. The browser displays those sources below the answer.

```text
                         OFFLINE / STARTUP INGESTION
 faqs.json -> Gemini document embeddings -> Qdrant vector collection
                                                    |
                                                    |
                         ONLINE QUESTION FLOW      |
 User -> FastAPI -> Gemini query embedding -> Qdrant semantic search
                                              |
                                      Retrieved FAQ context
                                              |
                                      Groq chat completion
                                              |
                                 Answer + retrieved sources
                                              |
                                         Web UI
```

This is a RAG application: the language model receives context retrieved from an external knowledge base at question time. It is not fine-tuned on the FAQ data.

## Features

- Semantic FAQ retrieval using Gemini embeddings and Qdrant.
- Context-grounded answer generation using Groq.
- Similarity threshold and configurable top-k retrieval.
- Source references and retrieval similarity scores in the chat UI.
- Fallback response when no FAQ entry passes the retrieval threshold.
- FastAPI request validation and health endpoint.
- Responsive chat interface with light/dark theme.
- Qdrant Cloud support and local persistent Qdrant mode for development.

## Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| API | FastAPI + Pydantic | HTTP endpoint and request/response validation |
| Embeddings | Gemini `gemini-embedding-001` | Convert FAQ text and questions into vectors |
| Vector database | Qdrant | Store vectors and retrieve similar FAQ entries |
| Generation | Groq | Generate answers grounded in retrieved context |
| Frontend | HTML, CSS, JavaScript | Chat interface and source display |
| Server | Uvicorn | Run the FastAPI application |

## Project structure

```text
.
├── app.py                 # FastAPI app, startup indexing, chat and health endpoints
├── rag_service.py         # Embedding, Qdrant retrieval, and Groq generation
├── faqs.json              # Source FAQ knowledge base
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── static/
│   ├── index.html         # Chat interface
│   ├── script.js          # API calls and source rendering
│   └── styles.css         # Responsive styling
├── run_server.bat         # Windows server shortcut
└── run_cli.bat            # Legacy CLI shortcut (see note below)
```

The original TF-IDF implementation has been replaced in the web application. The old `chatbot.py` and `cli.py` files are retained as historical examples and are not used by the RAG API.

## Prerequisites

- Python 3.10+
- A Gemini API key
- A Groq API key
- Qdrant Cloud cluster (recommended for deployment), or local Qdrant storage for development

## Local setup (Windows)

Clone the repository and enter the folder:

```powershell
git clone https://github.com/vayugautam/CodeAlpha_Chatbot_for_FAQs.git
cd CodeAlpha_Chatbot_for_FAQs
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Add your real API keys to `.env`. Never commit this file.

For a local Qdrant database, leave `QDRANT_URL` and `QDRANT_API_KEY` empty. The vector database is persisted in `./data/qdrant`.

Start the app:

```powershell
python app.py
```

Open [http://localhost:8000](http://localhost:8000). On startup, the application embeds the FAQ entries and indexes them into Qdrant. The first start and each restart can make Gemini embedding API calls.

## Qdrant Cloud configuration

Create a Qdrant Cloud cluster and set these values in `.env`:

```env
QDRANT_URL=https://YOUR-CLUSTER-URL
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=cloudify_faq_knowledge
```

Use the Qdrant cluster URL and API key from your Qdrant dashboard. Do not put credentials in source code.

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Gemini embedding API authentication |
| `GROQ_API_KEY` | Yes | — | Groq generation API authentication |
| `QDRANT_URL` | No | Local mode | Qdrant Cloud URL |
| `QDRANT_API_KEY` | For Cloud | — | Qdrant Cloud authentication |
| `QDRANT_COLLECTION` | No | `cloudify_faq_knowledge` | Collection name |
| `QDRANT_LOCAL_PATH` | No | `./data/qdrant` | Local persistent database path |
| `GEMINI_EMBEDDING_MODEL` | No | `gemini-embedding-001` | Embedding model |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Generation model |
| `RETRIEVAL_TOP_K` | No | `4` | Maximum FAQ matches sent to the LLM |
| `RETRIEVAL_SCORE_THRESHOLD` | No | `0.35` | Minimum Qdrant similarity score |
| `PORT` | No | `8000` | Web server port |

## API

### `GET /health`

Returns application status and the number of indexed FAQ entries.

### `POST /api/chat`

Request:

```json
{
  "message": "How long are backups retained?"
}
```

Response shape:

```json
{
  "reply": "Generated answer grounded in retrieved FAQ context [1].",
  "sources": [
    {
      "id": 1,
      "question": "How long are backups retained?",
      "source": "faqs.json",
      "score": 0.82
    }
  ],
  "retrieval_count": 1
}
```

The numeric score is a vector similarity score, not a probability or a measure of answer correctness.

## Updating the knowledge base

Edit `faqs.json` using this structure:

```json
{
  "question": "Your question?",
  "answer": "The factual answer."
}
```

Restart the application to rebuild the Qdrant collection from the updated file. The startup indexing process replaces the points in the configured collection, so use a dedicated collection for this project.

## Limitations and possible improvements

- The current knowledge base contains a small set of FAQ records; larger document sources would need chunking and metadata-aware ingestion.
- Startup indexing embeds all FAQ entries again. A production ingestion pipeline should detect changed records and update only those vectors.
- Retrieval uses a single dense-vector search. Hybrid search, reranking, and retrieval evaluation could improve quality.
- The score threshold is a configurable heuristic and should be tuned against a representative evaluation set.
- The current chat endpoint is stateless and does not retain conversation history.
- API usage, latency, and cost should be monitored before production deployment.

## Security

- Store API keys in environment variables or your hosting provider's secret manager.
- Keep `.env`, local vector storage, and logs out of version control.
- Do not expose API keys in frontend JavaScript.
- Apply rate limiting and authentication before exposing a public production endpoint.

## License

This project was created for an FAQ chatbot task and subsequently upgraded to demonstrate a RAG architecture.
