from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth_router, employee_router, finance_router, inventory_router, manager_router
# from app.routers import auth_router, employee_router, manager_router, inventory_router, finance_router

# 1. Initialize the app ONCE
app = FastAPI(
    title="Restaurant Management API"
)

# 2. Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Flutter Web to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include ALL your routers so the endpoints actually exist
app.include_router(auth_router.router)
app.include_router(employee_router.router)
app.include_router(manager_router.router)
app.include_router(inventory_router.router)
app.include_router(finance_router.router)

@app.get("/")
def root():
    return {"message": "Restaurant API is running successfully"}