from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .ai_prompt_matcher import AIPromptMatcher
from .config import settings
from .db import Database
from .errors import AppError
from .user_system import UserSystem
from .video_engine import VideoEngine

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VIDEO_DIR = DATA_DIR / "videos"
for directory in (UPLOAD_DIR, VIDEO_DIR):
    directory.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI视频生成平台", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
database = Database(settings.database_path)
user_system = UserSystem(settings.jwt_secret)


class VideoRequest(BaseModel):
    type: str = Field("text_to_video", pattern="^(text_to_video|image_to_video)$")
    prompt: str = Field(..., min_length=1, max_length=5000)
    original_prompt: str | None = None
    duration: int = Field(6, ge=1, le=30)
    resolution: str = "1080p"
    mode: str = Field("auto", pattern="^(auto|official|free)$")
    priority: int = Field(5, ge=1, le=10)
    ai_analysis: dict[str, Any] | None = None
    skills: dict[str, Any] | None = None
    effect: str | None = None
    image_path: str | None = None


class VideoResponse(BaseModel):
    task_id: str
    status: str
    video_url: str | None = None
    mode: str | None = None
    error: str | None = None


class UserRegister(BaseModel):
    email: str
    phone: str | None = None
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    account: str
    password: str


class ModeConfig(BaseModel):
    mode: str = Field(pattern="^(auto|official|free)$")
    official_api_key: str | None = None


class TaskManager:
    def __init__(self) -> None:
        self.tasks: dict[str, dict[str, Any]] = {}
        self.video_engine = VideoEngine(settings.comfyui_url)
        self.video_engine.set_mode("auto")
        if settings.official_api_key:
            self.video_engine.set_official_api(settings.official_api_key)

    async def create_task(self, request: VideoRequest) -> str:
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {"status": "queued", "request": request, "created_at": datetime.now().isoformat()}
        asyncio.create_task(self._process_task(task_id))
        return task_id

    async def _process_task(self, task_id: str) -> None:
        task = self.tasks[task_id]
        task["status"] = "processing"
        try:
            request = task["request"]
            result = await (self.video_engine.generate_text_to_video(request) if request.type == "text_to_video" else self.video_engine.generate_image_to_video(request))
            task.update(result, status="completed", video_url=f"/api/video/{task_id}")
        except Exception as error:  # task failures are stored for polling clients
            task.update(status="failed", error=str(error))
            logger.exception("视频任务失败: %s", task_id)

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return self.tasks.get(task_id)


task_manager = TaskManager()


@app.on_event("startup")
def startup() -> None:
    database.initialize()


@app.exception_handler(AppError)
async def app_error_handler(_, error: AppError):
    return JSONResponse(status_code=error.status_code, content={"success": False, "code": error.code, "detail": error.message})


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(ROOT / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "minimax-h3-api"}


@app.post("/api/user/register")
async def register(user_data: UserRegister) -> dict[str, Any]:
    user = user_system.register(user_data.email, user_data.password, user_data.phone)
    return {"success": True, "user_id": user["id"], "user": user}


@app.post("/api/user/login")
async def login(login_data: UserLogin) -> dict[str, Any]:
    return {"success": True, **user_system.login(login_data.account, login_data.password)}


@app.post("/api/video/generate", response_model=VideoResponse)
async def generate_video(request: VideoRequest) -> VideoResponse:
    task_id = await task_manager.create_task(request)
    return VideoResponse(task_id=task_id, status="queued")


@app.post("/api/video/generate-image", response_model=VideoResponse)
async def generate_image_video(image: UploadFile = File(...), prompt: str = Form(""), duration: int = Form(6), resolution: str = Form("1080p"), effect: str = Form("subtle")) -> VideoResponse:
    suffix = Path(image.filename or "upload.jpg").suffix.lower() or ".jpg"
    image_path = UPLOAD_DIR / f"{uuid.uuid4()}{suffix}"
    image_path.write_bytes(await image.read())
    request = VideoRequest(type="image_to_video", prompt=prompt, duration=duration, resolution=resolution, effect=effect, image_path=str(image_path))
    task_id = await task_manager.create_task(request)
    return VideoResponse(task_id=task_id, status="queued")


@app.get("/api/video/status/{task_id}", response_model=VideoResponse)
async def get_video_status(task_id: str) -> VideoResponse:
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return VideoResponse(task_id=task_id, status=task["status"], video_url=task.get("video_url"), mode=task.get("mode"), error=task.get("error"))


@app.get("/api/analyze/{prompt}")
async def analyze_prompt(prompt: str) -> dict[str, Any]:
    matcher = AIPromptMatcher()
    analysis = matcher.analyze(prompt)
    return {"original": prompt, "analysis": analysis, "enhanced": matcher.enhance(prompt, analysis)}


@app.post("/api/config/mode")
async def set_mode(config: ModeConfig) -> dict[str, str]:
    task_manager.video_engine.set_mode(config.mode)
    if config.official_api_key:
        task_manager.video_engine.set_official_api(config.official_api_key)
    return {"status": "success", "mode": config.mode}


app.mount("/static", StaticFiles(directory=ROOT), name="static")
app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
