from fastapi import FastAPI, Depends, HTTPException, status, Request, APIRouter, File, UploadFile
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import bcrypt
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, List
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
    name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    threshold = Column(Float, default=50.0)

   
    scans = relationship("Scan", back_populates="owner")
    tokens = relationship("AuthToken", back_populates="owner")
    wallet_history = relationship("Transaction", back_populates="owner")
    feedbacks = relationship("UserFeedback", back_populates="owner")
    source = relationship("ImageSource", back_populates="owner")
    note = relationship("ScanNote", back_populates="owner")
    

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
    source = relationship("ImageSource", back_populates="scan", uselist=False)
    note = relationship("ScanNote", back_populates="scan", uselist=False)   

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
    
class ImageSource(Base):
    __tablename__ = "image_sources"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scan_id = Column(Integer, ForeignKey("scans.id"), unique=True)
    source_name = Column(String, index=True)
    display_name = Column(String, index=True)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="source")
    scan = relationship("Scan", back_populates="source")

class ScanNote(Base):
    __tablename__ = "scan_notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scan_id = Column(Integer, ForeignKey("scans.id"), unique=True)
    text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="note")
    scan = relationship("Scan", back_populates="note")

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

class ImageSourceAdmin(ModelView, model=ImageSource):
    column_list = [ImageSource.id, ImageSource.user_id, ImageSource.scan_id, ImageSource.source_name, ImageSource.created_at]
    can_delete = True

class ScanNoteAdmin(ModelView, model=ScanNote):
    column_list = [ScanNote.id, ScanNote.user_id, ScanNote.scan_id, ScanNote.created_at]
    can_delete = True

admin.add_view(UserAdmin)
admin.add_view(ScanAdmin)
admin.add_view(TransactionAdmin)
admin.add_view(FeedbackAdmin)
admin.add_view(ModelMetadataAdmin)
admin.add_view(ImageSourceAdmin)
admin.add_view(ScanNoteAdmin)

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
    
    user_threshold = current_user.threshold or 50.0
    label = "Real" if prediction_val >= user_threshold else "Deepfake"
    
    new_scan = Scan(
        user_id=current_user.id,
        model_id=model_meta.id if model_meta else None,
        filename=file.filename,
        file_path=f"simulated_uploads/{file.filename}",
        prediction=label,
        confidence=prediction_val,
        processing_time_ms=proc_time
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    
    return {
        "prediction": prediction_val,
        "label": label,
        "threshold": user_threshold,
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

    
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    existing_cols = [c["name"] for c in inspector.get_columns("users")]
    migrations = {
        "name": "ALTER TABLE users ADD COLUMN name VARCHAR",
        "address": "ALTER TABLE users ADD COLUMN address VARCHAR",
        "company_name": "ALTER TABLE users ADD COLUMN company_name VARCHAR",
        "threshold": "ALTER TABLE users ADD COLUMN threshold FLOAT DEFAULT 50.0",
    }
    with engine.begin() as conn:
        for col_name, sql in migrations.items():
            if col_name not in existing_cols:
                conn.execute(text(sql))
                print(f"  Migrated: added column '{col_name}' to users table")

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
            "credits": user.credits
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
async def get_credits(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).order_by(Transaction.created_at.desc()).limit(50).all()
    return {
        "credits": current_user.credits,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.transaction_type,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            } for t in transactions
        ]
    }

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

class SourceSchema(BaseModel):
    scan_id: int
    display_name: str


@app.post("/source/")
@limiter.limit("5/minute")
async def submit_source(request: Request, source: SourceSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == source.scan_id, Scan.user_id == current_user.id).first()
    if not scan:
        raise HTTPException(status_code=403, detail="Not authorized to provide source for this scan")

    existing = db.query(ImageSource).filter(ImageSource.scan_id == source.scan_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source already set for this scan")

    new_source = ImageSource(
        user_id=current_user.id,
        scan_id=source.scan_id,
        source_name=source.display_name.strip().lower(),
        display_name=source.display_name.strip()
    )
    db.add(new_source)
    db.commit()
    return {"status": "success", "message": "Source saved"}


@app.get("/source-stats/")
@limiter.limit("10/minute")
async def get_source_stats(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sources = db.query(ImageSource).filter(ImageSource.user_id == current_user.id).all()

    stats = {}
    for src in sources:
        key = src.source_name
        if key not in stats:
            stats[key] = {"display_name": src.display_name, "total": 0, "real": 0}

        scan = db.query(Scan).filter(Scan.id == src.scan_id).first()
        if scan:
            stats[key]["total"] += 1
            if scan.prediction == "Real":
                stats[key]["real"] += 1

    result = []
    for source_name, data in stats.items():
        veridicity = (data["real"] / data["total"] * 100) if data["total"] > 0 else 0
        result.append({
            "source_name": source_name,
            "display_name": data["display_name"],
            "total_scans": data["total"],
            "real_count": data["real"],
            "veridicity_percentage": round(veridicity, 1)
        })

    return result



@app.get("/scans/")
@limiter.limit("10/minute")
async def get_scans(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scans = db.query(Scan).filter(Scan.user_id == current_user.id).order_by(Scan.created_at.desc()).all()
    result = []
    for s in scans:
        source_info = None
        if s.source:
            source_info = {"display_name": s.source.display_name, "source_name": s.source.source_name}
        feedback_info = None
        if s.feedback:
            feedback_info = {"is_correct": s.feedback.is_correct, "comment": s.feedback.comment}
        note_info = None
        if s.note:
            note_info = s.note.text

        result.append({
            "id": s.id,
            "filename": s.filename,
            "prediction": s.prediction,
            "confidence": s.confidence,
            "processing_time_ms": s.processing_time_ms,
            "created_at": s.created_at.isoformat(),
            "source": source_info,
            "feedback": feedback_info,
            "note": note_info
        })
    return result



@app.get("/stats/")
@limiter.limit("10/minute")
async def get_stats(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scans = db.query(Scan).filter(Scan.user_id == current_user.id).all()
    total_scans = len(scans)
    deepfake_count = sum(1 for s in scans if s.prediction == "Deepfake")
    real_count = total_scans - deepfake_count
    avg_confidence = round(sum(s.confidence for s in scans) / total_scans, 1) if total_scans > 0 else 0
    avg_processing_time = round(sum((s.processing_time_ms or 0) for s in scans) / total_scans) if total_scans > 0 else 0

    
    spent = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.amount < 0
    ).all()
    total_credits_spent = abs(sum(t.amount for t in spent))

    
    feedbacks = db.query(UserFeedback).filter(UserFeedback.user_id == current_user.id).all()
    feedback_correct = sum(1 for f in feedbacks if f.is_correct)
    feedback_total = len(feedbacks)
    accuracy_from_feedback = round(feedback_correct / feedback_total * 100, 1) if feedback_total > 0 else None

    
    from collections import Counter
    daily = Counter()
    for s in scans:
        day_key = s.created_at.strftime("%Y-%m-%d")
        daily[day_key] += 1

    return {
        "total_scans": total_scans,
        "deepfake_count": deepfake_count,
        "real_count": real_count,
        "avg_confidence": avg_confidence,
        "avg_processing_time_ms": avg_processing_time,
        "total_credits_spent": total_credits_spent,
        "current_credits": current_user.credits,
        "feedback_total": feedback_total,
        "feedback_correct": feedback_correct,
        "accuracy_from_feedback": accuracy_from_feedback,
        "scans_per_day": dict(sorted(daily.items())),
        "member_since": current_user.created_at.isoformat()
    }



@app.get("/profile/")
@limiter.limit("5/minute")
async def get_profile(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scan_count = db.query(Scan).filter(Scan.user_id == current_user.id).count()
    return {
        "username": current_user.username,
        "email": current_user.email,
        "credits": current_user.credits,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "member_since": current_user.created_at.isoformat(),
        "total_scans": scan_count,
        "name": current_user.name,
        "address": current_user.address,
        "company_name": current_user.company_name,
        "threshold": current_user.threshold or 50.0
    }


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    company_name: Optional[str] = None
    threshold: Optional[float] = None


@app.put("/profile/")
@limiter.limit("5/minute")
async def update_profile(request: Request, data: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.username is not None:
        clean = data.username.strip()
        existing = db.query(User).filter(User.username == clean, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = clean
    if data.name is not None:
        current_user.name = data.name.strip()
    if data.address is not None:
        current_user.address = data.address.strip()
    if data.company_name is not None:
        current_user.company_name = data.company_name.strip()
    if data.threshold is not None:
        if not (0 <= data.threshold <= 100):
            raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")
        current_user.threshold = data.threshold
    db.commit()
    return {"status": "success", "message": "Profile updated"}


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


@app.put("/change-password/")
@limiter.limit("3/minute")
async def change_password(request: Request, data: ChangePassword, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"status": "success", "message": "Password changed"}
