# import asyncio
# import logging
# import traceback
# import uvicorn
# import asyncpg

# # Importing from models
# from models import creator

# # Import the app instance from config (Make sure app is defined in config.py)
# from config import app

# async def main():
#     try:
#         # Create the necessary tables or perform any initial setup
#         await creator.create_table()

#         # Start the uvicorn server directly within this script
#         uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)  # Make sure to pass 'app' directly
#     except Exception:
#         print(traceback.format_exc())

# def run_server():
#     logging.basicConfig(level=logging.INFO)
#     try:
#         # Start the server by running the main async function
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print('Server stopped gracefully.')

# if __name__ == '__main__':
#     # This will ensure that the server starts when the script is run
#     run_server()

from fastapi import FastAPI
import os
import asyncpg
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# Load environment variables from .env file if in local development
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Access the environment variables
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL Database URL
SECRET_KEY = os.getenv("SECRET_KEY")  # Secret Key for JWT or encryption
DEBUG = os.getenv("DEBUG", "False")  # Default to "False" if not set

# Database connection
async def connect_to_db():
    try:
        connection = await asyncpg.connect(DATABASE_URL)
        return connection
    except Exception as e:
        return f"Error: {str(e)}"

@app.get("/")
async def read_root():
    # Example usage of environment variables
    db_connection = await connect_to_db()
    return {"message": "App is running", "database_connection": db_connection}

@app.get("/secret")
async def get_secret_key():
    # Return the secret key (or any other secured data)
    return {"secret_key": SECRET_KEY}
