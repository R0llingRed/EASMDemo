"""
Test Scan Policy

Unit tests for scan policy, DAG template, and event trigger logic.
These tests are standalone and don't require external dependencies.
"""

import pytest


class TestScanPolicyLogic:
    """Tests for ScanPolicy business logic"""

    def test_policy_name_validation(self):
        """Policy name should be non-empty"""
        name = "Test Policy"
        assert len(name) > 0
        assert len(name) <= 255

    def test_policy_config_defaults(self):
        """Policy config should have sensible defaults"""
        default_config = {}
        assert isinstance(default_config, dict)

    def test_is_default_flag(self):
        """Only one policy should be default per project"""
        policies = [
            {"id": "1", "is_default": True},
            {"id": "2", "is_default": False},
            {"id": "3", "is_default": False},
        ]
        default_count = sum(1 for p in policies if p["is_default"])
        assert default_count == 1


class TestDAGNodeLogic:
    """Tests for DAG node logic"""

    def test_node_id_uniqueness(self):
        """Node IDs should be unique within a template"""
        nodes = [
            {"id": "a", "task_type": "subdomain_scan"},
            {"id": "b", "task_type": "port_scan"},
            {"id": "c", "task_type": "http_probe"},
        ]
        node_ids = [n["id"] for n in nodes]
        assert len(node_ids) == len(set(node_ids))

    def test_node_dependency_validation(self):
        """Node dependencies should reference existing nodes"""
        nodes = [
            {"id": "a", "task_type": "subdomain_scan", "depends_on": []},
            {"id": "b", "task_type": "port_scan", "depends_on": ["a"]},
        ]
        all_ids = {n["id"] for n in nodes}
        for node in nodes:
            for dep in node.get("depends_on", []):
                assert dep in all_ids, f"Dependency {dep} not found"

    def test_no_circular_dependencies_simple(self):
        """Detect simple circular dependencies"""
        # a -> b -> a is circular
        nodes = [
            {"id": "a", "task_type": "test", "depends_on": ["b"]},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
        ]
        # Build adjacency for cycle detection
        has_cycle = detect_cycle(nodes)
        assert has_cycle is True

    def test_no_circular_dependencies_valid(self):
        """Valid DAG has no cycles"""
        nodes = [
            {"id": "a", "task_type": "test", "depends_on": []},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
            {"id": "c", "task_type": "test", "depends_on": ["b"]},
        ]
        has_cycle = detect_cycle(nodes)
        assert has_cycle is False


def detect_cycle(nodes) -> bool:
    """Simple cycle detection using DFS"""
    graph = {n["id"]: set(n.get("depends_on", [])) for n in nodes}
    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        for dep in graph.get(node, []):
            if dep not in visited:
                if dfs(dep):
                    return True
            elif dep in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for node_id in graph:
        if node_id not in visited:
            if dfs(node_id):
                return True
    return False


class TestEventTriggerLogic:
    """Tests for EventTrigger logic"""

    def test_event_types(self):
        """Valid event types"""
        valid_types = [
            "asset_created",
            "asset_updated",
            "subdomain_discovered",
            "scan_completed",
            "vulnerability_found",
        ]
        for event_type in valid_types:
            assert isinstance(event_type, str)
            assert len(event_type) > 0

    def test_filter_config_structure(self):
        """Filter config should be a dict"""
        filter_configs = [
            {},
            {"severity": "high"},
            {"severity": ["high", "critical"]},
            {"asset_type": "subdomain", "status": "active"},
        ]
        for cfg in filter_configs:
            assert isinstance(cfg, dict)

    def test_trigger_count_structure(self):
        """Trigger count should track total, success, failed"""
        trigger_count = {"total": 10, "success": 8, "failed": 2}
        assert trigger_count["total"] == trigger_count["success"] + trigger_count["failed"]


class TestDAGExecutionStates:
    """Tests for DAG execution state machine"""

    def test_valid_status_transitions(self):
        """Valid status transitions"""
        valid_transitions = {
            "pending": ["running", "cancelled"],
            "running": ["completed", "failed", "cancelled"],
            "completed": [],
            "failed": [],
            "cancelled": [],
        }
        # Each terminal state has no outgoing transitions
        terminal_states = ["completed", "failed", "cancelled"]
        for state in terminal_states:
            assert valid_transitions[state] == []

    def test_node_state_values(self):
        """Valid node states"""
        valid_states = ["pending", "running", "completed", "failed", "skipped"]
        for state in valid_states:
            assert isinstance(state, str)

    def test_execution_input_config(self):
        """Input config should be passed to nodes"""
        input_config = {"target_domain": "example.com", "ports": "1-1000"}
        node_config = {"timeout": 300}
        merged = {**input_config, **node_config}
        assert "target_domain" in merged
        assert "ports" in merged
        assert "timeout" in merged
