

from typing import Annotated, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pymongo import ReturnDocument
from pymongo.database import Database as MongoDB

from src.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.api.utils.auth import decode_token, hash_password, verify_password
from src.api.utils.jwt import create_access_token
from src.mongo import get_mongo_db


router = APIRouter(prefix="/auth", tags=["auth"])


def get_db() -> MongoDB:
    return get_mongo_db()


def get_authorization_token(authorization: Annotated[Optional[str], Header()] = None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return authorization.split(" ", 1)[1]


def get_current_user(token: Annotated[str, Depends(get_authorization_token)], db: Annotated[MongoDB, Depends(get_db)]):
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.get_collection("users").find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


def require_admin(user: Annotated[dict, Depends(get_current_user)]):
    if user.get("role") != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Annotated[MongoDB, Depends(get_db)]):
    users = db.get_collection("users")
    if users.find_one({"email": data.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user_doc = {
        "_id": data.email.lower(),
        "email": data.email.lower(),
        "full_name": data.full_name,
        "role": data.role,
        "password_hash": hash_password(data.password),
        "is_active": True,
    }
    users.insert_one(user_doc)
    return user_doc

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 60

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Annotated[MongoDB, Depends(get_db)]):
    users = db.get_collection("users")
    user = users.find_one({"email": data.email.lower()})
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    bolivia_offset = timedelta(hours=-4)
    if user:
        lockout_until = user.get("lockout_until")
        if lockout_until and lockout_until.tzinfo is None:
            lockout_until = lockout_until.replace(tzinfo=timezone.utc)
        if lockout_until and lockout_until > now:
            bolivia_time = (lockout_until + bolivia_offset).strftime('%Y-%m-%d %H:%M:%S Bolivia')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked. Try again after {bolivia_time}"
            )
        if not verify_password(data.password, user.get("password_hash", "")):
            attempts = user.get("failed_attempts", 0) + 1
            update = {"$set": {"failed_attempts": attempts}}
            if attempts >= MAX_LOGIN_ATTEMPTS:
                lockout_time = now + timedelta(minutes=LOCKOUT_MINUTES)
                update["$set"]["lockout_until"] = lockout_time
            users.update_one({"_id": user["_id"]}, update)
            if attempts >= MAX_LOGIN_ATTEMPTS:
                bolivia_time = (lockout_time + bolivia_offset).strftime('%Y-%m-%d %H:%M:%S Bolivia')
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Account locked due to too many failed attempts. Try again after {bolivia_time}"
                )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        users.update_one({"_id": user["_id"]}, {"$set": {"failed_attempts": 0, "lockout_until": None}})
        token = create_access_token({"sub": user["_id"], "role": user.get("role", "User")}, expires_delta=60 * 24)
        return TokenResponse(access_token=token)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[dict, Depends(get_current_user)]):
    return user


@router.patch("/users/{email}/deactivate", response_model=UserResponse)
def deactivate_user(email: str, _: Annotated[dict, Depends(require_admin)], db: Annotated[MongoDB, Depends(get_db)]):
    users = db.get_collection("users")
    res = users.find_one_and_update({"_id": email.lower()}, {"$set": {"is_active": False}}, return_document=ReturnDocument.AFTER)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return res


@router.patch("/users/{email}/activate", response_model=UserResponse)
def activate_user(email: str, _: Annotated[dict, Depends(require_admin)], db: Annotated[MongoDB, Depends(get_db)]):
    users = db.get_collection("users")
    res = users.find_one_and_update({"_id": email.lower()}, {"$set": {"is_active": True}}, return_document=ReturnDocument.AFTER)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return res


@router.delete("/users/{email}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(email: str, _: Annotated[dict, Depends(require_admin)], db: Annotated[MongoDB, Depends(get_db)]):
    users = db.get_collection("users")
    res = users.delete_one({"_id": email.lower()})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None