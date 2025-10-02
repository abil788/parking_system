from fastapi import APIRouter
from . import auth, cards, readers, logs

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
api_router.include_router(readers.router, prefix="/readers", tags=["readers"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
