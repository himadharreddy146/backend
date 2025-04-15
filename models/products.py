import asyncpg
import base64


async def create_table_shop_invoice(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS products(
            id serial PRIMARY KEY,
            sl_no INT,
            brand_number VARCHAR(20),
            brand_name VARCHAR(255),
            product_type VARCHAR(50),
            pack_type VARCHAR(5),
            size_ml INT,
            qty_cases_delivered INT,
            qty_bottles_delivered INT,
            case_rate NUMERIC(10, 2),
            btl_rate NUMERIC(10, 2),
            total NUMERIC(15, 2),
            sold_products INT DEFAULT 0 CHECK (sold_products >= 0),
            sold_price FLOAT DEFAULT 0 CHECK (sold_price >= 0),
            available_products FLOAT DEFAULT 0,
            available_price FLOAT DEFAULT 0,
            time_last_edited TIMESTAMP
        )
    ''')
    await conn.close()

