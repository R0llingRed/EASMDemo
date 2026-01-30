from celery import Celery

from shared.config import settings

celery_app = Celery(
    "easm",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.app.tasks.example", "worker.app.tasks.scan"],
)

celery_app.conf.update(
    task_routes={
        "worker.app.tasks.example.ping": {"queue": "default"},
        "worker.app.tasks.scan.run_scan": {"queue": "scan"},
    },
)
