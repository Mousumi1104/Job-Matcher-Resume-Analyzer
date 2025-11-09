from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from resumes.models import parsed_data
from jobs.models import JobListing
from matching.models import MatchResult
from django.contrib.auth import get_user_model
from .utils import build_job_corpus, resume_to_text, compute_tfidf_scores, compute_skill_overlap, combine_scores, safe_load_skills, extract_numeric_experience
from django.db import transaction
import math

TOP_N = 10
THRESHOLD_PCT = 10.0  # 60%

import re

def normalize_skills(skills_or_text):
    """Convert job/resume skills into a clean lowercase list."""
    if not skills_or_text:
        return []

    if isinstance(skills_or_text, str):
        # Handle text description or comma-separated list
        skills = re.split(r'[,\n]', skills_or_text)
    elif isinstance(skills_or_text, list):
        skills = skills_or_text
    else:
        return []

    # Clean and normalize
    cleaned = [
        re.sub(r'[^a-z0-9\+\#\.]', '', s.lower().strip())
        for s in skills
        if s.strip()
    ]
    # Remove duplicates and empties
    return list(set(filter(None, cleaned)))


def compute_matches_for_resume(request):
    """
    Compute top-N matches for a single parsed_data instance (resume).
    Saves MatchResult entries for those >= THRESHOLD_PCT.
    """
    try:
        parsed = parsed_data.objects.select_related('resume_id__user_id').all()
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
    return HttpResponse(scored_sorted)
# Create your views here.
