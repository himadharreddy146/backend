# import asyncio
# import logging
# import traceback
# import uvicorn
# import asyncpg
# import yaml
# from fastapi import FastAPI

# # FastAPI app initialization
# app = FastAPI()

# # Load configuration from config.yaml
# def load_config():
#     with open("configfile.yml", "r") as file:
#         return yaml.safe_load(file)

# config = load_config()

# @app.on_event("startup")
# async def startup_event():
#     try:
#         # Use the external URL for Render deployment
#         db_url = config["database"]["external_url"]
#         app.state.pool = await asyncpg.create_pool(db_url)
#         logging.info("Database connected successfully.")
#     except Exception as e:
#         logging.error(f"Error during database connection: {e}")
#         traceback.print_exc()

# @app.on_event("shutdown")
# async def shutdown_event():
#     try:
#         await app.state.pool.close()
#         logging.info("Database connection closed.")
#     except Exception as e:
#         logging.error(f"Error during database shutdown: {e}")
#         traceback.print_exc()

# # Sample route to verify API
# @app.get("/")
# async def root():
#     return {"message": "Connected to the database!"}

# def run_server():
#     logging.basicConfig(level=logging.INFO)
#     try:
#         uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
#     except KeyboardInterrupt:
#         print("Shutting down server...")

# if __name__ == "__main__":
#     run_server()

# import asyncio
# import logging
# import traceback
# from fastapi import FastAPI, HTTPException
# import uvicorn
# import asyncpg
# from pydantic import BaseModel

# # Initialize FastAPI app
# app = FastAPI()

# # Database connection configuration
# DATABASE_URL = "postgresql://alco_sales_user:qkto580CDni5cyF0fGk6t3ijjsMlEkQw@dpg-cvv6tuqdbo4c73fgvisg-a.virginia-postgres.render.com/alco_sales"

# # Define a Pydantic model for login input
# class LoginRequest(BaseModel):
#     username: str
#     password: str


# # Database connection pool
# db_pool = None


# @app.on_event("startup")
# async def startup():
#     global db_pool
#     try:
#         db_pool = await asyncpg.create_pool(DATABASE_URL)
#         logging.info("Connected to the database.")
#     except Exception as e:
#         logging.error(f"Failed to connect to the database: {str(e)}")
#         raise e


# @app.on_event("shutdown")
# async def shutdown():
#     global db_pool
#     if db_pool:
#         await db_pool.close()
#         logging.info("Database connection closed.")


# @app.get("/")
# async def root():
#     return {"message": "Connected to the database!"}


# @app.post("/login")
# async def login(request: LoginRequest):
#     query = "SELECT * FROM users WHERE username = $1 AND password = $2"
#     async with db_pool.acquire() as conn:
#         result = await conn.fetchrow(query, request.username, request.password)
#         if result:
#             return {"message": "Login successful", "user": dict(result)}
#         raise HTTPException(status_code=401, detail="Invalid credentials")


# async def main():
#     try:
#         uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
#     except Exception:
#         print(traceback.format_exc())


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("Application stopped.")


import asyncio
import logging
import traceback
import uvicorn
import asyncpg

# Importing from models
from models import creator

# Import the app instance from config (Make sure app is defined in config.py)
from config import app

# Set up logging for better error tracking
logging.basicConfig(level=logging.INFO)

async def main():
    try:
        # Log the start of the database setup process
        logging.info("Starting database setup...")
        
        # Create the necessary tables or perform any initial setup
        await creator.create_table()
        
        # Log successful database connection and setup
        logging.info("Database setup completed successfully.")
        
        # Start the Uvicorn server
        logging.info("Starting FastAPI server...")
        uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)
        
    except Exception as e:
        # Log detailed error information if anything fails
        logging.error(f"Error during setup or server startup: {traceback.format_exc()}")

def run_server():
    try:
        # Start the server by running the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        # Graceful shutdown when interrupted
        logging.info("Server stopped gracefully.")

if __name__ == '__main__':
    # This will ensure that the server starts when the script is run
    run_server()

