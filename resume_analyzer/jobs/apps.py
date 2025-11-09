from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        from django.db.utils import OperationalError
        import json
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='50',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='Asia/Kolkata'
        )
        task, created = PeriodicTask.objects.update_or_create(
            name='Daily Job Scraping Task',
            defaults={
                'task': 'myapp.tasks.scrape_jobs_for_resume',
                'enabled': True,
                'crontab': schedule,
            },
        )

