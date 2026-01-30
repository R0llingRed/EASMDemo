# 第2轮开发记录（扫描执行最小链路）

> 迭代周期：2周
> 版本目标：子域名收集 + DNS 解析 + 端口扫描（MVP）
> 关联设计：EASM-design-v2.md

---

## 1. 本轮范围

- 扫描任务管理（创建、查询、启动）
- 子域名收集任务
- DNS 解析任务
- 端口扫描任务
- 扫描结果入库与查询

---

## 2. 计划任务清单

### 2.1 数据模型

- [x] ScanTask 模型与表结构
- [x] Subdomain 模型与表结构
- [x] IPAddress 模型与表结构
- [x] Port 模型与表结构
- [x] Alembic 迁移脚本（0003_scan_tasks）

### 2.2 API 与业务逻辑

- [x] 扫描任务创建 API
- [x] 扫描任务列表 API（分页/可筛选）
- [x] 扫描任务详情 API
- [x] 扫描任务启动 API
- [x] 子域名列表 API
- [x] IP 地址列表 API
- [x] 端口列表 API

### 2.3 Celery 任务

- [x] 子域名收集任务（subfinder 集成 + 模拟回退）
- [x] DNS 解析任务（socket 解析）
- [x] 端口扫描任务（nmap 集成 + socket 回退）

### 2.4 结果归一化

- [x] 子域名去重入库（upsert）
- [x] IP 地址去重入库（upsert）
- [x] 端口去重入库（upsert）

---

## 3. 交付物

### 3.1 新增模型

- `server/app/models/scan_task.py`
- `server/app/models/subdomain.py`
- `server/app/models/ip_address.py`
- `server/app/models/port.py`

### 3.2 新增 Schema

- `server/app/schemas/scan_task.py`
- `server/app/schemas/subdomain.py`
- `server/app/schemas/ip_address.py`
- `server/app/schemas/port.py`

### 3.3 新增 CRUD

- `server/app/crud/scan_task.py`
- `server/app/crud/subdomain.py`
- `server/app/crud/ip_address.py`
- `server/app/crud/port.py`

### 3.4 新增 API

- `server/app/api/scans.py`
- `server/app/api/subdomains.py`
- `server/app/api/ips.py`
- `server/app/api/ports.py`

### 3.5 新增 Celery 任务

- `worker/app/tasks/scan.py`

### 3.6 数据库迁移

- `server/alembic/versions/0003_scan_tasks.py`

---

## 4. 验收标准

- [x] 可创建扫描任务
- [x] 可启动扫描任务
- [x] 子域名收集结果入库
- [x] DNS 解析结果入库
- [x] 端口扫描结果入库
- [x] 可查询扫描结果

---

## 5. API 接口说明

### 5.1 扫描任务

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /projects/{project_id}/scans | 创建扫描任务 |
| GET | /projects/{project_id}/scans | 列表扫描任务 |
| GET | /projects/{project_id}/scans/{task_id} | 获取任务详情 |
| POST | /projects/{project_id}/scans/{task_id}/start | 启动扫描任务 |

### 5.2 扫描结果

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /projects/{project_id}/subdomains | 子域名列表 |
| GET | /projects/{project_id}/ips | IP 地址列表 |
| GET | /ips/{ip_id}/ports | 端口列表 |

### 5.3 任务类型

| 类型 | 说明 | 配置参数 |
|------|------|----------|
| subdomain_scan | 子域名收集 | domain: 目标域名 |
| dns_resolve | DNS 解析 | root_domain: 可选，限定根域名 |
| port_scan | 端口扫描 | ports: 可选，端口列表 |

---

## 6. 变更记录

### 2026-01-30

- 初始化 ScanTask、Subdomain、IPAddress、Port 模型
- 增加扫描任务 API（创建、列表、详情、启动）
- 增加扫描结果查询 API（子域名、IP、端口）
- 实现 Celery 扫描任务（子域名收集、DNS 解析、端口扫描）
- 增加 Alembic 迁移脚本（0003_scan_tasks）
- 更新 Worker 配置支持 scan 队列

