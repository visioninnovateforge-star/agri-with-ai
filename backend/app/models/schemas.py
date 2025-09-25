"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    FARMER = "farmer"
    AGRONOMIST = "agronomist"
    RESEARCHER = "researcher"

class AlertType(str, Enum):
    IRRIGATION = "irrigation"
    PEST = "pest"
    WEATHER = "weather"
    DISEASE = "disease"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Authentication models
class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

# Farmer models
class FarmerProfile(BaseModel):
    location: str = Field(..., min_length=2, max_length=200)
    crops: str  # JSON string of crops list
    acres: float = Field(..., gt=0)
    contact_number: Optional[str] = None
    soil_data: Optional[Dict[str, Any]] = None
    water_level: Optional[float] = None

class FarmerUpdate(BaseModel):
    location: Optional[str] = None
    crops: Optional[str] = None
    acres: Optional[float] = None
    contact_number: Optional[str] = None
    soil_data: Optional[Dict[str, Any]] = None
    water_level: Optional[float] = None

class FieldData(BaseModel):
    crop: str = Field(..., min_length=2, max_length=50)
    soil_ph: float = Field(..., ge=0, le=14)
    soil_moisture: float = Field(..., ge=0, le=100)
    soil_nitrogen: float = Field(..., ge=0)
    soil_phosphorus: float = Field(..., ge=0)
    soil_potassium: float = Field(..., ge=0)
    temperature: float = Field(..., ge=-50, le=60)
    humidity: float = Field(..., ge=0, le=100)
    rainfall: float = Field(..., ge=0)
    acres: float = Field(..., gt=0)

# ML Model input/output models
class YieldPredictionInput(BaseModel):
    crop: str
    soil_ph: float = Field(..., ge=0, le=14)
    soil_moisture: float = Field(..., ge=0, le=100)
    soil_nitrogen: float
    soil_phosphorus: float
    soil_potassium: float
    temperature: float
    humidity: float
    rainfall: float
    acres: float

class YieldPredictionOutput(BaseModel):
    crop: str
    predicted_yield: float
    confidence: float
    recommendations: List[str]
    created_at: datetime

class CropHealthInput(BaseModel):
    crop: str
    ndvi_index: float = Field(..., ge=-1, le=1)
    temperature: float
    humidity: float
    soil_moisture: float

class CropHealthOutput(BaseModel):
    crop: str
    health_status: str  # excellent, good, moderate, poor, critical
    stress_indicators: List[str]
    recommendations: List[str]
    confidence: float

# Prediction models
class PredictionResponse(BaseModel):
    id: int
    crop: str
    prediction: float
    confidence: float
    validated_by_agronomist: bool
    agronomist_comments: Optional[str]
    created_at: datetime

class PredictionValidation(BaseModel):
    prediction_id: int
    is_valid: bool
    comments: str
    corrected_value: Optional[float] = None

# Alert models
class AlertCreate(BaseModel):
    farmer_id: int
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)
    recommendations: Optional[List[str]] = None

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    recommendations: Optional[List[str]]
    is_read: bool
    is_resolved: bool
    created_at: datetime

# Research models
class ResearchDataCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    region: Optional[str] = None
    crop_type: Optional[str] = None
    season: Optional[str] = None
    aggregated_results: Optional[Dict[str, Any]] = None
    ndvi_scores: Optional[Dict[str, Any]] = None
    yield_predictions: Optional[Dict[str, Any]] = None

class ResearchDataResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    region: Optional[str]
    crop_type: Optional[str]
    season: Optional[str]
    created_at: datetime

class AggregatedInsights(BaseModel):
    total_farmers: int
    total_predictions: int
    average_yield: float
    top_performing_crops: List[Dict[str, Any]]
    regional_performance: Dict[str, Any]
    seasonal_trends: Dict[str, Any]
    alert_statistics: Dict[str, Any]

# Generic response models
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None