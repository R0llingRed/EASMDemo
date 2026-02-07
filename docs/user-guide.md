# EASM 用户使用文档

## 1. 使用入口

- API 文档（Swagger）：`http://<API_HOST>:8000/docs`
- 健康检查：`GET /health`
- 前端入口（若已部署）：`http://<WEB_HOST>`

注意：当前前端页面为原型壳，核心能力建议优先通过 API 使用。

## 2. 认证方式

除 `/health` 外，接口默认需要 API Key：

- Header：`X-API-Key: <your-api-key>`

示例：

```bash
export API=http://localhost:8000
export KEY=dev-change-me
```

## 3. 标准操作流程

### 3.1 创建项目

```bash
curl -s -X POST "$API/projects" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"demo-project","description":"first project"}'
```

记录返回的 `project_id`。

### 3.2 导入资产

```bash
curl -s -X POST "$API/projects/<project_id>/assets/import" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "assets":[
      {"asset_type":"domain","value":"example.com","source":"manual"},
      {"asset_type":"ip","value":"8.8.8.8","source":"manual"},
      {"asset_type":"url","value":"https://example.com","source":"manual"}
    ]
  }'
```

### 3.3 创建扫描策略（可选）

```bash
curl -s -X POST "$API/projects/<project_id>/policies" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"default-policy",
    "is_default": true,
    "enabled": true,
    "scan_config": {"batch_size": 100}
  }'
```

### 3.4 创建并启动扫描任务

常见 `task_type`：

- `subdomain_scan`
- `dns_resolve`
- `port_scan`
- `http_probe`
- `fingerprint`
- `screenshot`
- `nuclei_scan`
- `xray_scan`
- `js_api_discovery`

创建：

```bash
curl -s -X POST "$API/projects/<project_id>/scans" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type":"js_api_discovery",
    "config":{"batch_size":50},
    "priority":8
  }'
```

启动：

```bash
curl -s -X POST "$API/projects/<project_id>/scans/<task_id>/start" \
  -H "X-API-Key: $KEY"
```

### 3.5 查看扫描结果

资产与探测结果：

- `GET /projects/{project_id}/subdomains`
- `GET /projects/{project_id}/ips`
- `GET /ips/{ip_id}/ports`
- `GET /projects/{project_id}/web-assets`
- `GET /projects/{project_id}/js-assets`
- `GET /projects/{project_id}/api-endpoints`

风险与漏洞：

- `GET /projects/{project_id}/vulnerabilities`
- `GET /projects/{project_id}/vulnerabilities/stats`
- `GET /projects/{project_id}/api-risks`

### 3.6 风险处置

更新 API 风险状态（闭环）：

```bash
curl -s -X PATCH "$API/projects/<project_id>/api-risks/<finding_id>/status" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status":"resolved",
    "updated_by":"secops@example.com",
    "resolution_notes":"fixed in release 1.0.3"
  }'
```

说明：

- `resolved` 与 `false_positive` 必须传 `resolution_notes`。

### 3.7 风险评分

触发计算：

```bash
curl -s -X POST "$API/projects/<project_id>/risk/scores/calculate" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"force_recalculate":true}'
```

查询：

- `GET /projects/{project_id}/risk/scores`
- `GET /projects/{project_id}/risk/statistics`

### 3.8 告警与通知

1. 创建通知渠道：`POST /projects/{project_id}/notification-channels`
2. 测试通知：`POST /projects/{project_id}/notification-channels/{channel_id}/test`
3. 创建告警策略：`POST /projects/{project_id}/alerts/policies`
4. 查看告警：`GET /projects/{project_id}/alerts`
5. 告警确认/解决：
- `POST /projects/{project_id}/alerts/{alert_id}/acknowledge`
- `POST /projects/{project_id}/alerts/{alert_id}/resolve`

## 4. 高级编排（DAG + 事件）

1. 创建 DAG 模板：`POST /projects/{project_id}/dag-templates`
2. 创建执行实例：`POST /projects/{project_id}/dag-executions`
3. 启动执行：`POST /projects/{project_id}/dag-executions/{execution_id}/start`
4. 创建事件触发器：`POST /projects/{project_id}/event-triggers`
5. 发送事件：`POST /projects/{project_id}/events/emit`

## 5. 前端页面说明（当前版本）

当前页面包含：

- Dashboard
- Projects
- Assets
- Risks
- Tasks
- Settings

现阶段主要用于导航和布局展示，业务数据尚未对接后端 API。

## 6. 常见返回码

- `200/201/202`：成功
- `400`：参数错误或状态不允许
- `401`：API Key 缺失/无效
- `403`：API Key 无项目访问权限
- `404`：资源不存在
- `422`：请求体校验失败
- `503`：数据库未初始化或不可用

