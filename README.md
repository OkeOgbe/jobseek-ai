# NextStep

## Run locally

Start the FastAPI backend from `api/`:

```sh
cd api
fastapi dev main.py
```

In another terminal, from the repository root:

```sh
node server.js
```

Open <http://127.0.0.1:5173>. Locally, the Node server proxies `POST /analyze_resume` to `http://127.0.0.1:8000` by default. Set `API_ORIGIN` if the local API uses another origin.

## Deploy to Vercel

Deploy the repository root as one project. Vercel detects the root `main.py` FastAPI entrypoint, and the root `requirements.txt` declares Python dependencies. The frontend posts to the same-origin `/analyze_resume` path, so the deployed request goes directly to the FastAPI app; do not set `API_ORIGIN` to the Vercel project's own URL.

Set these environment variables in Vercel Project Settings:

- `OPENAI_API_KEY` for resume analysis and recommendations.
- `JOOBLE_API_KEY` for job search results.

The resume endpoint accepts `POST /analyze_resume` with JSON shaped like `{"file":"extracted resume text"}`. Opening the route directly in a browser sends `GET`, so use the frontend form or send a POST request.
