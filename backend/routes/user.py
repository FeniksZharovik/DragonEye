# routes/user.py
from fastapi import APIRouter, HTTPException
from models.User import UserCreate, UserUpdate, UserResponse
from controllers.UserController import (
    get_all_users,  # ← Now it’s a real function!
    get_user_by_uid,
    create_user,
    update_user,
    delete_user
)

router = APIRouter()

@router.get("/", response_model=dict)
async def read_users(
    page: int = 1,
    limit: int = 10,
    search: str = None
):
    try:
        result = get_all_users(page=page, limit=limit, search=search)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{uid}", response_model=UserResponse)
async def read_user(uid: str):
    user = get_user_by_uid(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse)
async def create_new_user(user: UserCreate):
    return create_user(user.username, user.email, user.password)

@router.put("/{uid}", response_model=UserResponse)
async def update_existing_user(uid: str, user: UserUpdate):
    return update_user(
        uid=uid,
        username=user.username,
        email=user.email,
        password=user.password
    )

@router.delete("/{uid}")
async def delete_existing_user(uid: str):
    success = delete_user(uid)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}