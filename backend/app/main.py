from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import auth, cards, readers, logs
from .database import engine, Base
from .cache import ping as redis_ping
from typing import List
import json
import traceback

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Parking System API with RFID/NFC Access Control"
)

# CORS middleware - SIMPLIFY
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# WebSocket Connection Manager
# ============================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            print("⚠️ No active WebSocket connections")
            return
            
        print(f"📡 Broadcasting to {len(self.active_connections)} clients")
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                print(f"✅ Sent to client")
            except Exception as e:
                print(f"❌ Error sending to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")


# Create global manager instance
manager = ConnectionManager()

# IMPORTANT: Make manager available to other modules
app.state.ws_manager = manager


# ============================================
# Include routers
# ============================================
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(readers.router)
app.include_router(logs.router)


# ============================================
# Templates for dashboard
# ============================================
try:
    templates = Jinja2Templates(directory="app/templates")
except:
    templates = None
    print("⚠️ Templates directory not found")


# ============================================
# Root endpoints
# ============================================
@app.get("/")
def root():
    """API root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws",
        "active_ws_connections": len(manager.active_connections)
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    redis_status = "healthy" if redis_ping() else "unhealthy"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "database": "healthy",
        "websocket_connections": len(manager.active_connections)
    }


# ============================================
# WebSocket endpoint
# ============================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Optional: handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            else:
                print(f"📨 Received from client: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected normally")
    except Exception as e:
        print(f"WebSocket error: {e}")
        print(traceback.format_exc())
        manager.disconnect(websocket)


# ============================================
# Dashboard routes (if templates exist)
# ============================================
if templates:
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


# ============================================
# Startup/Shutdown events
# ============================================
@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📡 WebSocket endpoint: ws://localhost:8000/ws")
    print(f"📚 API docs: http://localhost:8000/docs")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Shutting down...")