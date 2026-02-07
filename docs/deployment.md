# EASM 部署文档

## 1. 部署说明

本项目由以下组件组成：

- `api`：FastAPI 服务（默认 `8000`）
- `worker`：Celery Worker（消费 `default,scan` 队列）
- `db`：PostgreSQL 15
- `redis`：Redis 7（Broker/Backend）
- `web`：Vue3 前端（当前为原型页面，可独立部署静态文件）

推荐使用 Docker Compose 进行一体化部署。

## 2. 环境要求

- Docker 24+
- Docker Compose v2+
- （可选）Node.js 20+（构建前端）

## 3. 环境变量配置

项目当前没有提交 `.env.example`，请在仓库根目录手工创建 `.env`：

```bash
cat > .env <<'EOF'
EASM_APP_ENV=dev
EASM_DATABASE_URL=postgresql+psycopg://easm:easm@db:5432/easm
EASM_REDIS_URL=redis://redis:6379/0
EASM_AUTH_ENABLED=true
EASM_API_KEYS=dev-change-me
EASM_API_KEY_PROJECT_MAP=
EASM_SCAN_VERIFY_TLS=true
EOF
```

说明：

- `EASM_API_KEYS` 为 API 访问密钥，多个用英文逗号分隔。
- `EASM_REDIS_URL` 在 docker 网络内必须使用 `redis:6379`。

## 4. Docker Compose 部署（推荐）

### 4.1 启动服务

```bash
docker compose up -d --build
```

### 4.2 执行数据库迁移

```bash
docker compose exec api alembic -c server/alembic.ini upgrade head
```

### 4.3 健康检查

```bash
curl http://localhost:8000/health
```

期望返回：

```json
{"status":"ok"}
```

## 5. 前端部署

### 5.1 本地开发模式

```bash
cd web
npm ci
npm run dev -- --host 0.0.0.0 --port 5173
```

访问：`http://localhost:5173`

### 5.2 生产构建

```bash
cd web
npm ci
npm run build
```

构建产物在 `web/dist`，可由 Nginx/静态服务器托管。

建议同域部署策略：

- `/` -> `web/dist`
- `/api` 或 `/` 下 API 路由 -> 反向代理到 `api:8000`

如果前后端跨域部署，需要在后端增加 CORS 中间件。

## 6. 本地非 Docker 部署（可选）

### 6.1 启动依赖

```bash
docker run -d --name easm-pg -e POSTGRES_DB=easm -e POSTGRES_USER=easm -e POSTGRES_PASSWORD=easm -p 5432:5432 postgres:15
docker run -d --name easm-redis -p 6379:6379 redis:7
```

### 6.2 安装依赖并迁移

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic -c server/alembic.ini upgrade head
```

### 6.3 启动 API 与 Worker

```bash
uvicorn server.app.main:app --host 0.0.0.0 --port 8000
celery -A worker.app.celery_app:celery_app worker -Q default,scan,orchestration,alerting -l info
```

## 7. 部署后检查清单

- `GET /health` 返回 `200`
- `POST /projects` 可成功创建项目（携带 `X-API-Key`）
- 可创建并启动一次扫描任务：`POST /projects/{id}/scans` + `/start`
- Worker 日志无持续报错
- `web/dist` 可正常访问（若部署前端）

## 8. 常见问题

1. `401 invalid or missing api key`
- 检查请求头 `X-API-Key` 是否与 `EASM_API_KEYS` 一致。

2. `database not initialized`
- 未执行 Alembic 迁移，运行 `alembic -c server/alembic.ini upgrade head`。

3. 扫描任务长期 `pending`
- Worker 未启动或未监听对应队列；确认 Worker 启动参数包含 `scan`。

4. 前端请求失败（浏览器跨域）
- 当前后端跨域时，后端需增加 CORS 配置或通过网关同域转发。

