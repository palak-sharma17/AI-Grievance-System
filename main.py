from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os

from database import engine, Base
from routes import router
from ai_classifier import classifier

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-generate SQLite Tables on startup
    Base.metadata.create_all(bind=engine)
    app.state.classifier = classifier
    print("✅ Database Tables Initialized Successfully")
    print("✅ AI Classifier Processing Pipeline Active")
    yield

app = FastAPI(
    title="AI Grievance System",
    description="AI-powered civic complaint management system with dynamic breadcrumbs",
    version="2.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing Layer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Router Mounting
app.include_router(router)

# Mount Static Files securely if subdirectory directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serves the SPA frontend dashboard dashboard securely from the local project root
    """
    # Look for index.html in the immediate folder directory to prevent 404 errors
    local_path = "index.html"
    fallback_path = "../frontend/templates/index.html"
    
    target_file = local_path if os.path.exists(local_path) else fallback_path
    
    if not os.path.exists(target_file):
        raise HTTPException(
            status_code=404, 
            detail=f"Frontend configuration template missing! Looked for: {os.path.abspath(target_file)}"
        )
        
    with open(target_file, "r") as f:
        return f.read()

@app.get("/health")
async def health():
    return {"status": "healthy", "system_year": 2026}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)