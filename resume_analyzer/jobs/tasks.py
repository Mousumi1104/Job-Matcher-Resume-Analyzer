from celery import shared_task
from django.http import HttpRequest
from .views import scrape_jobs_for_resume  # Import your function

@shared_task
def scrape_jobs_daily():
    """Celery task wrapper to run daily scraping."""
    # You can pass a dummy request if your view expects it
    request = HttpRequest()
    response = scrape_jobs_for_resume(request)
    print("✅ Daily scrape complete:", response.status_code)