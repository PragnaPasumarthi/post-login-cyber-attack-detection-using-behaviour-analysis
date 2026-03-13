from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, validator
from services.email_service import email_service
from services.redis_service import RedisService
from services.mongodb_service import mongodb_service

# Use a local Redis instance for this module to set session states
redis_client = RedisService()

router = APIRouter()

class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=50, description="Unique username of the employee")
    email: str = Field(..., description="Authorized company email address")

    @validator('email')
    def validate_email_format(cls, v):
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v

@router.post("/login")
async def login(request: LoginRequest):
    """
    1. User enters username and email.
    2. Check if the email exists in the hr_employees collection in MongoDB.
    3. If authorized, set them to "PENDING" in Redis.
    4. Send an email with a unique Verify/Kill token link.
    """
    
    # --- Authorization Check ---
    # We check the MongoDB 'hr_employees' collection to see if this user is "Hired"
    authorized_user = await mongodb_service.db.hr_employees.find_one({"email": request.email})
    
    if not authorized_user:
        print(f"SECURITY ALERT: Unauthorized login attempt blocked for {request.email}")
        raise HTTPException(
            status_code=401, 
            detail="Access Denied: This email is not in the authorized employee database."
        )

    print(f"SUCCESS: Authorized user {request.user_id} ({request.email}) identified.")
    
    # Send Email and get the new unique magic links
    tokens = email_service.send_verification_email(request.email, request.user_id)
    
    # Store their status in Redis
    redis_client.set_val(f"session:{request.user_id}", "PENDING", ex=300) # 5 min timeout
    
    # Keep track of the specific tokens linked to this user for security
    redis_client.set_val(f"token:{tokens['verify_token']}", request.user_id, ex=300)
    redis_client.set_val(f"token:{tokens['kill_token']}", request.user_id, ex=300)

    return {
        "status": "Check your email!",
        "message": f"Verification links sent to {request.email}. Workspace is locked until 'Yes, I'm in' is clicked."
    }

@router.get("/verify/{token}")
async def verify(token: str, user_id: str):
    """
    User clicked 'Yes, I'm In' from the email.
    We grant access to the workspace.
    """
    # Check if already verified to handle browser double-fetches
    session_status = redis_client.get_val(f"session:{user_id}")
    frontend_url = "http://localhost:5173"  # Default frontend URL

    if session_status == "ACTIVE":
         return RedirectResponse(url=f"{frontend_url}/dashboard")

    # Verify the token belongs to the user
    saved_user = redis_client.get_val(f"token:{token}")
    
    if saved_user != user_id:
        raise HTTPException(status_code=403, detail="Invalid Verification Token.")
    
    # Update Redis session to VERIFIED
    redis_client.set_val(f"session:{user_id}", "ACTIVE", ex=86400) # 24h
    
    # Clean up the single-use token
    redis_client.delete_val(f"token:{token}")
    
    # Redirect the user to the React Workspace dashboard.
    return RedirectResponse(url=f"{frontend_url}/dashboard")

@router.get("/report_compromise/{token}")
async def report_compromise(token: str, user_id: str):
    """
    User clicked 'This is not me'.
    We instantly Kill everything and alert the SOC team via WebSocket.
    """
    # Same check
    saved_user = redis_client.get_val(f"token:{token}")
    if saved_user != user_id:
        raise HTTPException(status_code=403, detail="Invalid Kill Token.")
    
    from api.websocket import manager # Import WebSocket manager
    
    # 1. Nuke their Redis session
    redis_client.clear_session(user_id)
    
    # 2. Tell the React App to immediately lock the screen via WebSocket
    await manager.send_termination(user_id)
    
    return {"message": f"SECURITY ALERT: Compromise Reported! All active sessions for {user_id} terminated."}

@router.get("/status/{user_id}")
async def check_status(user_id: str):
    """
    Frontend polling endpoint to see if the user has clicked the email link.
    Returns 'ACTIVE' if they are verified.
    """
    session_status = redis_client.get_val(f"session:{user_id}")
    return {"status": session_status or "PENDING"}
