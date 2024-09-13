import asyncpg


async def connect_to_database():
    conn = await asyncpg.connect(
        user="user", password="password",
        database="db", host="127.0.0.1"
    )
    return conn

async def close_database_connection(conn):
    await conn.close()
