from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Cookie, Depends, Header, HTTPException
from pydantic import BaseModel


class User(BaseModel):
    email: str
    is_active: bool = True


def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    access_token: Annotated[Optional[str], Cookie()] = None,
) -> User:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    if token != "demo-valid-token":
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    user = User(email="demo@example.com")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
