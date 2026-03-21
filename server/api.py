from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import bcrypt
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

# Configurație JWT
SECRET_KEY = "super-secret-key-pentru-licenta" # Schimbă-l cu ceva complex în producție
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 zile

SQLALCHEMY_DATABASE_URL = "sqlite:///./licenta.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELE DATABASE ---

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    price = Column(Float, default=0.0)
    monthly_credits = Column(Integer, default=5)
    users = relationship("User", back_populates="plan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    credits = Column(Integer, default=10) 
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("SubscriptionPlan", back_populates="users")
    scans = relationship("Scan", back_populates="owner")
    tokens = relationship("AuthToken", back_populates="owner")
    wallet_history = relationship("Transaction", back_populates="owner")
    feedbacks = relationship("UserFeedback", back_populates="owner")

class ModelMetadata(Base):
    __tablename__ = "model_metadata"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    version = Column(String)
    is_active = Column(Boolean, default=True)
    scans = relationship("Scan", back_populates="model")
    
class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_id = Column(Integer, ForeignKey("model_metadata.id"), nullable=True)
    filename = Column(String)
    file_path = Column(String) 
    prediction = Column(String)  
    confidence = Column(Float)   
    processing_time_ms = Column(Integer, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="scans")
    model = relationship("ModelMetadata", back_populates="scans")
    feedback = relationship("UserFeedback", back_populates="scan", uselist=False)
    
class AuthToken(Base):
    __tablename__ = "auth_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token_string = Column(String, unique=True, index=True)
    token_type = Column(String) 
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    owner = relationship("User", back_populates="tokens")   

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    transaction_type = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="wallet_history")

class UserFeedback(Base):
    __tablename__ = "user_feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_correct = Column(Boolean)
    user_label = Column(String)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    scan = relationship("Scan", back_populates="feedback")
    owner = relationship("User", back_populates="feedbacks")

Base.metadata.create_all(bind=engine)

# --- UTILS ---

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- API ---

app = FastAPI(title="Deepfake API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        if db.query(SubscriptionPlan).count() == 0:
            db.add_all([
                SubscriptionPlan(name="Free", price=0.0, monthly_credits=5),
                SubscriptionPlan(name="Pro", price=29.99, monthly_credits=100),
                SubscriptionPlan(name="Gold", price=99.99, monthly_credits=1000)
            ])
            db.commit()
        if db.query(ModelMetadata).count() == 0:
            db.add(ModelMetadata(name="ResNet50 + ViT Ensemble", version="1.0.0", is_active=True))
            db.commit()
    finally:
        db.close()

# --- ENDPOINTS ---

@app.post("/register/")
def register_user(email: str, password: str, username: str, db: Session = Depends(get_db)):
    email_clean = email.strip().lower()
    username_clean = username.strip()
    
    if db.query(User).filter((User.email == email_clean) | (User.username == username_clean)).first():
        raise HTTPException(status_code=400, detail="Email sau Username deja folosit.")
    
    free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Free").first()
    new_user = User(
        email=email_clean, username=username_clean,
        hashed_password=hash_password(password),
        plan_id=free_plan.id if free_plan else None,
        credits=10
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    db.add(Transaction(user_id=new_user.id, amount=10, transaction_type="BONUS", description="Bun venit"))
    db.commit()
    
    token = create_access_token(data={"sub": new_user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"email": new_user.email, "username": new_user.username, "credits": new_user.credits}}

class UserCredentials(BaseModel):
    email: str
    password: str

@app.post("/login/")
def login_user(credentials: UserCredentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email.strip().lower()).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Date incorecte")
    
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "user": {"email": user.email, "username": user.username, "credits": user.credits}}

@app.get("/validate-token/")
def validate_token(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalid")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalid")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilizator inexistent")
    
    return {"email": user.email, "username": user.username, "credits": user.credits}

@app.get("/plans/")
def get_plans(db: Session = Depends(get_db)):
    return db.query(SubscriptionPlan).all()

@app.post("/add-credits/")
def add_credits(email: str, amount: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user: raise HTTPException(status_code=404, detail="User negăsit")
    user.credits += amount
    db.add(Transaction(user_id=user.id, amount=amount, transaction_type="PURCHASE", description=f"Plus {amount}"))
    db.commit()
    return {"new_credits": user.credits}

@app.post("/upgrade-plan/")
def upgrade_plan(email: str, plan_name: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan_name).first()
    if not user or not plan: raise HTTPException(status_code=404, detail="Eroare")
    user.plan_id = plan.id
    user.credits += plan.monthly_credits
    db.commit()
    return {"new_credits": user.credits}

class FeedbackSchema(BaseModel):
    scan_id: Optional[int] = None
    email: str
    is_correct: bool
    comment: Optional[str] = None

@app.post("/feedback/")
def submit_feedback(feedback: FeedbackSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == feedback.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User negăsit")
    
    new_feedback = UserFeedback(
        user_id=user.id,
        scan_id=feedback.scan_id,
        is_correct=feedback.is_correct,
        comment=feedback.comment
    )
    db.add(new_feedback)
    db.commit()
    return {"status": "success", "message": "Feedback salvat"}
