from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.advisor import Advisor
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    from app.models.client import Client

    payload = decode_access_token(credentials.credentials)
    if not payload or payload.get("role") not in ("advisor", "client"):
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    model = Advisor if payload["role"] == "advisor" else Client
    user = db.get(model, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user


def get_current_advisor(user=Depends(get_current_user)) -> Advisor:
    if not isinstance(user, Advisor):
        raise HTTPException(status_code=403, detail="Advisor access required")
    return user


def get_current_client(user=Depends(get_current_user)):
    from app.models.client import Client
    if not isinstance(user, Client):
        raise HTTPException(status_code=403, detail="Client access required")
    return user


def visible_clients(db, user):
    from app.models.client import Client
    query = db.query(Client)
    if isinstance(user, Advisor):
        return query.filter(Client.advisor_id == user.id)
    return query.filter(Client.id == user.id)


def require_client_access(db, user, client_id):
    client = visible_clients(db, user).filter_by(id=client_id).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def authenticate_advisor(email: str, password: str, db: Session) -> Optional[Advisor]:
    """Authenticate an advisor by email and password."""
    advisor = db.query(Advisor).filter(Advisor.email == email).first()
    if not advisor:
        return None
    if not verify_password(password, advisor.hashed_password):
        return None
    return advisor
