import asyncpg
import base64


async def create_table_user(configfile):
    # Execute a statement to create a new table
    conn = await asyncpg.connect(
        user=base64.b64decode(configfile["database"]["username"]).decode("utf-8"),
        password=base64.b64decode(configfile["database"]["password"]).decode("utf-8"),
        database=base64.b64decode(configfile["database"]["name"]).decode("utf-8"),
        host=configfile["database"]["host"],
        port=configfile["database"]["port"]
    )
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS user_table(
            id serial PRIMARY KEY,
            shop_name varchar(150) default Null,
            username varchar(150) UNIQUE,
            supervisor_userid varchar(150),
            password varchar(150),
            user_type varchar(150),
            time_last_edited TIMESTAMP
        )
    ''')
    await conn.close()
