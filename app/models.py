from __future__ import annotations
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, Integer, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ENGINE = create_engine("sqlite:///./local.db", echo=False, future=True)
SessionLocal = sessionmaker(ENGINE, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    role: Mapped[str] = mapped_column(String)  # user|assistant
    content: Mapped[str] = mapped_column(Text)

class DayNutritionArtifact(Base):
    __tablename__ = "day_nutrition"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    payload_json: Mapped[str] = mapped_column(Text)  # DayNutrition JSON

class RawMealInput(Base):
    __tablename__ = "raw_meal_inputs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    date: Mapped[str] = mapped_column(String, index=True)  # YYYY-MM-DD format
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    raw_text: Mapped[str] = mapped_column(Text)  # User's free-form meal description
    processed: Mapped[bool] = mapped_column(default=False)  # Whether it's been included in daily summary
    edit_count: Mapped[int] = mapped_column(Integer, default=0)  # Track number of edits

class DailyNutritionSummary(Base):
    __tablename__ = "daily_nutrition_summaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    date: Mapped[str] = mapped_column(String, index=True)  # YYYY-MM-DD format
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    payload_json: Mapped[str] = mapped_column(Text)  # DayNutrition JSON
    raw_input_ids: Mapped[str] = mapped_column(Text)  # JSON array of RawMealInput IDs used
    edit_count: Mapped[int] = mapped_column(Integer, default=0)  # Total edits for this day

def init_db() -> None:
    Base.metadata.create_all(ENGINE)
