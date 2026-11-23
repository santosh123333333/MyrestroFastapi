from fastapi import APIRouter, Depends, HTTPException
from app.database import supabase
from app.auth import require_role
from app.models import PayslipCreate
from typing import List
from datetime import date
from pydantic import BaseModel

router = APIRouter(prefix="/manager", tags=["Manager"])

# ==========================================
# 1. PAYSLIPS (Payroll Management)
# ==========================================

@router.post("/payslips", status_code=201)
def create_payslip(payslip: PayslipCreate, user: dict = Depends(require_role(["manager", "admin"]))):
    """Generate a new payslip AND record it as an expense"""
    data = payslip.model_dump()
    data["net_pay"] = data["base_salary"] - data["deductions"]
    data["status"] = "pending"
    
    # 1. Save Payslip
    res = supabase.table("payslips").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to create payslip")

    # 2. Log as Expense in Transactions table
    expense_data = {
        "type": "expense",
        "category": "Salary",
        "amount": data["net_pay"], # This deducts the exact net pay
        "description": f"Salary for {data['month']}",
        "date": date.today().isoformat(),
        "created_by": user["id"]
    }
    supabase.table("transactions").insert(expense_data).execute()

    return res.data[0]

@router.get("/payslips")
def get_all_payslips(user: dict = Depends(require_role(["manager", "admin"]))):
    """Fetch all payslips and attach the employee's name for Flutter"""
    # 1. Fetch all payslips
    res = supabase.table("payslips").select("*").order("created_at", desc=True).execute()
    payslips = res.data

    # 2. Fetch users to map ID -> Full Name
    users_res = supabase.table("users").select("id, full_name").execute()
    user_map = {u["id"]: u["full_name"] for u in users_res.data}

    # 3. Attach the name to each payslip
    for slip in payslips:
        slip["employee_name"] = user_map.get(slip["user_id"], "Unknown Employee")

    return payslips

@router.put("/payslips/{payslip_id}/pay")
def mark_payslip_as_paid(payslip_id: int, user: dict = Depends(require_role(["manager", "admin"]))):
    """Update a payslip status from pending to paid"""
    res = supabase.table("payslips").update({"status": "paid"}).eq("id", payslip_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Payslip not found")
    return res.data[0]

# ==========================================
# 2. STAFF MANAGEMENT
# ==========================================

@router.get("/users")
def get_all_users(user: dict = Depends(require_role(["manager", "admin"]))):
    """Fetch all users to display in the Flutter Staff screen"""
    res = supabase.table("users").select("id, full_name, email, role, position, salary").execute()
    return res.data

# Model for updating a user
class UserUpdate(BaseModel):
    full_name: str
    position: str
    salary: float
    role: str

@router.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserUpdate, current_user: dict = Depends(require_role(["admin"]))):
    """Update an employee's details (Admin only)"""
    res = supabase.table("users").update(user_data.model_dump()).eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    return res.data[0]

@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(require_role(["admin"]))):
    """Delete an employee (Admin only)"""
    res = supabase.table("users").delete().eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}