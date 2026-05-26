import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityManager:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_session_token(self, user_id: str, expires_delta: timedelta = None) -> str:
        """Generate session token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode = {"user_id": user_id, "exp": expire}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            return user_id
        except jwt.PyJWTError:
            return None
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate OTP"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

security = SecurityManager()
