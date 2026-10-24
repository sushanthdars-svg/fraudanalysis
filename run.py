#!/usr/bin/env python
"""
Script to run the FastAPI application.
Usage: python run.py
"""

import uvicorn
import os
from app.core.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )
