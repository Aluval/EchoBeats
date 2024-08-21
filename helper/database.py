import motor.motor_asyncio
from pymongo import ReturnDocument
from config import DATABASE_URI, DATABASE_NAME
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datetime import datetime

# Initialize your database connection
class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users_col = self.db["users"]
        self.media_info_col = self.db.media_info
        self.stats_col = self.db.stats
        self.banned_col = self.db["banned_users"]

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

        
    async def add_user(self, user_id: int, username: str):
        try:
            await self.users_col.update_one(
                {"user_id": user_id},
                {"$set": {
                    "username": username,
                    "joined_updates_channel": False,
                    "joined_group_channel": False
                }},
                upsert=True
            )
        except PyMongoError as e:
            print(f"An error occurred while updating the user: {e}")
            raise

    async def store_media_info_in_db(self, media_info):
        result = await self.media_info_col.insert_one(media_info)
        return result.inserted_id
 
    async def ban_user(self, user_id: int):
        try:
            await self.banned_col.update_one(
                {"user_id": user_id},
                {"$set": {"banned": True}},
                upsert=True
            )
        except PyMongoError as e:
            print(f"An error occurred while banning the user: {e}")
            raise    

    async def unban_user(self, user_id: int):
        try:
            await self.banned_col.delete_one({"user_id": user_id})
        except PyMongoError as e:
            print(f"An error occurred while unbanning user: {e}")
            raise

    async def count_users(self):
        try:
            return await self.users_col.count_documents({})
        except PyMongoError as e:
            print(f"An error occurred while counting users: {e}")
            raise

    async def count_banned_users(self):
        try:
            return await self.banned_col.count_documents({})
        except PyMongoError as e:
            print(f"An error occurred while counting banned users: {e}")
            raise

    async def get_user(self, user_id: int):
        try:
            return await self.users_col.find_one({"user_id": user_id})
        except PyMongoError as e:
            print(f"An error occurred while retrieving user: {e}")
            raise

    async def is_user_banned(self, user_id: int):
        try:
            banned_user = await self.banned_col.find_one({"user_id": user_id})
            return banned_user is not None
        except PyMongoError as e:
            print(f"An error occurred while checking if user is banned: {e}")
            raise

    async def update_user_membership(self, user_id: int, joined_updates_channel: bool, joined_group_channel: bool):
        try:
            await self.users_col.update_one(
                {"user_id": user_id},
                {"$set": {
                    "joined_updates_channel": joined_updates_channel,
                    "joined_group_channel": joined_group_channel
                }},
                upsert=True
            )
        except PyMongoError as e:
            print(f"An error occurred while updating user membership: {e}")
            raise  

  
    async def save_stats(self, stats):
        try:
            await self.stats_col.update_one(
                {'_id': 'server_stats'},
                {'$set': stats},
                upsert=True
            )
        except Exception as e:
            print(f"An error occurred while saving stats: {e}")

    async def get_stats(self):
        try:
            stats = await self.stats_col.find_one({'_id': 'server_stats'})
            if stats:
                return stats
            return {}
        except Exception as e:
            print(f"An error occurred while retrieving stats: {e}")
            return {}


    async def clear_database(self):
        # Drop all collections
        await self.users_col.drop()        
        await self.media_info_col.drop()
        await self.stats_col.drop()
        await self.banned_col.drop()
        

                
    async def get_all_user_ids(self):
        try:
            cursor = self.users_col.find({}, {"user_id": 1})
            user_ids = await cursor.to_list(length=10000)
            return [user['user_id'] for user in user_ids if 'user_id' in user]
        except PyMongoError as e:
            print(f"An error occurred while retrieving all user IDs: {e}")
            raise
            
# Initialize the database instance
db = Database(DATABASE_URI, DATABASE_NAME)    
