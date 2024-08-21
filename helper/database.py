import motor.motor_asyncio
from pymongo import ReturnDocument
from config import DATABASE_URI, DATABASE_NAME
# Initialize your database connection
class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users_col = self.db["users"]

    async def get_user_metadata(self, user_id):
        user = await self.users_col.find_one({"user_id": user_id})
        return user.get("metadata", {}) if user else {}

    async def set_user_metadata(self, user_id, metadata):
        await self.users_col.find_one_and_update(
            {"user_id": user_id},
            {"$set": {"metadata": metadata}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

# Initialize the database instance
db = Database(DATABASE_URI, DATABASE_NAME)    
