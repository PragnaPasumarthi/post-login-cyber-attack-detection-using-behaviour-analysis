from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

class MongoDBService:
    def __init__(self):
        self.client = None
        self.db = None
        self.uri = settings.MONGODB_URL

    async def connect(self):
        """Initialize the MongoDB connection"""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            # Send a ping to confirm a successful connection
            await self.client.admin.command('ping')
            self.db = self.client.threatsense_db
            
            # Create indexes for faster queries
            await self.db.security_events.create_index("user")
            await self.db.security_events.create_index("timestamp")
            await self.db.security_events.create_index("risk_score")
            
            # Additional indexes for dashboards
            await self.db.sales_customers.create_index("email", unique=True)
            await self.db.sales_customers.create_index("status")
            await self.db.sales_customers.create_index("company")
            
            await self.db.sales_appointments.create_index("customerId")
            await self.db.sales_appointments.create_index("date")
            
            await self.db.hr_employees.create_index("department")
            await self.db.hr_employees.create_index("status")
            
            print("SUCCESS: MongoDB Connected Successfully.")
            print("SUCCESS: Database indexes created for all collections.")
        except Exception as e:
            print(f"ERROR: Could not connect to MongoDB: {e}")
            print("Check if MongoDB Compass/Server is running on your machine.")

    async def close(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()

    async def log_security_event(self, event_data):
        """Permanently store a security event or alert"""
        if self.db is not None:
            await self.db.security_events.insert_one(event_data)

# Singleton instance
mongodb_service = MongoDBService()
