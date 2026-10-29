from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from typing import List, Optional

#set database
SQLALCHEMY_DATABASE_URL = "sqlite:///./hazards.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MessageRecord(Base):
    tablename = "messages"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(String, nullable=False)
    location = Column(String, nullable=True, index=True)  
    hazard = Column(String, nullable=True, index=True)    
    created_at = Column(DateTime, default=datetime)

#database table
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# ۲. مدل‌های اعتبارسنجی داده (Pydantic)
# ==========================================
class MessageCreate(BaseModel):
    text: str = Field(..., min_length=3, example="در خیابان ولیعصر تهران آتش‌سوزی بزرگی رخ داده است.")

class MessageResponse(BaseModel):
    id: int
    raw_text: str
    location: Optional[str] = None
    hazard: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True  # سازگار با Pydantic v2 (در نسخه‌های قدیمی‌تر: orm_mode = True)

# ==========================================
# ۳. مدل پردازش متن (استخراج مکان و خطر)
# ==========================================
def extract_hazard_and_location(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    در این بخش مدل هوش مصنوعی یا NLP شما قرار می‌گیرد.
    فعلاً از یک منطق نمونه مبتنی بر کلمات کلیدی استفاده شده است.
    """
    known_locations = ["تهران", "اصفهان", "شیراز", "تبریز", "مشهد", "اهواز", "کرج", "خیابان ولیعصر", "اتوبان همت"]
    known_hazards = ["آتش‌سوزی", "سیل", "زلزله", "تصادف", "انفجار", "ریزش آوار", "نشت گاز"]

    detected_location = None
    detected_hazard = None

    for loc in known_locations:
        if loc in text:
            detected_location = loc
            break

    for haz in known_hazards:
        if haz in text:
            detected_hazard = haz
            break

    return detected_location, detected_hazard

# ==========================================
# ۴. تعریف برنامه و دکوراتورها (FastAPI Routes)
# ==========================================
app = FastAPI(
    title="سیستم پایش و استخراج حوادث و مکان‌ها",
    description="دریافت پیام، پردازش با مدل و ذخیره‌سازی تفکیک‌شده در دیتابیس"
)

# ۱. دکوراتور دریافت پیام، پردازش با مدل و ذخیره در دیتابیس
@app.post("/messages/", response_model=MessageResponse, status_code=201, tags=["Messages"])
def create_and_process_message(payload: MessageCreate, db: Session = Depends(get_db)):
    # الف) اجرای مدل روی متن پیام برای استخراج موقعیت و خطر
    extracted_location, extracted_hazard = extract_hazard_and_location(payload.text)

    # ب) ساخت رکورد دیتابیس با فیلدهای مجزا
    db_message = MessageRecord(
        raw_text=payload.text,
        location=extracted_location,
        hazard=extracted_hazard
    )
    
    # ج) ذخیره در دیتابیس
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

# ۲. دکوراتور نمایش تمامی پیام‌ها
@app.get("/messages/", response_model=List[MessageResponse], tags=["Messages"])
def get_all_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    messages = db.query(MessageRecord).offset(skip).limit(limit).all()
    return messages# ۳. دکوراتور فیلتر کردن پیام‌ها بر اساس نوع حادثه (خطر)
@app.get("/messages/by-hazard/", response_model=List[MessageResponse], tags=["Filters"])
def get_messages_by_hazard(
    hazard_type: Optional[str] = Query(None, description="نوع حادثه را وارد کنید (مثلاً: سیل، زلزله). اگر خالی بگذارید، تمام پیام‌های دارای حادثه نمایش داده می‌شوند."),
    db: Session = Depends(get_db)
):
    query = db.query(MessageRecord).filter(MessageRecord.hazard.isnot(None))
    
    # اگر کاربر نوع خاصی از حادثه را مشخص کرده باشد
    if hazard_type:
        query = query.filter(MessageRecord.hazard.contains(hazard_type))
        
    return query.all()

# ۴. دکوراتور نمایش پیام‌هایی که مکان از آن‌ها استخراج شده است
@app.get("/messages/with-location/", response_model=List[MessageResponse], tags=["Filters"])
def get_messages_with_extracted_location(db: Session = Depends(get_db)):
    messages = db.query(MessageRecord).filter(
        MessageRecord.location.isnot(None),
        MessageRecord.location != ""
    ).all()
    return messages