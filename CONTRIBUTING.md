# 贡献指南

感谢关注本项目。

## 提交流程建议

1. Fork / 克隆仓库并创建分支  
2. 本地按 [安装部署](./docs/deployment.md) 跑通前后端  
3. 修改代码，保持风格与现有目录一致  
4. 自测相关页面与接口  
5. 提交清晰说明，并创建 Pull Request  

## 约定

- **不要提交** `.env`、`.env.development.local`、真实 Key、数据库密码、`uploads` 用户文件  
- 数据库变更请新增 Alembic 迁移，勿仅改模型不写迁移  
- 业务异常走项目统一 `AppException` + `{ code, message, data }` 响应  
- 文档变更优先更新 `docs/` 下对应文件  

## 问题反馈

请在 GitHub Issues 描述：环境、复现步骤、期望与实际结果。
