from worker.app.celery_app import celery_app


@celery_app.task(name="app.tasks.example.ping")
def ping() -> dict:
    return {"status": "pong"}
