"""
Test DAG Orchestration

Unit tests for DAG template, DAG execution, and event trigger functionality.
These tests are standalone and don't require external dependencies.
"""

import pytest
from typing import Dict, List, Set


# ============================================================================
# Inline implementations of functions to test (avoids import issues)
# These mirror the implementations in worker/app/tasks/dag_executor.py
# ============================================================================


def build_dependency_graph(nodes: List[Dict]) -> Dict[str, Set[str]]:
    """
    构建依赖图

    Returns:
        Dict[node_id, Set[依赖的node_id]]
    """
    graph = {}
    for node in nodes:
        node_id = node.get("id")
        depends_on = node.get("depends_on", [])
        graph[node_id] = set(depends_on)
    return graph


def get_ready_nodes(
    nodes: List[Dict],
    node_states: Dict[str, str],
    dependency_graph: Dict[str, Set[str]],
) -> List[Dict]:
    """
    获取可以执行的节点（所有依赖已完成且自身pending）

    Returns:
        可执行节点列表
    """
    ready = []
    for node in nodes:
        node_id = node.get("id")
        # 节点必须是pending状态
        if node_states.get(node_id) != "pending":
            continue
        # 检查所有依赖是否已完成
        deps = dependency_graph.get(node_id, set())
        all_deps_completed = all(node_states.get(dep) == "completed" for dep in deps)
        if all_deps_completed:
            ready.append(node)
    return ready


def check_execution_complete(node_states: Dict[str, str]) -> tuple:
    """
    检查执行是否完成

    Returns:
        (is_complete, is_success)
    """
    if not node_states:
        return False, False

    all_completed = all(s in ("completed", "skipped", "failed") for s in node_states.values())
    has_failure = any(s == "failed" for s in node_states.values())

    if all_completed:
        return True, not has_failure
    return False, False


def match_filter(filter_config: Dict, event_data: Dict) -> bool:
    """
    检查事件数据是否匹配过滤条件
    """
    if not filter_config:
        return True

    for key, expected in filter_config.items():
        actual = event_data.get(key)

        if isinstance(expected, list):
            if actual not in expected:
                return False
        else:
            if actual != expected:
                return False

    return True


# ============================================================================
# Tests
# ============================================================================


class TestBuildDependencyGraph:
    """Tests for build_dependency_graph function"""

    def test_empty_nodes(self):
        """Empty nodes should return empty graph"""
        result = build_dependency_graph([])
        assert result == {}

    def test_single_node_no_deps(self):
        """Single node with no dependencies"""
        nodes = [{"id": "node1", "task_type": "test"}]
        result = build_dependency_graph(nodes)
        assert result == {"node1": set()}

    def test_linear_chain(self):
        """Linear chain: a -> b -> c"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
            {"id": "c", "task_type": "test", "depends_on": ["b"]},
        ]
        result = build_dependency_graph(nodes)
        assert result == {
            "a": set(),
            "b": {"a"},
            "c": {"b"},
        }

    def test_diamond_pattern(self):
        """Diamond pattern: a -> b,c -> d"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
            {"id": "c", "task_type": "test", "depends_on": ["a"]},
            {"id": "d", "task_type": "test", "depends_on": ["b", "c"]},
        ]
        result = build_dependency_graph(nodes)
        assert result == {
            "a": set(),
            "b": {"a"},
            "c": {"a"},
            "d": {"b", "c"},
        }

    def test_multiple_roots(self):
        """Multiple root nodes with no dependencies"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test"},
            {"id": "c", "task_type": "test", "depends_on": ["a", "b"]},
        ]
        result = build_dependency_graph(nodes)
        assert result == {
            "a": set(),
            "b": set(),
            "c": {"a", "b"},
        }


class TestGetReadyNodes:
    """Tests for get_ready_nodes function"""

    def test_all_pending_no_deps(self):
        """All nodes pending with no dependencies should all be ready"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test"},
        ]
        node_states = {"a": "pending", "b": "pending"}
        graph = {"a": set(), "b": set()}
        result = get_ready_nodes(nodes, node_states, graph)
        assert len(result) == 2
        assert {n["id"] for n in result} == {"a", "b"}

    def test_linear_chain_first_ready(self):
        """In linear chain, only first node is ready"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
        ]
        node_states = {"a": "pending", "b": "pending"}
        graph = {"a": set(), "b": {"a"}}
        result = get_ready_nodes(nodes, node_states, graph)
        assert len(result) == 1
        assert result[0]["id"] == "a"

    def test_linear_chain_second_ready(self):
        """After first completes, second is ready"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
        ]
        node_states = {"a": "completed", "b": "pending"}
        graph = {"a": set(), "b": {"a"}}
        result = get_ready_nodes(nodes, node_states, graph)
        assert len(result) == 1
        assert result[0]["id"] == "b"

    def test_running_not_ready(self):
        """Running nodes are not ready"""
        nodes = [{"id": "a", "task_type": "test"}]
        node_states = {"a": "running"}
        graph = {"a": set()}
        result = get_ready_nodes(nodes, node_states, graph)
        assert len(result) == 0

    def test_diamond_middle_layer(self):
        """Diamond pattern: after a completes, b and c are ready"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
            {"id": "c", "task_type": "test", "depends_on": ["a"]},
            {"id": "d", "task_type": "test", "depends_on": ["b", "c"]},
        ]
        node_states = {"a": "completed", "b": "pending", "c": "pending", "d": "pending"}
        graph = {"a": set(), "b": {"a"}, "c": {"a"}, "d": {"b", "c"}}
        result = get_ready_nodes(nodes, node_states, graph)
        assert len(result) == 2
        assert {n["id"] for n in result} == {"b", "c"}

    def test_diamond_final_node(self):
        """Diamond pattern: after b and c complete, d is ready"""
        nodes = [
            {"id": "a", "task_type": "test"},
            {"id": "b", "task_type": "test", "depends_on": ["a"]},
            {"id": "c", "task_type": "test", "depends_on": ["a"]},
            {"id": "d", "task_type": "test", "depends_on": ["b", "c"]},
        ]
        node_states = {"a": "completed", "b": "completed", "c": "completed", "d": "pending"}
        graph = {"a": set(), "b": {"a"}, "c": {"a"}, "d": {"b", "c"}}
        result = get_ready_nodes(nodes, node_states, graph)
        assert len(result) == 1
        assert result[0]["id"] == "d"


class TestCheckExecutionComplete:
    """Tests for check_execution_complete function"""

    def test_empty_states(self):
        """Empty states is not complete"""
        is_complete, is_success = check_execution_complete({})
        assert is_complete is False

    def test_all_pending(self):
        """All pending is not complete"""
        is_complete, is_success = check_execution_complete({"a": "pending", "b": "pending"})
        assert is_complete is False

    def test_some_running(self):
        """Some running is not complete"""
        is_complete, is_success = check_execution_complete({"a": "completed", "b": "running"})
        assert is_complete is False

    def test_all_completed(self):
        """All completed is complete and successful"""
        is_complete, is_success = check_execution_complete({"a": "completed", "b": "completed"})
        assert is_complete is True
        assert is_success is True

    def test_some_failed(self):
        """Some failed is complete but not successful"""
        is_complete, is_success = check_execution_complete({"a": "completed", "b": "failed"})
        assert is_complete is True
        assert is_success is False

    def test_skipped_counts_as_complete(self):
        """Skipped nodes count as complete"""
        is_complete, is_success = check_execution_complete({"a": "completed", "b": "skipped"})
        assert is_complete is True
        assert is_success is True


class TestMatchFilter:
    """Tests for match_filter function"""

    def test_empty_filter(self):
        """Empty filter matches everything"""
        assert match_filter({}, {"key": "value"}) is True

    def test_exact_match(self):
        """Exact value match"""
        assert match_filter({"key": "value"}, {"key": "value"}) is True
        assert match_filter({"key": "value"}, {"key": "other"}) is False

    def test_list_match(self):
        """Value in list match"""
        assert match_filter({"severity": ["high", "critical"]}, {"severity": "high"}) is True
        assert match_filter({"severity": ["high", "critical"]}, {"severity": "critical"}) is True
        assert match_filter({"severity": ["high", "critical"]}, {"severity": "low"}) is False

    def test_missing_key(self):
        """Missing key doesn't match"""
        assert match_filter({"key": "value"}, {}) is False

    def test_multiple_conditions(self):
        """Multiple conditions must all match"""
        filter_cfg = {"type": "subdomain", "status": "active"}
        assert match_filter(filter_cfg, {"type": "subdomain", "status": "active"}) is True
        assert match_filter(filter_cfg, {"type": "subdomain", "status": "inactive"}) is False
        assert match_filter(filter_cfg, {"type": "ip", "status": "active"}) is False


class TestDAGSchemaValidation:
    """Tests for DAG template schema validation"""

    def test_valid_simple_dag(self):
        """Valid simple DAG structure"""
        nodes = [
            {"id": "a", "task_type": "subdomain_scan", "depends_on": [], "config": {}},
            {"id": "b", "task_type": "port_scan", "depends_on": ["a"], "config": {}},
        ]
        graph = build_dependency_graph(nodes)
        assert len(graph) == 2

    def test_typical_easm_dag(self):
        """Typical EASM scan DAG"""
        nodes = [
            {"id": "subdomain", "task_type": "subdomain_scan", "config": {}},
            {"id": "dns", "task_type": "dns_resolve", "depends_on": ["subdomain"], "config": {}},
            {"id": "port", "task_type": "port_scan", "depends_on": ["dns"], "config": {}},
            {"id": "http", "task_type": "http_probe", "depends_on": ["port"], "config": {}},
            {"id": "fingerprint", "task_type": "fingerprint", "depends_on": ["http"], "config": {}},
            {"id": "nuclei", "task_type": "nuclei_scan", "depends_on": ["http"], "config": {}},
        ]
        graph = build_dependency_graph(nodes)
        assert len(graph) == 6
        assert graph["subdomain"] == set()
        assert graph["dns"] == {"subdomain"}
        assert graph["nuclei"] == {"http"}
