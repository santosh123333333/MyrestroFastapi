from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth import require_role
from app.database import supabase
from app.models import TransactionCreate

router = APIRouter(prefix="/finance", tags=["Financials"])

# ==========================================
# 1. ADD TRANSACTION (Sales or Expenses)
# ==========================================
@router.post("/transactions", status_code=201)
def add_transaction(txn: TransactionCreate, user: dict = Depends(require_role(["manager", "admin"]))):
    data = txn.model_dump()
    data["created_by"] = user["id"]
    data["date"] = date.today().isoformat()
    res = supabase.table("transactions").insert(data).execute()
    return res.data[0]

# ==========================================
# 2. GET FINANCIAL SUMMARY (Dashboard Cards)
# ==========================================
@router.get("/summary")
def get_summary(period: str = "daily", user: dict = Depends(require_role(["manager", "admin"]))):
    today = date.today()
    
    # Calculate start date based on the selected period
    if period == "daily": start = today - timedelta(days=1)
    elif period == "weekly": start = today - timedelta(days=7)
    elif period == "monthly": start = today.replace(day=1)
    elif period == "yearly": start = today.replace(month=1, day=1)
    else: start = today - timedelta(days=1)

    # Fetch ALL sales
    sales = supabase.table("transactions").select("amount").eq("type", "sale").gte("date", start.isoformat()).execute()
    # Fetch ALL expenses (this now includes the salaries auto-added by the manager router)
    exps = supabase.table("transactions").select("amount").eq("type", "expense").gte("date", start.isoformat()).execute()

    t_sales = sum(x['amount'] for x in sales.data)
    t_exps = sum(x['amount'] for x in exps.data)

    return {
        "period": period,
        "total_sales": t_sales,
        "total_expenses": t_exps,
        "total_salaries": 0, # Salaries are already included in total_expenses
        "net_profit": t_sales - t_exps
    }

# ==========================================
# 3. GET TRANSACTIONS (With Search & Filter)
# ==========================================

@router.get("/transactions")
def get_transactions(
    period: str = "daily", 
    search: Optional[str] = Query(None), 
    user: dict = Depends(require_role(["manager", "admin"]))
):
    today = date.today()
    if period == "daily": start_date = today - timedelta(days=1)
    elif period == "weekly": start_date = today - timedelta(days=7)
    elif period == "monthly": start_date = today.replace(day=1)
    elif period == "yearly": start_date = today.replace(month=1, day=1)
    else: start_date = today - timedelta(days=1)

    query = supabase.table("transactions").select("*").gte("date", start_date.isoformat())
    
    if search:
        query = query.or_(f"type.ilike.%{search}%,category.ilike.%{search}%,description.ilike.%{search}%")
        
    res = query.order("date", desc=True).execute()
    transactions = res.data

    # --- NEW CODE: FETCH CREATOR NAMES ---
    users_res = supabase.table("users").select("id, full_name").execute()
    user_map = {u["id"]: u["full_name"] for u in users_res.data}
    
    # Attach the creator's name to each transaction
    for txn in transactions:
        txn["creator_name"] = user_map.get(txn.get("created_by"), "System")

    return transactions

# ==========================================
# 4. FETCH SINGLE TRANSACTION BY ID
# ==========================================
@router.get("/transactions/{transaction_id}")
def get_transaction_by_id(transaction_id: int, user: dict = Depends(require_role(["manager", "admin"]))):
    res = supabase.table("transactions").select("*").eq("id", transaction_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return res.data[0]

# ==========================================
# 5. GET CHART DATA (Last 7 Days for Flutter Charts)
# ==========================================
@router.get("/chart-data")
def get_chart_data(user: dict = Depends(require_role(["manager", "admin"]))):
    today = date.today()
    chart_data = []
    
    for i in range(6, -1, -1): # Last 7 days
        day_str = (today - timedelta(days=i)).isoformat()
        
        sales_res = supabase.table("transactions").select("amount").eq("type", "sale").eq("date", day_str).execute()
        exp_res = supabase.table("transactions").select("amount").eq("type", "expense").eq("date", day_str).execute()
        
        chart_data.append({
            "date": day_str,
            "sales": sum(item['amount'] for item in sales_res.data),
            "expenses": sum(item['amount'] for item in exp_res.data)
        })
        
    return chart_data