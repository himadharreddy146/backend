import asyncpg
import base64


async def create_invoice_table(configfile):
    # Execute a statement to create a new table for invoices
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS invoice (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL,
            file_data BYTEA NOT NULL,
            upload_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER NOT NULL,  -- Reference to the user who uploaded
            FOREIGN KEY (uploaded_by) REFERENCES user_table(id)  -- Assuming there's a user_table
        );
    ''')
    await conn.close()