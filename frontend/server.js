const http = require("node:http");
const { readFile } = require("node:fs/promises");
const path = require("node:path");

const frontendDirectory = __dirname;
const apiOrigin = (process.env.API_ORIGIN || "http://127.0.0.1:8000").replace(/\/$/, "");
const port = Number(process.env.PORT || 5173);
const maxBodyBytes = 12 * 1024 * 1024;

async function readRequestBody(request) {
  const chunks = [];
  let totalBytes = 0;

  for await (const chunk of request) {
    totalBytes += chunk.length;
    if (totalBytes > maxBodyBytes) {
      const error = new Error("Request body is too large.");
      error.statusCode = 413;
      throw error;
    }
    chunks.push(chunk);
  }

  return Buffer.concat(chunks);
}

const server = http.createServer(async (request, response) => {
  const requestUrl = new URL(request.url, `http://${request.headers.host || "localhost"}`);

  if (request.method === "GET" && ["/", "/index.html"].includes(requestUrl.pathname)) {
    try {
      const html = await readFile(path.join(frontendDirectory, "index.html"));
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      response.end(html);
    } catch {
      response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      response.end("Could not load the frontend.");
    }
    return;
  }

  if (request.method === "POST" && requestUrl.pathname === "/analyze_resume") {
    try {
      const body = await readRequestBody(request);
      const apiResponse = await fetch(`${apiOrigin}/analyze_resume`, {
        method: "POST",
        headers: { "Content-Type": request.headers["content-type"] || "application/json" },
        body
      });
      const responseBody = Buffer.from(await apiResponse.arrayBuffer());
      response.writeHead(apiResponse.status, {
        "Content-Type": apiResponse.headers.get("content-type") || "application/json"
      });
      response.end(responseBody);
    } catch (error) {
      const statusCode = error.statusCode || 502;
      response.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
      response.end(JSON.stringify({ detail: statusCode === 413 ? error.message : `Could not reach the API at ${apiOrigin}.` }));
    }
    return;
  }

  response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  response.end("Not found.");
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Frontend available at http://127.0.0.1:${port}`);
  console.log(`API requests proxy to ${apiOrigin}/analyze_resume`);
});