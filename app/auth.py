# JWt Authentication logic


import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv




#load secret key
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(base_dir, ".env"))
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Valid for 2 hours


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# OAuth2 Scheme (Points to our login endpoint for Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login",auto_error=False)


# --- Password Helpers ---
def hash_password(password: str):
    return pwd_context.hash(password)



def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# --- Token Helpers ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    #ADD THIS CHECK: If no token, return None immediately!
    if token is None:
          return None
  

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            raise credentials_exception
            
        return {"id": int(user_id), "role": role}
    except JWTError:
        raise credentials_exception


def require_role(allowed_roles: list):
    async def role_checker(user: dict = Depends(get_current_user)):
        
         # ADD THIS CHECK: If no user, deny access cleanly
        if not user:
            raise HTTPException(
                status_code=401, 
                detail="Not authenticated. Please log in."
            )

        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not enough permissions"
            )
        return user
    return role_checker
    