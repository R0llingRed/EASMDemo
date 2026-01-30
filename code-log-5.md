# 第5轮开发记录（可靠性增强）

> 迭代周期：2周
> 版本目标：资产去重、结果可信度、扫描速率控制
> 关联设计：EASM-design-v2.md Phase 2

---

## 1. 本轮范围

- 资产实体统一ID与去重机制
- 扫描结果可信度评分
- 扫描速率控制与配额管理
- 任务优先级队列

---

## 2. 计划任务清单

### 2.1 资产去重

- [x] 资产指纹哈希计算
- [x] 去重策略（域名/IP/URL）
- [x] 资产合并逻辑

### 2.2 可信度评分

- [x] 可信度评分模型
- [x] 多源交叉验证
- [x] 误报标记机制

### 2.3 扫描治理

- [x] 速率限制（QPS/PPS）
- [x] 扫描配额管理
- [x] 任务优先级队列

### 2.4 其他

- [x] 扫描黑白名单
- [ ] 审计日志增强

---

## 3. 交付物

### 3.1 新增文件

| 文件路径 | 说明 |
|---------|------|
| `server/app/utils/fingerprint.py` | 资产指纹哈希计算工具 |
| `server/app/utils/rate_limiter.py` | Redis 分布式速率限制器 |
| `worker/app/utils/scan_helpers.py` | 扫描任务辅助函数 |
| `server/alembic/versions/0006_reliability.py` | 数据库迁移脚本 |
| `test/test_fingerprint_utils.py` | 指纹工具测试（15个用例） |
| `server/app/utils/scan_filter.py` | 扫描黑白名单过滤器 |
| `server/app/utils/vuln_validation.py` | 漏洞可信度评分 |
| `test/test_scan_utils.py` | 扫描工具测试（13个用例） |

### 3.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `server/app/models/subdomain.py` | 添加 fingerprint_hash 字段 |
| `server/app/models/ip_address.py` | 添加 fingerprint_hash 字段 |
| `server/app/models/web_asset.py` | 添加 fingerprint_hash 字段 |
| `server/app/models/project.py` | 添加 rate_limit_config 字段 |
| `server/app/models/vulnerability.py` | 添加 confidence 字段 |
| `server/app/crud/subdomain.py` | 集成指纹哈希计算 |
| `server/app/crud/web_asset.py` | 集成指纹哈希计算 |
| `server/app/models/scan_task.py` | 添加 priority 字段 |
| `server/app/schemas/scan_task.py` | 添加 priority 字段 |

---

## 4. 验收标准

- [ ] 重复资产可自动合并
- [ ] 扫描结果有可信度评分
- [ ] 扫描速率可配置限制

---

## 5. 技术实现细节

### 5.1 资产指纹哈希

- 基于 SHA256 计算，截取前32位
- 输入格式：`{project_id}:{type}:{normalized_value}`
- 支持类型：subdomain, ip, url
- URL 自动标准化（去除默认端口、统一大小写）

### 5.2 可信度评分模型

- 评分范围：0-100
- 默认值：50（中等可信度）
- 影响因素：扫描器类型、多源验证、历史命中

### 5.3 速率限制实现

- 算法：Token Bucket（令牌桶）
- 存储：Redis Sorted Set
- 配置：max_requests_per_second, max_concurrent_scans
- 支持：阻塞等待、剩余配额查询

---

## 6. 测试结果

```
test/test_fingerprint_utils.py - 15 passed
test/test_scan_utils.py - 13 passed
Total: 73 passed
```

---

## 7. 变更记录

| 日期 | 变更内容 |
|-----|---------|
| 2026-01-30 | 创建第5轮开发计划 |
| 2026-01-30 | 完成资产指纹哈希计算与去重 |
| 2026-01-30 | 完成速率限制器实现 |
| 2026-01-30 | 添加可信度评分字段 |
| 2026-01-30 | 完成资产合并逻辑 |
| 2026-01-30 | 完成扫描黑白名单 |
| 2026-01-30 | 完成任务优先级队列 |
| 2026-01-30 | 完成多源验证模块 |
