# 第4轮开发记录（漏洞发现基础）

> 迭代周期：2周
> 版本目标：Nuclei 扫描、漏洞表、漏洞列表
> 关联设计：EASM-design-v2.md

---

## 1. 本轮范围

- Nuclei 漏洞扫描任务
- 漏洞数据模型与存储
- 漏洞结果解析
- 严重度映射
- 漏洞列表 API

---

## 2. 计划任务清单

### 2.1 数据模型

- [x] Vulnerability 模型与表结构
- [x] Alembic 迁移脚本（0005_vulnerabilities）

### 2.2 API 与业务逻辑

- [x] 漏洞列表 API（分页/可筛选）
- [x] 漏洞详情 API
- [x] 漏洞统计 API

### 2.3 Celery 任务

- [x] Nuclei 扫描任务
- [x] 结果解析与入库

### 2.4 其他

- [x] 严重度映射（critical/high/medium/low/info）
- [x] TaskType 枚举更新

---

## 3. 交付物

### 3.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `server/app/models/vulnerability.py` | Vulnerability 数据模型 |
| `server/app/schemas/vulnerability.py` | Vulnerability Pydantic 模式 |
| `server/app/crud/vulnerability.py` | Vulnerability CRUD 操作 |
| `server/app/api/vulnerabilities.py` | 漏洞 API 路由 |
| `server/alembic/versions/0005_vulnerabilities.py` | 数据库迁移脚本 |
| `worker/app/tasks/nuclei_scan.py` | Nuclei 扫描 Celery 任务 |
| `test/test_vulnerability.py` | 漏洞严重度映射测试 |

### 3.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `server/app/schemas/scan_task.py` | 新增 TaskType: nuclei_scan |
| `server/app/api/router.py` | 注册 vulnerabilities 路由 |
| `server/app/api/scans.py` | 更新任务分发逻辑 |
| `worker/app/celery_app.py` | 注册 nuclei_scan 任务模块 |

---

## 4. 验收标准

- [x] Nuclei 扫描结果可追踪
- [x] 漏洞可按严重度过滤
- [x] 漏洞可按状态过滤

---

## 5. 技术实现细节

### 5.1 Vulnerability 模型

- 支持字段：target_url, template_id, severity, title, description
- 状态管理：open, confirmed, fixed, false_positive
- 证据存储：matched_at, extracted_results, curl_command
- 原始输出：raw_output (JSONB)

### 5.2 Nuclei 扫描

- 使用 nuclei CLI 工具执行扫描
- 支持配置：severity, templates, batch_size
- JSON 输出解析
- 结果自动入库（upsert）

### 5.3 严重度映射

| Nuclei | 系统 |
|--------|------|
| critical | critical |
| high | high |
| medium | medium |
| low | low |
| info | info |
| unknown | info |

---

## 6. 测试结果

```
test/test_vulnerability.py - 8 passed
Total: 8 passed
```

---

## 7. 变更记录

| 日期 | 变更内容 |
|-----|---------|
| 2026-01-30 | 完成 Vulnerability 模型、Schema、CRUD、API |
| 2026-01-30 | 完成 Nuclei 扫描 Celery 任务 |
| 2026-01-30 | 完成数据库迁移 0005_vulnerabilities |
| 2026-01-30 | 完成单元测试（8 个测试用例） |
