import motor.motor_asyncio
from pyrogram import Client, filters
from pydub import AudioSegment
from pyrogram.types import Message
import os
import subprocess
from pymongo import ReturnDocument

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

db = Database("mongodb_uri", "database_name")
