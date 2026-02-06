# 第8轮开发记录（JS 与 API 深度）

> 迭代周期：2周
> 版本目标：API 安全测试与深度 JS 资产分析
> 关联设计：EASM-design-v2.md Phase 4
> 启动日期：2026-02-06

---

## 1. 本轮范围

- JS 文件发现与依赖关系提取
- JS 中 API 端点提取与归一化
- API 风险检测基础规则（鉴权、敏感接口暴露、弱配置）
- 与现有 DAG/事件机制联动（作为可编排任务节点）

---

## 2. 计划任务清单

### 2.1 数据模型与Schema

- [x] JS 资产模型（脚本 URL、哈希、来源页面、版本指纹）
- [x] API 端点模型（路径、方法、参数、鉴权要求）
- [x] API 风险记录模型（规则命中、证据、严重度）

### 2.2 任务执行链路

- [x] JS 深度抓取任务（递归脚本发现）
- [x] 端点抽取任务（静态+正则启发式）
- [x] API 风险检测任务（规则引擎）
- [x] 接入 Celery 队列与 DAG 调度

### 2.3 API 路由

- [x] JS 资产查询 API
- [x] API 端点查询 API
- [x] API 风险查询与确认 API

### 2.4 测试

- [x] 端点提取规则单元测试
- [x] 风险规则单元测试
- [x] 任务链路集成测试（mock）
- [x] 端到端联调测试（scan create/start -> api-risks query）

---

## 3. 本次启动动作

- [x] 第8轮开发计划建立
- [x] 范围与交付边界对齐（JS 与 API 深度能力）
- [x] 与第7轮安全修复并行推进（避免带病迭代）

---

## 4. 里程碑

- M1：完成 JS/API 数据模型与迁移
- M2：完成任务链路与最小可用规则
- M3：完成 API 与测试，进入联调验收

---

## 5. 当前交付（2026-02-06）

- 数据库迁移：`0010_js_api_deep_analysis`，新增 `js_asset`、`api_endpoint`、`api_risk_finding`
- 新增任务：`worker.app.tasks.js_api_discovery.run_js_api_discovery`
- 路由新增：
  - `GET /projects/{project_id}/js-assets`
  - `GET /projects/{project_id}/api-endpoints`
  - `GET /projects/{project_id}/api-risks`
  - `PATCH /projects/{project_id}/api-risks/{finding_id}/status`
- 调度接入：
  - 扫描任务类型 `js_api_discovery`
  - Celery `scan` 队列路由
  - DAG 执行器任务分发映射
- API 风险闭环能力：
  - 状态流转：`open` -> `investigating` -> `resolved` / `false_positive` / `accepted_risk`
  - 审计字段：`updated_by`、`resolution_notes`、`status_history`
