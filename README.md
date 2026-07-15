# 族谱系统 Family Tree

面向单家族的数字化族谱平台：管理端维护人物与关系，展示端提供世系浏览、人物检索与族人分布地图。

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Vue](https://img.shields.io/badge/vue-3-brightgreen)
![MySQL](https://img.shields.io/badge/mysql-8-orange)

---

## 项目介绍

本项目包含两个子工程：

| 目录 | 说明 | 默认端口 |
|------|------|----------|
| [`genealogy-server`](./genealogy-server) | FastAPI + MySQL + Alembic REST API | `8000` |
| [`genealogy-web`](./genealogy-web) | Vue 3 + Element Plus 管理端 & `/portal` 展示端 | `5173` |

**主要能力：**

- 用户注册登录（JWT）与三角色 RBAC：`member` / `editor` / `admin`
- 家族与人物档案 CRUD，亲属关系（父母、配偶）维护
- 族谱可视化：世系全图 / 男系世系 / 以人为中心（检索与高亮）
- 公开 Portal：家族、族谱、检索、地图（游客可读）
- 地理标记：族群分布点与坟地（高德地图）
- Excel 导入导出人物与关系
- 附件上传与头像

**技术栈摘要：** FastAPI · SQLAlchemy 2 · Pydantic v2 · MySQL 8 · Vue 3 · Vite 5 · Pinia · Element Plus · 高德 JS API

---

## 文档

| 文档 | 链接 |
|------|------|
| 需求文档 | [docs/requirements.md](./docs/requirements.md) |
| 数据库表说明 | [docs/database.md](./docs/database.md) |
| 接口说明 | [docs/api.md](./docs/api.md) |
| 安装部署教程 | [docs/deployment.md](./docs/deployment.md) |
| 依赖说明 | [docs/dependencies.md](./docs/dependencies.md) |
| 文档索引 | [docs/README.md](./docs/README.md) |
| 开发备忘（详细） | [PROJECT.md](./PROJECT.md) |

---

## 快速开始

详细步骤见 **[安装部署教程](./docs/deployment.md)**。摘要如下：

### 1. MySQL

```sql
CREATE DATABASE genealogy DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端

```bash
cd genealogy-server
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # Windows 可用 copy
# 编辑 DATABASE_URL、SECRET_KEY
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 前端

```bash
cd genealogy-web
npm install
# 配置 .env.development / .env.development.local（API、高德 Key）
npm run dev
```

访问：

- 展示端：http://localhost:5173/portal  
- API 文档：http://127.0.0.1:8000/docs  

（可选）示例数据：

```bash
cd genealogy-server
python scripts/seed_sample_data.py
```

---

## 安全提醒（上传 GitHub 前）

- 不要提交 `.env`、`.env.development.local` 或任何真实密钥  
- 高德 Key / 安全密钥仅放本地环境文件  
- 若密钥曾泄露到聊天或提交历史，请在对应平台重置  

仓库已提供根目录 [`.gitignore`](./.gitignore) 忽略常见密钥与构建产物。

---

## 目录结构

```text
familytree/
├── README.md                 # 本文件
├── LICENSE
├── CONTRIBUTING.md
├── PROJECT.md                # 开发总览备忘
├── docs/                     # 正式文档
├── genealogy-server/         # 后端
└── genealogy-web/            # 前端
```

---

## 许可证

[MIT License](./LICENSE)

## 贡献

见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 未完成功能
小程序端orAPP端，多人协作，宗族信息展示，显示搬迁动画，实景照片。
