from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth import get_current_user, require_role
from app.database import supabase
from app.models import InventoryCreate, InventoryResponse, WastageCreate


router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post("/", status_code=201)
def add_item(item: InventoryCreate, user: dict = Depends(require_role(["admin"]))):
    return supabase.table("inventory").insert(item.model_dump()).execute().data[0]


@router.put("/{item_id}", response_model=InventoryResponse)
def update_stock(item_id: int, item: InventoryCreate, user: dict = Depends(require_role(["admin"]))):
    res = supabase.table("inventory").update(item.model_dump()).eq("id", item_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return res.data[0]


@router.get("/")
def get_inventory(
    search: Optional[str] = Query(None, description="Search by item name"),
    user: dict = Depends(get_current_user)
):
    # 1. Fetch all from DB
    res = supabase.table("inventory").select("*").order("item_name").execute()
    items = res.data

    # 2. If search is provided, filter the list
    if search and search.strip():
        search_lower = search.strip().lower()
        items = [i for i in items if search_lower in i["item_name"].lower()]

    # 3. Calculate total wastage for each item
    for item in items:
        waste_res = supabase.table("wastage").select("quantity").eq("item_id", item["id"]).execute()
        total_wasted = sum(w['quantity'] for w in waste_res.data)
        item["total_wasted"] = total_wasted # Add the new field

    return items


# GET SINGLE ITEM BY ID
@router.get("/{item_id}", response_model=InventoryResponse)
def get_inventory_item(item_id: int, user: dict = Depends(get_current_user)):
    res = supabase.table("inventory").select("*").eq("id", item_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return res.data[0]


# DELETE AN ITEM (Admin only)
@router.delete("/{item_id}")
def delete_item(item_id: int, user: dict = Depends(require_role(["admin"]))):
    res = supabase.table("inventory").delete().eq("id", item_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}



# RECORD WASTAGE (Manager/Admin only)
@router.post("/wastage", status_code=201)
def record_wastage(waste: WastageCreate, user: dict = Depends(require_role(["manager", "admin"]))):
    # 1. Log the wastage
    supabase.table("wastage").insert(waste.model_dump()).execute()
    
    # 2. Deduct from inventory
    item = supabase.table("inventory").select("quantity").eq("id", waste.item_id).execute()
    if not item.data:
        raise HTTPException(status_code=404, detail="Item not found in inventory")
    
    new_qty = item.data[0]['quantity'] - waste.quantity
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Wastage exceeds current stock")
        
    supabase.table("inventory").update({"quantity": new_qty}).eq("id", waste.item_id).execute()
    
    return {"message": "Wastage recorded and stock updated"}



