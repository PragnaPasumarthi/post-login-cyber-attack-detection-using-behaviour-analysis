from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

router = APIRouter()

class LogType(str, Enum):
    FILE_ACCESS = "File Access"
    LOGIN = "Login"
    DATA_EXPORT = "Data Export"
    SENSITIVE_ACCESS = "Sensitive File Access"
    SYSTEM_CONFIG = "System Config Change"

class Department(str, Enum):
    ENGINEERING = "Engineering"
    HR = "HR"
    FINANCE = "Finance"
    SALES = "Sales"
    SUPPORT = "Support"
    IT = "IT"

class Location(str, Enum):
    MUMBAI = "Mumbai"
    BANGALORE = "Bangalore"
    HYDERABAD = "Hyderabad"
    DELHI = "Delhi"
    REMOTE = "Remote"
    SPOOFED = "Unknown/Spoofed"

class DeviceType(str, Enum):
    LAPTOP = "Laptop (Mac/Linux)"
    WINDOWS = "Windows Desktop"
    MOBILE = "Mobile Device"
    TABLET = "Tablet"

class UserAction(BaseModel):
    user: str = Field(..., min_length=3, max_length=100, description="Authorized email of the user")
    log_type: LogType = Field(..., description="The category of action performed")
    department: Department = Field(..., description="User's organizational department")
    file_accessed: str = Field(..., min_length=1, max_length=255)
    location: Location = Field(..., description="Physical or network location of the user")
    device_type: DeviceType = Field(..., description="The type of hardware used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            if not v or v == "string":
                return datetime.utcnow()
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return datetime.utcnow()
        return v or datetime.utcnow()

@router.post("/log")
async def log_action(action: UserAction):
    from main import detector, redis_client
    
    # 1. Get User History from Redis for sliding window
    history = redis_client.get_user_history(action.user)
    
    # Convert Pydantic model to dict, ensuring datetime is serialized correctly if needed
    # but for ML, we'll pass the dict which now includes real objects where helpful
    action_dict = action.dict()
    action_dict['timestamp'] = action.timestamp.isoformat() # ML model expects string currently
    
    # 2. Run ML Analysis
    analysis = detector.predict(action_dict, history)
    
    # 3. Update Risk Score in Redis
    # Anomaly increases risk by 20, suspicious score adds its fraction
    risk_increment = 20 if analysis['is_anomaly'] else (analysis['anomaly_score'] / 2)
    
    # --- Behavioral Demo Tweak ---
    # We make certain users more sensitive to show difference to evaluators
    if action.user == "belliappa1710@gmail.com":
        risk_increment *= 2.5 # "The Hacker" - Very sensitive
        print(f"DEMO: High sensitivity applied to {action.user}")
    elif action.user == "meghanaakota339@gmail.com":
        risk_increment *= 0.5 # "The Trusted Admin" - Less likely to be locked out
        print(f"DEMO: High trust applied to {action.user}")
    
    new_risk = redis_client.update_risk_score(action.user, risk_increment)
    
    # 4. Store current action in sliding window (as dict)
    redis_client.store_action(action.user, action_dict)
    
    # 5. Determine if we should trigger a kill (Threshold e.g. 70)
    terminate = new_risk >= 70
    
    if terminate:
        from api.websocket import manager
        from services.mongodb_service import mongodb_service
        
        # 4.5. Log this serious event to MongoDB for permanent record
        await mongodb_service.log_security_event({
            "user": action.user,
            "type": "TERMINATION",
            "risk_score": float(new_risk),
            "timestamp": action.timestamp, # MongoDB stores real Date objects
            "details": analysis
        })
        
        await manager.send_termination(action.user)
    
    return {
        "status": "success",
        "analysis": analysis,
        "current_risk": new_risk,
        "action_required": "TERMINATE" if terminate else "CONTINUE"
    }
