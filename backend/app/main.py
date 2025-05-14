from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

from app.api.routes import document
from app.db.session import engine
from app.db.base import Base

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Arabic PDF Processing and LLM Training Platform",
    description="Platform for processing Arabic PDFs and training language models",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(document.router, prefix="/api/documents", tags=["documents"])

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
