# MiniMax H3 Video Studio

基于你提供的系统架构实现的 MiniMax H3 AI 视频生成平台，包含官方 API、免费方案和自动切换三种视频引擎模式。

## Features

- 文生视频 / 图生视频工作流
- 提示词分析与智能增强
- 生成进度、预览画布和任务历史
- 本地注册、登录与积分演示
- FastAPI 用户与视频任务接口
- AI 提示词场景/主体/风格匹配
- ComfyUI 免费方案工作流适配边界
- 响应式商用工作台界面

## Local preview

```powershell
python -m http.server 8787
```

打开 `http://127.0.0.1:8787/`。

## Backend

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

API 文档：`http://127.0.0.1:8000/docs`

前端要连接真实 API，在浏览器控制台设置：

```js
localStorage.setItem('minimax-h3-api', 'http://127.0.0.1:8000')
```

## GitHub Pages

推送到 `master` 分支后，GitHub Actions 会自动部署静态页面。

当前没有 `MINIMAX_API_KEY` 时，官方模式会明确报错；没有可用免费账号时，免费模式也会明确报错，不会伪装成已生成视频。账号批量接码注册默认关闭，需要经过合规审核后由运营方自行接入。
