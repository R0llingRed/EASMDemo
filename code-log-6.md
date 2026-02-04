# 第6轮开发记录（任务编排升级）

> 迭代周期：2周
> 版本目标：DAG 编排、事件驱动、策略中心
> 关联设计：EASM-design-v2.md Phase 3

---

## 1. 本轮范围

- 策略中心（ScanPolicy）
- DAG 模板（DAGTemplate）
- DAG 执行实例（DAGExecution）
- 事件触发器（EventTrigger）
- DAG 编排执行引擎
- 事件驱动调度器

---

## 2. 计划任务清单

### 2.1 数据模型

- [x] ScanPolicy 策略模型
- [x] DAGTemplate DAG模板模型
- [x] DAGExecution DAG执行实例模型
- [x] EventTrigger 事件触发器模型
- [x] Alembic 迁移脚本（0007_dag_orchestration）

### 2.2 Schema 定义

- [x] ScanPolicy Schema
- [x] DAGTemplate Schema（含节点验证）
- [x] DAGExecution Schema
- [x] EventTrigger Schema

### 2.3 CRUD 操作

- [x] ScanPolicy CRUD（含默认策略管理）
- [x] DAGTemplate CRUD（含全局模板支持）
- [x] DAGExecution CRUD（含节点状态更新）
- [x] EventTrigger CRUD（含触发计数）

### 2.4 API 路由

- [x] 策略中心 API（/projects/{project_id}/policies）
- [x] DAG 模板 API（/projects/{project_id}/dag-templates）
- [x] DAG 执行 API（/projects/{project_id}/dag-executions）
- [x] 事件触发器 API（/projects/{project_id}/event-triggers）
- [x] 事件发送 API（/projects/{project_id}/events/emit）

### 2.5 Celery 任务

- [x] DAG 编排执行任务（dag_executor）
- [x] 节点完成回调（on_node_completed）
- [x] 事件处理任务（event_handler）

### 2.6 测试

- [x] DAG 编排单元测试（24 个用例）
- [x] 策略中心单元测试（13 个用例）

---

## 3. 交付物

### 3.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `server/app/models/scan_policy.py` | 扫描策略模型 |
| `server/app/models/dag_template.py` | DAG模板模型 |
| `server/app/models/dag_execution.py` | DAG执行实例模型 |
| `server/app/models/event_trigger.py` | 事件触发器模型 |
| `server/app/schemas/scan_policy.py` | 策略 Pydantic Schema |
| `server/app/schemas/dag_template.py` | DAG模板 Schema |
| `server/app/schemas/dag_execution.py` | DAG执行 Schema |
| `server/app/schemas/event_trigger.py` | 事件触发器 Schema |
| `server/app/crud/scan_policy.py` | 策略 CRUD |
| `server/app/crud/dag_template.py` | DAG模板 CRUD |
| `server/app/crud/dag_execution.py` | DAG执行 CRUD |
| `server/app/crud/event_trigger.py` | 事件触发器 CRUD |
| `server/app/api/policies.py` | 策略中心 API |
| `server/app/api/dag_templates.py` | DAG模板 API |
| `server/app/api/dag_executions.py` | DAG执行 API |
| `server/app/api/event_triggers.py` | 事件触发器 API |
| `server/alembic/versions/0007_dag_orchestration.py` | 数据库迁移 |
| `worker/app/tasks/dag_executor.py` | DAG执行 Celery 任务 |
| `worker/app/tasks/event_handler.py` | 事件处理 Celery 任务 |
| `test/test_dag_orchestration.py` | DAG编排测试（24用例） |
| `test/test_scan_policy.py` | 策略测试（13用例） |

### 3.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------| 
| `server/app/api/router.py` | 注册新路由（policies, dag_templates, dag_executions, event_triggers, events） |
| `worker/app/celery_app.py` | 注册 dag_executor, event_handler 任务模块，新增 orchestration 队列 |

---

## 4. 验收标准

- [x] 可创建和管理扫描策略
- [x] 可创建 DAG 模板定义任务依赖
- [x] 可启动 DAG 执行并观察状态流转
- [x] 事件触发后任务可按 DAG 自动串联

---

## 5. 技术实现细节

### 5.1 DAG 模板结构

```json
{
  "nodes": [
    {"id": "subdomain", "task_type": "subdomain_scan", "config": {}},
    {"id": "dns", "task_type": "dns_resolve", "depends_on": ["subdomain"]},
    {"id": "port", "task_type": "port_scan", "depends_on": ["dns"]},
    {"id": "http", "task_type": "http_probe", "depends_on": ["port"]},
    {"id": "nuclei", "task_type": "nuclei_scan", "depends_on": ["http"]}
  ]
}
```

### 5.2 DAG 执行流程

1. 创建 DAGExecution，初始化所有节点为 pending
2. 调用 execute_dag 任务
3. 构建依赖图，查找就绪节点（所有依赖已完成）
4. 为就绪节点创建 ScanTask 并分发
5. 更新节点状态为 running
6. 等待 on_node_completed 回调
7. 重复 3-6 直到所有节点完成

### 5.3 事件驱动机制

- 事件类型：asset_created, scan_completed, vulnerability_found 等
- 过滤匹配：支持精确匹配和列表匹配
- 触发计数：跟踪 total, success, failed

### 5.4 新增 Celery 队列

- `orchestration` 队列：DAG 执行和事件处理任务

---

## 6. 测试结果

```
test/test_dag_orchestration.py - 24 passed
test/test_scan_policy.py - 13 passed
Total: 37 passed
```

---

## 7. 变更记录

| 日期 | 变更内容 |
|-----|---------| 
| 2026-02-04 | 创建第6轮开发计划 |
| 2026-02-04 | 完成 ScanPolicy, DAGTemplate, DAGExecution, EventTrigger 模型 |
| 2026-02-04 | 完成所有 Schema、CRUD、API 模块 |
| 2026-02-04 | 完成数据库迁移 0007_dag_orchestration |
| 2026-02-04 | 完成 DAG 执行引擎与事件处理任务 |
| 2026-02-04 | 完成单元测试（37 个测试用例） |
