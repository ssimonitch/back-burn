from typing import Any

from fastapi import FastAPI

app = FastAPI(
    title="Slow Burn API",
    description="Backend API for the AI Fitness Companion application",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, Any]:
    return {"message": "Hello World", "app": "Slow Burn AI Fitness Companion"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
