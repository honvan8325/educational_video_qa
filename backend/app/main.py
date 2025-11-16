from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from app.database import connect_to_mongo, close_mongo_connection
from app.api.endpoints import auth, workspace, video, qa


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Educational Video Q&A API",
    description="API for educational video question answering using RAG",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(workspace.router, prefix="/api/workspaces", tags=["Workspaces"])
app.include_router(video.router, prefix="/api/workspaces", tags=["Videos"])
app.include_router(qa.router, prefix="/api/workspaces", tags=["Q&A"])

# Mount static file directories for serving videos and thumbnails AFTER API routes
videos_dir = Path("./storage/videos")
thumbnails_dir = Path("./storage/thumbnails")
videos_dir.mkdir(parents=True, exist_ok=True)
thumbnails_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static/videos", StaticFiles(directory=str(videos_dir)), name="videos")
app.mount("/static/thumbnails", StaticFiles(directory=str(thumbnails_dir)), name="thumbnails")


@app.get("/")
async def root():
    return {"message": "Educational Video Q&A API", "version": "1.0.0", "docs": "/docs"}
