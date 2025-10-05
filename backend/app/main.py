from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import auth, cards, readers, logs
from .database import engine, Base
from .cache import ping as redis_ping
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from typing import List


settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Parking System API with RFID/NFC Access Control"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Ubah ini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(readers.router)
app.include_router(logs.router)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Templates for dashboard
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def root():
    """API root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    redis_status = "healthy" if redis_ping() else "unhealthy"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "database": "healthy"  # Could add DB ping too
    }

# Dashboard routes (simple HTML interface)
@app.get("/dashboard")
def dashboard_home(request: Request):
    """Dashboard home page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard/login")
def dashboard_login(request: Request):
    """Dashboard login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard/cards")
def dashboard_cards(request: Request):
    """Dashboard cards page"""
    return templates.TemplateResponse("cards.html", {"request": request})


@app.get("/dashboard/logs")
def dashboard_logs(request: Request):
    """Dashboard logs page"""
    return templates.TemplateResponse("logs.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)