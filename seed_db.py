import asyncio
import random
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from services.mongodb_service import mongodb_service

# --- Realistic Indian Names and Companies ---
INDIAN_FIRST_NAMES = [
    "Aarav", "Vihaan", "Vivaan", "Ananya", "Diya", "Aditya", "Arjun", "Sai",
    "Riya", "Kavya", "Dhruv", "Kabir", "Siddharth", "Ishita", "Anjali",
    "Rohan", "Vikram", "Neha", "Pooja", "Rahul", "Sneha", "Karan", "Sanjay",
    "Amit", "Priya", "Sunita", "Deepak", "Rajesh", "Anita", "Anil", "Manoj",
    "Suresh", "Meena", "Ramesh", "Kiran", "Vijay", "Geeta", "Dinesh", "Rekha",
    "Nitin", "Ashok", "Sita", "Gaurav", "Swati", "Nishant", "Preeti", "Alok",
    "Shruti", "Tarun", "Divya"
]

INDIAN_LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Deshmukh", "Jain", "Reddy",
    "Rao", "Nair", "Iyer", "Chetty", "Chaudhary", "Verma", "Yadav", "Tiwari",
    "Mishra", "Pandey", "Mehta", "Bose", "Das", "Mukherjee", "Chatterjee",
    "Banerjee", "Sengupta", "Kaur", "Ahluwalia", "Bhatia", "Chopra", "Kapur",
    "Malhotra", "Mehra", "Sethi", "Suri", "Tandon", "Ahuja", "Arora", "Bedi",
    "Chawla", "Garg", "Goel", "Joshi", "Kulkarni", "Jadhav", "Pawar", "Shinde",
    "Tambe", "Gaikwad", "Naik", "Kale"
]

COMPANIES = [
    "Tata Consultancy Services", "Infosys", "Wipro", "HCL Technologies",
    "Tech Mahindra", "Reliance Industries", "Larsen & Toubro", "HDFC Bank",
    "ICICI Bank", "State Bank of India", "Bharti Airtel", "Maruti Suzuki",
    "Mahindra & Mahindra", "Bajaj Auto", "Sun Pharmaceutical", "ITC Limited",
    "Asian Paints", "Hindustan Unilever", "UltraTech Cement", "Nestle India",
    "Zomato", "Swiggy", "Ola Cabs", "Flipkart", "Razorpay", "Paytm", "Zerodha",
    "Postman", "Freshworks", "Zoho", "Pine Labs", "Dream11", "CRED",
    "BharatPe", "Meesho", "ShareChat", "Delhivery", "Nykaa", "Unacademy",
    "BYJU'S", "Upstox", "FirstCry", "Lenskart", "Pharmeasy", "Urban Company",
    "CarDekho", "Spinny", "Groww", "Acko", "Cure.fit"
]

# --- Real User Emails (REQUIRED: Add your real email here to test login) ---
USER_EMAILS = [
    "meghanaakota339@gmail.com",
    "meghu17102006@gmail.com",
    "pragnapasumarthi25@gmail.com",
    "pragnashetty559@gmail.com",
    "belliappa1710@gmail.com"
]

STATUSES = ["New", "Contacted", "Negotiation", "Closed"]

DEAL_VALUES = [50000, 150000, 200000, 500000, 1000000, 2500000, 5000000]

def generate_random_phone():
    return f"+91 {random.randint(6, 9)}{random.randint(1000, 9999)} {random.randint(10000, 99999)}"

async def seed_database():
    print(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.threatsense_db

    print("Dropping existing collections for a fresh start...")
    await db.sales_customers.drop()
    await db.sales_appointments.drop()
    await db.hr_employees.drop()
    await db.soc_alerts.drop()
    await db.security_events.drop()

    print("Re-initializing indexes...")
    await mongodb_service.connect()

    # --- 1. Seed 50 Sales Customers ---
    print("Generating 50 realistic Indian Sales Customers...")
    customers = []
    for i in range(50):
        first_name = random.choice(INDIAN_FIRST_NAMES)
        last_name = random.choice(INDIAN_LAST_NAMES)
        domain = random.choice(COMPANIES).lower().replace(" ", "").replace("&", "")
        
        # Random date within the last 30 days
        last_contact = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
        
        customer = {
            "name": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}@{domain}.com",
            "phone": generate_random_phone(),
            "company": random.choice(COMPANIES),
            "status": random.choice(STATUSES),
            "revenue": random.choice(DEAL_VALUES),
            "lastContactDate": last_contact.isoformat()
        }
        customers.append(customer)

    await db.sales_customers.insert_many(customers)
    print(f"✅ Inserted {len(customers)} sales customers.")

    # --- 2. Seed Sales Appointments ---
    print("Generating Sales Appointments...")
    appointments = []
    
    # Needs some active customer IDs
    cursor = db.sales_customers.find({}, {"_id": 1, "name": 1, "company": 1}).limit(5)
    active_customers = await cursor.to_list(length=5)

    meeting_types = ["Demo", "Follow-up", "Contract Discussion", "Initial Pitch"]
    
    for i, active_customer in enumerate(active_customers):
        appt_date = datetime.now(timezone.utc) + timedelta(days=random.randint(1, 14))
        appt = {
            "customerId": str(active_customer["_id"]),
            "clientName": active_customer["name"],
            "company": active_customer["company"],
            "executive": "Sales User",
            "date": appt_date.strftime("%Y-%m-%d"),
            "time": f"{random.randint(10, 16):02d}:00",
            "meetingType": random.choice(meeting_types),
            "status": "Scheduled"
        }
        appointments.append(appt)

    await db.sales_appointments.insert_many(appointments)
    print(f"✅ Inserted {len(appointments)} sales appointments.")

    # --- 3. Seed HR Employees ---
    print("Generating HR Employees Database...")
    departments = ["Engineering", "Sales", "Support", "Marketing", "HR"]
    roles = ["Manager", "Lead", "Associate", "Analyst", "Director"]
    
    employees = []
    for i in range(20):
        first_name = random.choice(INDIAN_FIRST_NAMES)
        last_name = random.choice(INDIAN_LAST_NAMES)
        employees.append({
            "name": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}@threatsense.io",
            "department": random.choice(departments),
            "role": random.choice(roles),
            "status": "Active" if random.random() > 0.1 else "Departed",
            "hireDate": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1000))).isoformat()
        })
    
    await db.hr_employees.insert_many(employees)
    
    # --- 3b. Seed Real User Emails ---
    if USER_EMAILS and USER_EMAILS[0] != "your-email@example.com":
        print(f"Authorizing real user emails: {USER_EMAILS}...")
        
        # We assign different roles to show different behaviors for the demo
        real_user_profiles = [
            {"dept": "Engineering", "role": "Director (Admin)"},
            {"dept": "HR", "role": "Manager"},
            {"dept": "Finance", "role": "Finance Head"},
            {"dept": "Sales", "role": "Lead"},
            {"dept": "Support", "role": "Senior Associate"}
        ]
        
        real_users = []
        for i, email in enumerate(USER_EMAILS):
            name = email.split('@')[0].capitalize()
            # Cycle through profiles or default
            profile = real_user_profiles[i % len(real_user_profiles)]
            
            real_users.append({
                "name": f"{name} ({profile['role']})",
                "email": email,
                "department": profile['dept'],
                "role": profile['role'],
                "status": "Active",
                "hireDate": datetime.now(timezone.utc).isoformat()
            })
            
        await db.hr_employees.insert_many(real_users)
        print(f"✅ Authorized {len(real_users)} real user(s) with custom behavioral roles.")
    else:
        print("ℹ️ Note: No real USER_EMAILS detected. Update 'seed_db.py' to add your email for testing.")

    print(f"✅ Inserted {len(employees)} total HR employees.")

    # --- 4. Seed SOC Alerts / Security Events ---
    print("Generating SOC Alerts / Security Events...")
    anomaly_types = ["Off-Hours Access", "High Velocity Access", "Unusual ISP", "Mass Download"]
    severities = ["Low", "Medium", "High", "Critical"]
    
    security_events = []
    for i in range(30):
        timestamp = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))
        event = {
            "user": random.choice(["alice@threatsense.io", "bob@threatsense.io", "charlie@threatsense.io"]),
            "action_type": "Data Export",
            "endpoint": "/api/sales/export",
            "timestamp": timestamp.isoformat(),
            "ip_address": f"192.168.1.{random.randint(10, 200)}",
            "risk_score": random.randint(40, 95),
            "anomaly_type": random.choice(anomaly_types),
            "severity": random.choice(severities),
            "status": "Open" if random.random() > 0.5 else "Investigating"
        }
        security_events.append(event)
        
    await db.security_events.insert_many(security_events)
    print(f"✅ Inserted {len(security_events)} security events.")
    
    print("\n🎉 Database Seed Complete! Your frontend dashboards now have premium data.")

if __name__ == "__main__":
    asyncio.run(seed_database())
