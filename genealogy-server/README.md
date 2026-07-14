# genealogy-server

族谱系统后端服务（v1）。

## 技术栈

- FastAPI + SQLAlchemy 2.0 + Pydantic v2
- MySQL 8.0 + Alembic
- JWT 鉴权

## 项目结构

```text
genealogy-server/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # config / security / deps
│   ├── db/                  # SQLAlchemy Base + Session
│   ├── models/              # ORM 模型
│   ├── schemas/             # Pydantic DTO
│   ├── api/                 # 路由
│   ├── services/            # 业务逻辑
│   └── utils/               # 统一响应 / 异常
├── alembic/                 # 数据库迁移
├── uploads/                 # 本地上传目录
├── requirements.txt
└── .env.example
```

## 快速开始

```powershell
cd genealogy-server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env：填入 MySQL 密码和 SECRET_KEY
```

MySQL 建库：

```sql
CREATE DATABASE genealogy
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

执行迁移并启动：

```powershell
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API 文档：http://localhost:8000/docs

## 第一阶段验收

```text
POST /api/auth/register  -> 注册用户
POST /api/auth/login     -> 获取 access_token
GET  /api/auth/me        -> Bearer token 获取当前用户
```

示例：

```powershell
# 注册
curl -X POST http://localhost:8000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{"username":"zhangsan","password":"123456","nickname":"张三"}'

# 登录
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"username":"zhangsan","password":"123456"}'

# 获取当前用户（替换 <token>）
curl http://localhost:8000/api/auth/me `
  -H "Authorization: Bearer <token>"
```

## 当前进度

- [x] 项目脚手架与目录结构
- [x] config / db / security / deps
- [x] users 模型 + Alembic 初始迁移
- [x] 注册 / 登录 / me 接口（联调通过）
- [x] families 表 + CRUD + owner 校验（联调通过）
- [x] persons 表 + CRUD + 筛选查询（联调通过）  
- [x] person_relations 表 + parent/spouse 关系 + sibling 推导（联调通过）
- [x] tree/full、tree/ancestors、tree/descendants（MVP 闭环通过）
- [x] 附件上传 R6：本地上传、StaticFiles、头像回写、删除同步清磁盘（联调通过）
- [x] Excel 导入导出 R7：人物/关系模板导入、导出、行级错误反馈（联调通过）

**后端 v1 全部完成。下一步：genealogy-web 前端。**

## 本地环境说明

本机已探测到：

```text
MySQL: D:\Develop\mysql-8.0.34-winx64
root 密码: 123456（已写入 .env）
数据库: genealogy
```

若 pip 因 SSL 失败，可使用离线安装脚本：

```powershell
.\.venv\Scripts\python scripts\install_offline_ps.py
```

密码哈希使用 `bcrypt` 直接实现（未使用 passlib，避免与 bcrypt 5.x 兼容问题）。

## 联调脚本

```powershell
# R1 认证
.\.venv\Scripts\python scripts\smoke_auth.py

# R2 家族
.\.venv\Scripts\python scripts\smoke_family.py

# R3 人物
.\.venv\Scripts\python scripts\smoke_person.py

# R4+R5 MVP 闭环（注册→家族→人物→关系→族谱树）
.\.venv\Scripts\python scripts\smoke_mvp.py

# R6 附件上传
.\.venv\Scripts\python scripts\smoke_media.py

# R7 Excel 导入导出
.\.venv\Scripts\python scripts\smoke_import_export.py
```
