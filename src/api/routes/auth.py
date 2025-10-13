from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src import ENV
from src.api.utils.jwt import create_access_token
from starlette.status import HTTP_401_UNAUTHORIZED

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    if data.email != ENV.admin_email or data.password != ENV.admin_password.get_secret_value():
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    token = create_access_token({"sub": data.email})
    return TokenResponse(access_token=token)