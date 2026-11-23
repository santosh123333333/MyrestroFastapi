from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import hash_password, verify_password, create_access_token, require_role, get_current_user
from typing import Optional

from app.models import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserRegister, current_user: Optional[dict] = Depends(get_current_user)):
    # 1. Check if ANY users exist in the database
    all_users = supabase.table("users").select("id").execute()
    
    # 2. If users exist, enforce Admin role
    if all_users.data:
        # If no current_user (no token) OR user is not admin -> Block
        if not current_user or current_user["role"] != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Only admins can register new users."
            )
            
    # 3. Check if the specific email already exists
    existing = supabase.table("users").select("id").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(400, "Email already exists")
        
    # 4. If this is the very first user, force their role to 'admin'
    data = user.model_dump(exclude={"password"})
    if not all_users.data:
        data["role"] = "admin" # First user is always admin
        
    data["password_hash"] = hash_password(user.password)
    
    # 5. Save to database
    res = supabase.table("users").insert(data).execute()
    return res.data[0]
# @router.post("/login", response_model=TokenResponse)
# def login(credentials: UserLogin):
#     res = supabase.table("users").select("*").eq("email", credentials.email).execute()
#     if not res.data:
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     user = res.data[0]
#     if not verify_password(credentials.password, user["password_hash"]):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]})
#     return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Swagger uses 'username', so we map it to the email column
    res = supabase.table("users").select("*").eq("email", form_data.username).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = res.data[0]
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}