from fastapi import FastAPI
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from fastapi import HTTPException
from tools import fetch_jobs
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tools import recommend_jobs
import requests
import json
import re

load_dotenv()

app = FastAPI()

class Resume(BaseModel):
    file: str


class JobSearch(BaseModel):
    skills: list[str] = Field(min_length=1)
    location: str = "remote"


def get_jobs(skills: str | list[str], location: str = "remote") -> dict:
    try:
        return fetch_jobs(skills, location)
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail="The Jooble job search request failed.") from error


@app.post("/jobs")
def search_jobs(search: JobSearch):
    return get_jobs(search.skills, search.location)



@app.post("/analyze_resume")
def analyze_resume(resume: Resume):

    print("Analyzing resume file and extracting relevant information...")

    chat_model = init_chat_model(
        model="gpt-4.1-mini",
        temperature=0.7,
    )

    extracted_info = chat_model.invoke(
        "Analyze this resume and return valid JSON with a 'skills' array of concise job-search keywords "
        "and an 'experience' summary:\n\n"
        f"{resume.file}"
    )

    response = extracted_info.content
    response_text = response if isinstance(response, str) else str(response)
    fenced_json = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", response_text, flags=re.DOTALL | re.IGNORECASE)
    if fenced_json:
        response_text = fenced_json.group(1).strip()

    try:
        extracted_profile = json.loads(response_text)
        if not isinstance(extracted_profile, dict):
            extracted_profile = {}
    except (json.JSONDecodeError, TypeError):
        extracted_profile = {}

    search_skills = extracted_profile.get("skills", [])
    if isinstance(search_skills, str):
        search_skills = [search_skills]
    if not isinstance(search_skills, list):
        search_skills = []
    experience = extracted_profile.get("experience", "")
    if not isinstance(experience, str):
        experience = str(experience)

    jobs_payload = get_jobs([str(skill) for skill in search_skills])
    jobs_for_prompt = [
        {
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "snippet": job.get("snippet"),
            "link": job.get("link"),
        }
        for job in jobs_payload.get("jobs", [])
    ]

    print("Extracted information from resume:", extracted_info)
    print("Formatted extracted information:", extracted_info.content)

    # Analyze the resume file and extract relevant information
    # Use the extracted information to create an agent that can fetch relevant job postings and provide personalized recommendations to the user
    

    print("Creating an agent to fetch relevant job postings and provide personalized recommendations...")
    agent = create_agent(
        model="gpt-5",
        tools=[recommend_jobs],
        system_prompt=f"You are a helpful assistant that explains why job postings fit a candidate. Candidate skills and experience: {search_skills}; {experience}",
    )

    # Use the agent to fetch relevant job postings and provide personalized recommendations to the user.
    agent_response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"Use these Jooble postings to recommend suitable jobs. Do not invent postings. If no jobs match, say so.\n{jobs_for_prompt}"
            },
        ]
    })

    print("Skills response:", search_skills)

    return {
        "recommendations": agent_response['messages'][-1].content, 
        "skills": search_skills,
        "experience": experience,
        "jobs": jobs_payload,
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to the Job Recommendation API. Use the /analyze_resume endpoint to analyze a resume and get personalized job recommendations."}