from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import auth, cards, readers, logs
from .database import engine, Base

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

# Include routers
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(readers.router)
app.include_router(logs.router)

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
    return {"status": "healthy"}


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