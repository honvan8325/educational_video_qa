from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def get_database():
    return db.client[settings.mongodb_database]


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    print("Connected to MongoDB")


async def close_mongo_connection():
    db.client.close()
    print("Closed MongoDB connection")
