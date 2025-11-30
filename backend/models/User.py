# models/User.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str  
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None 
    email: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel): 
    uid: str
    username: str
    email: str

    class Config:
        from_attributes = True  
        
class UserInDB(UserResponse):
    hashed_password: str