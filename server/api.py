from fastapi import FastAPI, Depends, HTTPException, status, Request, APIRouter
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import bcrypt
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from dotenv import load_dotenv
import os
import stripe
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqladmin import Admin, ModelView

load_dotenv("/Users/21scoob/Desktop/Code/ProiectLicentaCNN/.env")

SECRET_KEY = os.getenv('SECRETKEYFORAPI')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 

SQLALCHEMY_DATABASE_URL = "sqlite:///./licenta.db"
app = FastAPI(title="Deepfake API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

admin = Admin(app, engine)

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
    
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username, User.role, User.credits]
    can_edit = True
    can_delete = True
    can_create = True
    can_export = True
    
admin.add_view(UserAdmin)

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

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()     
        
@app.post("/create-checkout-session/")
@limiter.limit("5/minute")
async def create_checkout_session(request:Request, email: str, amount: int, price_eur: float, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': f'{amount} Credits Deepfake Detection'},
                    'unit_amount': int(price_eur * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"http://localhost:8501/Credits?success=true&session_id={{CHECKOUT_SESSION_ID}}&amount={amount}",
            cancel_url="http://localhost:8501/Credits?canceled=true",
            customer_email=email,
            metadata={"amount": amount, "user_email": email}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/verify-payment/")
@limiter.limit("5/minute")
async def verify_payment(request:Request, session_id: str, email: str, amount: int, db: Session = Depends(get_db)):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.credits += amount
                db.add(Transaction(user_id=user.id, amount=amount, transaction_type="PURCHASE", description=f"Stripe: {amount} credite"))
                db.commit()
                return {"status": "success", "new_credits": user.credits}
        return {"status": "failed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@app.post("/register/")
@limiter.limit("5/minute")
async def register_user(request:Request, email: str, password: str, username: str, db: Session = Depends(get_db)):
    email_clean = email.strip().lower()
    username_clean = username.strip()
    
    if db.query(User).filter((User.email == email_clean) | (User.username == username_clean)).first():
        raise HTTPException(status_code=400, detail="Email or Username already taken")
    
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
    
    db.add(Transaction(user_id=new_user.id, amount=10, transaction_type="BONUS", description="Welcome!"))
    db.commit()
    
    token = create_access_token(data={"sub": new_user.email})
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {
            "email": new_user.email, 
            "username": new_user.username, 
            "credits": new_user.credits,
            "plan": new_user.plan.name if new_user.plan else "Free"
        }
    }

class UserCredentials(BaseModel):
    email: str
    password: str

@app.post("/login/")
@limiter.limit("5/minute")
async def login_user(request:Request, credentials: UserCredentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email.strip().lower()).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect Data")
    
    token = create_access_token(data={"sub": user.email})
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {
            "email": user.email, 
            "username": user.username, 
            "credits": user.credits,
            "plan": user.plan.name if user.plan else "Free"
        }
    }

@app.get("/validate-token/")
@limiter.limit("5/minute")
async def validate_token(request:Request, token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalid")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalid")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Nonexistent User")
    
    return {
        "email": user.email, 
        "username": user.username, 
        "credits": user.credits,
        "plan": user.plan.name if user.plan else "Free"
    }

@app.get("/plans/")
@limiter.limit("5/minute")
async def get_plans(request:Request, db: Session = Depends(get_db)):
    return db.query(SubscriptionPlan).all()

@app.post("/add-credits/")
@limiter.limit("5/minute")
async def add_credits(request:Request, email: str, amount: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user: raise HTTPException(status_code=404, detail="Uknown User")
    user.credits += amount
    db.add(Transaction(user_id=user.id, amount=amount, transaction_type="PURCHASE", description=f"Plus {amount}"))
    db.commit()
    return {"new_credits": user.credits}

@app.post("/upgrade-plan/")
@limiter.limit("5/minute")
async def upgrade_plan(request:Request, email: str, plan_name: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan_name).first()
    if not user or not plan: raise HTTPException(status_code=404, detail="Error")
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
@limiter.limit("5/minute")
async def submit_feedback(request:Request, feedback: FeedbackSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == feedback.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Unknown User")
    
    new_feedback = UserFeedback(
        user_id=user.id,
        scan_id=feedback.scan_id,
        is_correct=feedback.is_correct,
        comment=feedback.comment
    )
    db.add(new_feedback)
    db.commit()
    return {"status": "success", "message": "Saved Feedback"}
