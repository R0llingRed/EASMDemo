from celery import Celery

from shared.config import settings

settings.validate_runtime()

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
        "worker.app.tasks.xray_scan",
        "worker.app.tasks.js_api_discovery",
        "worker.app.tasks.dag_executor",
        "worker.app.tasks.event_handler",
        "worker.app.tasks.risk_calculator",
        "worker.app.tasks.alerter",
        "worker.app.tasks.notifier",
    ],
)

celery_app.conf.update(
    task_queue_max_priority=10,
    task_default_priority=5,
    broker_transport_options={
        "queue_order_strategy": "priority",
    },
    task_routes={
        "worker.app.tasks.example.ping": {"queue": "default"},
        "worker.app.tasks.scan.run_scan": {"queue": "scan"},
        "worker.app.tasks.http_probe.run_http_probe": {"queue": "scan"},
        "worker.app.tasks.fingerprint.run_fingerprint": {"queue": "scan"},
        "worker.app.tasks.screenshot.run_screenshot": {"queue": "scan"},
        "worker.app.tasks.nuclei_scan.run_nuclei_scan": {"queue": "scan"},
        "worker.app.tasks.xray_scan.run_xray_scan": {"queue": "scan"},
        "worker.app.tasks.js_api_discovery.run_js_api_discovery": {"queue": "scan"},
        "worker.app.tasks.dag_executor.execute_dag": {"queue": "orchestration"},
        "worker.app.tasks.dag_executor.on_node_completed": {"queue": "orchestration"},
        "worker.app.tasks.event_handler.process_event": {"queue": "orchestration"},
        "worker.app.tasks.event_handler.emit_asset_event": {"queue": "orchestration"},
        "worker.app.tasks.event_handler.emit_scan_event": {"queue": "orchestration"},
        "worker.app.tasks.risk_calculator.calculate_project_risks": {"queue": "alerting"},
        "worker.app.tasks.alerter.check_vulnerability_alert": {"queue": "alerting"},
        "worker.app.tasks.alerter.check_risk_score_alert": {"queue": "alerting"},
        "worker.app.tasks.alerter.send_alert_notifications": {"queue": "alerting"},
        "worker.app.tasks.notifier.send_notification": {"queue": "alerting"},
        "worker.app.tasks.notifier.test_channel": {"queue": "alerting"},
    },
)
