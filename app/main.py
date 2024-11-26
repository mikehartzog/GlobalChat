from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.api import auth_routes, message_routes, ws_routes  # Add ws_routes
from app import models

app = FastAPI(title="GlobalChat", description="Real-time chat with AI translation")

# Create tables on startup
create_tables()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(message_routes.router, prefix="/api/messages", tags=["messages"])
app.include_router(ws_routes.router, tags=["websocket"])  # No prefix for WebSocket routes

@app.get("/")
async def root():
    return {"message": "Welcome to GlobalChat API"}