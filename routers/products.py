from decimal import Decimal

from fastapi import APIRouter,Header, HTTPException, status, UploadFile, Form
from fastapi.responses import JSONResponse
import asyncpg
import os
from utils.tools import find_user_id_by_token
from validations.user import Response
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yaml
import base64
import pdfplumber
import pandas as pd
import re
from pathlib import Path
from datetime import datetime


scriptDir = os.path.dirname(os.path.abspath(__file__))
configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

router = APIRouter()

# @router.post("/products/add", response_model=Response, summary="Upload invoice.", tags=["Products"])
# async def products_add(file: UploadFile, token: str = Header(...)):
#     try:
#         # Validate file type
#         if file.content_type != "application/pdf":
#             raise HTTPException(status_code=400, detail="File must be in PDF format")
#
#         # Retrieve user ID from token
#         loop = asyncio.get_running_loop()
#         user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
#         if not user_id:
#             return Response(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 message="Invalid session ID"
#             )
#
#         # Connect to the database
#         conn = await asyncpg.connect(
#             user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
#             password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
#             database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
#             host=configfile["database"]["host"],
#             port=configfile["database"]["port"]
#         )
#
#         # Verify user type
#         query = "SELECT * FROM user_table WHERE id = $1"
#         admin_record = await conn.fetchrow(query, int(user_id))
#         if admin_record["user_type"] != "accountant":
#             return Response(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 message="You do not have permission to perform this action"
#             )
#
#         # Save uploaded file in `upload` table
#         file_content = await file.read()
#         now = datetime.utcnow()
#         query = """
#             INSERT INTO upload (file_name, file_data, uploaded_at)
#             VALUES ($1, $2, $3) RETURNING id
#         """
#         file_record = await conn.fetchrow(query, file.filename, file_content, now)
#
#         if not file_record:
#             return Response(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 message="Failed to save the file in the database"
#             )
#
#         # Extract the PDF from the saved record
#         file_id = file_record["id"]
#         query = "SELECT file_data FROM upload WHERE id = $1"
#         file_data = await conn.fetchval(query, file_id)
#
#         # Use the file data to create the PDF reader
#         pdf_reader = PdfReader(file_data)
#
#         # Extract the specific table from the PDF (Assuming table_index = 2)
#         table_index = 2
#         specific_table = extract_table_by_name(pdf_reader, table_index)
#
#         if specific_table is None:
#             return Response(
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 message="Table 2 not found in the PDF."
#             )
#
#         # Process and insert the table data into `Products`
#         page_number, table_data = specific_table
#         insert_query = """
#             INSERT INTO Products (
#                 sl_no, brand_number, brand_name, product_type,
#                 pack_type, size_ml, qty_cases_delivered,
#                 qty_bottles_delivered, case_rate, btl_rate, total
#             )
#             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
#         """
#         for record in print_table_as_json(table_data):
#             rate_string = record["Case Rate / Btl Rate"]
#             extracted_values = re.findall(r"[\d.]+", rate_string)
#
#             if len(extracted_values) == 2:
#                 case_rate, btl_rate = map(float, extracted_values)
#             else:
#                 continue
#
#             await conn.execute(
#                 insert_query,
#                 int(record["Sl.No."]),
#                 record["Brand Number"],
#                 record["Brand Name"],
#                 record["Product Type"],
#                 record["Pack Type"],
#                 int(record["Size (ml)"]),
#                 int(record["Qty (Cases Delivered)"]),
#                 int(record["Qty (Bottles Delivered)"]),
#                 case_rate,
#                 btl_rate,
#                 float(record["Total"])
#             )
#
#         await conn.close()
#         return Response(
#             status_code=status.HTTP_201_CREATED,
#             message="The products data has been updated successfully."
#         )
#
#     except Exception as e:
#         return Response(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             message=f"An error occurred: {str(e)}"
#         )
TEMP_FOLDER = Path("C:/AlcoSales/invoices")
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists


def generate_datestamped_filename(original_filename: str) -> str:
    # Get the current date and time in the format YYYY-MM-DD_HHMMSS
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Split the original filename into name and extension
    name, extension = os.path.splitext(original_filename)

    # Generate the new filename with the datestamp
    new_filename = f"{name}_{timestamp}{extension}"

    return new_filename

def extract_table_by_name(pdf_path, table_index):
    """Extract tables containing the specified name from a PDF."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            extracted_tables = page.extract_tables()
            if extracted_tables:
                for table in extracted_tables:
                    tables.append((page_number, table))
                    if len(tables) >= table_index:
                        return tables[table_index - 1]  # Return the specific table
    return None

def clean_data(data):
    """Clean data by removing newline characters and extra spaces."""
    return [[cell.replace("\n", " ").strip() if isinstance(cell, str) else cell for cell in row] for row in data]

def print_table_as_json(table_data):
    """Convert extracted table data to JSON and print it."""
    # Clean table data
    clean_table = clean_data(table_data)

    # Convert to DataFrame
    columns = clean_table[0]  # First row as column names
    rows = clean_table[1:]  # Remaining rows as data
    df = pd.DataFrame(rows, columns=columns)

    # Convert to JSON
    json_data = df.to_dict(orient="records")
    return json_data


async def insert_products(data):
    """Insert or update product data in the database."""
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"],
    )

    select_query = """
        SELECT id, qty_cases_delivered, qty_bottles_delivered, total, available_products, available_price
        FROM products
        WHERE brand_number = $1
        AND brand_name = $2
        AND product_type = $3
        AND pack_type = $4
        AND size_ml = $5
    """

    update_query = """
        UPDATE products
        SET
            qty_cases_delivered = qty_cases_delivered + $1,
            qty_bottles_delivered = $2,
            total_bottles_delivered = $3,
            total = total + $4,
            available_products = available_products + $5,  -- Update available_products
            available_price = available_price + $6,        -- Update available_price
            time_last_edited = $7
        WHERE id = $8
    """

    insert_query = """
        INSERT INTO products (
            sl_no, brand_number, brand_name, product_type, pack_type,
            size_ml, qty_cases_delivered, qty_bottles_delivered,
            total_bottles_delivered, case_rate, btl_rate, total,
            available_products, available_price, time_last_edited
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
    """

    def calculate_bottles_per_case(product_type, size_ml):
        """Calculate bottles per case based on product type and size."""
        if product_type.lower() == "beer":
            if size_ml == 650:
                return 12
            elif size_ml == 350:
                return 24
            elif size_ml == 500 and "tin" in product_type.lower():
                return 24
        else:
            size_to_bottles = {
                375: 24,
                180: 48,
                1000: 9,
                2000: 4,
                750: 12,
                90: 96,
            }
            return size_to_bottles.get(size_ml, 0)

    for record in data:
        try:
            print(f"Processing record: {record}")

            # Extract and parse data from record
            rate_string = record["Case Rate / Btl Rate"]
            extracted_values = re.findall(r"[\d.]+", rate_string)

            if len(extracted_values) != 2:
                print(f"Failed to extract valid rates from: {rate_string}")
                continue

            case_rate, btl_rate = map(float, extracted_values)

            sl_no = int(record["Sl.No."])
            brand_number = record["Brand Number"]
            brand_name = record["Brand Name"]
            product_type = record["Product Type"]
            pack_type = record["Pack Type"]
            size_ml = int(record["Size (ml)"])
            qty_cases_delivered = int(record["Qty (Cases Delivered)"])
            qty_bottles_delivered = int(record["Qty (Bottles Delivered)"])
            total = float(record["Total"])
            time_last_edited = datetime.utcnow()

            bottles_per_case = calculate_bottles_per_case(product_type, size_ml)
            # Compute total bottles delivered
            total_bottles_delivered = qty_cases_delivered * bottles_per_case + qty_bottles_delivered

            # Check if the product exists
            existing_product = await conn.fetchrow(
                select_query, brand_number, brand_name, product_type, pack_type, size_ml
            )

            if existing_product:
                product_id = existing_product["id"]
                print(f"Updating existing product with ID: {product_id}")

                # Update the existing product
                await conn.execute(
                    update_query,
                    qty_cases_delivered,
                    qty_bottles_delivered,
                    total_bottles_delivered,
                    total,
                    total_bottles_delivered,  # Add total_bottles_delivered to available_products
                    total,  # Add total to available_price
                    time_last_edited,
                    product_id,
                )
            else:
                print("Inserting new product")

                # Insert as a new product
                await conn.execute(
                    insert_query,
                    sl_no,
                    brand_number,
                    brand_name,
                    product_type,
                    pack_type,
                    size_ml,
                    qty_cases_delivered,
                    qty_bottles_delivered,
                    total_bottles_delivered,
                    case_rate,  # Assign case_rate correctly
                    btl_rate,  # Assign btl_rate correctly
                    total,
                    total_bottles_delivered,  # Set available_products to total_bottles_delivered
                    total,  # Set available_price to total
                    time_last_edited,
                )

        except Exception as e:
            print(f"Error processing record: {record}, Error: {e}")

    await conn.close()


@router.post("/products/add", response_model=Response, summary="Upload invoice.", tags=["Products"])
async def products_add(file: UploadFile, token: str = Header(...)):
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File must be in PDF format")

        # Retrieve user ID from token
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
        if not user_id:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid session ID"
            )

        # Connect to the database
        conn = await asyncpg.connect(
            user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
            password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
            database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
            host=configfile["database"]["host"],
            port=configfile["database"]["port"]
        )

        # Verify user type
        query = "SELECT * FROM user_table WHERE id = $1"
        admin_record = await conn.fetchrow(query, int(user_id))
        if admin_record["user_type"] != "accountant":
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to perform this action"
            )

        # Save uploaded file to disk for processing
        TEMP_FOLDER.mkdir(exist_ok=True)
        file_path = TEMP_FOLDER / file.filename

        # Debugging the file path
        print(f"Saving file to: {file_path}")

        with open(file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Extract data using extract_table_by_name
        table_index = 2  # Assuming you're looking for the second table in the PDF
        extracted_table = extract_table_by_name(file_path, table_index)

        if not extracted_table:
            file_path.unlink()  # Clean up the file
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No table data found in the PDF."
            )

        page_number, table_data = extracted_table

        # Process and insert the table data into `Products`
        json_data = print_table_as_json(table_data)
        await insert_products(json_data)

        # Save the PDF file info into the `invoice` table
        now = datetime.utcnow()
        user_id = int(user_id)

        # Generate a filename with a datestamp
        original_filename = file.filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        name, extension = os.path.splitext(original_filename)
        datestamped_filename = f"{name}_{timestamp}{extension}"

        # Read file data into binary format
        file_data = await file.read()
        now = datetime.now()
        query = """
                    INSERT INTO invoice (file_name, file_data, upload_date, uploaded_by)
                    VALUES ($1, $2, $3, $4)
                """
        await conn.execute(query, datestamped_filename, file_data, now, user_id)

        await conn.close()
        return Response(
            status_code=status.HTTP_201_CREATED,
            message="The products data has been updated successfully."
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"An error occurred: {str(e)}"
        )

@router.get("/users/products", tags=["Products"])
async def get_products(token: str, brand_name: str = None, brand_number: str = None):
    try:
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
        if not user_id:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid session ID"
            )

        # Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # Fetch the user type
        query = "SELECT user_type FROM user_table WHERE id = $1"
        user_data = await conn.fetchrow(query, int(user_id))
        if user_data['user_type'] != 'accountant':
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have access to this section",
                data=None,
                detail=None
            )

        # Build the query dynamically based on the search criteria
        base_query = """
                    SELECT id, brand_number, brand_name, product_type, pack_type, size_ml, qty_cases_delivered, qty_bottles_delivered, case_rate, btl_rate, total, sold_products, sold_price, available_products, available_price
                    FROM products
                """
        filters = []
        values = []

        if brand_name:
            filters.append(f"brand_name ILIKE ${len(values) + 1}")
            values.append(f"%{brand_name}%")

        if brand_number:
            filters.append(f"brand_number = ${len(values) + 1}")
            values.append(brand_number)

        if filters:
            base_query += " WHERE " + " AND ".join(filters)

        # Fetch filtered or all products
        products = await conn.fetch(base_query, *values)
        if not products:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No product data found matching the search criteria",
                data=None,
                detail=None
            )

        # Process and structure the product data
        product_list = []
        for product in products:
            product_data = {
                "id": product['id'],
                "Brand Number": product['brand_number'],
                "Brand Name": product['brand_name'],
                "Product type": product['product_type'],
                "Pack Type": product['pack_type'],
                "Size (ml)": product['size_ml'],
                "QTY (Cases Delivered)": product['qty_cases_delivered'],
                "QTY (Bottles Delivered)": product['qty_bottles_delivered'],
                "Case Rate": product["case_rate"],
                "Btl Rate": product["btl_rate"],
                "Total": product["total"],
                "Sold Products": product["sold_products"],
                "Sold Price": product["sold_price"],
                "Available Products": product["available_products"],
                "Available Price": product["available_price"]
            }
            product_list.append(product_data)

        # Return the response
        return Response(
            status_code=status.HTTP_200_OK,
            message="The request was successful",
            data=product_list,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve products: {str(e)}",
            data=None,
            detail=None
        )


@router.post("/products/sell", response_model=Response, summary="Update sold products.", tags=["Products"])
async def update_sold_products(brand_number: str, sold_quantity: int, token: str = Header(...)) -> Response:
    try:
        # Validate the brand_number to ensure it's alphanumeric
        if not brand_number.isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Brand number must be alphanumeric."
            )

        # Validate the token
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
        if not user_id:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid session ID"
            )

        # Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # Check if the product exists
        query_check = """
                    SELECT sold_products, total_bottles_delivered, btl_rate, total, available_price, available_products, id
                    FROM products
                    WHERE brand_number = $1
                """
        product = await conn.fetchrow(query_check, brand_number)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found."
            )

        # Convert fetched values to Decimal to ensure consistent types
        current_quantity = product["total_bottles_delivered"] or 0
        btl_rate =product["btl_rate"] or 0
        current_sold = product["sold_products"] or 0  # Ensure `sold_products` is treated as 0 if null
        current_available_price = product["total"] or 0

        # Check if the sold quantity exceeds the available quantity
        if sold_quantity > current_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available quantity: {current_quantity}."
            )

        # Update the sold_products column
        new_sold_total = current_sold + Decimal(sold_quantity)
        sold_price = new_sold_total * btl_rate  # Calculate the total sold price based on quantity sold

        # Calculate new available price and products
         # Subtract the sold price from available price

        # **Fix the available_products calculation** by subtracting the sold quantity from the total quantity delivered
        new_available_products = current_quantity - new_sold_total  # available products = total delivered - sold
        new_available_price = btl_rate * new_available_products
        # Ensure available_products doesn't go negative
        new_available_products = max(new_available_products, 0)

        # Update the table
        query_update = """
                    UPDATE products
                    SET sold_products = $1,
                        sold_price = $2,
                        available_price = $3,
                        available_products = $4
                    WHERE brand_number = $5
                """
        await conn.execute(
            query_update,
            new_sold_total,
            sold_price,
            new_available_price,
            new_available_products,
            brand_number
        )

        # Fetch and order the updated records
        query_ordered = """
            SELECT * FROM products
            ORDER BY id
        """
        products = await conn.fetch(query_ordered)

        print(products)

        # Close the connection
        await conn.close()

        return Response(
            status_code=status.HTTP_200_OK,
            message=f"Sold products updated successfully. Total sold: {new_sold_total}."
        )

    except HTTPException as e:
        # Handle HTTP exceptions specifically
        return Response(
            status_code=e.status_code,
            message=e.detail
        )

    except Exception as e:
        # Handle unexpected errors
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"An unexpected error occurred: {str(e)}"
        )




def calculate_bottles_per_case(product_type: str, size_ml: int) -> int:
    """Calculate bottles per case based on product type and size."""
    if product_type.lower() == "beer":
        if size_ml == 650:
            return 12
        elif size_ml == 350:
            return 24
        elif size_ml == 500 and "tin" in product_type.lower():
            return 24
    else:
        size_to_bottles = {
            375: 24,
            180: 48,
            1000: 9,
            2000: 4,
            750: 12,
            90: 96,
        }
        return size_to_bottles.get(size_ml, 0)


@router.post("/products/manual", tags=["Products"])
async def insert_manual_products(
        token: str = Header(...),
        sl_no: int = Form(...),
        brand_number: str = Form(...),
        brand_name: str = Form(...),
        product_type: str = Form(...),
        pack_type: str = Form(...),
        size_ml: int = Form(...),
        qty_cases_delivered: int = Form(...),
        qty_bottles_delivered: int = Form(...),
        case_rate: float = Form(...),
        btl_rate: float = Form(...),
        total: float = Form(...),
):
    try:
        # Validate token
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session ID")

        # Calculate derived values
        bottles_per_case = calculate_bottles_per_case(product_type, size_ml)
        total_bottles_delivered = qty_cases_delivered * bottles_per_case + qty_bottles_delivered
        available_products = total_bottles_delivered
        available_price = total

        # Debug prints for request parameters and derived values
        print("Received manual product entry:")
        print(f"sl_no: {sl_no}, brand_number: {brand_number}, brand_name: {brand_name}")
        print(f"product_type: {product_type}, pack_type: {pack_type}, size_ml: {size_ml}")
        print(f"qty_cases_delivered: {qty_cases_delivered}, qty_bottles_delivered: {qty_bottles_delivered}")
        print(f"case_rate: {case_rate}, btl_rate: {btl_rate}, total: {total}")
        print(f"Calculated bottles_per_case: {bottles_per_case}")
        print(f"Calculated total_bottles_delivered: {total_bottles_delivered}")
        print(f"Set available_products: {available_products}, available_price: {available_price}")

        # Connect to the database
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )

        # Check if product exists based on multiple fields
        select_query = """
            SELECT id FROM products
            WHERE brand_number = $1
              AND brand_name = $2
              AND product_type = $3
              AND pack_type = $4
              AND size_ml = $5
        """
        # Normalize string fields for matching
        existing_product = await conn.fetchrow(
            select_query,
            brand_number,
            brand_name,
            product_type,
            pack_type,
            size_ml
        )
        print(
            f"Select Query Params: {brand_number.strip().lower()}, {brand_name.strip().lower()}, {product_type.strip().lower()}, {pack_type.strip().lower()}, {size_ml}")

        if existing_product:
            product_id = existing_product["id"]
            print(f"Product exists (ID: {product_id}). Updating record...")

            # Update query: add the new quantities and totals to the existing ones.
            update_query = """
                UPDATE products
                SET
                    qty_cases_delivered = qty_cases_delivered + $1,
                    qty_bottles_delivered = qty_bottles_delivered + $2,
                    total_bottles_delivered = total_bottles_delivered + $3,
                    total = total + $4,
                    available_products = available_products + $5,
                    available_price = available_price + $6,
                    time_last_edited = $7
                WHERE id = $8
            """
            print(
                f"Update Query Params: {qty_cases_delivered}, {qty_bottles_delivered}, {total_bottles_delivered}, {total}, {total_bottles_delivered}, {total}, {datetime.utcnow()}, {product_id}")
            await conn.execute(
                update_query,
                qty_cases_delivered,
                qty_bottles_delivered,
                total_bottles_delivered,
                total,
                total_bottles_delivered,  # Increase available_products by new total_bottles_delivered
                total,  # Increase available_price by new total
                datetime.utcnow(),
                product_id,
            )
        else:
            print("Product not found. Inserting new record...")
            insert_query = """
                INSERT INTO products (
                    sl_no, brand_number, brand_name, product_type, pack_type,
                    size_ml, qty_cases_delivered, qty_bottles_delivered,
                    total_bottles_delivered, case_rate, btl_rate, total,
                    available_products, available_price, time_last_edited
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, CURRENT_TIMESTAMP)
                RETURNING id;
            """
            print(
                f"Insert Query Params: {sl_no}, {brand_number.strip().lower()}, {brand_name.strip().lower()}, {product_type.strip().lower()}, {pack_type.strip().lower()}, {size_ml}, {qty_cases_delivered}, {qty_bottles_delivered}, {total_bottles_delivered}, {case_rate}, {btl_rate}, {total}, {available_products}, {available_price}, {datetime.utcnow()}")
            result = await conn.fetchrow(
                insert_query,
                sl_no,
                brand_number,
                brand_name,
                product_type,
                pack_type,
                size_ml,
                qty_cases_delivered,
                qty_bottles_delivered,
                total_bottles_delivered,
                case_rate,
                btl_rate,
                total,
                available_products,
                available_price
            )
            print(f"Inserted product with ID: {result['id']}")

        await conn.close()
        return JSONResponse(status_code=201, content={"message": "Product processed successfully"})

    except Exception as e:
        print(f"Error processing manual product: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
