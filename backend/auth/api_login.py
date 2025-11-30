from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel
from controllers.UserController import get_user_by_username_or_email, get_user_by_uid
from auth.security import verify_password
from auth.session import create_session, get_session, delete_session

router = APIRouter(tags=["Auth"])

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    uid: str
    username: str
    email: str

async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    user = get_user_by_uid(session["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Handle preflight requests
@router.options("/login")
async def options_login():
    return {"message": "OK"}

@router.post("/login")
async def login(response: Response, request: LoginRequest):
    user = get_user_by_username_or_email(request.username_or_email)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session_id = create_session(user["uid"])
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600
    )
    return {
        "message": "Logged in successfully",
        "session_id": session_id,
        "user": UserResponse(
            uid=user["uid"],
            username=user["username"],
            email=user["email"]
        )
    }

@router.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    user_info = {"uid": None, "username": None}

    if session_id:
        session = get_session(session_id)
        if session:
            user = get_user_by_uid(session["user_id"])
            if user:
                user_info = {
                    "uid": user["uid"],
                    "username": user["username"]
                }
        delete_session(session_id)

    response.delete_cookie("session_id")
    message = (
        f"User '{user_info['username']}' logged out successfully"
        if user_info["username"]
        else "Logged out successfully"
    )
    return {"message": message, "user": user_info}

# Handle preflight for logout
@router.options("/logout")
async def options_logout():
    return {"message": "OK"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user

# Handle preflight for me
@router.options("/me")
async def options_me():
    return {"message": "OK"}