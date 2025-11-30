# auth/login.py
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from models.User import UserInDB
from controllers.UserController import get_user_by_username_or_email 
from auth.security import verify_password
from auth.session import create_session

# ✅ No prefix here — will be set in main.py
router = APIRouter(tags=["auth"])

@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = get_user_by_username_or_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
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
    
    return {"message": "Logged in successfully"}

@router.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        from auth.session import delete_session
        delete_session(session_id)
    response.delete_cookie("session_id")
    return {"message": "Logged out"}

# Dependency to get current user
async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    
    from controllers.UserController import get_user_by_uid
    user = get_user_by_uid(session["user_id"])
    return user

@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user