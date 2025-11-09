from django.shortcuts import render, redirect
from fake_useragent import UserAgent
import requests, http.client, urllib.parse, json
from bs4 import BeautifulSoup
from datetime import datetime
from resumes.models import Resume, parsed_data
from matching.models import MatchResult, SavedJobs
from django.http import HttpResponse, JsonResponse
from .models import JobListing
from django.contrib.auth import get_user_model
from google import genai
import re, json,  asyncio, aiohttp
from asgiref.sync import sync_to_async
from django.db.models import Exists, OuterRef, Value, BooleanField

client = genai.Client(api_key="AIzaSyAd4rplAifue8VyRpz6NGoqmcHMIXFEKtw")

# Create your views here.

def job_listing(request):
    saved_jobs_subquery = SavedJobs.objects.filter(
        user=OuterRef('user'),
        job=OuterRef('job'),
        resume=OuterRef('resume')
    )
    match = MatchResult.objects.prefetch_related('job', 'resume', 'user').annotate(is_saved=Exists(saved_jobs_subquery)).filter(user=request.user, status='1', resume__status='2')
    
    return render(request,'jobs/job_list.html' , {'match':match})
def job_details(request, id):
    saved_jobs_subquery = SavedJobs.objects.filter(
        user=OuterRef('user'),
        job=OuterRef('job'),
        resume=OuterRef('resume')
    )
    job = MatchResult.objects.prefetch_related('job', 'resume', 'user').annotate(is_saved=Exists(saved_jobs_subquery)).get(user=request.user, job_id=id, status='1', resume__status='2')
    
    return render(request,'jobs/job_detail.html' , {'job':job})

def save_jobs(request, id, resume_id):
    job = MatchResult.objects.select_related('job','resume').get(job_id=id, user=request.user, resume_id=resume_id, status='1')
    saveJob = SavedJobs()
    saveJob.user = request.user
    saveJob.job = job.job
    saveJob.resume = job.resume
    saveJob.save()
    return redirect('job_listing')

def remove_save_jobs(request, id, resume_id):
    job = SavedJobs.objects.get(job_id=id, user=request.user, resume_id=resume_id)
    job.delete()
    return redirect('job_listing')

def dismiss_jobs(request, id, resume_id):
    job = SavedJobs.objects.filter(job_id=id, user=request.user, resume_id=resume_id)
    if job:
        job.delete()

    match = MatchResult.objects.get(job_id=id, user=request.user, resume_id=resume_id)
    match.status = '5'
    match.save()
    return redirect('job_listing')
async def fetch_jobs_for_tag(session, tag):
    """Async call to RapidAPI JSearch."""
    encoded_tag = urllib.parse.quote_plus(tag)
    url = f"https://jsearch.p.rapidapi.com/search?query={encoded_tag}&country=in&date_posted=month"
    headers = {
        'x-rapidapi-key': "8088a3533emsh2ac002464b519d0p1131d0jsn7ef68b0c0553",
        'x-rapidapi-host': "jsearch.p.rapidapi.com"
    }

    async with session.get(url, headers=headers) as response:
        data = await response.json()
        return data.get('data', [])

async def parse_with_gemini(description):
    """Async Gemini job info extractor."""
    prompt = f"""
    You are a professional job information extractor.
    From the job description below, extract and return only a valid JSON object with these exact fields:

    {{
    "skills": [],
    "experience_year": ""
    }}

    Rules:
    - "skills" must be an array of relevant technical and soft skills (e.g., ["Python", "Django", "REST APIs"]).
    - "experience_year" must capture any mentioned experience requirement (e.g., "2+ years", "Minimum 3 years", "Fresher", etc.).
    - If no experience is mentioned, set "experience_year": "Not specified".

    Job Description:
    {description}

    Return only valid JSON — no markdown, no explanations.
    """

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text.strip()
        if not text:
            raise ValueError("Llama parser returned empty result")

        # 5️⃣ Clean JSON-safe
        skills_str = re.sub(r'(?i)^json\s*', '', str(text).strip())
        match = re.search(r'\{[\s\S]*\}', skills_str)
        if match:
            skills_str = match.group(0)

        if match:
            structured = json.loads(skills_str)
            return structured.get("skills", []), structured.get("experience_year", "Not specified")

    except Exception as e:
        print(f"⚠️ Gemini parse failed: {e}")

    return [], "Not specified" 
async def async_scrape_logic():
    """Main async logic for scraping."""
    parsed_resumes = await sync_to_async(list)(parsed_data.objects.all())

    async with aiohttp.ClientSession() as session:
        for res in parsed_resumes:
            job_list = await fetch_jobs_for_tag(session, res.tag)
            print(f"✅ Found {len(job_list)} jobs for {res.tag}")

            for job in job_list:
                exists = await sync_to_async(JobListing.objects.filter(j_id=job["job_id"]).exists)()
                if exists:
                    continue

                # Parse job details with Gemini
                skills, experience_year = await parse_with_gemini(job.get("job_description", ""))

                # Save job to DB
                await sync_to_async(JobListing.objects.create)(
                    j_id=job.get("job_id"),
                    title=job.get("job_title"),
                    company=job.get("employer_name"),
                    location=job.get("job_location", "India"),
                    description=job.get("job_description"),
                    experience_year=experience_year,
                    skills=skills,
                    source=job.get("job_publisher", ""),
                    source_url=job.get("job_google_link", ""),
                    remote=job.get("job_is_remote", False),
                    salary=job.get("job_salary_period", ""),
                    apply_url=job.get("job_apply_link"),
                    date_posted=datetime.fromisoformat(
                        job.get("job_posted_at_datetime_utc").replace("Z", "+00:00")
                    ) if job.get("job_posted_at_datetime_utc") else None,
                )

                # Throttle to avoid hitting RPM limit
                await asyncio.sleep(3)

    return {"status": "✅ Job scraping and parsing complete"}


def scrape_jobs_for_resume(request):
    """Synchronous Django view that runs async logic."""
    try:
        result = asyncio.run(async_scrape_logic())
        return JsonResponse(result)
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)   

# def scrape_jobs_for_resume(request):
#     """
#     Scrape Indeed for jobs relevant to extracted resume skills & role.
#     """
    

    

#     jobs = []
#     parsed_resumes = parsed_data.objects.all()
    

#     for res in parsed_resumes:

#         skills = res.skills
#         query = f"{res.tag}"
#         query = urllib.parse.quote_plus(f"{query}")
        
#         conn = http.client.HTTPSConnection("jsearch.p.rapidapi.com")

#         headers = {
#             'x-rapidapi-key': "8088a3533emsh2ac002464b519d0p1131d0jsn7ef68b0c0553",
#             'x-rapidapi-host': "jsearch.p.rapidapi.com"
#         }

#         conn.request("GET", f"/search?query={query}&country=in&date_posted=month", headers=headers)
#         # conn.request("GET", f"/search?query=Python+developers+in+Kolkata&country=in&date_posted=month", headers=headers)

#         res = conn.getresponse()
#         data = res.read()  # limit top 5 skills for query
#         job_json = data.decode('utf-8')
#         jobs = json.loads(job_json) if isinstance(job_json, str) else job_json
#         jobList = jobs['data']

#         # Check for duplicates
#         if not jobList:
#             raise ValueError("⚠️ No jobs found in API response.")
#         else:    
#             for job in jobList:
#                 if JobListing.objects.filter(j_id=job["job_id"]).exists():
#                     continue
                    

#                 # Extract skills safely from the job_description
#                 skills = job.get("job_description", "").lower().split(",")
#                 skills = [s.strip() for s in skills if len(s.strip()) > 2]

#                 prompt = f"""
#                 You are a professional job information extractor.
#                 From the job description below, extract and return only a valid JSON object with these exact fields:

#                 {{
#                 "skills": [],
#                 "experience_year": ""
#                 }}

#                 Rules:
#                 - "skills" must be an array of relevant technical and soft skills (e.g., ["Python", "Django", "REST APIs"]).
#                 - "experience_year" must capture any mentioned experience requirement (e.g., "2+ years", "Minimum 3 years", "Fresher", etc.).
#                 - If no experience is mentioned, set "experience_year": "Not specified".

#                 Job Description:
#                 {job.get("job_description")}

#                 Return only valid JSON — no markdown, no explanations.
#                 """

#                 try:
#                     response = client.models.generate_content(
#                         model="gemini-2.5-flash", contents=prompt
#                     )
                    
#                     # print("🧾 raw response:", response.text)

                    
                    

#                     # Try parsing as JSON:
#                     skills_str = response.text
                    
#                 except Exception as e:
#                     print("⚠️ Gemini parsing failed:", e)
#                     return None
                
#                 if not skills:
#                     raise ValueError("Llama parser returned empty result")

#                 # 5️⃣ Clean JSON-safe
#                 skills_str = re.sub(r'(?i)^json\s*', '', str(skills_str).strip())
#                 match = re.search(r'\{[\s\S]*\}', skills_str)
#                 if match:
#                     skills_str = match.group(0)

#                 try:
#                     structured = json.loads(skills_str)
#                 except Exception as e:
#                     print("⚠️ JSON decode failed:", e)
#                     print("Raw structured_str:", skills_str[:300])
#                     structured = {}

#                 skills = structured.get("skills", [])
#                 experience_year = structured.get("experience_year", "Not specified")    


#                 # Create record
#                 JobListing.objects.create(
#                     j_id = job.get("job_id"),
#                     title=job.get("job_title"),
#                     company=job.get("employer_name"),
#                     location=job.get("job_location", "India"),
#                     description=job.get("job_description"),
#                     experience_year = experience_year,
#                     skills=skills,
#                     source=job.get("job_publisher", ""),
#                     source_url=job.get("job_google_link", ""),
#                     remote=job.get("job_is_remote", False),
#                     salary=job.get("job_salary_period", ""),
#                     apply_url=job.get("job_apply_link"),
#                     date_posted=datetime.fromisoformat(job.get("job_posted_at_datetime_utc").replace("Z", "+00:00"))
#                         if job.get("job_posted_at_datetime_utc") else None,
#                 )

        

    
#     return HttpResponse(jobList)
