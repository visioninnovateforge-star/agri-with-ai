"""
Farmer-specific routes for field data management and predictions
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import json
from datetime import datetime

from ..models.schemas import (
    FarmerProfile, FarmerUpdate, FieldData, PredictionResponse, 
    AlertResponse, SuccessResponse
)
from ..models.database import get_supabase_client
from .auth import get_current_user

router = APIRouter()

def require_farmer_role(current_user: dict = Depends(get_current_user)):
    """Ensure current user is a farmer"""
    if current_user["role"] != "farmer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only farmers can access this endpoint"
        )
    return current_user

@router.get("/profile")
async def get_farmer_profile(current_user: dict = Depends(require_farmer_role)):
    """Get farmer profile information"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("farmers").select("*").eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer profile not found"
            )
        
        farmer_data = result.data[0]
        return {
            "id": farmer_data["id"],
            "location": farmer_data["location"],
            "crops": farmer_data["crops"],
            "acres": farmer_data["acres"],
            "contact_number": farmer_data.get("contact_number"),
            "soil_data": farmer_data.get("soil_data", {}),
            "water_level": farmer_data.get("water_level"),
            "created_at": farmer_data["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch farmer profile: {str(e)}"
        )

@router.put("/profile")
async def update_farmer_profile(
    profile_update: FarmerUpdate,
    current_user: dict = Depends(require_farmer_role)
):
    """Update farmer profile information"""
    try:
        supabase = get_supabase_client()
        
        # Prepare update data (only include non-None values)
        update_data = {}
        if profile_update.location is not None:
            update_data["location"] = profile_update.location
        if profile_update.crops is not None:
            update_data["crops"] = profile_update.crops
        if profile_update.acres is not None:
            update_data["acres"] = profile_update.acres
        if profile_update.contact_number is not None:
            update_data["contact_number"] = profile_update.contact_number
        if profile_update.soil_data is not None:
            update_data["soil_data"] = profile_update.soil_data
        if profile_update.water_level is not None:
            update_data["water_level"] = profile_update.water_level
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided for update"
            )
        
        result = supabase.table("farmers").update(update_data).eq("user_id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer profile not found"
            )
        
        return SuccessResponse(
            message="Profile updated successfully",
            data=result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/field-data")
async def add_field_data(
    field_data: FieldData,
    current_user: dict = Depends(require_farmer_role)
):
    """Add field data and trigger ML prediction"""
    try:
        supabase = get_supabase_client()
        
        # Get farmer ID
        farmer_result = supabase.table("farmers").select("id").eq("user_id", current_user["id"]).execute()
        
        if not farmer_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer profile not found"
            )
        
        farmer_id = farmer_result.data[0]["id"]
        
        # Store the field data as input for ML prediction
        input_data = {
            "crop": field_data.crop,
            "soil_ph": field_data.soil_ph,
            "soil_moisture": field_data.soil_moisture,
            "soil_nitrogen": field_data.soil_nitrogen,
            "soil_phosphorus": field_data.soil_phosphorus,
            "soil_potassium": field_data.soil_potassium,
            "temperature": field_data.temperature,
            "humidity": field_data.humidity,
            "rainfall": field_data.rainfall,
            "acres": field_data.acres
        }
        
        # For now, create a mock prediction (replace with actual ML model call)
        # In production, this would call the ML model endpoint
        mock_prediction = {
            "prediction": 75.5,  # Mock yield prediction
            "confidence": 0.85
        }
        
        # Store prediction in database
        prediction_data = {
            "farmer_id": farmer_id,
            "crop": field_data.crop,
            "prediction": mock_prediction["prediction"],
            "confidence": mock_prediction["confidence"],
            "input_data": input_data,
            "model_version": "1.0"
        }
        
        result = supabase.table("predictions").insert(prediction_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store prediction"
            )
        
        # Generate alerts based on field data
        alerts = []
        
        # Low soil moisture alert
        if field_data.soil_moisture < 30:
            alert_data = {
                "farmer_id": farmer_id,
                "alert_type": "irrigation",
                "severity": "high" if field_data.soil_moisture < 20 else "medium",
                "title": "Low Soil Moisture Detected",
                "message": f"Soil moisture is at {field_data.soil_moisture}%. Consider irrigation.",
                "recommendations": ["Increase irrigation frequency", "Check irrigation system", "Monitor soil moisture daily"]
            }
            supabase.table("alerts").insert(alert_data).execute()
            alerts.append("Low soil moisture alert generated")
        
        # Nutrient deficiency alerts
        if field_data.soil_nitrogen < 50:
            alert_data = {
                "farmer_id": farmer_id,
                "alert_type": "disease",
                "severity": "medium",
                "title": "Low Nitrogen Levels",
                "message": f"Soil nitrogen is at {field_data.soil_nitrogen} ppm. Consider fertilization.",
                "recommendations": ["Apply nitrogen fertilizer", "Consider organic compost", "Test soil again in 2 weeks"]
            }
            supabase.table("alerts").insert(alert_data).execute()
            alerts.append("Low nitrogen alert generated")
        
        return SuccessResponse(
            message="Field data added and prediction generated successfully",
            data={
                "prediction": result.data[0],
                "alerts_generated": alerts
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add field data: {str(e)}"
        )

@router.get("/predictions", response_model=List[PredictionResponse])
async def get_my_predictions(current_user: dict = Depends(require_farmer_role)):
    """Get all predictions for the current farmer"""
    try:
        supabase = get_supabase_client()
        
        # Get farmer ID
        farmer_result = supabase.table("farmers").select("id").eq("user_id", current_user["id"]).execute()
        
        if not farmer_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer profile not found"
            )
        
        farmer_id = farmer_result.data[0]["id"]
        
        # Get predictions
        result = supabase.table("predictions").select("*").eq("farmer_id", farmer_id).order("created_at", desc=True).execute()
        
        predictions = []
        for pred in result.data:
            predictions.append(PredictionResponse(
                id=pred["id"],
                crop=pred["crop"],
                prediction=pred["prediction"],
                confidence=pred["confidence"],
                validated_by_agronomist=pred["validated_by_agronomist"],
                agronomist_comments=pred.get("agronomist_comments"),
                created_at=pred["created_at"]
            ))
        
        return predictions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch predictions: {str(e)}"
        )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_my_alerts(current_user: dict = Depends(require_farmer_role)):
    """Get all alerts for the current farmer"""
    try:
        supabase = get_supabase_client()
        
        # Get farmer ID
        farmer_result = supabase.table("farmers").select("id").eq("user_id", current_user["id"]).execute()
        
        if not farmer_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer profile not found"
            )
        
        farmer_id = farmer_result.data[0]["id"]
        
        # Get alerts
        result = supabase.table("alerts").select("*").eq("farmer_id", farmer_id).order("created_at", desc=True).execute()
        
        alerts = []
        for alert in result.data:
            alerts.append(AlertResponse(
                id=alert["id"],
                alert_type=alert["alert_type"],
                severity=alert["severity"],
                title=alert["title"],
                message=alert["message"],
                recommendations=alert.get("recommendations", []),
                is_read=alert["is_read"],
                is_resolved=alert["is_resolved"],
                created_at=alert["created_at"]
            ))
        
        return alerts
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {str(e)}"
        )

@router.put("/alerts/{alert_id}/read")
async def mark_alert_as_read(
    alert_id: int,
    current_user: dict = Depends(require_farmer_role)
):
    """Mark an alert as read"""
    try:
        supabase = get_supabase_client()
        
        # Get farmer ID
        farmer_result = supabase.table("farmers").select("id").eq("user_id", current_user["id"]).execute()
        farmer_id = farmer_result.data[0]["id"]
        
        # Update alert
        result = supabase.table("alerts").update(
            {"is_read": True}
        ).eq("id", alert_id).eq("farmer_id", farmer_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return SuccessResponse(message="Alert marked as read")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark alert as read: {str(e)}"
        )