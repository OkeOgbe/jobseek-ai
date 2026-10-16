from fastapi import FastAPI
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import ToolMessage
from fastapi import HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import requests
import json
import re

try:
    from .tools import fetch_jobs, recommend_jobs
except ImportError:
    from tools import fetch_jobs, recommend_jobs

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

    model = init_chat_model(
        model="gpt-4.1-mini",
        temperature=0.7,
    )

    # Create different chains to extract skills and experience from the resume and generate a cover letter using extracted info from chain 1 
    # Chain 1: Extract the skills and experience from the resume
    # Chain 2: Generate a comprehensive cover letter for job application 

    extraction_prompt = PromptTemplate.from_template(
        "Analyze this resume and return valid JSON with a 'skills' array of concise job-search keywords "
        "and an 'experience' summary:\n\n"
        "{resume}"
    )

    extraction_chain = (
        extraction_prompt | model | JsonOutputParser()
    )

    cover_letter_prompt = PromptTemplate.from_template(
        "Generate a comprehensive cover letter for a job application based on the extracted skills and "
        "experience below. The cover letter should NOT be more than 200 words and should be tailored to the "
        "job search keywords and highlight the candidate's relevant experience:\n\n"
        "{profile}"
    )

    cover_letter_chain = (
        cover_letter_prompt | model | StrOutputParser()
    )

    final_chain = RunnablePassthrough.assign(profile=extraction_chain) | RunnablePassthrough.assign(cover_letter=cover_letter_chain)

    skills_and_cover_letter = final_chain.invoke({"resume": resume.file})

    skills = skills_and_cover_letter["profile"]["skills"]
    experience = skills_and_cover_letter["profile"]["experience"]
    cover_letter = skills_and_cover_letter["cover_letter"]
   
    print("Extracted skills from resume:", skills)
    print("Extracted experience summary: ", experience)
    print("Generated cover letter", cover_letter)

    # New Agent Task: Get desired salary from request body, find similar jobs in the industry that pay that salary and more and display the role and roadmap to get there (with top linkedin profiles in the field)  
    # Use the extracted information to create an agent that can fetch relevant job postings and provide personalized recommendations to the user
    

    print("Creating an agent to fetch relevant job postings and provide personalized recommendations...")
    agent = create_agent(
        model="gpt-5",
        tools=[recommend_jobs],
        system_prompt=f"You are a helpful assistant that scouts and fetches suitable job postings for candidates based on their skill and experience. Candidate skills and experience: {skills}; {experience}",
    )

    # Use the agent to fetch relevant job postings and provide personalized recommendations to the user.
    agent_response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"Use the recommend_jobs tool to fetch suitable jobs for the candidate from Jooble based on their skillset and experience, minimum of 50 job postings except results are not up to that but do NOT invent postings. If no jobs match, say so. Do not ask any follow up questions"
            },
        ]
    })

    # Separate agent call so the career options come back as their own response
    career_agent = create_agent(
        model="gpt-5",
        tools=[],
        system_prompt=f"You are a career advisor who suggests higher-paying career paths a candidate can move into from their current background. Candidate skills and experience: {skills}; {experience}",
    )

    career_response = career_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "Search the internet for similar career options that the candidate can switch to in search of higher pay (include the average annual salary of a junior in the field) and how they can get started from their current skillset. Maximum 10. Do not ask any follow up questions"
            },
        ]
    })

    # Collect the real postings from the recommend_jobs tool calls, deduplicated by link
    jobs = []
    seen_links = set()
    for message in agent_response["messages"]:
        if isinstance(message, ToolMessage) and message.name == "recommend_jobs" and isinstance(message.artifact, dict):
            for job in message.artifact.get("jobs", []):
                link = job.get("link")
                if link in seen_links:
                    continue
                if link:
                    seen_links.add(link)
                jobs.append(job)


    return {
        "career_options": career_response["messages"][-1].content,
        "cover_letter": cover_letter,
        "skills": skills,
        "experience": experience,
        "jobs": {"jobs": jobs},
    }

# Kept off "/" so it doesn't shadow public/index.html on Vercel
@app.get("/health")
def read_root():
    return {"message": "Welcome to the Job Recommendation API. Use the /analyze_resume endpoint to analyze a resume and get personalized job recommendations."}