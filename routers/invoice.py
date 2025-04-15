import io

import pandas as pd
from fastapi import APIRouter, Request, Header, HTTPException, status, Request, Query, Path
from fastapi import Response as resp
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import asyncpg
# import aiofiles
import os
import json
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, PageBreak, Paragraph
from reportlab.lib import colors

from reportlab.lib.units import inch


from models.creator import configfile
from utils.tools import find_country_code, save_user_token, find_user_id_by_token, connect_to_redis, count_records_by_user_id, \
    delete_user_tokens, hash_password, verify_password, deactivate_all_tokens
from validations.user import (Response, AdminRegistration, EditDetails, ValidateSession, CompleteRegistration, Login, Logout, DeleteAdmin, ChangePassword, EmailRequest)
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
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


REPORTS_DIR = os.getenv("REPORTS_DIR", r"C:\AlcoSales\reports")  # Default for local development

# Ensure the main reports directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

# @router.get("/products/download_report_csv", tags=["Products"])
# async def download_product_csv_report(token: str):
#     try:
#         # Extract user_id from token
#         loop = asyncio.get_running_loop()
#         user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
#
#         if not user_id:
#             raise HTTPException(status_code=401, detail="Invalid session ID")
#
#         user_id = int(user_id)
#
#         # Connect to the database
#         conn = await asyncpg.connect(
#             user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
#             password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
#             database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
#             host=str(configfile["database"]["host"]),
#             port=str(configfile["database"]["port"])
#         )
#
#         query = "SELECT shop_name FROM user_table WHERE id = $1"
#         user_data = await conn.fetchrow(query, user_id)
#
#         if not user_data or not user_data['shop_name']:
#             raise HTTPException(status_code=404, detail="Shop name not found for the user")
#
#         shop_name = user_data['shop_name']
#
#         product_query = "SELECT * FROM products"
#         products = await conn.fetch(product_query)
#
#         if not products:
#             raise HTTPException(status_code=404, detail="No products found")
#
#         product_data = [dict(product) for product in products]
#         df = pd.DataFrame(product_data)
#
#         # Create a folder for the current date (YYYY-MM-DD format)
#         date_dir = os.path.join(REPORTS_DIR, datetime.now().strftime('%Y-%m-%d'))
#         os.makedirs(date_dir, exist_ok=True)  # Create the folder if it doesn't exist
#
#         # Generate a unique filename for the report
#         filename = f"{shop_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
#         file_path = os.path.join(date_dir, filename)
#
#         # Save the DataFrame as a CSV file
#         df.to_csv(file_path, index=False)
#
#         # Return the CSV file as a downloadable response
#         return StreamingResponse(
#             io.BytesIO(open(file_path, "rb").read()),
#             media_type="text/csv",
#             headers={"Content-Disposition": f"attachment; filename={filename}"}
#         )
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to generate CSV report: {str(e)}")

@router.get("/products/download_report_pdf", tags=["Invoices"])
async def download_product_pdf_report(token: str = Header(...)):
    try:
        # Extract user_id from token
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session ID")

        user_id = int(user_id)

        # Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        query = "SELECT shop_name FROM user_table WHERE id = $1"
        user_data = await conn.fetchrow(query, user_id)

        if not user_data or not user_data['shop_name']:
            raise HTTPException(status_code=404, detail="Shop name not found for the user")

        shop_name = user_data['shop_name']

        product_query = "SELECT * FROM products ORDER BY id ASC"
        products = await conn.fetch(product_query)

        if not products:
            raise HTTPException(status_code=404, detail="No products found")

        product_data = [dict(product) for product in products]

        # Remove the 'id' and 'time_last_edited' columns from the data
        for product in product_data:
            product.pop('id', None)
            product.pop('time_last_edited', None)

        # Calculate sums for specified columns
        total_qty_cases = 0
        total_qty_bottles = 0
        total_case_rate = 0
        total_bottle_rate = 0
        total_total = 0
        total_sold_qty = 0
        total_sold_price = 0
        total_available_qty = 0
        total_available_price = 0
        total_bottles_delivered=0

        for row in product_data:
            total_qty_cases += row.get('qty_cases_delivered', 0)
            total_qty_bottles += row.get('qty_bottles_delivered', 0)
            total_case_rate += row.get('case_rate', 0)
            total_bottle_rate += row.get('btl_rate', 0)
            total_total += row.get('total', 0)
            total_sold_qty += row.get('sold_products', 0)
            total_sold_price += row.get('sold_price', 0)
            total_available_qty += row.get('available_products', 0)
            total_available_price += row.get('available_price', 0)
            total_bottles_delivered += row.get('total_bottles_delivered',0)

        # Create a folder for the current date (YYYY-MM-DD format)
        date_dir = os.path.join(REPORTS_DIR, datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(date_dir, exist_ok=True)  # Create the folder if it doesn't exist

        # Generate a unique filename for the report
        filename = f"{shop_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        file_path = os.path.join(date_dir, filename)

        # Create the PDF in landscape mode
        pdf_doc = SimpleDocTemplate(file_path, pagesize=landscape(A4))
        elements = []

        # Add shop name at the top
        shop_name_paragraph = Paragraph(f"<b>{shop_name}</b>", getSampleStyleSheet()['Title'])
        elements.append(shop_name_paragraph)

        # Add some space after the shop name
        elements.append(Paragraph("<br /><br />", getSampleStyleSheet()['Normal']))

        # Define custom header names
        custom_headers = [
            'Sl.No', 'Brand Code', 'Brand Name', 'Product Type', 'Pack Type',
            'Size (ml)', 'Qty Delivered (Cases)', 'Qty Delivered (Bottles)', 'Case Rate',
            'Bottle Rate', 'Total Bottles', 'Total', 'Available Qty', 'Available Price','Sold Price', 'Sold Qty'
        ]

        # Prepare table data with wrapped headers using Paragraph
        wrapped_headers = [
            Paragraph(header, getSampleStyleSheet()['Normal'])
            for header in custom_headers
        ]

        data = [wrapped_headers]  # Add wrapped custom headers to table data

        # Prepare the rows with the product data
        for row in product_data:
            wrapped_row = [
                Paragraph(str(row[col]), getSampleStyleSheet()["BodyText"]) if isinstance(row[col], str) else str(row[col])
                for col in row
            ]
            data.append(wrapped_row)

        # Append the sum row to the table data
        sum_row = [
            Paragraph('<b>Total</b>', getSampleStyleSheet()["Normal"]),  # Add label 'Total'
            '', '', '', '', '',  # Empty columns for the first few headers
            total_qty_cases,
            total_qty_bottles,
            total_case_rate,
            total_bottle_rate,
            total_bottles_delivered,
            total_total,
            total_available_qty,
            total_available_price,
            total_sold_qty,
            total_sold_price
        ]
        data.append(sum_row)

        # Adjust column widths to fit the content better
        col_widths = [
            0.4 * inch, 0.5 * inch, 1.2 * inch, 0.9 * inch, 0.7 * inch,
            0.4 * inch, 0.5 * inch, 0.7 * inch, 0.7 * inch, 0.6 * inch,
            0.7 * inch, 0.8 * inch, 0.7 * inch, 0.7 * inch, 0.6 * inch
        ]

        # Create the table
        table = Table(data, colWidths=col_widths)

        # Apply table styles
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),  # Font size for headers
            ('FONTSIZE', (0, 1), (-1, -1), 7),  # Font size for rows
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        # Append the table to elements
        elements.append(table)

        # Build the PDF
        pdf_doc.build(elements)

        # Return the PDF file as a downloadable response
        return FileResponse(
            file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")


@router.get("/products/reports", tags=["Invoices"])
async def get_reports_by_date(
        start_date: str = Query(..., description="Start date in DD-MM-YY format"),
        end_date: Optional[str] = Query(None, description="End date in DD-MM-YY format (optional)"),
        token: str = Header(...),
):
    try:
        # Convert start_date to datetime object
        start_date_obj = datetime.strptime(start_date, "%d-%m-%Y")

        # If end_date is provided, convert it to datetime object, else use start_date as the end date
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%d-%m-%Y")
        else:
            end_date_obj = start_date_obj

        # Extract user_id from token
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session ID")

        user_id = int(user_id)

        # Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # List all directories under REPORTS_DIR and filter by the date range
        reports_in_range = []
        for folder_name in os.listdir(REPORTS_DIR):
            folder_path = os.path.join(REPORTS_DIR, folder_name)

            # Ensure we're checking directories only
            if os.path.isdir(folder_path):
                try:
                    # Extract date from folder name assuming folder names are in YYYY-MM-DD format
                    folder_date = datetime.strptime(folder_name, "%Y-%m-%d")

                    # Check if the folder date is within the specified range
                    if start_date_obj <= folder_date <= end_date_obj:
                        # List files in this folder
                        files = os.listdir(folder_path)
                        if files:
                            reports_in_range.append({"date": folder_name, "reports": files})
                except ValueError:
                    # If the folder name isn't a valid date, skip it
                    continue

        if not reports_in_range:
            raise HTTPException(status_code=404, detail="No reports found for the specified date(s)")

        return {"start_date": start_date, "end_date": end_date or start_date, "reports": reports_in_range}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
