import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exc = HTTPException(
        status_code=401, detail="Не авторизован", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        if not email:
            raise credentials_exc
    except jwt.PyJWTError:
        raise credentials_exc
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not user.is_active:
        raise credentials_exc
    return user


def require_roles(*roles: models.Role):
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(
                status_code=403, detail="Недостаточно прав для операции"
            )
        return user

    return checker
