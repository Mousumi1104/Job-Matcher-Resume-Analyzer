from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
urlpatterns = [
    path('job-scrapper', views.scrape_jobs_for_resume, name="scrape_jobs_for_resume"),
    path('jobs-list', views.job_listing, name="job_listing"),
    path('jobs-details/<int:id>', views.job_details, name="job_details"),
    path('jobs-save/<int:id>/<int:resume_id>', views.save_jobs, name="save_jobs"),
    path('jobs-remove/<int:id>/<int:resume_id>', views.remove_save_jobs, name="remove_saved_job"),
    path('dismiss-job/<int:id>/<int:resume_id>', views.dismiss_jobs, name="dismiss_jobs"),
]