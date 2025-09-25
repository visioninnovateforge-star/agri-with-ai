"""
Agronomist-specific routes for validation and farmer management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
import json
from datetime import datetime

from ..models.schemas import (
    PredictionResponse, PredictionValidation, SuccessResponse
)
from ..models.database import get_supabase_client
from .auth import get_current_user

router = APIRouter()

def require_agronomist_role(current_user: dict = Depends(get_current_user)):
    """Ensure current user is an agronomist"""
    if current_user["role"] != "agronomist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agronomists can access this endpoint"
        )
    return current_user

@router.get("/farmers")
async def get_all_farmers(current_user: dict = Depends(require_agronomist_role)):
    """Get all farmers with their basic information"""
    try:
        supabase = get_supabase_client()
        
        # Get all farmers with user information
        result = supabase.table("farmers").select(
            "*, users(id, name, email, created_at)"
        ).execute()
        
        farmers = []
        for farmer in result.data:
            farmers.append({
                "id": farmer["id"],
                "user_id": farmer["user_id"],
                "name": farmer["users"]["name"],
                "email": farmer["users"]["email"],
                "location": farmer["location"],
                "crops": farmer["crops"],
                "acres": farmer["acres"],
                "contact_number": farmer.get("contact_number"),
                "created_at": farmer["created_at"]
            })
        
        return {"farmers": farmers, "total_count": len(farmers)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch farmers: {str(e)}"
        )

@router.get("/farmers/{farmer_id}")
async def get_farmer_details(
    farmer_id: int,
    current_user: dict = Depends(require_agronomist_role)
):
    """Get detailed information about a specific farmer"""
    try:
        supabase = get_supabase_client()
        
        # Get farmer with user information
        farmer_result = supabase.table("farmers").select(
            "*, users(id, name, email, created_at)"
        ).eq("id", farmer_id).execute()
        
        if not farmer_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer not found"
            )
        
        farmer = farmer_result.data[0]
        
        # Get farmer's predictions
        predictions_result = supabase.table("predictions").select("*").eq(
            "farmer_id", farmer_id
        ).order("created_at", desc=True).execute()
        
        # Get farmer's alerts
        alerts_result = supabase.table("alerts").select("*").eq(
            "farmer_id", farmer_id
        ).order("created_at", desc=True).execute()
        
        return {
            "farmer": {
                "id": farmer["id"],
                "user_id": farmer["user_id"],
                "name": farmer["users"]["name"],
                "email": farmer["users"]["email"],
                "location": farmer["location"],
                "crops": farmer["crops"],
                "acres": farmer["acres"],
                "contact_number": farmer.get("contact_number"),
                "soil_data": farmer.get("soil_data", {}),
                "water_level": farmer.get("water_level"),
                "created_at": farmer["created_at"]
            },
            "predictions": predictions_result.data,
            "alerts": alerts_result.data,
            "statistics": {
                "total_predictions": len(predictions_result.data),
                "validated_predictions": len([p for p in predictions_result.data if p["validated_by_agronomist"]]),
                "active_alerts": len([a for a in alerts_result.data if not a["is_resolved"]])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch farmer details: {str(e)}"
        )

@router.get("/predictions/pending")
async def get_pending_predictions(
    limit: Optional[int] = 50,
    current_user: dict = Depends(require_agronomist_role)
):
    """Get all predictions that need validation"""
    try:
        supabase = get_supabase_client()
        
        # Get unvalidated predictions with farmer information
        result = supabase.table("predictions").select(
            "*, farmers(id, location, crops, users(name, email))"
        ).eq("validated_by_agronomist", False).order(
            "created_at", desc=True
        ).limit(limit).execute()
        
        predictions = []
        for pred in result.data:
            predictions.append({
                "id": pred["id"],
                "crop": pred["crop"],
                "prediction": pred["prediction"],
                "confidence": pred["confidence"],
                "created_at": pred["created_at"],
                "farmer": {
                    "id": pred["farmers"]["id"],
                    "name": pred["farmers"]["users"]["name"],
                    "email": pred["farmers"]["users"]["email"],
                    "location": pred["farmers"]["location"],
                    "crops": pred["farmers"]["crops"]
                },
                "input_data": pred.get("input_data", {})
            })
        
        return {"predictions": predictions, "total_count": len(predictions)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending predictions: {str(e)}"
        )

@router.post("/predictions/validate")
async def validate_prediction(
    validation: PredictionValidation,
    current_user: dict = Depends(require_agronomist_role)
):
    """Validate or correct a prediction"""
    try:
        supabase = get_supabase_client()
        
        # Prepare update data
        update_data = {
            "validated_by_agronomist": True,
            "agronomist_comments": validation.comments
        }
        
        # If prediction is corrected, update the prediction value
        if not validation.is_valid and validation.corrected_value is not None:
            update_data["prediction"] = validation.corrected_value
            update_data["agronomist_comments"] += f" (Original: {validation.corrected_value}, Corrected by agronomist)"
        
        # Update prediction
        result = supabase.table("predictions").update(update_data).eq(
            "id", validation.prediction_id
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found"
            )
        
        return SuccessResponse(
            message="Prediction validated successfully",
            data={
                "prediction_id": validation.prediction_id,
                "is_valid": validation.is_valid,
                "updated_prediction": result.data[0]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate prediction: {str(e)}"
        )

@router.get("/analytics/overview")
async def get_analytics_overview(current_user: dict = Depends(require_agronomist_role)):
    """Get analytics overview for agronomist dashboard"""
    try:
        supabase = get_supabase_client()
        
        # Get total farmers
        farmers_result = supabase.table("farmers").select("id", count="exact").execute()
        total_farmers = farmers_result.count or 0
        
        # Get total predictions
        predictions_result = supabase.table("predictions").select("id", count="exact").execute()
        total_predictions = predictions_result.count or 0
        
        # Get validated predictions
        validated_result = supabase.table("predictions").select("id", count="exact").eq(
            "validated_by_agronomist", True
        ).execute()
        validated_predictions = validated_result.count or 0
        
        # Get active alerts
        alerts_result = supabase.table("alerts").select("id", count="exact").eq(
            "is_resolved", False
        ).execute()
        active_alerts = alerts_result.count or 0
        
        # Get recent predictions for analysis
        recent_predictions = supabase.table("predictions").select(
            "crop, prediction, confidence, created_at"
        ).order("created_at", desc=True).limit(100).execute()
        
        # Calculate crop-wise statistics
        crop_stats = {}
        total_yield = 0
        for pred in recent_predictions.data:
            crop = pred["crop"]
            if crop not in crop_stats:
                crop_stats[crop] = {
                    "count": 0,
                    "total_yield": 0,
                    "avg_confidence": 0
                }
            crop_stats[crop]["count"] += 1
            crop_stats[crop]["total_yield"] += pred["prediction"]
            crop_stats[crop]["avg_confidence"] += pred["confidence"]
            total_yield += pred["prediction"]
        
        # Calculate averages
        for crop in crop_stats:
            crop_stats[crop]["avg_yield"] = crop_stats[crop]["total_yield"] / crop_stats[crop]["count"]
            crop_stats[crop]["avg_confidence"] = crop_stats[crop]["avg_confidence"] / crop_stats[crop]["count"]
        
        return {
            "summary": {
                "total_farmers": total_farmers,
                "total_predictions": total_predictions,
                "validated_predictions": validated_predictions,
                "pending_validations": total_predictions - validated_predictions,
                "active_alerts": active_alerts,
                "validation_rate": (validated_predictions / total_predictions * 100) if total_predictions > 0 else 0
            },
            "crop_statistics": crop_stats,
            "recent_activity": {
                "avg_yield_prediction": total_yield / len(recent_predictions.data) if recent_predictions.data else 0,
                "most_predicted_crop": max(crop_stats.keys(), key=lambda x: crop_stats[x]["count"]) if crop_stats else None
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analytics: {str(e)}"
        )

@router.get("/farmers/{farmer_id}/recommendations")
async def get_farmer_recommendations(
    farmer_id: int,
    current_user: dict = Depends(require_agronomist_role)
):
    """Generate recommendations for a specific farmer based on their data"""
    try:
        supabase = get_supabase_client()
        
        # Get farmer details
        farmer_result = supabase.table("farmers").select("*").eq("id", farmer_id).execute()
        
        if not farmer_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer not found"
            )
        
        farmer = farmer_result.data[0]
        
        # Get recent predictions and alerts
        predictions_result = supabase.table("predictions").select("*").eq(
            "farmer_id", farmer_id
        ).order("created_at", desc=True).limit(10).execute()
        
        alerts_result = supabase.table("alerts").select("*").eq(
            "farmer_id", farmer_id
        ).eq("is_resolved", False).execute()
        
        # Generate recommendations based on data
        recommendations = []
        
        # Soil-based recommendations
        soil_data = farmer.get("soil_data", {})
        if soil_data:
            if soil_data.get("ph", 7) < 6:
                recommendations.append({
                    "category": "Soil Management",
                    "priority": "High",
                    "recommendation": "Soil pH is acidic. Consider liming to improve nutrient availability.",
                    "estimated_impact": "15-20% yield improvement"
                })
            
            if soil_data.get("organic_matter", 0) < 3:
                recommendations.append({
                    "category": "Soil Health",
                    "priority": "Medium",
                    "recommendation": "Low organic matter detected. Incorporate compost or cover crops.",
                    "estimated_impact": "10-15% yield improvement"
                })
        
        # Prediction-based recommendations
        if predictions_result.data:
            avg_confidence = sum(p["confidence"] for p in predictions_result.data) / len(predictions_result.data)
            if avg_confidence < 0.7:
                recommendations.append({
                    "category": "Data Quality",
                    "priority": "Medium",
                    "recommendation": "Consider installing more sensors for better prediction accuracy.",
                    "estimated_impact": "Improved decision making"
                })
        
        # Alert-based recommendations
        irrigation_alerts = [a for a in alerts_result.data if a["alert_type"] == "irrigation"]
        if len(irrigation_alerts) > 2:
            recommendations.append({
                "category": "Water Management",
                "priority": "High",
                "recommendation": "Frequent irrigation alerts suggest upgrading to smart irrigation system.",
                "estimated_impact": "20-30% water savings"
            })
        
        return {
            "farmer_id": farmer_id,
            "recommendations": recommendations,
            "data_summary": {
                "recent_predictions": len(predictions_result.data),
                "active_alerts": len(alerts_result.data),
                "avg_prediction_confidence": sum(p["confidence"] for p in predictions_result.data) / len(predictions_result.data) if predictions_result.data else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )