import os
from datetime import datetime, timedelta
from pydantic import BaseModel

from dotenv import load_dotenv
from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext

load_dotenv()

ALGORITHM = "HS256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or ""

class Token(BaseModel):
    access_type: str
    token_type: str

class TokenData(BaseModel):
    username: str


pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expiry_time: timedelta | None = None):
    to_encode = data.copy()
    if expiry_time:
        expire = datetime.utcnow() + expiry_time
    else:
        expire = datetime.utcnow() + timedelta(seconds=30)

    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    credentials_exception = HTTPException(
        status_code = 401,
        detail = "Could not validate credentials",
        headers = {"WWW-Authenticate": "Bearer"}
    )

    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if username is None:
        raise credentials_exception

    token_data = TokenData(username=username)
    return token_data

def hash_password(plain: str):
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

