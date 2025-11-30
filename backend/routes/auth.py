# auth/api_login.py
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel
from controllers.UserController import get_user_by_username_or_email, get_user_by_uid
from auth.security import verify_password
from auth.session import create_session, get_session, delete_session

router = APIRouter(prefix="/api/auth", tags=["Auth"])

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
    
    # ✅ RETURN session_id in response
    return {
        "message": "Logged in successfully",
        "session_id": session_id,  # ← ADD THIS
        "user": UserResponse(
            uid=user["uid"],
            username=user["username"],
            email=user["email"]
        )
    }

@router.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    
    user_info = {"uid": None, "username": None}  # default in case of anonymous/no session

    if session_id:
        session = get_session(session_id)  # retrieve session data
        if session:
            user = get_user_by_uid(session["user_id"])
            if user:
                user_info = {
                    "uid": user["uid"],
                    "username": user["username"]
                }
        # Delete the session regardless
        delete_session(session_id)

    # Always delete the cookie
    response.delete_cookie("session_id")

    return {
        "message": f"User '{user_info['username']}' logged out successfully" 
                   if user_info["username"] 
                   else "Logged out successfully",
        "user": user_info
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user