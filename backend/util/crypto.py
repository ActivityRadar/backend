import os
from datetime import datetime, timedelta

from beanie import PydanticObjectId
from dotenv import load_dotenv
from fastapi import Form, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

load_dotenv()

ALGORITHM = "HS256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or ""
SESSION_TOKEN_EXPIRE = timedelta(minutes=20)
PASSWORD_RESET_TOKEN_EXPIRE = timedelta(hours=2)


class Token(BaseModel):
    access_type: str
    token_type: str


class TokenData(BaseModel):
    id: PydanticObjectId


class RepeatPasswordForm(BaseModel):
    new_password: str = Form()
    new_password_repeated: str = Form()


class ResetPasswordForm(RepeatPasswordForm):
    ...


class ChangePasswordForm(RepeatPasswordForm):
    old_password: str = Form()


pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(data: dict, expiry_time: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expiry_time

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


def decode_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    id = payload.get("sub")
    if id is None:
        raise credentials_exception

    token_data = TokenData(id=PydanticObjectId(id))
    return token_data


def create_access_token(data: dict, expiry_time: timedelta | None = None):
    expiry_time = expiry_time or SESSION_TOKEN_EXPIRE
    token, _ = create_token(data, expiry_time)
    return token


def decode_session_token(token: str):
    return decode_token(token)


def create_password_reset_token(data: dict, expiry_time: timedelta | None = None):
    expiry_time = expiry_time or PASSWORD_RESET_TOKEN_EXPIRE
    token, expiry = create_token(data, expiry_time)
    return token, expiry


def decode_password_reset_token(token: str):
    return decode_token(token)


def hash_password(plain: str):
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)
