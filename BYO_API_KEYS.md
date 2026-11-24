# Bring Your Own LLM API Key

This app lets each user choose OpenAI, Anthropic, or Google Gemini and provide their own API key for resume analysis. Provider settings open in a modal automatically when the page loads without a key, and can be reopened using the AI settings button beside Analyze resume. The key is held in JavaScript memory for the active page session only, not in browser storage or a server-side session.

## User Flow

1. Open the resume analysis page. If no key exists in this page session, the provider settings modal opens automatically.
2. Choose a provider: OpenAI, Anthropic, or Google Gemini.
3. Confirm or edit the suggested model name. The model must be available to the selected provider and enabled for the user's account.
4. Paste an API key created with that provider and save the settings. The password field is cleared after save; the key remains in a JavaScript variable for this page session.
5. Select a resume and submit it. Reopen AI settings beside Analyze resume to change provider/model or replace the key. Leaving the key field blank keeps the current page-session key.
6. The browser sends the extracted resume text, provider, model, and in-memory API key to `POST /analyze_resume` as JSON.
7. The Node development server forwards the request body unchanged. In a Vercel deployment, the request goes directly to the FastAPI route.
8. FastAPI validates the provider and required values, uses the key to construct one LangChain chat model, and reuses that model for extraction, cover-letter generation, job recommendations, and career advice.
9. The request returns analysis results. The key remains available for another analysis in the current page session and is discarded when the page is reloaded or closed.

## Provider Dependencies

The Python dependencies include one LangChain integration for each provider:

- `langchain-openai`
- `langchain-anthropic`
- `langchain-google-genai`

The provider values sent to the API are `openai`, `anthropic`, and `google_genai`. The model name is passed directly to LangChain's `init_chat_model`, so users can use any compatible model supported by the selected provider.

## Deployment

The app's own environment does not need `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` for resume analysis. Configure `JOOBLE_API_KEY` separately if job-search results are enabled. Install updated Python dependencies after deploying this change.

## Security and Privacy

- The API key is sent to this app's backend over the same-origin HTTPS connection in production, then used for provider requests. Never deploy this flow over plain HTTP.
- The backend does not intentionally persist or log the supplied API key. It is request data held in memory while the request runs; avoid adding request-body logging, tracing, or error reporting that captures it.
- The password input is cleared after the user saves settings. The page-session key remains in JavaScript memory so the user can run another analysis without re-entering it.
- Reloading or closing the page discards the in-memory key. Closing the page before a request completes does not provide a guarantee that the server has stopped processing that request.
- Resume text is sent to the selected AI provider. Users should review that provider's data-handling terms before submitting a resume.
- A browser extension or compromised device can read page input. A password field is masking, not a substitute for device security.
- A key may remain in browser-managed memory until the page is closed or reclaimed. The app does not persist it to browser storage.
- If a provider rejects a key or model, verify the key, provider selection, and model identifier with the provider. The key must never be copied into application logs or support messages.

## Operational Notes

The key is retained only in the active browser page's JavaScript memory, then included in each `/analyze_resume` request. It is not retained by the server between requests. This avoids relying on in-memory server session state, which is not reliable across Vercel serverless invocations. Reloading the page requires the user to enter the key again.
