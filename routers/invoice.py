import io

import pandas as pd
from fastapi import APIRouter, Request, Header, HTTPException, status, Request, Query, Path
from fastapi import Response as resp
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import asyncpg
# import aiofiles
import os
import json

from models.creator import configfile
from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens, hash_password, verify_password, deactivate_all_tokens
from validations.user import (Response, AdminRegistration, EditDetails, ValidateSession, CompleteRegistration, Login, Logout, DeleteAdmin, ChangePassword, EmailRequest)
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from pydantic import BaseModel, ValidationError
import pytz
import yaml
import base64
import bcrypt
import requests
from fastapi import APIRouter, Response, status
import asyncpg
import base64
import os
from fastapi.responses import FileResponse
from pathlib import Path


router = APIRouter()

# Endpoint to get all invoices
@router.get("/invoices", tags=["Invoices"])
async def get_all_invoices(token: str):
    try:
        # Fetch the user ID from the token
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Invalid session ID"}
            )

        # Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # Fetch the invoices from the database
        query = "SELECT id, file_name, upload_date FROM invoice"
        invoices = await conn.fetch(query)

        if not invoices:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"message": "No invoices found"}
            )

        # Prepare the invoices data to return
        invoices_list = []
        for invoice in invoices:
            invoices_data = {
                "id": invoice['id'],
                "file_name": invoice['file_name'],
                 "upload_date": convert_datetime_to_str(invoice['upload_date'])
            }
            invoices_list.append(invoices_data)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "The request was successful", "data": invoices_list}
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to retrieve invoices: {str(e)}"}
        )

def convert_datetime_to_str(dt):
    if isinstance(dt, datetime):
        return dt.isoformat()  # Convert datetime to ISO 8601 string
    return dt

@router.get("/invoices/download/{file_name}", tags=["Invoices"])
async def download_invoice(file_name: str):
    try:
        # Step 1: Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # Step 2: Query to fetch the file data and filename
        query = "SELECT file_name, file_data FROM invoice WHERE file_name = $1"
        invoice = await conn.fetchrow(query, file_name)

        # Step 3: If the file is not found, raise an exception
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Step 4: Retrieve the file data
        file_data = invoice['file_data']

        # Step 5: Check if file_data is empty
        if len(file_data) == 0:
            raise HTTPException(status_code=404, detail="File data not found")

        # Step 6: Return the file as a downloadable response
        return Response(
            content=file_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={invoice['file_name']}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download invoice: {str(e)}")


@router.get("/products/download_report_csv", tags=["Products"])
async def download_product_csv_report(token: str):
    try:
        # Get user_id from the token
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session ID")

        # Ensure user_id is an integer
        user_id = int(user_id)

        # Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # Fetch the shop_name of the user based on user_id
        query = "SELECT shop_name FROM user_table WHERE id = $1"
        user_data = await conn.fetchrow(query, user_id)

        if not user_data or not user_data['shop_name']:
            raise HTTPException(status_code=404, detail="Shop name not found for the user")

        shop_name = user_data['shop_name']

        # Fetch product data from the database
        product_query = "SELECT * FROM products"
        products = await conn.fetch(product_query)

        if not products:
            raise HTTPException(status_code=404, detail="No products found")

        # Convert data to DataFrame
        product_data = [dict(product) for product in products]
        df = pd.DataFrame(product_data)

        # Convert the DataFrame to CSV in memory
        csv_file = io.StringIO()
        df.to_csv(csv_file, index=False)
        csv_file.seek(0)

        # Convert the string data to bytes
        csv_file_bytes = csv_file.getvalue().encode("utf-8")

        # Generate the filename based on shop_name and current timestamp
        filename = f"{shop_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"

        # Return the CSV file as a downloadable response
        return StreamingResponse(
            io.BytesIO(csv_file_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV report: {str(e)}")