# 第3轮开发记录（Web 探测与指纹）

> 迭代周期：2周
> 版本目标：HTTP 探测、指纹识别、截图存档
> 关联设计：EASM-design-v2.md

---

## 1. 本轮范围

- HTTP 服务探测（httpx 接入）
- Web 指纹识别
- 网页截图存档
- Web 资产管理

---

## 2. 计划任务清单

### 2.1 数据模型

- [x] WebAsset 模型与表结构
- [x] Alembic 迁移脚本（0004_web_assets）

### 2.2 API 与业务逻辑

- [x] Web 资产列表 API（分页/可筛选）
- [x] Web 资产详情 API
- [ ] 截图文件服务（静态文件挂载）

### 2.3 Celery 任务

- [x] HTTP 探测任务（httpx 集成）
- [x] 指纹识别任务
- [x] 截图任务

### 2.4 存储

- [x] 截图文件存储配置（EASM_SCREENSHOT_DIR 环境变量）
- [x] 指纹库数据（内置模式匹配）

---

## 3. 交付物

### 3.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `server/app/models/web_asset.py` | WebAsset 数据模型 |
| `server/app/schemas/web_asset.py` | WebAsset Pydantic 模式 |
| `server/app/crud/web_asset.py` | WebAsset CRUD 操作 |
| `server/app/api/web_assets.py` | Web 资产 API 路由 |
| `server/alembic/versions/0004_web_assets.py` | 数据库迁移脚本 |
| `worker/app/tasks/http_probe.py` | HTTP 探测 Celery 任务 |
| `worker/app/tasks/fingerprint.py` | 指纹识别 Celery 任务 |
| `worker/app/tasks/screenshot.py` | 截图 Celery 任务 |
| `test/test_fingerprint.py` | 指纹识别测试 |
| `test/test_http_probe.py` | HTTP 探测测试 |
| `test/test_web_asset.py` | Web 资产模式测试 |

### 3.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `server/app/schemas/scan_task.py` | 新增 TaskType: http_probe, fingerprint, screenshot |
| `server/app/api/router.py` | 注册 web_assets 路由 |
| `server/app/api/scans.py` | 更新任务分发逻辑 |
| `worker/app/celery_app.py` | 注册新任务模块和路由 |

---

## 4. 验收标准

- [x] 可在 Web 资产列表看到状态码
- [x] 可在 Web 资产列表看到指纹
- [x] 可在 Web 资产列表看到截图链接

---

## 5. 技术实现细节

### 5.1 HTTP 探测

- 优先使用 httpx CLI 工具（如已安装）
- 回退到 Python urllib 实现
- 提取信息：title, status_code, content_length, content_type, server, technologies

### 5.2 指纹识别

- 基于 Server 头识别：Nginx, Apache, IIS, Tomcat
- 基于 Title 识别：WordPress, Drupal, Jenkins, GitLab, Grafana 等 13 种

### 5.3 截图

- 使用 gowitness 工具（如已安装）
- 截图存储路径：`EASM_SCREENSHOT_DIR` 环境变量（默认 `/app/data/screenshots`）
- 文件命名：`{project_id}_{url_hash}.png`

---

## 6. 测试结果

```
test/test_fingerprint.py - 9 passed
test/test_http_probe.py - 8 passed
test/test_web_asset.py - 3 passed
Total: 20 passed
```

---

## 7. 变更记录

| 日期 | 变更内容 |
|-----|---------|
| 2026-01-30 | 完成 WebAsset 模型、Schema、CRUD、API |
| 2026-01-30 | 完成 HTTP 探测、指纹识别、截图 Celery 任务 |
| 2026-01-30 | 完成数据库迁移 0004_web_assets |
| 2026-01-30 | 完成单元测试（20 个测试用例） |
