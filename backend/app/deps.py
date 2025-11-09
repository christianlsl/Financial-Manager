from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session

from .core.config import settings
from .core.security import create_access_token
from .db import get_db
from .models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(response: Response, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        subject: str | None = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except ExpiredSignatureError:
        # Provide a clearer message when token is expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == subject).first()
    if user is None:
        raise credentials_exception
    # Sliding refresh: if token remaining lifetime below threshold, issue new token
    exp_ts = payload.get("exp")
    if isinstance(exp_ts, (int, float)):
        now = datetime.now(timezone.utc).timestamp()
        remaining = exp_ts - now
        threshold_seconds = settings.REFRESH_THRESHOLD_DELTA.total_seconds()
        if remaining < threshold_seconds:
            new_token = create_access_token(subject=user.email)
            # Return new token via header; client should replace its stored token
            response.headers["X-New-Token"] = new_token
    return user
