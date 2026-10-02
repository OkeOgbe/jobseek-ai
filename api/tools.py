from langchain.tools import tool
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


@tool("recommend_jobs", description="Search Jooble for job postings matching the provided skills.")
def recommend_jobs(skills: list[str], location: str = "remote") -> dict:
    return fetch_jobs(skills, location)