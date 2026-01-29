# 第1轮开发记录（资产治理基础）

> 迭代周期：2周
> 版本目标：项目/资产导入、资产实体模型（domain/ip/url）最小可用
> 关联设计：EASM-design-v2.md

---

## 1. 本轮范围

- 项目管理 API
- 资产导入 API（批量）
- 资产实体模型与基础去重
- 资产列表分页

---

## 2. 计划任务清单

### 2.1 数据模型

- [x] Project 模型与表结构
- [x] AssetEntity 模型与表结构
- [x] Alembic 迁移脚本

### 2.2 API 与业务逻辑

- [x] 项目创建 API
- [x] 项目列表 API（分页）
- [x] 资产批量导入 API
- [x] 资产列表 API（分页/可筛选）

### 2.3 去重与约束

- [x] 资产唯一约束（project_id + asset_type + value）
- [x] 批量导入冲突忽略

---

## 3. 交付物

- `server/app/models/project.py`
- `server/app/models/asset_entity.py`
- `server/app/api/projects.py`
- `server/app/api/assets.py`
- `server/alembic/versions/0002_assets.py`

---

## 4. 验收标准

- [ ] 批量导入可用
- [ ] 重复资产不重复入库
- [ ] 列表分页可用

---

## 5. 变更记录

### 2026-01-29

- 初始化 Project 与 AssetEntity 模型
- 增加项目与资产 API
- 支持资产批量导入与分页列表
- 增加 Alembic 迁移脚本（0002_assets）
