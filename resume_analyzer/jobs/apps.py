from django.apps import AppConfig
from django.db.models.signals import post_migrate


def register_daily_scrape(sender, **kwargs):
    """Create/update the daily job-scraping Celery beat entry.

    Runs after `migrate` (via post_migrate) instead of at app start-up, so a
    fresh database can be migrated before the celery-beat tables exist.
    """
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='50',
        hour='0',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='Asia/Kolkata',
    )
    PeriodicTask.objects.update_or_create(
        name='Daily Job Scraping Task',
        defaults={
            'task': 'jobs.tasks.scrape_jobs_daily',
            'enabled': True,
            'crontab': schedule,
        },
    )


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        post_migrate.connect(register_daily_scrape, sender=self)
