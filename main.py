import asyncio
import logging
import traceback
import uvicorn
import asyncpg

# Importing from models
from models import creator

# Import the app instance from config (Make sure app is defined in config.py)
from config import app

async def main():
    try:
        # Create the necessary tables or perform any initial setup
        await creator.create_table()

        # Start the uvicorn server directly within this script
        uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)  # Make sure to pass 'app' directly
    except Exception:
        print(traceback.format_exc())

def run_server():
    logging.basicConfig(level=logging.INFO)
    try:
        # Start the server by running the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Server stopped gracefully.')

if __name__ == '__main__':
    # This will ensure that the server starts when the script is run
    run_server()
