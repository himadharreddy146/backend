import pdfplumber
import pandas as pd
import asyncpg
import json
import re
import asyncio

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

DB_CONFIG = {
    "user": "postgres",
    "password": "@Suneel1*",
    "database": "project",
    "host": "localhost",
    "port": 5432,
}
async def update_database_async(dataframe, table_name):
    """Asynchronously update the database with DataFrame data."""
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        # Create table structure based on DataFrame columns
        columns = ", ".join([f"{col} TEXT" for col in dataframe.columns])
        await conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});")

        # Insert data into the table
        for _, row in dataframe.iterrows():
            values = ", ".join([f"${i + 1}" for i in range(len(row))])
            sql = f"INSERT INTO {table_name} VALUES ({values})"
            await conn.execute(sql, *row)

        print(f"Data updated for table: {table_name}")
    finally:
        await conn.close()


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

    # Convert to JSON and print
    json_data = df.to_dict(orient="records")
    return json_data
    # return json.dumps(json_data, indent=4)  # Pretty print JSON


async def insert_products(data):
    conn = await asyncpg.connect(
        user='postgres',
        password='@Suneel1*',
        database='project',
        host='localhost',
        port=5432
    )
    # Define the SQL statement
    query = """
        INSERT INTO Products (
            sl_no, brand_number, brand_name, product_type,
            pack_type, size_ml, qty_cases_delivered,
            qty_bottles_delivered, case_rate, btl_rate, total
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    """
    for record in data:
        # case_rate, btl_rate = map(
        #     float, re.findall(r"[\d.]+", record["Case Rate / Btl Rate"])
        # )
        # case_rate, btl_rate = map(float, re.findall(r"[\d.]+", record["Case Rate / Btl Rate"]))
        # print(case_rate)
        # print(btl_rate)
        print(record)
        rate_string = record["Case Rate / Btl Rate"]

        # Extract the numbers using regex
        extracted_values = re.findall(r"[\d.]+", rate_string)

        # Ensure that we have exactly two values (case rate and btl rate)
        if len(extracted_values) == 2:
            case_rate, btl_rate = map(float, extracted_values)
            print(f"Brand Number: {record['Brand Number']}, Case Rate: {case_rate}, Btl Rate: {btl_rate}")
        else:
            # Handle the case where extraction doesn't work as expected
            print(f"Failed to extract valid rates from: {rate_string}")
            continue
        # Insert each record
        await conn.execute(
            query,
            int(record["Sl.No."]),
            record["Brand Number"],
            record["Brand Name"],
            record["Product Type"],
            record["Pack Type"],
            int(record["Size (ml)"]),
            int(record["Qty (Cases Delivered)"]),
            int(record["Qty (Bottles Delivered)"]),
            case_rate,
            btl_rate,
            float(record["Total"])
        )

    await conn.close()

if __name__ == "__main__":
    pdf_path = "invoice.pdf"
    table_index = 2  # Extract the 2nd table
    # print(extract_table_by_name(pdf_path, table_index))
    specific_table = extract_table_by_name(pdf_path, table_index)
    if specific_table:
        page_number, table_data = specific_table
        print(f"Table 2 extracted from page {page_number}.\n")

        # Step 2: Print the table data as JSON
        asyncio.run(insert_products(print_table_as_json(table_data)))
        # print_table_as_json(table_data)

    else:
        print("Table 2 not found in the PDF.")
