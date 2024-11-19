from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.api import auth_routes, message_routes
from app import models
from app.services.translation import translate_text, detect_language
from fastapi import HTTPException

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
app.include_router(message_routes.router, prefix="/api/messages", tags=["messages"]
)

@app.get("/")
async def root():
    return {"message": "Welcome to GlobalChat API"}

@app.post("/api/test/translate")
def test_translation(text: str, target_language: str):
    try:
        translated = translate_text(text, target_language)
        return {
            "original": text,
            "translated": translated,
            "target_language": target_language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test/detect")
async def test_language_detection(text: str):
    try:
        detected = await detect_language(text)
        return {
            "text": text,
            "detected_language": detected
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))