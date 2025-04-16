import asyncio
import logging
import traceback
import uvicorn
import asyncpg
from fastapi import FastAPI
from pydantic import BaseSettings

# Importing models for database setup
from models import creator

# FastAPI app initialization
app = FastAPI()

# Configuration class for settings
class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()

@app.on_event("startup")
async def startup_event():
    try:
        app.state.pool = await asyncpg.create_pool(settings.database_url)
        await creator.create_table()
        logging.info("Database connected and tables created.")
    except Exception as e:
        logging.error(f"Error during startup: {e}")
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await app.state.pool.close()
        logging.info("Database connection closed.")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")
        traceback.print_exc()

# Sample route to verify API
@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

def run_server():
    logging.basicConfig(level=logging.INFO)
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Shutting down server...")

if __name__ == "__main__":
    run_server()
