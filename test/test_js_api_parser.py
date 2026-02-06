"""Tests for JS endpoint extraction and risk classification."""

from worker.app.utils.js_api_parser import (
    classify_endpoint_risks,
    extract_endpoints_from_js,
    extract_scripts_from_html,
    normalize_endpoint,
)


def test_extract_scripts_from_html_supports_external_and_inline():
    html = """
    <html>
      <head>
        <script src="/static/app.js"></script>
      </head>
      <body>
        <script>fetch("/api/users")</script>
      </body>
    </html>
    """
    scripts = extract_scripts_from_html(html, "https://example.com/index.html")
    assert len(scripts) == 2
    assert scripts[0]["script_type"] == "external"
    assert scripts[0]["script_url"] == "https://example.com/static/app.js"
    assert scripts[1]["script_type"] == "inline"
    assert scripts[1]["script_url"] == "https://example.com/index.html#inline-0"


def test_extract_endpoints_from_js_parses_fetch_axios_and_generic():
    js = """
    axios.post("/admin/user", payload);
    fetch("https://api.example.com/v1/data", { method: "PATCH" });
    const path = "/graphql";
    """
    endpoints = extract_endpoints_from_js(js)
    pairs = {(item["method"], item["endpoint"]) for item in endpoints}
    assert ("POST", "/admin/user") in pairs
    assert ("PATCH", "https://api.example.com/v1/data") in pairs
    assert ("GET", "/graphql") in pairs


def test_normalize_endpoint_rejects_dynamic_templates():
    assert normalize_endpoint("/api/users") == "/api/users"
    assert normalize_endpoint("api/v1/users") == "/api/v1/users"
    assert normalize_endpoint("https://example.com/api") == "https://example.com/api"
    assert normalize_endpoint("${apiHost}/users") is None


def test_classify_endpoint_risks_applies_expected_rules():
    risks = classify_endpoint_risks("http://example.com/admin/config", "DELETE")
    rule_names = {risk["rule_name"] for risk in risks}
    assert "insecure_transport" in rule_names
    assert "sensitive_api_surface" in rule_names
    assert "mutation_on_sensitive_surface" in rule_names

    graphql_risks = classify_endpoint_risks("/graphql", "POST")
    assert any(r["rule_name"] == "graphql_surface" for r in graphql_risks)
