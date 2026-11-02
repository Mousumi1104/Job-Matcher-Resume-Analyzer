from celery import shared_task
from .views import run_job_scrape

@shared_task
def scrape_jobs_daily():
    """Celery task wrapper to run daily scraping."""
    result = run_job_scrape()
    print("✅ Daily scrape complete:", result)