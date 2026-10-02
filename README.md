# Frontend

Run the FastAPI backend on port 8000, then start the frontend proxy:

```sh
cd frontend
node server.js
```

Open <http://127.0.0.1:5173>. The frontend sends same-origin requests to `/analyze_resume`; `server.js` forwards them to `http://127.0.0.1:8000/analyze_resume`, avoiding browser CORS restrictions. Set `API_ORIGIN` to use a different backend address or `PORT` to change the frontend port.

The backend should accept a JSON body shaped like `{ "file": "resume text" }` and return JSON with `analysis` and `recommendations` fields. PDF and DOCX text extraction loads PDF.js and Mammoth from CDNs; TXT extraction works in the browser directly.