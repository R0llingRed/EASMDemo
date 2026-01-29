# 第 1 轮测试用例（资产治理基础）

> 目标：验证项目管理、资产导入、去重与分页

## 0. 环境准备

```bash
cp .env.example .env
docker compose up --build
docker compose exec api python -m alembic -c server/alembic.ini upgrade head
```

如果你在本机虚拟环境直接运行 Alembic，需要把 DB host 改为 localhost：

```bash
EASM_DATABASE_URL=postgresql+psycopg://easm:easm@localhost:5432/easm \
  alembic -c server/alembic.ini upgrade head
```

## 1. 创建项目

```bash
curl -s -X POST http://localhost:8000/projects \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Acme-Sec",
    "description": "Acme external assets"
  }'
```

期望：返回 `id/name/created_at/updated_at`。

## 2. 重复创建项目

```bash
curl -s -X POST http://localhost:8000/projects \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Acme-Sec",
    "description": "dup"
  }'
```

期望：`409`，`project already exists`。

## 3. 获取项目 ID

```bash
PROJECT_ID=$(curl -s http://localhost:8000/projects | jq -r '.items[0].id')
echo $PROJECT_ID
```

期望：输出项目 UUID。

## 4. 批量导入资产

```bash
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/assets/import \
  -H 'Content-Type: application/json' \
  -d '{
    "assets": [
      {"asset_type": "domain", "value": "example.com", "source": "manual"},
      {"asset_type": "domain", "value": "api.example.com", "source": "manual"},
      {"asset_type": "ip", "value": "1.2.3.4", "source": "manual"},
      {"asset_type": "url", "value": "https://example.com/login", "source": "manual"}
    ]
  }'
```

期望：`inserted=4, skipped=0, total=4`。

## 5. 重复导入（去重 + 更新 last_seen）

```bash
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/assets/import \
  -H 'Content-Type: application/json' \
  -d '{
    "assets": [
      {"asset_type": "domain", "value": "example.com", "source": "manual"},
      {"asset_type": "ip", "value": "1.2.3.4", "source": "manual"}
    ]
  }'
```

期望：`inserted=0`，`skipped=2`。

## 6. 资产列表分页

```bash
curl -s "http://localhost:8000/projects/$PROJECT_ID/assets?offset=0&limit=2"
```

期望：`total=4`，`items` 长度为 2。

## 7. 按类型过滤

```bash
curl -s "http://localhost:8000/projects/$PROJECT_ID/assets?asset_type=domain"
```

期望：仅返回 `domain` 类型资产。

## 8. 非法资产类型

```bash
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/assets/import \
  -H 'Content-Type: application/json' \
  -d '{
    "assets": [
      {"asset_type": "unknown", "value": "bad.example"}
    ]
  }'
```

期望：`422`，`detail` 中包含 `enum` 校验错误。

## 9. 分页参数越界

```bash
curl -s "http://localhost:8000/projects/$PROJECT_ID/assets?offset=-1&limit=500"
```

期望：`422`，`detail` 中包含 `ge/le` 校验错误。
