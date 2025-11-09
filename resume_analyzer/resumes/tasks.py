from celery import shared_task
from .models import Resume, parsed_data
from jobs.models import JobListing
from matching.models import MatchResult, SavedJobs
from matching.utils import *
from django.utils import timezone
import  docx, re, spacy, json, os, fitz
from google import genai
from decouple import config

# Load NLP model (only once)
nlp = spacy.load("en_core_web_sm")
client = genai.Client(api_key="AIzaSyAd4rplAifue8VyRpz6NGoqmcHMIXFEKtw")
TOP_N = 10
THRESHOLD_PCT = 10.0 

# ---------------------------------------------------
# 🧹 CLEANING HELPERS
# ---------------------------------------------------
def clean_string(s):
    """Remove control characters, null bytes, and invalid unicode."""
    if not isinstance(s, str):
        return s
    s = s.encode("utf-8", "ignore").decode("utf-8", "ignore")
    s = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)  # remove control chars
    s = s.replace('\u0000', '')  # remove null characters
    return s.strip()


def clean_json_data(value):
    """Recursively clean all strings inside lists/dicts for JSONFields."""
    if isinstance(value, str):
        return value.replace("\x00", "").replace("\u0000", "")
    elif isinstance(value, list):
        return [clean_json_data(v) for v in value]
    elif isinstance(value, dict):
        return {k: clean_json_data(v) for k, v in value.items()}
    else:
        return value


# ---------------------------------------------------
# 🧾 FILE TEXT EXTRACTION
# ---------------------------------------------------
def extract_text_from_pdf(file_path):
    """Extract text from PDF files safely page by page."""
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                # Extract text directly from page
                page_text = page.get_text("text") or ""
                text += page_text + "\n"
    except Exception as e:
        print(f"⚠️ Error reading PDF: {e}")
        return ""

    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    # Deep clean
    text = text.replace("\x00", "").replace("\u0000", "")
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX files paragraph by paragraph."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception:
        return ""

def parse_resume_with_gemini(cleaned_text: str):
   
    prompt = f"""
    You are a professional resume parser. 
    Extract and return a valid JSON object with these exact fields:
    {{
        "fullname": "",
        "emails": [],
        "phones": [],
        "skills": [],
        "education": [{{"degree": "", "institution": "", "year": ""}}],
        "experience_years": float number,
        "summary": "",
        "keywords":[],
        "tag": ""  // This should be the best-matching job role such as "Backend Developer", "Frontend Developer", "Full Stack Developer", "DevOps Engineer", "Data Scientist", etc.
    }}

    Resume Text:
    {cleaned_text}
    Return only valid JSON.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        
        # print("🧾 raw response:", response.text)

        
        

        # Try parsing as JSON:
        result = response.text
        return result
    except Exception as e:
        print("⚠️ Gemini parsing failed:", e)
        return None

def compute_matches_for_resume(resume_id):
    """
    Compute top-N matches for a single parsed_data instance (resume).
    Saves MatchResult entries for those >= THRESHOLD_PCT.
    """
    try:
        parsed = parsed_data.objects.select_related('resume_id__user_id').filter(resume_id_id=resume_id)
    except parsed_data.DoesNotExist:
        return

    # Fetch candidate jobs (all or filtered). To optimize, filter by date or tag if available:
    # If parsed.tag exists, narrow by job title containing tag for relevancy
    for p in parsed:
        if getattr(p, 'tag', None):
            jobs_qs = JobListing.objects.filter(title__icontains=p.tag)
        else:
            jobs_qs = JobListing.objects.all()

        # Preload into memory (could be chunked for large DBs)
        job_list = list(jobs_qs)
        if not job_list:
            return

        job_ids, job_texts = build_job_corpus(job_list)
        resume_text = resume_to_text(p)
        sims = compute_tfidf_scores(resume_text, job_texts)  # numpy array

        # compute combined scores
        resume_skills = safe_load_skills(p.skills)
        print(resume_skills)
        resume_exp = p.experience_years
        
        scored = []
        for idx, job in enumerate(job_list):
            tfidf_score = float(sims[idx])
            job_skills = safe_load_skills(job.skills)
            job_exp_text = getattr(job, "experience_year", "")
            job_exp = extract_numeric_experience(job_exp_text)
            # print(job_skills)
            overlap = compute_skill_overlap(resume_skills, job_skills)
            if job_exp == 0.0:  # job didn’t specify experience
                exp_score = 1.0
            else:
                exp_score = max(0.0, 1 - abs(resume_exp - job_exp) / max(job_exp, 1.0))

            score = combine_scores(tfidf_score, overlap)
            final_score = (0.6 * score) + (0.4 * exp_score)
            score_pct = round(final_score * 100.0, 2)
            scored.append((job, job_skills, job_exp, score_pct, tfidf_score, overlap))

        # pick top N by score_pct
        scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)[:TOP_N]

        results = []
        for job, job_skills, job_exp, score_pct, tfidf_score, overlap in scored_sorted:
            if score_pct >= THRESHOLD_PCT:
                
                details = {
                    "overlapping_skills": list(set(resume_skills) & set(job_skills)),
                    "missing_skills": list(set(job_skills) - set(resume_skills)),
                    "reasons": [
                        f"tfidf:{tfidf_score:.3f}",
                        f"skill_overlap:{overlap:.3f}"
                    ]
                }
                # Upsert MatchResult for idempotency
                obj, created = MatchResult.objects.update_or_create(
                    user=p.resume_id.user_id,
                    resume=p.resume_id,
                    job=job,
                    defaults={
                        "match_score": score_pct,
                        "details": details
                    }
                )
                results.append((obj, created))
    # Return count for logging
    return scored_sorted

# ---------------------------------------------------
# 🧠 CELERY TASK: PARSE RESUME
# ---------------------------------------------------
@shared_task
def parse_resume_task(resume_id):
    """
    Celery task to extract and parse resume contents.
    Steps:
    1. Extract text from file (PDF/DOCX)
    2. Clean text from broken unicode
    3. Validate that it's a resume
    4. Use Ollama to extract basic fields
    5. Save parsed data in parsed_data model
    6. Update resume status (0=uploaded, 1=processing, 2=done, 5=failed)
    """
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        print(f"❌ Resume ID {resume_id} not found.")
        return

    resume.status = '1'  # Processing
    resume.save()

    # print(resume)

    try:
        # 1️⃣ Extract raw text
        if resume.file.name.endswith('.pdf'):
            text = extract_text_from_pdf(resume.file.path)
        elif resume.file.name.endswith('.docx'):
            text = extract_text_from_docx(resume.file.path)
        else:
            resume.status = '5'  # Unsupported file type
            resume.save()
            return

        # 2️⃣ Clean text
        text = clean_string(text)

        # print(text)

        # 3️⃣ Validate it’s likely a resume
        if not any(word in text.lower() for word in ['experience', 'education', 'skills', 'projects', 'resume']):
            resume.status = '5'  # Not a resume
            resume.save()
            print("⚠️ Parsing failed:", e)
            return

        structured = parse_resume_with_gemini(text)
        if not structured:
            raise ValueError("Llama parser returned empty result")

        # 5️⃣ Clean JSON-safe
        structured_str = str(structured).strip()

        # 🧹 Remove the "json" prefix if Gemini adds it
        structured_str = re.sub(r'(?i)^json\s*', '', structured_str)

        # 🧹 Extract JSON only
        match = re.search(r'\{[\s\S]*\}', structured_str)
        if match:
            structured_str = match.group(0)

        try:
            structured = json.loads(structured_str)
        except Exception as e:
            print("⚠️ JSON decode failed:", e)
            print("Raw structured_str:", structured_str[:300])
            structured = {}
        print(structured)
        # structured = clean_json_data(structured)
        fullname = structured.get("fullname", "")
        emails = structured.get("emails", [])
        phones = structured.get("phones", [])
        skills = structured.get("skills", [])
        education = structured.get("education", [])
        experience = structured.get("experience_years", [])
        summary = structured.get("summary", "")
        keywords = structured.get("keywords", "")
        tag = structured.get("tag", "")

        # 6️⃣ Save parsed data
        parsed_data.objects.create(
            resume_id=resume,
            fullname=fullname,
            emails=emails,
            phones=phones,
            skills=skills,
            education=education,
            experience_years=experience,
            summary_text=summary,
            keywords=keywords,
            tag = tag,
            created_at=timezone.now(),
        )

        # 7️⃣ Update resume record
        resume.extracted_text = text
        resume.status = "2"
        resume.save()
        compute_matches_for_resume(resume.id)


        print(f"✅ Resume {resume_id} parsed successfully using Llama3.")

    except Exception as e:
        resume.status = '5'  # Failed
        resume.save()
        print("⚠️ Parsing failed:", e)
