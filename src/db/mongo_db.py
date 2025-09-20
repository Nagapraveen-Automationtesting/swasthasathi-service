import ssl

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any

from src.config.settings import settings


class MongoConnect:
    def __init__(self, uri: str = settings.MONGO_CONNECTION_STRING, db_name: str = settings.DATABASE):
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[Any] = None

    async def connect_to_mongo(self):
        self.client = AsyncIOMotorClient(self.uri,  tls=True,
    tlsAllowInvalidCertificates=True)
        self.db = self.client[self.db_name]
        print("✅ Connected to MongoDB")

    async def close_mongo_connection(self):
        if self.client:
            self.client.close()
            print("🛑 MongoDB connection closed")

    async def fetch_one(self, collection: str, query: Dict, sort: List = None) -> Optional[Dict]:
        print(f"DB instance : {self.db}")
        if sort:
            result = await self.db[collection].find_one(query, sort=sort)
        else:
            result = await self.db[collection].find_one(query)
        return result if result else None

    async def fetch_many(self, collection: str, query: Dict, limit: int = 10, skip: int = 0, sort: List = None) -> List[Dict]:
        cursor = self.db[collection].find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return [doc async for doc in cursor]

    async def update_one(self, collection: str, query: Dict, update: Dict) -> Dict:
        result = await self.db[collection].update_one(query, update)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }

    async def insert_one(self, collection: str, query: Dict) -> Dict:
        print(f"\n\n{self.db}\n\nquery:\n{query}\n\n\n\n\n")
        result = await self.db[collection].insert_one(query)
        print(f"\n\n{result}\n\n")
        return {
            "status": result.acknowledged
        }

    async def update_many(self, collection: str, query: Dict, update: Dict) -> Dict:
        result = await self.db[collection].update_many(query, update)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }

    async def delete_one(self, collection: str, query: Dict) -> Dict:
        result = await self.db[collection].delete_one(query)
        return {"deleted_count": result.deleted_count}

    async def delete_many(self, collection: str, query: Dict) -> Dict:
        result = await self.db[collection].delete_many(query)
        return {"deleted_count": result.deleted_count}

    async def count_documents(self, collection: str, query: Dict) -> int:
        count = await self.db[collection].count_documents(query)
        return count

mongo = MongoConnect()
