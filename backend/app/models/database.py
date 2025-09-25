"""
Database models and configuration for Agriculture Insights Platform
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
from supabase import create_client, Client

Base = declarative_base()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # farmer, agronomist, researcher
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    farmer_profile = relationship("Farmer", back_populates="user", uselist=False)

class Farmer(Base):
    __tablename__ = "farmers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    location = Column(String, nullable=False)
    crops = Column(Text)  # JSON string of crops
    acres = Column(Float, nullable=False)
    soil_data = Column(JSON)  # Store soil analysis data
    water_level = Column(Float)
    contact_number = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="farmer_profile")
    predictions = relationship("Prediction", back_populates="farmer")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    crop = Column(String, nullable=False)
    prediction = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    input_data = Column(JSON)  # Store the input data used for prediction
    model_version = Column(String, default="1.0")
    validated_by_agronomist = Column(Boolean, default=False)
    agronomist_comments = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    farmer = relationship("Farmer", back_populates="predictions")

class ResearchData(Base):
    __tablename__ = "research_data"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    aggregated_results = Column(JSON)
    ndvi_scores = Column(JSON)
    yield_predictions = Column(JSON)
    region = Column(String)
    crop_type = Column(String)
    season = Column(String)
    data_source = Column(String, default="system_generated")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    alert_type = Column(String, nullable=False)  # irrigation, pest, weather, disease
    severity = Column(String, nullable=False)  # low, medium, high, critical
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    recommendations = Column(JSON)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

# Database initialization
async def init_db():
    """Initialize database connection and create tables if needed"""
    try:
        # For now, we'll use Supabase's built-in table management
        # In production, you might want to use Alembic for migrations
        print("Database connection initialized with Supabase")
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False

def get_supabase_client():
    """Get Supabase client instance"""
    return supabase