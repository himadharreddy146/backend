import asyncio
import logging
import traceback
import uvicorn
import asyncpg
import yaml
from fastapi import FastAPI

# FastAPI app initialization
app = FastAPI()

# Load configuration from config.yaml
def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

config = load_config()

@app.on_event("startup")
async def startup_event():
    try:
        # Use the external URL for Render deployment
        db_url = config["database"]["external_url"]
        app.state.pool = await asyncpg.create_pool(db_url)
        logging.info("Database connected successfully.")
    except Exception as e:
        logging.error(f"Error during database connection: {e}")
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await app.state.pool.close()
        logging.info("Database connection closed.")
    except Exception as e:
        logging.error(f"Error during database shutdown: {e}")
        traceback.print_exc()

# Sample route to verify API
@app.get("/")
async def root():
    return {"message": "Connected to the database!"}

def run_server():
    logging.basicConfig(level=logging.INFO)
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("Shutting down server...")

if __name__ == "__main__":
    run_server()
