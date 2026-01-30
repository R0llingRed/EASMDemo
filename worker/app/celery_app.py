from celery import Celery

from shared.config import settings

celery_app = Celery(
    "easm",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "worker.app.tasks.example",
        "worker.app.tasks.scan",
        "worker.app.tasks.http_probe",
        "worker.app.tasks.fingerprint",
        "worker.app.tasks.screenshot",
        "worker.app.tasks.nuclei_scan",
    ],
)

celery_app.conf.update(
    task_routes={
        "worker.app.tasks.example.ping": {"queue": "default"},
        "worker.app.tasks.scan.run_scan": {"queue": "scan"},
        "worker.app.tasks.http_probe.run_http_probe": {"queue": "scan"},
        "worker.app.tasks.fingerprint.run_fingerprint": {"queue": "scan"},
        "worker.app.tasks.screenshot.run_screenshot": {"queue": "scan"},
        "worker.app.tasks.nuclei_scan.run_nuclei_scan": {"queue": "scan"},
    },
)
