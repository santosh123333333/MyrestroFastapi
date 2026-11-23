from datetime import datetime

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


class ProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    qualification: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    bio: Optional[str] = None



class ProfileCreate(ProfileBase):
    pass





class ProfileResponse(ProfileBase):
    id: int






## ================= AUTH & USERS =================
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:str
    token_type:str="bearer"

#userregister

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "employee"
    position: Optional[str] = None
    salary: float = 0

#userResponse

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    position: Optional[str]
    salary: float

# create finance section 
class TransactionCreate(BaseModel):
    type: str  # 'sale' or 'expense'
    category: str
    amount: float
    description: Optional[str] = None


# ================= INVENTORY =================
class InventoryCreate(BaseModel):
    item_name: str
    quantity: float
    unit: str
    cost_per_unit: float
class InventoryResponse(InventoryCreate):
    id: int
    last_updated: Optional[datetime] = None  


# Wastage create
class WastageCreate(BaseModel):
    item_id: int
    quantity: float
    reason: str



# ================= PAYSLIPS =================
class PayslipCreate(BaseModel):
    user_id: int
    month: str
    base_salary: float
    deductions: float = 0