# 数据库表说明

- 引擎：MySQL 8.0（utf8mb4）
- ORM：SQLAlchemy 2.0
- 迁移：Alembic（`genealogy-server/alembic/versions/`）

## 1. ER 概览

```text
users 1───* families
families 1───* persons
families 1───* person_relations
families 1───* geo_places
persons 1───* media
persons 1───* geo_places (optional related_person_id)
persons *───* persons  (via person_relations)
```

## 2. 表结构

### 2.1 `users` 用户

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | 用户 ID |
| username | VARCHAR(50) UNIQUE | 登录名 |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| nickname | VARCHAR(50) NULL | 昵称 |
| role | VARCHAR(20) | `member` / `editor` / `admin`，默认 `member` |
| created_at / updated_at | DATETIME | 时间戳 |

迁移：`001_create_users`，角色字段 `007_add_user_role`。

### 2.2 `families` 家族

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | 家族 ID |
| owner_id | BIGINT FK → users.id | 所有者 |
| name | VARCHAR(100) | 家族名 |
| description | TEXT NULL | 简介 |
| origin_place | VARCHAR(100) NULL | 籍贯/地望 |
| created_at / updated_at | DATETIME | 时间戳 |

迁移：`002_create_families`。

### 2.3 `persons` 人物

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | 人物 ID |
| family_id | BIGINT FK → families.id | 所属家族 |
| name | VARCHAR(50) | 姓名 |
| nickname | VARCHAR(50) | 小名 |
| gender | SMALLINT | 0 未知 / 1 男 / 2 女 |
| generation | INT NULL | 辈分（第几世） |
| birth_year | INT NULL | 出生年 |
| birth_date / death_date | DATE NULL | 出生/去世日期 |
| birthplace | VARCHAR(100) NULL | 籍贯 |
| phone | VARCHAR(30) NULL | 电话 |
| address | VARCHAR(200) NULL | 现住址 |
| biography / remark | TEXT NULL | 简介 / 备注 |
| is_alive | SMALLINT | 1 在世 / 0 已故 |
| avatar_url | VARCHAR(255) NULL | 头像 URL |
| created_at / updated_at | DATETIME | 时间戳 |

迁移：`003_create_persons`，小名与出生年 `006`，联系方式 `008_add_person_contact`。

### 2.4 `person_relations` 亲属关系

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | 关系 ID |
| family_id | BIGINT FK | 家族 |
| from_person_id | BIGINT FK → persons.id | 起点 |
| to_person_id | BIGINT FK → persons.id | 终点 |
| relation_type | VARCHAR(50) | `parent` 或 `spouse` |
| created_at | DATETIME | 创建时间 |

唯一约束：`(family_id, from_person_id, to_person_id, relation_type)`。

- `parent`：`from` 是 `to` 的父母
- `spouse`：配偶（存一条）

迁移：`004_create_person_relations`。

### 2.5 `media` 附件

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | 附件 ID |
| person_id | BIGINT FK | 关联人物 |
| family_id | BIGINT FK | 家族 |
| file_name | VARCHAR(255) | 原始文件名 |
| file_path | VARCHAR(500) | 相对存储路径 |
| mime_type | VARCHAR(100) | MIME |
| file_size | BIGINT | 字节大小 |
| created_at | DATETIME | 上传时间 |

文件实体存放于服务端 `uploads/`，HTTP 挂载 `/uploads`。

迁移：`005_create_media`。

### 2.6 `geo_places` 地理标记

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AI | 标记 ID |
| family_id | BIGINT FK | 家族 |
| place_type | VARCHAR(20) | `distribution` / `cemetery` |
| name | VARCHAR(100) | 地点名称 |
| longitude / latitude | DECIMAL(10,6) | 经纬度 |
| address | VARCHAR(200) NULL | 文字地址 |
| description | TEXT NULL | 备注 |
| related_person_id | BIGINT FK NULL | 可选关联人物 |
| created_at / updated_at | DATETIME | 时间戳 |

迁移：`009_create_geo_places`。

## 3. 迁移历史

| Revision | 说明 |
|----------|------|
| 001_create_users | 用户表 |
| 002_create_families | 家族表 |
| 003_create_persons | 人物表 |
| 004_create_person_relations | 关系表 |
| 005_create_media | 附件表 |
| 006_add_person_nickname_birth_year | 小名、出生年 |
| 007_add_user_role | 用户角色 |
| 008_person_contact | 电话、地址 |
| 009_geo_places | 地理标记 |

执行：

```bash
cd genealogy-server
alembic upgrade head
```

## 4. 示例数据

脚本：`genealogy-server/scripts/seed_sample_data.py`

写入「李氏」示例族谱（约 6 世、20+ 人）及若干地理标记点，便于联调。
