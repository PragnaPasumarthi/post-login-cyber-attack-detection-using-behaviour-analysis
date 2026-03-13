from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from services.mongodb_service import mongodb_service

router = APIRouter()

# --- Pydantic Models for Input Validation ---

class AppointmentCreate(BaseModel):
    client_name: str = Field(..., description="Name of the client")
    company: str = Field(..., description="Company name")
    executive: str = Field(..., description="Sales executive assigned")
    date: str = Field(..., description="Date of appointment YYYY-MM-DD")
    time: str = Field(..., description="Time of appointment HH:MM AM/PM")
    meeting_type: str = Field(..., description="Type of meeting")
    status: str = Field(default="Scheduled", description="Status of the appointment")

class DealCreate(BaseModel):
    deal_id: str = Field(..., description="Reference ID generated from the appointment")
    client_name: str = Field(..., description="Name of the client")
    company: str = Field(..., description="Company name")
    email: str = Field(..., description="Client email address")
    phone_no: str = Field(..., description="Client phone number")
    status: str = Field(..., description="Current status of the deal (e.g., Negotiation, Closed)")
    revenue: float = Field(..., description="Total value/revenue of the deal")
    last_contact_date: str = Field(..., description="Last date contacted YYYY-MM-DD")

# --- Helper to serialize MongoDB documents ---
def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# --- Routes ---

@router.get("/appointments")
async def get_appointments():
    """Fetch the latest 10 appointments to display on the Sales dashboard."""
    cursor = mongodb_service.db.sales_appointments.find().sort("_id", -1).limit(10)
    appointments = await cursor.to_list(length=10)
    return [serialize_doc(apt) for apt in appointments]

@router.post("/appointments")
async def create_appointment(appointment: AppointmentCreate):
    """Save a new appointment and generate a pseudo Deal ID."""
    apt_dict = appointment.dict()
    
    # We prefix a deal ID based on the timestamp for HR side usage
    apt_dict["generated_deal_id"] = f"DL-{datetime.now().strftime('%m%d%H%M%S')}"
    
    result = await mongodb_service.db.sales_appointments.insert_one(apt_dict)
    
    if result.inserted_id:
        return {"status": "success", "id": str(result.inserted_id), "deal_id": apt_dict["generated_deal_id"]}
    raise HTTPException(status_code=500, detail="Failed to create appointment")


@router.get("/deals")
async def get_deals():
    """Fetch the deals pipeline built by HR to display on the Sales dashboard."""
    # Getting from sales_customers collection as requested
    cursor = mongodb_service.db.sales_customers.find({"deal_id": {"$exists": True}}).sort("_id", -1)
    deals = await cursor.to_list(length=100)
    return [serialize_doc(deal) for deal in deals]

@router.post("/deals")
async def create_deal(deal: DealCreate):
    """Receive additional data from HR and insert it into the deal pipeline."""
    deal_dict = deal.dict()
    
    # We insert this enriched data into sales_customers to form the pipeline
    result = await mongodb_service.db.sales_customers.insert_one(deal_dict)
    
    if result.inserted_id:
        return {"status": "success", "id": str(result.inserted_id)}
    raise HTTPException(status_code=500, detail="Failed to create deal")
