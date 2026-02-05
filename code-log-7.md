# 第7轮开发记录（风险评估与告警）

> 迭代周期：2周
> 版本目标：风险评分、告警策略、多渠道通知
> 关联设计：EASM-design-v2.md Phase 4

---

## 1. 本轮范围

- 资产风险评分（AssetRiskScore）
- 风险因子管理（RiskFactor）
- 告警策略（AlertPolicy）
- 告警记录（AlertRecord）
- 通知渠道（NotificationChannel）
- 多渠道通知发送（Email, Webhook, 钉钉, 飞书, 企业微信）

---

## 2. 计划任务清单

### 2.1 数据模型

- [x] RiskFactor 风险因子模型
- [x] AssetRiskScore 资产风险评分模型
- [x] NotificationChannel 通知渠道模型
- [x] AlertPolicy 告警策略模型
- [x] AlertRecord 告警记录模型
- [x] Alembic 迁移脚本（0008_risk_and_alerts）

### 2.2 Schema 定义

- [x] RiskScore Schema
- [x] Alert Schema
- [x] NotificationChannel Schema

### 2.3 CRUD 操作

- [x] RiskFactor CRUD
- [x] AssetRiskScore CRUD（含统计功能）
- [x] NotificationChannel CRUD
- [x] AlertPolicy CRUD
- [x] AlertRecord CRUD（含聚合、冷却）

### 2.4 API 路由

- [x] 风险因子 API（/projects/{project_id}/risk/factors）
- [x] 风险评分 API（/projects/{project_id}/risk/scores）
- [x] 风险统计 API（/projects/{project_id}/risk/statistics）
- [x] 告警策略 API（/projects/{project_id}/alerts/policies）
- [x] 告警记录 API（/projects/{project_id}/alerts）
- [x] 通知渠道 API（/projects/{project_id}/notification-channels）

### 2.5 Celery 任务

- [x] 风险评分计算任务（risk_calculator）
- [x] 告警检测任务（alerter）
- [x] 多渠道通知任务（notifier）

### 2.6 测试

- [x] 风险评分单元测试（17 个用例）
- [x] 告警系统单元测试（22 个用例）

---

## 3. 交付物

### 3.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `server/app/models/risk_score.py` | 风险评分模型 |
| `server/app/models/alert.py` | 告警相关模型 |
| `server/app/schemas/risk_score.py` | 风险评分 Schema |
| `server/app/schemas/alert.py` | 告警 Schema |
| `server/app/crud/risk_score.py` | 风险评分 CRUD |
| `server/app/crud/alert.py` | 告警 CRUD |
| `server/app/api/risk.py` | 风险评分 API |
| `server/app/api/alerts.py` | 告警 API |
| `server/app/api/notifications.py` | 通知渠道 API |
| `server/alembic/versions/0008_risk_and_alerts.py` | 数据库迁移 |
| `worker/app/tasks/risk_calculator.py` | 风险计算 Celery 任务 |
| `worker/app/tasks/alerter.py` | 告警检测 Celery 任务 |
| `worker/app/tasks/notifier.py` | 通知发送 Celery 任务 |
| `test/test_risk_score.py` | 风险评分测试（17用例） |
| `test/test_alert.py` | 告警测试（22用例） |

### 3.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `server/app/api/router.py` | 注册 risk, alerts, notifications 路由 |
| `worker/app/celery_app.py` | 注册 risk_calculator, alerter, notifier 任务，新增 alerting 队列 |

---

## 4. 验收标准

- [x] 可配置风险因子及权重
- [x] 可触发项目级风险评分计算
- [x] 可创建告警策略（严重度阈值、通知渠道）
- [x] 告警支持聚合和冷却机制
- [x] 可配置多种通知渠道（Webhook, 钉钉, 飞书, 企业微信）
- [x] 告警可确认和解决

---

## 5. 技术实现细节

### 5.1 风险评分算法

```python
# 风险因子示例
factors = [
    {"factor_type": "vulnerability", "weight": 0.6},  # 漏洞因子
    {"factor_type": "exposure", "weight": 0.4},       # 暴露因子
]

# 综合评分 = Σ(factor_score * weight) / Σ(weight)
# 结果范围 0-100
```

### 5.2 严重度等级阈值

| 分数范围 | 严重度 |
|---------|--------|
| 80-100 | critical |
| 60-79 | high |
| 40-59 | medium |
| 20-39 | low |
| 0-19 | info |

### 5.3 告警聚合机制

- 使用 aggregation_key 标识可聚合的告警
- 在 aggregation_window 分钟内的相同告警会合并
- 冷却期内（cooldown_minutes）不重复发送同类告警

### 5.4 通知渠道配置

```python
# Webhook 配置
{"url": "https://example.com/webhook", "headers": {"Authorization": "Bearer xxx"}}

# 钉钉配置
{"webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx", "at_all": False}

# 飞书配置
{"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"}

# 企业微信配置
{"webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"}
```

### 5.5 新增 Celery 队列

- `alerting` 队列：风险计算、告警检测、通知发送任务

---

## 6. 测试结果

```
test/test_risk_score.py - 17 passed
test/test_alert.py - 22 passed
Total: 39 passed
```

---

## 7. 变更记录

| 日期 | 变更内容 |
|-----|---------| 
| 2026-02-05 | 创建第7轮开发计划 |
| 2026-02-05 | 完成 RiskFactor, AssetRiskScore, AlertPolicy, AlertRecord, NotificationChannel 模型 |
| 2026-02-05 | 完成所有 Schema、CRUD、API 模块 |
| 2026-02-05 | 完成数据库迁移 0008_risk_and_alerts |
| 2026-02-05 | 完成风险计算、告警检测、通知发送 Celery 任务 |
| 2026-02-05 | 完成单元测试（39 个测试用例） |
