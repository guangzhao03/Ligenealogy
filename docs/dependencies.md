# 依赖说明

## 1. 后端（`genealogy-server/requirements.txt`）

| 包 | 用途 |
|----|------|
| fastapi | Web 框架 |
| uvicorn[standard] | ASGI 服务器 |
| sqlalchemy>=2.0 | ORM |
| pymysql | MySQL 驱动 |
| cryptography | MySQL/TLS 与安全相关 |
| pydantic>=2.0 | 请求/响应校验 |
| pydantic-settings | `.env` 配置 |
| python-jose[cryptography] | JWT |
| bcrypt | 密码哈希（直接使用，不用 passlib） |
| python-multipart | 文件上传 |
| openpyxl | Excel 导入导出 |
| alembic | 数据库迁移 |

安装：

```bash
cd genealogy-server
python -m venv .venv
# 激活 venv 后
pip install -r requirements.txt
```

建议 Python **3.10+**。

## 2. 前端（`genealogy-web/package.json`）

### 运行时依赖

| 包 | 用途 |
|----|------|
| vue | UI 框架 |
| vue-router | 路由 |
| pinia | 状态管理 |
| axios | HTTP |
| element-plus | UI 组件库 |
| @element-plus/icons-vue | 图标 |
| @amap/amap-jsapi-loader | 高德地图 JS API 加载器 |
| @antv/g6 | 图可视化依赖（历史引入；主族谱树为 SVG 自绘） |
| @dagrejs/dagre | 图布局相关工具 |

### 开发依赖

| 包 | 用途 |
|----|------|
| vite | 构建与开发服务器 |
| typescript | 类型系统 |
| vue-tsc | Vue TS 检查 |
| @vitejs/plugin-vue | Vite Vue 插件 |
| @types/node | Node 类型 |
| @vue/tsconfig | TS 基础配置 |

安装：

```bash
cd genealogy-web
npm install
```

建议 Node.js **18+**。当前 Vite 锁定在 5.x（Windows 环境下更高版本曾有绑定问题）。

## 3. 外部服务（非 npm/pip）

| 服务 | 说明 |
|------|------|
| MySQL 8 | 业务数据库 |
| 高德地图 Web JS API | 展示端/管理端地图；需自行申请 Key |

## 4. 许可证注意

第三方库均遵循各自开源许可证（MIT / Apache 等）。高德地图使用须遵守[高德开放平台服务条款](https://lbs.amap.com/)。本仓库代码默认 MIT（见根目录 `LICENSE`）。
