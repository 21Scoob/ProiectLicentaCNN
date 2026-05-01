from fastapi import FastAPI, Depends, HTTPException, status, Request, APIRouter, File, UploadFile
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import bcrypt
from pydantic import BaseModel, EmailStr
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
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

load_dotenv()

SECRET_KEY = os.getenv('SECRETKEYFORAPI')
assert SECRET_KEY is not None, "The api key is not in .env"
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
assert STRIPE_SECRET_KEY is not None, "The api stripe key is not in .env"
SQLALCHEMY_DATABASE_URL = os.getenv('DATABASELOC')
stripe.api_key = STRIPE_SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 

app = FastAPI(title="Deepfake API")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

admin = Admin(app, engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    credits = Column(Integer, default=10) 
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

   
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

class ProcessedPayment(Base):
    __tablename__ = "processed_payments"
    id = Column(Integer, primary_key=True, index=True)
    stripe_session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Sources(Base):
    __tablename__ = "user_sources"
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username, User.role, User.credits]
    can_edit = True
    can_delete = True
    can_create = True
    can_export = True

class ScanAdmin(ModelView, model=Scan):
    column_list = [Scan.id, Scan.user_id, Scan.filename, Scan.prediction, Scan.confidence, Scan.created_at]
    can_delete = True

class TransactionAdmin(ModelView, model=Transaction):
    column_list = [Transaction.id, Transaction.user_id, Transaction.amount, Transaction.transaction_type, Transaction.created_at]

class FeedbackAdmin(ModelView, model=UserFeedback):
    column_list = [UserFeedback.id, UserFeedback.user_id, UserFeedback.scan_id, UserFeedback.is_correct, UserFeedback.created_at]

class ModelMetadataAdmin(ModelView, model=ModelMetadata):
    column_list = [ModelMetadata.id, ModelMetadata.name, ModelMetadata.version, ModelMetadata.is_active]

admin.add_view(UserAdmin)
admin.add_view(ScanAdmin)
admin.add_view(TransactionAdmin)
admin.add_view(FeedbackAdmin)
admin.add_view(ModelMetadataAdmin)

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

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing Token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid Token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user   
        
@app.post("/create-checkout-session/")
@limiter.limit("5/minute")
async def create_checkout_session(request:Request, amount: int, price_eur: float, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
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
            customer_email=current_user.email,
            metadata={"amount": amount, "user_email": current_user.email}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/verify-payment/")
@limiter.limit("5/minute")
async def verify_payment(request:Request, session_id: str, amount: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        already_processed = db.query(ProcessedPayment).filter(ProcessedPayment.stripe_session_id == session_id).first()
        if already_processed:
            return {"status": "already_processed", "new_credits": current_user.credits}
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':            
            current_user.credits += amount
            db.add(Transaction(user_id=current_user.id, amount=amount, transaction_type="PURCHASE", description=f"Stripe: {amount} credite"))
            db.add(ProcessedPayment(stripe_session_id=session_id))
            db.commit()
            return {"status": "success", "new_credits": current_user.credits}
        return {"status": "failed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/")
@limiter.limit("10/minute")
async def predict_image(request:Request, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.credits <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    start_time = datetime.utcnow()
    current_user.credits -= 1
    db.add(Transaction(user_id=current_user.id, amount=-1, transaction_type="SCAN", description=f"Scan: {file.filename}"))
    model_meta = db.query(ModelMetadata).filter(ModelMetadata.is_active == True).first()
    prediction_val = 87.5 
    end_time = datetime.utcnow()
    proc_time = int((end_time - start_time).total_seconds() * 1000)
    
    new_scan = Scan(
        user_id=current_user.id,
        model_id=model_meta.id if model_meta else None,
        filename=file.filename,
        file_path=f"simulated_uploads/{file.filename}",
        prediction="Deepfake" if prediction_val > 50 else "Real",
        confidence=prediction_val,
        processing_time_ms=proc_time
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    
    return {
        "prediction": prediction_val,
        "new_credits": current_user.credits,
        "scan_id": new_scan.id
    }

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        if db.query(ModelMetadata).count() == 0:
            db.add(ModelMetadata(name="ResNet50 + ViT Ensemble", version="1.0.0", is_active=True))
            db.commit()
    finally:
        db.close()

class UserRegister(BaseModel):
    email: EmailStr 
    password: str
    username: str

@app.post("/register/")
@limiter.limit("5/minute")
async def register_user(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    email_clean = user_data.email.strip().lower()
    username_clean = user_data.username.strip()
    password = user_data.password

    if db.query(User).filter((User.email == email_clean) | (User.username == username_clean)).first():
        raise HTTPException(status_code=400, detail="Email or Username already taken")    
    new_user = User(
        email=email_clean, username=username_clean,
        hashed_password=hash_password(password),
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
async def validate_token(request:Request, current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email, 
        "username": current_user.username, 
        "credits": current_user.credits,
    }

@app.get("/credits/")
@limiter.limit("5/minute")
async def get_credits(request:Request, db: Session = Depends(get_db)):
    return

class FeedbackSchema(BaseModel):
    scan_id: Optional[int] = None
    is_correct: bool
    comment: Optional[str] = None

@app.post("/feedback/")
@limiter.limit("5/minute")
async def submit_feedback(request:Request, feedback: FeedbackSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    if feedback.scan_id:
        scan = db.query(Scan).filter(Scan.id == feedback.scan_id, Scan.user_id == current_user.id).first()
        if not scan:
            raise HTTPException(status_code=403, detail="Not authorized to provide feedback for this scan")

    new_feedback = UserFeedback(
        user_id=current_user.id,
        scan_id=feedback.scan_id,
        is_correct=feedback.is_correct,
        comment=feedback.comment
    )
    db.add(new_feedback)
    db.commit()
    return {"status": "success", "message": "Saved Feedback"}
