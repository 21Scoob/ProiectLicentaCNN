from fastapi import FastAPI, Depends, HTTPException, status, Request, APIRouter, File, UploadFile
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean, func, update, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
import bcrypt
import html
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Optional, List
from collections import Counter
from dotenv import load_dotenv
import os
import stripe
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

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
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

CREDIT_PACKAGES = {
    10:  500,
    50:  2000,
    100: 3500,
}

app = FastAPI(title="Deepfake API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if username == os.getenv("ADMIN_USER", "admin") and password == os.getenv("ADMIN_PASS"):
            request.session["admin_auth"] = True
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.pop("admin_auth", None)
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_auth", False)

admin = Admin(app, engine, authentication_backend=AdminAuth(secret_key=SECRET_KEY))

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
async def create_checkout_session(request:Request, amount: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if amount not in CREDIT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid credit package")
    unit_amount = CREDIT_PACKAGES[amount]
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': f'{amount} Credits Deepfake Detection'},
                    'unit_amount': unit_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{FRONTEND_URL}/Credits?success=true&session_id={{CHECKOUT_SESSION_ID}}&amount={amount}",
            cancel_url=f"{FRONTEND_URL}/Credits?canceled=true",
            customer_email=current_user.email,
            metadata={"amount": str(amount), "user_email": current_user.email}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/verify-payment/")
@limiter.limit("5/minute")
async def verify_payment(request:Request, session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        already_processed = db.query(ProcessedPayment).filter(ProcessedPayment.stripe_session_id == session_id).first()
        if already_processed:
            return {"status": "already_processed", "new_credits": current_user.credits}
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            actual_amount = int(session.metadata.get("amount", 0))
            if actual_amount not in CREDIT_PACKAGES:
                raise HTTPException(status_code=400, detail="Invalid payment amount")
            current_user.credits += actual_amount
            db.add(Transaction(user_id=current_user.id, amount=actual_amount, transaction_type="PURCHASE", description=f"Stripe: {actual_amount} credite"))
            db.add(ProcessedPayment(stripe_session_id=session_id))
            db.commit()
            return {"status": "success", "new_credits": current_user.credits}
        return {"status": "failed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/")
@limiter.limit("10/minute")
async def predict_image(request:Request, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # File validation
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG images accepted")
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum 10MB")
    
    # Race-safe credit deduction
    result = db.execute(
        update(User).where(User.id == current_user.id, User.credits > 0)
        .values(credits=User.credits - 1)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    db.add(Transaction(user_id=current_user.id, amount=-1, transaction_type="SCAN", description=f"Scan: {file.filename}"))
    
    start_time = datetime.now(timezone.utc)
    model_meta = db.query(ModelMetadata).filter(ModelMetadata.is_active == True).first()
    prediction_val = 87.5
    end_time = datetime.now(timezone.utc)
    proc_time = int((end_time - start_time).total_seconds() * 1000)
    
    db.refresh(current_user)
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

    
    from sqlalchemy import inspect as sa_inspect
    insp = sa_inspect(engine)
    existing_cols = [c["name"] for c in insp.get_columns("users")]
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
    password: str = Field(min_length=6, max_length=128)
    username: str = Field(min_length=2, max_length=50)

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
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)

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
    comment: Optional[str] = Field(default=None, max_length=1000)

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
    display_name: str = Field(min_length=1, max_length=100)


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
    sources = db.query(ImageSource).options(
        joinedload(ImageSource.scan)
    ).filter(ImageSource.user_id == current_user.id).all()

    stats = {}
    for src in sources:
        key = src.source_name
        if key not in stats:
            stats[key] = {"display_name": src.display_name, "total": 0, "real": 0}
        if src.scan:
            stats[key]["total"] += 1
            if src.scan.prediction == "Real":
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
async def get_scans(request: Request, skip: int = 0, limit: int = 50, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scans = db.query(Scan).options(
        joinedload(Scan.source),
        joinedload(Scan.feedback),
        joinedload(Scan.note)
    ).filter(Scan.user_id == current_user.id).order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
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
    uid = current_user.id
    total_scans = db.query(func.count(Scan.id)).filter(Scan.user_id == uid).scalar() or 0
    deepfake_count = db.query(func.count(Scan.id)).filter(Scan.user_id == uid, Scan.prediction == "Deepfake").scalar() or 0
    real_count = total_scans - deepfake_count
    avg_confidence = round(db.query(func.avg(Scan.confidence)).filter(Scan.user_id == uid).scalar() or 0, 1)
    avg_processing_time = round(db.query(func.avg(Scan.processing_time_ms)).filter(Scan.user_id == uid).scalar() or 0)

    total_credits_spent = abs(db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == uid, Transaction.amount < 0
    ).scalar())

    feedback_total = db.query(func.count(UserFeedback.id)).filter(UserFeedback.user_id == uid).scalar() or 0
    feedback_correct = db.query(func.count(UserFeedback.id)).filter(UserFeedback.user_id == uid, UserFeedback.is_correct == True).scalar() or 0
    accuracy_from_feedback = round(feedback_correct / feedback_total * 100, 1) if feedback_total > 0 else None

    # Scans per day — still needs raw rows for grouping
    scans = db.query(Scan.created_at).filter(Scan.user_id == uid).all()
    daily = Counter()
    for s in scans:
        daily[s.created_at.strftime("%Y-%m-%d")] += 1

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
@limiter.limit("10/minute")
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
    username: Optional[str] = Field(default=None, max_length=50)
    name: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=200)
    company_name: Optional[str] = Field(default=None, max_length=100)
    threshold: Optional[float] = None


@app.put("/profile/")
@limiter.limit("10/minute")
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
    old_password: str = Field(max_length=128)
    new_password: str = Field(min_length=6, max_length=128)

import resend

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
assert RESEND_API_KEY is not None, "api key for emailing system nonexistent"
resend.api_key = RESEND_API_KEY

def send_reset_email(to_email: str, token: str):
    if not RESEND_API_KEY:
        print("RESEND_API_KEY missing, skipping email sending. Token:", token)
        return
        
    reset_link = f"{FRONTEND_URL}/Reset_Password?token={token}"
    html_body = f"<p>Click on this link to reset your password: <a href='{reset_link}'>{reset_link}</a></p><p>If you did not request this, please ignore this email.</p>"
    
    try:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": to_email,
            "subject": "Password Reset Request",
            "html": html_body
        })
        print(f"Sent reset email to {to_email}. Resend response: {r}")
    except Exception as e:
        print(f"Failed to send email: {e}")

class ForgotPassword(BaseModel):
    email: EmailStr

@app.post("/forgot-password/")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: ForgotPassword, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if user:
        to_encode = {"sub": user.email, "type": "reset"}
        expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        send_reset_email(user.email, token)
        
    return {"status": "success", "message": "If email exists, link was sent."}

class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)

@app.post("/reset-password/")
@limiter.limit("3/minute")
async def reset_password(request: Request, data: ResetPassword, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "reset":
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
        
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"status": "success", "message": "Password reset"}
