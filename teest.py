# import asyncio
#
# from utils import send_result_to_api
#
# asyncio.run(send_result_to_api())
#



import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
DATABASE_URL = "postgresql+asyncpg://postgres:2134@localhost:5432/dialdepp"

async def test_connection():
    engine = create_async_engine(DATABASE_URL, echo=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("Database connection successful:", result.scalar_one())
    except Exception as e:
        print("Database connection failed:", str(e))
    finally:
        await engine.dispose()

asyncio.run(test_connection())
