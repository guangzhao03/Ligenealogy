# 接口说明

- Base URL（本地）：`http://127.0.0.1:8000`
- 在线文档：启动后端后访问 `http://127.0.0.1:8000/docs`（Swagger）
- 统一响应：

```json
{ "code": 0, "message": "ok", "data": {} }
```

业务失败多为 HTTP 200 + `code != 0`。管理类接口需 Header：`Authorization: Bearer <token>`。

---

## 1. 认证 `/api/auth`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 否 | 注册，默认 role=`member` |
| POST | `/api/auth/login` | 否 | 登录，返回 `access_token` |
| GET | `/api/auth/me` | 是 | 当前用户信息（含 role） |

---

## 2. 用户 `/api/users`（admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 用户列表 |
| PUT | `/api/users/{id}/role` | 修改角色；不可取消最后一个 admin |

---

## 3. 公开展示 `/api/public`（默认免登录）

展示家族由 `DISPLAY_FAMILY_ID` 或「人物最多家族」决定。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/public/family` | 家族概况 + stats |
| GET | `/api/public/persons` | 人物分页，`keyword` / `generation` |
| GET | `/api/public/persons/{id}` | 人物详情 |
| GET | `/api/public/persons/{id}/relations` | 父母/子女/配偶/兄弟姐妹 |
| GET | `/api/public/tree/full` | 世系全图 |
| GET | `/api/public/tree/patrilineal` | 男系世系 |
| GET | `/api/public/tree/lineage` | 以人为中心 |
| GET | `/api/public/tree/person` | 统一指定人物树 |
| GET | `/api/public/geo-places` | 地理标记列表，`place_type` 可选 |
| GET | `/api/public/residences` | 有坐标的族人现住址（住宅点） |

常用查询参数：

- `lineage`：`person_id`（必填），`up_generations`，`down_generations`（0–30）
- `patrilineal`：`root_person_id`，`max_generations`

---

## 4. 家族 `/api/families`（admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/families` | 创建 |
| GET | `/api/families` | 我的家族列表 |
| GET | `/api/families/{id}` | 详情 |
| GET | `/api/families/{id}/stats` | 统计 |
| PUT | `/api/families/{id}` | 更新 |
| DELETE | `/api/families/{id}` | 删除 |

---

## 5. 人物 `/api/persons`（admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/persons` | 创建（name/nickname/generation/birth_year 必填） |
| GET | `/api/persons` | 列表：`family_id` 必填；`keyword`、`generation`、分页 |
| GET | `/api/persons/{id}` | 详情 |
| PUT | `/api/persons/{id}` | 更新 |
| DELETE | `/api/persons/{id}` | 删除（清理 media） |
| GET | `/api/persons/{id}/relations` | 亲属 |
| GET | `/api/persons/{id}/media` | 附件列表 |

`page_size` 最大 100。

---

## 6. 关系 `/api/relations`（admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/relations` | 创建 `parent` 或 `spouse` |
| DELETE | `/api/relations/{id}` | 删除 |

---

## 7. 族谱树 `/api/tree`（admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tree/full` | 世系全图，`family_id` |
| GET | `/api/tree/patrilineal` | 男系世系 |
| GET | `/api/tree/lineage` | 以人为中心 |
| GET | `/api/tree/person` | 统一接口，`direction=center\|ancestors\|descendants\|patrilineal` |
| GET | `/api/tree/ancestors` | 向上查祖 |
| GET | `/api/tree/descendants` | 向下查孙 |

响应图结构含 `nodes`、`edges`，部分模式含 `focus_person_id`。

---

## 8. 地理标记 `/api/geo-places`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/geo-places` | admin | `family_id` 必填；`place_type` 可选 |
| POST | `/api/geo-places` | editor+ | 创建 |
| PUT | `/api/geo-places/{id}` | editor+ | 更新 |
| DELETE | `/api/geo-places/{id}` | editor+ | 删除 |

请求体字段：`place_type`、`name`、`longitude`、`latitude`、`address`、`description`、`related_person_id`。

---

## 9. 附件 `/api/media`（admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/media/upload` | multipart 上传，可设为头像 |
| DELETE | `/api/media/{id}` | 删除 |

静态访问：`GET /uploads/<path>`。

---

## 10. 导入导出

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/import/persons` | Excel 导入人物 |
| POST | `/api/import/relations` | Excel 导入关系 |
| GET | `/api/export/persons?family_id=` | 导出人物 |
| GET | `/api/export/relations?family_id=` | 导出关系 |

人物表头示例：`姓名, 小名, 性别, 辈分, 出生年份, 出生日期, 去世日期, 籍贯, 简介, 备注, 是否在世`。

---

## 11. 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | `{ "status": "ok" }` |
