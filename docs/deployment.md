# 安装与部署教程

## 1. 环境要求

| 组件 | 版本建议 |
|------|----------|
| 操作系统 | Windows 10+ / Linux / macOS |
| Python | 3.10+ |
| Node.js | 18+（推荐 20 LTS） |
| MySQL | 8.0+ |
| 可选 | 高德开放平台「Web 端(JS API)」Key |

## 2. 获取代码

```bash
git clone <你的仓库地址>.git
cd familytree
```

仓库结构：

```text
familytree/
├── genealogy-server/   # 后端 FastAPI
├── genealogy-web/      # 前端 Vue3
├── docs/               # 文档
└── README.md
```

## 3. 数据库准备

```sql
CREATE DATABASE genealogy DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

记下账号密码，填入后端 `.env` 的 `DATABASE_URL`。

## 4. 后端安装与启动

```bash
cd genealogy-server
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env      # Linux: cp .env.example .env
```

编辑 `genealogy-server/.env`：

```env
DATABASE_URL=mysql+pymysql://用户:密码@127.0.0.1:3306/genealogy?charset=utf8mb4
SECRET_KEY=请换成足够长的随机串
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=uploads
# 可选：固定 Portal 展示家族
# DISPLAY_FAMILY_ID=6
# PUBLIC_REQUIRE_AUTH=false
```

执行迁移：

```bash
alembic upgrade head
```

（可选）写入李氏示例数据：

```bash
python scripts/seed_sample_data.py --family-id <已有家族ID>
```

启动：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

验证：

- 健康检查：http://127.0.0.1:8000/health  
- Swagger：http://127.0.0.1:8000/docs  

## 5. 前端安装与启动

```bash
cd genealogy-web
npm install
copy .env.example .env.development   # 或直接使用 .env.development
```

编辑环境变量（开发）：

```env
VITE_API_BASE_URL=
# 留空表示同源代理或相对路径（视 vite 配置）；若后端独立端口，可写 http://127.0.0.1:8000

# 高德地图（Portal / 管理端地图与点选）
VITE_AMAP_KEY=你的Web端Key
VITE_AMAP_SECURITY_CODE=你的安全密钥
```

建议将含密钥的内容放在 **`.env.development.local`**（已被 gitignore），不要提交到 GitHub。

启动：

```bash
npm run dev
```

默认：http://localhost:5173/

- 展示端：`/portal`  
- 管理后台：登录后（admin）进入 `/families` 等  

首次使用：注册账号 → 创建家族 → 录入人物关系；或在后端写入 seed 后把 `DISPLAY_FAMILY_ID` 指到该家族。

### 高德控制台注意

1. 申请 **Web 端(JS API)** Key  
2. 配置安全密钥（securityJsCode）  
3. 域名白名单增加 `localhost`、`127.0.0.1`（或调试期使用 `*`）  

## 6. 生产构建（简要）

### 前端

```bash
cd genealogy-web
npm run build
# 产物在 dist/，用 Nginx 托管，API 反代到后端
```

Nginx 示例要点：

- `/` → `dist` 静态资源，`try_files` 回退 `index.html`（SPA）
- `/api`、`/uploads` → 反代 `http://127.0.0.1:8000`

### 后端

```bash
cd genealogy-server
# 关闭 reload，绑定内网或 Unix socket，前加进程管理（systemd / supervisor）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

生产务必：

- 更换强 `SECRET_KEY`
- 限制 CORS（`genealogy-server/app/core/config.py` / 环境变量）
- MySQL 独立账号最小权限
- 备份 `uploads` 与数据库

## 7. 常见问题

| 现象 | 排查 |
|------|------|
| 接口 404 / 旧数据 | 确认已执行 `alembic upgrade head`，并重启 uvicorn |
| 登录成功但后台进不去 | 账号 `role` 是否为 `admin`（创建家族后的 owner 会按迁移策略成为 admin） |
| 地图灰屏有标记 | 检查 Key、安全密钥、域名白名单；强制刷新前端 |
| 端口占用 | Windows：`Get-NetTCPConnection -LocalPort 8000` 结束占用进程 |
| CORS | 开发时前后端端口不同需在后端配置允许的 origins |

## 8. 开发端口一览

| 服务 | 端口 |
|------|------|
| 后端 API | 8000 |
| 前端 Vite | 5173 |
