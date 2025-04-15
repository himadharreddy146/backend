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

import os
import asyncpg
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

# Initialize the FastAPI app
app = FastAPI()

# Function to connect to the PostgreSQL database
async def connect_to_db():
    # Retrieve the DATABASE_URL from environment variables
    database_url = os.getenv("DATABASE_URL")
    
    # Connect to the PostgreSQL database
    conn = await asyncpg.connect(dsn=database_url)

    # Query data from the database (for example, getting users)
    result = await conn.fetch('SELECT * FROM user_table LIMIT 10')

    # Close the connection after the query
    await conn.close()

    # Since `fetch` returns a list of records (dict-like), we can serialize it
    return jsonable_encoder(result)

# API endpoint to fetch users
@app.get("/users")
async def get_users():
    try:
        # Fetch users from the database
        users = await connect_to_db()
        return {"users": users}  # Return the serialized data
    except Exception as e:
        # Handle any errors by returning a message
        return {"error": str(e)}
