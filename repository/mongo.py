import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv(
    "MONGO_URL",
    "mongodb://mongo_admin:password@localhost:27017/?authSource=admin"
)

client = AsyncIOMotorClient(MONGO_URL)
database = client["library_db"]

async def get_database():
    return database