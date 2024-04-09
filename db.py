import asyncpg


async def connect_to_database():
    conn = await asyncpg.connect(
        user="pasha", password="703568ks",
        database="storage", host="127.0.0.1"
    )
    return conn

async def close_database_connection(conn):
    await conn.close()