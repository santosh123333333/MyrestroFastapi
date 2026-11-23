from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase
from app.auth import get_current_user

router = APIRouter(prefix="/employee", tags=["Employees"])

@router.get("/me")
def get_my_profile(user: dict = Depends(get_current_user)):
    res = supabase.table("users").select("id, full_name, email, role, position, salary").eq("id", user["id"]).execute()
    if not res.data:
        raise HTTPException(404, "User not found")
    return res.data[0]

@router.get("/my-payslips")
def get_my_payslips(user: dict = Depends(get_current_user)):
    res = supabase.table("payslips").select("*").eq("user_id", user["id"]).execute()
    return res.data

