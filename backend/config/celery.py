import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("cleardocs")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks from installed Django apps AND our root-level tasks package
app.autodiscover_tasks()
app.autodiscover_tasks(["tasks"])
