import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("cleardocs")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Task modules live in a root-level `tasks` package (not per-app). Import them
# explicitly so the worker registers them: autodiscover_tasks(["tasks"]) does
# NOT work here — it looks for a `tasks.tasks` submodule, not these modules.
app.conf.imports = (
    "tasks.ocr",
    "tasks.analysis",
    "tasks.pipeline",
    "tasks.translation",
    "tasks.chat",
    "tasks.maintenance",
)

# Also discover any conventional <app>/tasks.py modules in installed apps.
app.autodiscover_tasks()
