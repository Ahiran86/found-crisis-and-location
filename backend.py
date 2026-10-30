from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from typing import List, Optional

# database
SQLALCHEMY_DATABASE_URL = "sqlite:///./hazards.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(String, nullable=False)
    location = Column(String, nullable=True, index=True)  
    hazard = Column(String, nullable=True, index=True)    
    created_at = Column(DateTime, default=datetime)



Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# validation
class MessageCreate(BaseModel):
    text: str = Field(..., min_length=3, example="از سقف حموم الغدیر آب میاد")

class MessageResponse(BaseModel):
    id: int
    raw_text: str
    location: Optional[str] = None
    hazard: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True 




# app
app = FastAPI(
    title="سیستم پایش و استخراج حوادث و مکان‌ها",
    description="دریافت پیام، پردازش با مدل و ذخیره‌سازی تفکیک‌شده در دیتابیس"
)


@app.post("/messages/", response_model=MessageResponse, status_code=201, tags=["Messages"])
def create_and_process_message(payload: MessageCreate, db: Session = Depends(get_db)):

# model should deply here


# insert in to database deply here with db_message variable name


    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

# show all message decorator
@app.get("/messages/", response_model=List[MessageResponse], tags=["Messages"])
def get_all_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    messages = db.query(MessageRecord).offset(skip).limit(limit).all()
    return messages

# filter message by crisis decorator
@app.get("/messages/by-hazard/", response_model=List[MessageResponse], tags=["Filters"])
def get_messages_by_hazard(
    hazard_type: Optional[str] = Query(None, description="نوع حادثه را وارد کنید (مثلاً: سیل، زلزله). اگر خالی بگذارید، تمام پیام‌های دارای حادثه نمایش داده می‌شوند."),
    db: Session = Depends(get_db)
):
    query = db.query(MessageRecord).filter(MessageRecord.hazard.isnot(None))
    
    
    if hazard_type:
        query = query.filter(MessageRecord.hazard.contains(hazard_type))
        
    return query.all()

# Show messages whose location has been identified by the decorator.
@app.get("/messages/with-location/", response_model=List[MessageResponse], tags=["Filters"])
def get_messages_with_extracted_location(db: Session = Depends(get_db)):
    messages = db.query(MessageRecord).filter(
        MessageRecord.location.isnot(None),
        MessageRecord.location != ""
    ).all()
    return messages