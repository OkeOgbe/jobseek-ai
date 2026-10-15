from langchain.tools import tool
import json
import os
import requests

def fetch_jobs(skills: str | list[str], location: str = "remote") -> dict:
    api_key = os.getenv("JOOBLE_API_KEY")
    if not api_key:
        raise ValueError("JOOBLE_API_KEY is not configured.")

    keywords = ", ".join(skills) if isinstance(skills, list) else skills
    response = requests.post(
        f"https://jooble.org/api/{api_key}",
        json={"keywords": keywords, "location": location},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


@tool(
    "recommend_jobs",
    description="Search Jooble for job postings matching the provided skills.",
    response_format="content_and_artifact",
)
def recommend_jobs(skills: list[str], location: str = "remote") -> tuple[str, dict]:
    payload = fetch_jobs(skills, location)
    # The model sees a trimmed summary; the raw payload is kept as the artifact for the API response
    summary = [
        {
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "snippet": job.get("snippet"),
            "link": job.get("link"),
        }
        for job in payload.get("jobs", [])
    ]
    return json.dumps(summary), payload