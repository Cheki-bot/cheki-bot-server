import jwt
from datetime import datetime, timedelta
from src import ENV

def create_access_token(data: dict, expires_delta: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, ENV.jwt_secret.get_secret_value(), algorithm="HS256")
    return encoded_jwt