# MiniMax H3 Video Studio

MiniMax H3 AI 视频工作台的静态前端 MVP。

## Features

- 文生视频 / 图生视频工作流
- 提示词分析与智能增强
- 生成进度、预览画布和任务历史
- 本地注册、登录与积分演示
- 响应式商用工作台界面

## Local preview

```powershell
python -m http.server 8787
```

打开 `http://127.0.0.1:8787/`。

## GitHub Pages

推送到 `master` 分支后，GitHub Actions 会自动部署静态页面。

当前账户和积分仍保存在浏览器 `localStorage`，真实生产环境需要接入 FastAPI、数据库和 MiniMax H3 API。
