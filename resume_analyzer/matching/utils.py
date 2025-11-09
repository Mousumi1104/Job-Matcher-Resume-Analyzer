# matching/utils.py
# Purpose: provide reusable scoring functions and helpers.

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re, json

def normalize_text(s):
    """Minimal cleaning for TF-IDF (lowercase, remove small tokens)."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[\r\n]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def build_job_corpus(job_qs):
    """
    Build a list of cleaned job_text strings and a parallel list of job IDs.
    job_text = title + description + ' '.join(skills)
    """
    job_texts = []
    job_ids = []
    for job in job_qs:
        parts = [
            job.title or "",
            job.description or "",
            
        ]
        job_text = normalize_text(" ".join(parts))
        job_texts.append(job_text)
        job_ids.append(job.id)
    return job_ids, job_texts

def resume_to_text(parsed):
    """Convert parsed_data instance to a single searchable text blob."""
    parts = [
        parsed.summary_text or "",
        " ".join(parsed.skills or []),
        " ".join(parsed.keywords or [])
    ]
    return normalize_text(" ".join(parts))

def compute_tfidf_scores(resume_text, job_texts):
    """
    Fit TF-IDF on job_texts + resume_text (so vocab consistent), return cosine similarities.
    Returns numpy array of similarity scores (resume vs each job).
    """
    corpus = job_texts + [resume_text]  # put resume at last index
    vect = TfidfVectorizer(max_features=15000, ngram_range=(1,2)).fit(corpus)
    tfidf = vect.transform(corpus)
    resume_vec = tfidf[-1]
    job_vecs = tfidf[:-1]
    sims = cosine_similarity(resume_vec, job_vecs).flatten()  # shape: (n_jobs,)
    # clamp possible NaNs
    sims = np.nan_to_num(sims)
    return sims  # values 0..1

def extract_numeric_experience(exp_text):
    """
    Normalize experience text like '2+ years', '3-5 years', 'Minimum 1 year', 'Fresher'
    into an approximate number of years (float).
    """
    if not exp_text:
        return 0.0

    exp_text = exp_text.lower().strip()

    # Handle "fresher" or "not specified"
    if "fresher" in exp_text or "not specified" in exp_text:
        return 0.0

    # Match patterns like "3 years", "2+ years", "3 to 5 years"
    range_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)', exp_text)
    if range_match:
        low, high = range_match.groups()
        return (float(low) + float(high)) / 2.0

    num_match = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*(?:year|yr)', exp_text)
    if num_match:
        return float(num_match.group(1))

    return 0.0


def safe_load_skills(skills_field):
    """Convert JSON string, dict, or list into a clean lowercase list of skills."""
    if not skills_field:
        return []

    # Case 1: Already a list
    if isinstance(skills_field, list):
        return [s.strip().lower() for s in skills_field if isinstance(s, str) and s.strip()]

    # Case 2: Already a dict with 'skills'
    if isinstance(skills_field, dict) and "skills" in skills_field:
        return [s.strip().lower() for s in skills_field["skills"] if isinstance(s, str) and s.strip()]

    # Case 3: JSON string (may be dict or list)
    if isinstance(skills_field, str):
        try:
            data = json.loads(skills_field.replace("'", '"'))  # handle single quotes too
            if isinstance(data, dict) and "skills" in data:
                return [s.strip().lower() for s in data["skills"] if isinstance(s, str) and s.strip()]
            elif isinstance(data, list):
                return [s.strip().lower() for s in data if isinstance(s, str) and s.strip()]
        except Exception:
            pass

    return []


def compute_skill_overlap(resume_skills, job_skills):
    """Return overlap ratio between resume and job skills."""
    set_r = set(resume_skills)
    set_j = set(job_skills)
    if not set_j:
        return 0.0
    overlap = set_r.intersection(set_j)
    return len(overlap) / float(len(set_j))


def combine_scores(tfidf_score, overlap, w_tfidf=0.7, w_overlap=0.3):
    """Weighted combination, returns float 0..1"""
    return (w_tfidf * tfidf_score) + (w_overlap * overlap)
