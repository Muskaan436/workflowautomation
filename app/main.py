from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, workflows
from app.celery import celery_app
import os

app = FastAPI(title="Workflow Automation API", version="1.0.0")

# Configure CORS for production
origins = [
    "http://localhost:3000",  # React development server
    "http://localhost:5500", 
    "http://127.0.0.1:5500",
    "http://127.0.0.1:3000",
    "https://your-frontend-domain.com",  # Replace with your actual frontend domain
]

# Add environment variable for additional origins
if os.getenv("ALLOWED_ORIGINS"):
    origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])

@app.get("/")
async def root():
    return {"message": "Workflow Automation API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "celery": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)