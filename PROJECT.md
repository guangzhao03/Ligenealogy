# 族谱系统（Family Tree）项目总览



> 本文档用于快速熟悉项目现状。最后更新：2026-07-14  
> 正式对外文档请优先查看 [`docs/`](./docs/) 与根目录 [`README.md`](./README.md)。



---



## 1. 项目简介



这是一个**个人/单家族族谱管理系统**，支持：



- 用户注册登录（JWT）

- 家族创建与管理（按 `owner_id` 归属）

- 人物档案 CRUD（姓名、小名、辈分、出生年份等）

- 亲属关系维护（父母、配偶；兄弟姐妹由共同父母推导）

- **族谱树可视化**（世系全图 / 男系世系 / 以人为中心 / 向上查祖 / 向下查孙）

- 头像/附件上传

- Excel 批量导入导出人物与关系

- **公开展示端 Portal**（`/portal`）：游客免登录只读；登录共用 JWT

- **RBAC 三角色**：`member` 普通族民 / `editor` 信息发布员 / `admin` 管理员（层级包含，后续看板写权限挂 editor+）



**典型使用场景：** 用户管理 **一个大家族**，数据量可达 **二十多代**。管理端负责录入维护；展示端面向族人/访客只读浏览。系统针对此场景做了唯一家族自动选中、按世代深度加载、男系世系等优化。



**示例数据：** 李氏大家族（河南新乡卫滨区平原镇），6 代 24 人，可通过 `scripts/seed_sample_data.py` 写入。



---



## 2. 仓库结构



本工作区包含 **两个独立子项目**（非 monorepo，各自有 README）：



```text

familytree/

├── PROJECT.md              ← 本文档（总览）

├── genealogy-server/       ← 后端 FastAPI（v1 功能完整）

└── genealogy-web/          ← 前端 Vue3（主要功能已实现）

```



| 子项目 | 说明 | 默认端口 |

|--------|------|----------|

| `genealogy-server` | REST API + MySQL + 文件上传 | `8000` |

| `genealogy-web` | SPA 前端：管理端 + 公开展示端 `/portal` | `5173` |



---



## 3. 技术栈



### 后端 `genealogy-server`



| 类别 | 技术 |

|------|------|

| 框架 | FastAPI |

| ORM | SQLAlchemy 2.0 |

| 校验 | Pydantic v2 |

| 数据库 | MySQL 8.0 |

| 迁移 | Alembic |

| 认证 | JWT（python-jose）+ bcrypt 直调（**不用 passlib**，避免与 bcrypt 5.x 冲突） |

| Excel | openpyxl |

| 静态文件 | FastAPI StaticFiles → `/uploads` |



### 前端 `genealogy-web`



| 类别 | 技术 |

|------|------|

| 框架 | Vue 3 + TypeScript |

| 构建 | Vite 5.4.11（**已从 Vite 8 降级**，Windows 上 rolldown 绑定有问题） |

| UI | Element Plus |

| 状态 | Pinia |

| 路由 | Vue Router 4 |

| HTTP | Axios |

| 族谱图 | **SVG 自绘** + `genealogyLayout.ts` 树形布局（已从 G6 重构） |



UI 风格参考 [pure-genealogy](https://github.com/yunfengsa/pure-genealogy)：深色侧栏、纸纹背景、按世代渐变色（松柏绿系）。



---



## 4. 权限与数据模型（v1）



### 权限



- **v1 仅支持单用户拥有家族**：`families.owner_id = users.id`

- 暂无 `family_members` 多成员协作表

- 所有业务 API 需 Bearer Token，并校验 `owner_id`



### 核心表



```text

users              用户

families           家族（owner_id → users.id）

persons            人物

person_relations   亲属关系

media              附件（头像等）

```



### 关系类型（DB 仅存两种）



| 类型 | 方向 | 说明 |

|------|------|------|

| `parent` | from → to | from 是 to 的父母 |

| `spouse` | 双向存一条 | 配偶关系 |



**兄弟姐妹**：不存表，由「有相同 parent」在后端推导。



### 人物字段 `persons`



| 字段 | 类型 | 必填 | 说明 |

|------|------|------|------|

| `name` | string | ✅ | 姓名 |

| `nickname` | string | ✅ | 小名，展示时用括号：`张三（狗娃）` |

| `generation` | int | ✅ | 辈分 / 第几代 |

| `birth_year` | int | ✅ | 出生年份 |

| `gender` | 0/1/2 | | 未知/男/女 |

| `birth_date` | date | | 可选精确日期 |

| `death_date` | date | | |

| `birthplace` | string | | 籍贯 |

| `biography` | text | | 简介 |

| `remark` | text | | 备注 |

| `is_alive` | 0/1 | | 是否在世 |

| `avatar_url` | string | | 头像 URL |



> 迁移 `006` 新增 `nickname`、`birth_year`。旧数据 `nickname` 可能为空，需在前端补全。



---



## 5. 数据库迁移（Alembic）



| Revision | 文件 | 内容 |

|----------|------|------|

| 001 | `001_create_users` | 用户表 |

| 002 | `002_create_families` | 家族表 |

| 003 | `003_create_persons` | 人物表 |

| 004 | `004_create_person_relations` | 关系表 |

| 005 | `005_create_media` | 附件表 |

| 006 | `006_add_person_nickname_birth_year` | 小名、出生年份 |



**首次 / 更新后执行：**



```powershell

cd genealogy-server

alembic upgrade head

```



---



## 6. 后端 API 一览



统一响应格式：



```json

{ "code": 0, "message": "ok", "data": { ... } }

```



业务异常也返回 HTTP 200，`code != 0`（HTTP 404 仅表示路由不存在，多见于旧后端进程未重启）。



### 认证 `/api/auth`



| 方法 | 路径 | 说明 |

|------|------|------|

| POST | `/register` | 注册 |

| POST | `/login` | 登录，返回 `access_token` |

| GET | `/me` | 当前用户（含 `role`） |



### 角色与权限



| 角色码 | 显示名 | 能力 |

|--------|--------|------|

| `member` | 普通族民 | 登录后展示端；后续看板可读更多 |

| `editor` | 信息发布员 | 含 member；后续可发布/编辑看板 |

| `admin` | 管理员 | 含 editor；后台 CRUD + 用户角色管理 |



游客仍可阅览 `/portal` 与 `/api/public/*`。管理 API 需 `admin`。注册默认 `member`；家族 owner 迁移回填为 `admin`。



### 用户 `/api/users`（仅 admin）



| 方法 | 路径 | 说明 |

|------|------|------|

| GET | `/` | 用户列表 |

| PUT | `/{id}/role` | 修改角色（禁止取消最后一个 admin） |



### 公开展示 `/api/public`（免登录只读）



配置 `DISPLAY_FAMILY_ID` 可固定展示家族；未配置则自动选择人物最多的家族。`OptionalUserDep` 已预留，`PUBLIC_REQUIRE_AUTH=true` 时可强制登录。



| 方法 | 路径 | 说明 |

|------|------|------|

| GET | `/family` | 家族概况 + stats |

| GET | `/persons` | 人物搜索分页 |

| GET | `/persons/{id}` | 人物详情 |

| GET | `/persons/{id}/relations` | 亲属 |

| GET | `/tree/full` | 世系全图 |

| GET | `/tree/patrilineal` | 男系世系 |

| GET | `/tree/lineage` | 以人为中心 |

| GET | `/tree/person` | 统一指定人物树 |



### 家族 `/api/families`



| 方法 | 路径 | 说明 |

|------|------|------|

| POST | `/` | 创建家族 |

| GET | `/` | 我的家族列表 |

| GET | `/{id}` | 家族详情 |

| GET | `/{id}/stats` | 统计：总人数、男女数、世代跨度 |

| PUT | `/{id}` | 更新 |

| DELETE | `/{id}` | 删除 |



### 人物 `/api/persons`



| 方法 | 路径 | 说明 |

|------|------|------|

| POST | `/` | 创建（name/nickname/generation/birth_year 必填） |

| GET | `/` | 分页列表，支持 `family_id`、`keyword`、`generation`；**page_size 最大 100** |

| GET | `/{id}` | 详情 |

| PUT | `/{id}` | 更新 |

| DELETE | `/{id}` | 删除（级联清理 media） |

| GET | `/{id}/relations` | 父母/子女/配偶/兄弟姐妹 |

| GET | `/{id}/media` | 附件列表 |



### 关系 `/api/relations`



| 方法 | 路径 | 说明 |

|------|------|------|

| POST | `/` | 创建 parent 或 spouse |

| DELETE | `/{id}` | 删除 |



### 族谱树 `/api/tree`



| 方法 | 路径 | 说明 |

|------|------|------|

| GET | `/full?family_id=` | 世系全图（**大家族慎用**，一次加载全部） |

| GET | `/person?family_id=&person_id=&direction=&up_generations=&down_generations=` | **统一指定人物接口**；`direction`: `center` / `ancestors` / `descendants` / `patrilineal` |

| GET | `/patrilineal?family_id=&root_person_id=&max_generations=` | 男系世系，默认深度 12 |

| GET | `/lineage?family_id=&person_id=&up_generations=&down_generations=` | 以人为中心（含配偶、兄弟姐妹） |

| GET | `/ancestors?family_id=&start_generation=&max_generations=&person_id=` | 向上查祖 |

| GET | `/descendants?family_id=&start_generation=&max_generations=&person_id=` | 向下查孙 |



> **注意：** 指定 `person_id` 查祖先/后代时，需同时传 `start_generation`（人物所在辈分），否则旧版后端可能返回 422。



**族谱树业务规则：**



1. **男系世系 `patrilineal`**

   - 以指定祖先向下展示男系主脉

   - 女儿会显示，但**不延续其后代**

   - 配偶标注在节点上（`spouse_name` / `spouse_nickname`）



2. **以人为中心 `lineage` / `person?direction=center`**

   - 指定人物为焦点，向上/向下各 N 世

   - 包含配偶、兄弟姐妹及配偶关系边

   - 响应含 `focus_person_id`



3. **祖先/后代树**

   - 指定 `person_id` 时以该人为锚点

   - `max_generations` 控制向上/向下深度



4. **世系全图 `full`**

   - 前端可按 `viewGenFrom` / `viewGenTo` 过滤显示辈分范围

   - 布局按 `generation` 分行，子女居中于父母下方



5. **树节点 `TreeNode` 字段**

   - `label`：已格式化，如 `张三（狗娃）`

   - `name`, `nickname`, `birth_year`, `generation`

   - `is_main_line`：是否男系主脉

   - `spouse_name`, `spouse_nickname`



### 附件 `/api/media`



| 方法 | 路径 | 说明 |

|------|------|------|

| POST | `/upload` | 上传（multipart，可设头像） |

| DELETE | `/{id}` | 删除 |



静态访问：`http://127.0.0.1:8000/uploads/...`



### 导入导出



| 方法 | 路径 | 说明 |

|------|------|------|

| POST | `/api/import/persons` | Excel 导入人物 |

| POST | `/api/import/relations` | Excel 导入关系 |

| GET | `/api/export/persons?family_id=` | 导出人物 |

| GET | `/api/export/relations?family_id=` | 导出关系 |



**人物 Excel 表头（当前）：**



```text

姓名, 小名, 性别, 辈分, 出生年份, 出生日期, 去世日期, 籍贯, 简介, 备注, 是否在世

```



---



## 7. 后端目录与关键文件



```text

genealogy-server/app/

├── main.py                    # 路由注册 + CORS + /uploads 静态目录

├── core/

│   ├── config.py              # .env 配置

│   ├── security.py            # JWT + bcrypt

│   └── deps.py                # DbDep, CurrentUserDep

├── models/

├── schemas/

├── api/

│   └── tree.py                # 族谱树路由（含 /person、/lineage）

└── services/

    ├── family_service.py      # owner 校验 + stats

    ├── tree_service.py        # ★ 族谱图构建核心

    └── ...

```



**`tree_service.py` 是族谱核心**，包含：



- `get_patrilineal_tree()` — 男系裁剪 + 深度限制

- `get_lineage_tree()` — 以人为中心（含配偶、兄弟姐妹）

- `get_person_tree()` — 统一指定人物入口（按 direction 分发）

- `get_ancestors_tree()` / `get_descendants_tree()` — 按辈分/人物查祖查孙

- `get_full_tree()` — 全量图



**脚本：**



| 脚本 | 说明 |

|------|------|

| `scripts/seed_sample_data.py` | 清空并写入李氏示例族谱（24 人） |

| `scripts/test_person_tree.py` | 测试 `/api/tree/person` 四种 direction |



```powershell

cd genealogy-server

.\.venv\Scripts\python scripts/seed_sample_data.py --family-id 6

.\.venv\Scripts\python scripts/test_person_tree.py

```



---



## 8. 前端结构与页面



```text

genealogy-web/src/

├── main.ts

├── router/index.ts

├── stores/

│   ├── auth.ts

│   ├── family.ts              # 管理端 currentFamily

│   └── portal.ts              # 展示端家族概况缓存

├── api/

│   ├── tree.ts

│   └── public.ts              # /api/public/*

├── components/

│   ├── layout/AppLayout.vue   # 管理端侧栏

│   ├── layout/PortalLayout.vue # 展示端顶栏

│   └── tree/FamilyTree.vue

└── views/

    ├── family/ / person/ / tree/ / import/   # 管理端

    └── portal/

        ├── PortalHomeView.vue

        ├── PortalTreeView.vue

        └── PortalPersonView.vue



```



### 路由



| 路径 | 页面 | 说明 |

|------|------|------|

| `/login` | 登录 | 公开；链到展厅 |

| `/register` | 注册 | 公开 |

| `/portal` | 家族展厅首页 | **公开展示** |

| `/portal/tree` | 族谱浏览 | 公开只读 |

| `/portal/person/:id` | 人物档案 | 公开只读 |

| `/families` | 家族概览 | 管理端，需登录 |

| `/persons` | 人物管理 | 管理端 |

| `/tree` | 族谱树 | 管理端 |

| `/users` | 用户权限 | 管理端，改角色 |

| `/import-export` | 导入导出 | |



### 族谱树（TreeView）五种模式



| 模式 | 前端 API | 说明 |

|------|----------|------|

| 世系全图 | `fetchFullTree` | 全族按辈分树形展示，可筛选起止世 |

| 男系世系 | `fetchPatrilinealTree` | 指定人物为根，向下 N 世 |

| 以人为中心 | `fetchCenterPersonTree` | 向上/向下各 N 世；**兼容旧后端**（见下） |

| 向上查祖 | `fetchAncestorsTree` | 需传 `start_generation` |

| 向下查孙 | `fetchDescendantsTree` | 需传 `start_generation` |



**指定人物交互：** 文本框 + 自动建议 + 查询按钮；切换模式时静默解析当前搜索框中的人物。



**`fetchCenterPersonTree` 兼容策略**（`api/tree.ts`）：



1. 优先 `/api/tree/person?direction=center`

2. 其次 `/api/tree/lineage`

3. 若均 404，合并 `/ancestors` + `/descendants` 结果作为 fallback



### SVG 族谱图（FamilyTree.vue）



- 左侧世代标尺（第一世、第二世…）

- 节点卡片：姓名（小名）、年份、辈分、配偶

- 正交父子连线

- 点击节点高亮祖先（金色）/ 后代（绿色）

- 拖拽平移、滚轮缩放、适应画布



### 前端特性摘要



| 功能 | 实现 |

|------|------|

| 登录态 | localStorage 存 token |

| 家族上下文 | localStorage 存 `currentFamily`；仅 1 个家族时**自动选中** |

| 人物搜索 | 走后端 `keyword` API，`page_size` ≤ 100 |

| 人物表单 | 姓名/小名/辈分/出生年份必填 |



---



## 9. 本地开发环境



### 已探测的本机配置



```text

MySQL:    D:\Develop\mysql-8.0.34-winx64

账号:     root / 123456（写在 genealogy-server/.env，勿提交 Git）

数据库:   genealogy

后端:     http://127.0.0.1:8000

前端:     http://127.0.0.1:5173

API 文档: http://127.0.0.1:8000/docs

```



### 启动步骤



**后端（推荐用 venv，避免 `--reload` 在 Windows 上拉起系统 Python）：**



```powershell

cd genealogy-server

.\.venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env   # 首次

alembic upgrade head

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

```



**前端：**



```powershell

cd genealogy-web

npm install

npm run dev

```



### 停止服务



- **PyCharm 运行：** 在 Run 窗口点击 Stop

- **命令行：** 在对应终端 `Ctrl+C`

- **端口仍被占用：**



```powershell

Get-NetTCPConnection -LocalPort 8000,5173 -State Listen | ForEach-Object { taskkill /F /T /PID $_.OwningProcess }

```



若 8000 仍无法释放，检查 PyCharm / 其他终端是否还有后端进程。



### 构建



```powershell

cd genealogy-web

npm run build    # 已验证通过

```



---



## 10. 联调 / 冒烟测试脚本



均在 `genealogy-server/scripts/`，需先启动后端：



```powershell

cd genealogy-server

.\.venv\Scripts\python scripts\smoke_auth.py

.\.venv\Scripts\python scripts\smoke_family.py

.\.venv\Scripts\python scripts\smoke_person.py

.\.venv\Scripts\python scripts\smoke_mvp.py

.\.venv\Scripts\python scripts\smoke_media.py

.\.venv\Scripts\python scripts\smoke_import_export.py

.\.venv\Scripts\python scripts\test_person_tree.py   # 指定人物族谱

.\.venv\Scripts\python scripts\smoke_public.py       # 公开展示 API

.\.venv\Scripts\python scripts\smoke_rbac.py         # RBAC 角色与用户管理

```



---



## 11. 模块完成度



### 后端（genealogy-server）— ✅ v1 完成



| 模块 | 状态 | 说明 |

|------|------|------|

| R1 认证 | ✅ | JWT 注册/登录/me |

| R2 家族 | ✅ | CRUD + owner 校验 + stats |

| R3 人物 | ✅ | CRUD + 分页筛选 + keyword |

| R4 关系 | ✅ | parent/spouse + sibling 推导 |

| R5 族谱树 | ✅ | full / patrilineal / lineage / person / ancestors / descendants |

| R6 附件 | ✅ | 上传、StaticFiles、头像、删除 |

| R7 Excel | ✅ | 导入导出 + 行级错误 |



### 前端（genealogy-web）— ✅ 主流程可用



| 模块 | 状态 | 说明 |

|------|------|------|

| 登录注册 | ✅ | |

| 家族概览 | ✅ | 单家族自动选中 + 统计面板 |

| 人物管理 | ✅ | 必填校验、关系抽屉 |

| 族谱树 | ✅ | 五种模式 + SVG 树形图 + 人物搜索 |

| 导入导出 | ✅ | |

| UI 美化 | 🔶 | 基础可用，可继续参考 pure-genealogy 细化 |



---



## 12. 已知问题与注意事项



1. **`.env` 含真实数据库密码**，已在 `.gitignore`，不要提交。

2. **全谱模式 `tree/full`** 对二十多代大家族可能较慢，默认应使用男系 + 深度限制。

3. **迁移 006** 若未执行，创建人物会因缺字段报错。

4. **人物列表 `page_size` 最大 100**，超过会 422；族谱页搜索应使用 `keyword` 而非一次拉全量。

5. Vite 使用 **5.4.11**，不要贸然升到 Vite 8（Windows rolldown 问题）。

6. **Windows 后端重启：** `uvicorn --reload` 可能拉起 `C:\Python310\python.exe` 而非 venv，导致代码未更新；建议用 `.\.venv\Scripts\python.exe -m uvicorn ...` 且不用 `--reload`，或先在 PyCharm 停止旧进程。

7. **8000 端口占用：** 切换族谱模式出现 404 / Not Found，多为旧后端未加载 `/api/tree/person`、`/api/tree/lineage`；重启后端或依赖前端 `fetchCenterPersonTree` 兼容层。

8. **辈分** 当前为「第几代」整数（`generation`），不是字辈字符；若要字辈需另加字段。



---



## 13. 用户场景与设计决策



针对「一个大家族、二十多代」场景：



| 问题 | 解决方案 |

|------|----------|

| 每次都要选家族 | `ensureFamilySelected()` 登录后自动选中唯一家族 |

| 全谱太大 | 男系世系 + `max_generations` 滑块；全图可按世过滤 |

| 辈分错位 | 布局按 `generation` 分行，不用图深度排版 |

| 指定人物不好用 | 统一 `/api/tree/person` + 前端搜索框 |

| 切换模式 404 | 各模式走独立 API；以人为中心有 ancestors+descendants 合并 fallback |

| 男系显示不全 | 按辈分范围截断，支持指定根人物 |



---



## 14. 后续可扩展方向（未做）



- [ ] 字辈字符字段（与「第几代」分离）

- [ ] 按支系自动分脉、点击节点懒加载子树

- [ ] 多家族成员协作（`family_members` + 角色权限）

- [ ] 族谱树节点点击跳转人物详情

- [ ] 导出族谱为 PDF / 图片

- [ ] 生产部署（Docker、Nginx 反向代理）

- [ ] 前端代码分割（主 bundle 较大 ~1.2MB）



---



## 15. 快速定位问题



| 想改什么 | 看哪里 |

|----------|--------|

| 族谱算法/裁剪/森林 | `genealogy-server/app/services/tree_service.py` |

| 族谱 API 参数 | `genealogy-server/app/api/tree.py` |

| SVG 渲染/样式 | `genealogy-web/src/components/tree/FamilyTree.vue` |

| 树形布局算法 | `genealogy-web/src/utils/genealogyLayout.ts` |

| 族谱页控件/模式切换 | `genealogy-web/src/views/tree/TreeView.vue` |

| 以人为中心兼容层 | `genealogy-web/src/api/tree.ts` → `fetchCenterPersonTree` |

| 家族自动选中 | `stores/family.ts` + `AppLayout.vue` |

| 公开展示 Portal | `api/public.py` + `public_service.py` + `views/portal/*` |

| 示例数据 | `scripts/seed_sample_data.py` |



---



## 16. 相关文档



- 后端 README：`genealogy-server/README.md`

- API 交互式文档：启动后端后访问 `/docs`

- UI 参考：https://github.com/yunfengsa/pure-genealogy



---



*如在新的对话中继续开发，可将本文档路径发给 AI：`familytree/PROJECT.md`*

