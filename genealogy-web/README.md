# genealogy-web

族谱系统前端（Vue3 + Element Plus + AntV G6）。

## 技术栈

- Vue 3 + TypeScript + Vite
- Element Plus
- Pinia + Vue Router + Axios
- AntV G6 族谱树

## UI 参考

界面布局参考了开源族谱项目 [pure-genealogy](https://github.com/yunfengsa/pure-genealogy) 的常见模式：

- 左侧深色导航 + 纸色内容区
- 家族卡片选择当前上下文
- 人物表格管理 + 关系抽屉
- 纵向族谱树，按世代渐变色展示

## 快速开始

```powershell
cd genealogy-web
npm install
npm run dev
```

默认访问：http://localhost:5173

请确保后端 `genealogy-server` 已在 `http://127.0.0.1:8000` 运行。

## 页面

- `/login` 登录
- `/register` 注册
- `/families` 家族管理
- `/persons` 人物管理
- `/tree` 族谱树
- `/import-export` Excel 导入导出
