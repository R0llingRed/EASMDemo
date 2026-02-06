"""Round 8 end-to-end flow test: scan create/start -> API risks query."""

from dataclasses import dataclass, field
from typing import Dict, List
from uuid import uuid4

from worker.app.utils.js_api_parser import (
    classify_endpoint_risks,
    extract_endpoints_from_js,
    extract_scripts_from_html,
)


@dataclass
class ScanTask:
    id: str
    project_id: str
    task_type: str
    config: Dict
    status: str = "pending"


@dataclass
class APIRisk:
    project_id: str
    endpoint: str
    method: str
    rule_name: str
    severity: str


@dataclass
class InMemoryStore:
    scans: Dict[str, ScanTask] = field(default_factory=dict)
    api_risks: List[APIRisk] = field(default_factory=list)


def create_scan(store: InMemoryStore, project_id: str, task_type: str, config: Dict) -> ScanTask:
    task = ScanTask(id=str(uuid4()), project_id=project_id, task_type=task_type, config=config)
    store.scans[task.id] = task
    return task


def start_scan(store: InMemoryStore, task_id: str) -> ScanTask:
    task = store.scans[task_id]
    if task.status != "pending":
        raise ValueError("Task is not in pending status")
    if task.task_type != "js_api_discovery":
        raise ValueError("Unsupported task type")
    task.status = "running"
    _run_js_api_discovery_pipeline(store=store, task=task)
    task.status = "completed"
    return task


def list_api_risks(store: InMemoryStore, project_id: str) -> List[APIRisk]:
    return [item for item in store.api_risks if item.project_id == project_id]


def _run_js_api_discovery_pipeline(store: InMemoryStore, task: ScanTask) -> None:
    page_url = "https://target.example"
    html = '<script src="/static/main.js"></script><script>fetch("/graphql")</script>'
    external_js = 'axios.post("/admin/user", body);'
    script_content_map = {
        "https://target.example/static/main.js": external_js,
    }

    scripts = extract_scripts_from_html(html, page_url)
    for script in scripts:
        if script["script_type"] == "external":
            content = script_content_map.get(script["script_url"], "")
        else:
            content = script["content"] or ""
        for endpoint_result in extract_endpoints_from_js(content):
            endpoint = endpoint_result["endpoint"]
            method = endpoint_result["method"]
            for risk in classify_endpoint_risks(endpoint, method):
                store.api_risks.append(
                    APIRisk(
                        project_id=task.project_id,
                        endpoint=endpoint,
                        method=method,
                        rule_name=risk["rule_name"],
                        severity=risk["severity"],
                    )
                )


def test_round8_end_to_end_scan_to_api_risks_flow():
    store = InMemoryStore()
    project_id = str(uuid4())

    created = create_scan(
        store=store,
        project_id=project_id,
        task_type="js_api_discovery",
        config={"batch_size": 50},
    )
    assert created.status == "pending"

    started = start_scan(store=store, task_id=created.id)
    assert started.status == "completed"

    risks = list_api_risks(store=store, project_id=project_id)
    assert len(risks) >= 2
    rule_names = {risk.rule_name for risk in risks}
    assert "graphql_surface" in rule_names
    assert "sensitive_api_surface" in rule_names
