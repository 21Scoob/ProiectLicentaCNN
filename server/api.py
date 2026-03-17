from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import bcrypt
from pydantic import BaseModel
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./licenta.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    role = Column(String, default="user")
    credits = Column(Integer, default=5) 
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("Scan", back_populates="owner")
    tokens = relationship("AuthToken", back_populates="owner")
    
class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    filename = Column(String)
    file_path = Column(String) 
    
    prediction = Column(String)  
    confidence = Column(Float)   
    processing_time_ms = Column(Integer, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="scans")
    
class AuthToken(Base):
    __tablename__ = "auth_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    token_string = Column(String, unique=True, index=True)
    token_type = Column(String) 
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    
    owner = relationship("User", back_populates="tokens")   

Base.metadata.create_all(bind=engine)

Base.metadata.create_all(bind=engine)

def hash_password(password: str) -> str:
    
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

app = FastAPI(title="Deepfake API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register/")
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    
    email_clean = email.strip().lower()
     
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Acest email este deja înregistrat.")
    
    new_user = User(email=email_clean, hashed_password=hash_password(password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user) 
    return {"message": "Cont creat cu succes!", "user_email": new_user.email}

class UserCredentials(BaseModel):
    email: str
    password: str

@app.post("/login/")
def login_user(credentials: UserCredentials, db: Session = Depends(get_db)):
    
    email_clean = credentials.email.strip().lower()
    db_user = db.query(User).filter(User.email == email_clean).first()
    
    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Email sau parolă incorectă.")
    
    return {
        "message": "Logare reușită!", 
        "user_email": db_user.email
    }
    
    1
