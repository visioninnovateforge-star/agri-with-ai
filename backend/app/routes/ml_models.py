"""
Machine Learning model endpoints for predictions and analysis
"""
from fastapi import APIRouter, HTTPException, Depends, status
import numpy as np
import pickle
import os
from typing import List, Dict, Any
from datetime import datetime

from ..models.schemas import (
    YieldPredictionInput, YieldPredictionOutput, CropHealthInput, 
    CropHealthOutput, AlertCreate, SuccessResponse
)
from .auth import get_current_user

router = APIRouter()

# Global variable to access ML models (loaded in main.py)
def get_ml_models():
    """Get ML models from global cache"""
    from main import ml_models_cache
    return ml_models_cache

@router.post("/predict-yield", response_model=YieldPredictionOutput)
async def predict_yield(
    input_data: YieldPredictionInput,
    current_user: dict = Depends(get_current_user)
):
    """Predict crop yield based on soil and weather conditions"""
    try:
        models = get_ml_models()
        
        # Prepare features for the model
        features = np.array([
            input_data.soil_ph,
            input_data.soil_moisture,
            input_data.soil_nitrogen,
            input_data.soil_phosphorus,
            input_data.soil_potassium,
            input_data.temperature,
            input_data.humidity,
            input_data.rainfall,
            input_data.acres
        ]).reshape(1, -1)
        
        # Use ML model if available, otherwise use rule-based prediction
        if "yield_model" in models:
            try:
                prediction = models["yield_model"].predict(features)[0]
                confidence = 0.85  # This would come from model's confidence score
            except Exception as e:
                print(f"ML model prediction failed: {e}")
                prediction, confidence = rule_based_yield_prediction(input_data)
        else:
            prediction, confidence = rule_based_yield_prediction(input_data)
        
        # Generate recommendations based on prediction and input data
        recommendations = generate_yield_recommendations(input_data, prediction)
        
        return YieldPredictionOutput(
            crop=input_data.crop,
            predicted_yield=round(prediction, 2),
            confidence=round(confidence, 3),
            recommendations=recommendations,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yield prediction failed: {str(e)}"
        )

@router.post("/crop-health", response_model=CropHealthOutput)
async def analyze_crop_health(
    input_data: CropHealthInput,
    current_user: dict = Depends(get_current_user)
):
    """Analyze crop health based on NDVI and environmental conditions"""
    try:
        models = get_ml_models()
        
        # Prepare features for the model
        features = np.array([
            input_data.ndvi_index,
            input_data.temperature,
            input_data.humidity,
            input_data.soil_moisture
        ]).reshape(1, -1)
        
        # Use ML model if available, otherwise use rule-based analysis
        if "crop_health_model" in models:
            try:
                health_score = models["crop_health_model"].predict(features)[0]
                confidence = 0.80
            except Exception as e:
                print(f"ML model health analysis failed: {e}")
                health_score, confidence = rule_based_health_analysis(input_data)
        else:
            health_score, confidence = rule_based_health_analysis(input_data)
        
        # Convert health score to status
        if health_score >= 0.8:
            health_status = "excellent"
        elif health_score >= 0.65:
            health_status = "good"
        elif health_score >= 0.5:
            health_status = "moderate"
        elif health_score >= 0.3:
            health_status = "poor"
        else:
            health_status = "critical"
        
        # Generate stress indicators and recommendations
        stress_indicators = generate_stress_indicators(input_data)
        recommendations = generate_health_recommendations(input_data, health_status, stress_indicators)
        
        return CropHealthOutput(
            crop=input_data.crop,
            health_status=health_status,
            stress_indicators=stress_indicators,
            recommendations=recommendations,
            confidence=round(confidence, 3)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crop health analysis failed: {str(e)}"
        )

@router.get("/alerts")
async def generate_alerts(
    farmer_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Generate smart alerts based on current conditions and predictions"""
    try:
        # This would typically fetch recent sensor data and make predictions
        # For now, we'll simulate based on common agricultural scenarios
        
        alerts = []
        current_time = datetime.utcnow()
        
        # Mock environmental data (in production, this would come from sensors/APIs)
        mock_conditions = {
            "temperature": 35.5,  # High temperature
            "humidity": 45,       # Low humidity
            "soil_moisture": 25,  # Low soil moisture
            "rainfall_forecast": 0,  # No rain expected
            "wind_speed": 20      # High wind
        }
        
        # Temperature-based alerts
        if mock_conditions["temperature"] > 35:
            alerts.append({
                "type": "weather",
                "severity": "high",
                "title": "Heat Stress Warning",
                "message": f"Temperature is {mock_conditions['temperature']}°C. Crops may experience heat stress.",
                "recommendations": [
                    "Increase irrigation frequency",
                    "Consider shade netting for sensitive crops",
                    "Monitor crops for wilting signs",
                    "Harvest early morning if possible"
                ],
                "priority": 1
            })
        
        # Irrigation alerts
        if mock_conditions["soil_moisture"] < 30:
            severity = "critical" if mock_conditions["soil_moisture"] < 20 else "high"
            alerts.append({
                "type": "irrigation",
                "severity": severity,
                "title": "Low Soil Moisture Alert",
                "message": f"Soil moisture is at {mock_conditions['soil_moisture']}%. Immediate irrigation recommended.",
                "recommendations": [
                    "Start irrigation immediately",
                    "Check irrigation system for blockages",
                    "Monitor soil moisture levels hourly",
                    "Consider drip irrigation for efficiency"
                ],
                "priority": 1 if severity == "critical" else 2
            })
        
        # Pest/disease risk alerts
        if mock_conditions["humidity"] > 80 and mock_conditions["temperature"] > 25:
            alerts.append({
                "type": "pest",
                "severity": "medium",
                "title": "Fungal Disease Risk",
                "message": "High humidity and temperature create favorable conditions for fungal diseases.",
                "recommendations": [
                    "Apply preventive fungicide spray",
                    "Improve air circulation around plants",
                    "Reduce irrigation frequency temporarily",
                    "Monitor leaves for early disease signs"
                ],
                "priority": 3
            })
        
        # Weather-based alerts
        if mock_conditions["wind_speed"] > 15:
            alerts.append({
                "type": "weather",
                "severity": "medium",
                "title": "High Wind Advisory",
                "message": f"Wind speed is {mock_conditions['wind_speed']} km/h. Protect vulnerable crops.",
                "recommendations": [
                    "Install windbreaks for young plants",
                    "Secure support stakes and ties",
                    "Postpone pesticide applications",
                    "Check for physical crop damage after wind subsides"
                ],
                "priority": 3
            })
        
        # Nutrient alerts (mock based on common deficiency patterns)
        alerts.append({
            "type": "disease",
            "severity": "low",
            "title": "Seasonal Nutrient Check",
            "message": "Consider soil testing for optimal nutrient management.",
            "recommendations": [
                "Schedule soil nutrient analysis",
                "Monitor crop color for nutrient deficiency signs",
                "Plan fertilization schedule",
                "Consider organic amendments"
            ],
            "priority": 4
        })
        
        # Sort alerts by priority
        alerts.sort(key=lambda x: x["priority"])
        
        return {
            "farmer_id": farmer_id,
            "generated_at": current_time,
            "conditions": mock_conditions,
            "alerts": alerts,
            "total_alerts": len(alerts),
            "high_priority_alerts": len([a for a in alerts if a["severity"] in ["critical", "high"]])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert generation failed: {str(e)}"
        )

@router.get("/model-info")
async def get_model_info(current_user: dict = Depends(get_current_user)):
    """Get information about loaded ML models"""
    try:
        models = get_ml_models()
        
        model_info = {
            "loaded_models": list(models.keys()),
            "model_details": {}
        }
        
        for model_name, model in models.items():
            try:
                model_info["model_details"][model_name] = {
                    "type": type(model).__name__,
                    "loaded": True,
                    "features": getattr(model, 'n_features_in_', 'Unknown')
                }
            except Exception as e:
                model_info["model_details"][model_name] = {
                    "type": "Unknown",
                    "loaded": True,
                    "error": str(e)
                }
        
        return model_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )

# Helper functions for rule-based predictions (fallback when ML models aren't available)

def rule_based_yield_prediction(input_data: YieldPredictionInput) -> tuple:
    """Rule-based yield prediction as fallback"""
    base_yield = 50.0  # Base yield per acre
    
    # Soil factor
    soil_factor = 1.0
    if 6.0 <= input_data.soil_ph <= 7.5:
        soil_factor += 0.1
    elif input_data.soil_ph < 5.5 or input_data.soil_ph > 8.0:
        soil_factor -= 0.2
    
    # Moisture factor
    if 60 <= input_data.soil_moisture <= 80:
        soil_factor += 0.15
    elif input_data.soil_moisture < 40:
        soil_factor -= 0.3
    
    # Temperature factor
    temp_factor = 1.0
    if 20 <= input_data.temperature <= 30:
        temp_factor += 0.1
    elif input_data.temperature > 35 or input_data.temperature < 10:
        temp_factor -= 0.2
    
    # Rainfall factor
    rainfall_factor = 1.0
    if 500 <= input_data.rainfall <= 1000:
        rainfall_factor += 0.1
    elif input_data.rainfall < 300:
        rainfall_factor -= 0.2
    
    # Nutrient factors
    nutrient_factor = 1.0
    if input_data.soil_nitrogen > 50:
        nutrient_factor += 0.05
    if input_data.soil_phosphorus > 20:
        nutrient_factor += 0.05
    if input_data.soil_potassium > 150:
        nutrient_factor += 0.05
    
    prediction = base_yield * soil_factor * temp_factor * rainfall_factor * nutrient_factor * input_data.acres
    confidence = 0.7  # Moderate confidence for rule-based prediction
    
    return prediction, confidence

def rule_based_health_analysis(input_data: CropHealthInput) -> tuple:
    """Rule-based crop health analysis as fallback"""
    health_score = 0.5  # Base health score
    
    # NDVI factor (most important for crop health)
    if input_data.ndvi_index > 0.6:
        health_score += 0.3
    elif input_data.ndvi_index > 0.4:
        health_score += 0.1
    elif input_data.ndvi_index < 0.2:
        health_score -= 0.3
    
    # Temperature stress
    if 20 <= input_data.temperature <= 30:
        health_score += 0.1
    elif input_data.temperature > 35 or input_data.temperature < 5:
        health_score -= 0.2
    
    # Humidity factor
    if 50 <= input_data.humidity <= 70:
        health_score += 0.05
    elif input_data.humidity < 30 or input_data.humidity > 90:
        health_score -= 0.1
    
    # Soil moisture
    if 50 <= input_data.soil_moisture <= 80:
        health_score += 0.1
    elif input_data.soil_moisture < 30:
        health_score -= 0.2
    
    health_score = max(0, min(1, health_score))  # Clamp between 0 and 1
    confidence = 0.75
    
    return health_score, confidence

def generate_yield_recommendations(input_data: YieldPredictionInput, prediction: float) -> List[str]:
    """Generate recommendations based on yield prediction and input conditions"""
    recommendations = []
    
    if input_data.soil_ph < 6.0:
        recommendations.append("Consider liming to increase soil pH for better nutrient uptake")
    elif input_data.soil_ph > 8.0:
        recommendations.append("Consider adding organic matter to lower soil pH")
    
    if input_data.soil_moisture < 40:
        recommendations.append("Increase irrigation frequency to maintain optimal soil moisture")
    
    if input_data.soil_nitrogen < 50:
        recommendations.append("Apply nitrogen fertilizer to boost crop growth")
    
    if input_data.soil_phosphorus < 20:
        recommendations.append("Consider phosphorus supplementation for root development")
    
    if input_data.temperature > 30:
        recommendations.append("Monitor for heat stress and consider shade protection")
    
    if prediction < 40:
        recommendations.append("Current conditions may limit yield. Consider soil amendments and improved irrigation")
    elif prediction > 80:
        recommendations.append("Excellent growing conditions. Maintain current management practices")
    
    return recommendations

def generate_stress_indicators(input_data: CropHealthInput) -> List[str]:
    """Generate stress indicators based on crop health input"""
    indicators = []
    
    if input_data.ndvi_index < 0.4:
        indicators.append("Low vegetation vigor detected")
    
    if input_data.temperature > 35:
        indicators.append("Heat stress risk")
    elif input_data.temperature < 10:
        indicators.append("Cold stress risk")
    
    if input_data.humidity < 30:
        indicators.append("Low humidity stress")
    elif input_data.humidity > 85:
        indicators.append("High humidity disease risk")
    
    if input_data.soil_moisture < 30:
        indicators.append("Water stress")
    elif input_data.soil_moisture > 90:
        indicators.append("Waterlogging risk")
    
    return indicators

def generate_health_recommendations(input_data: CropHealthInput, health_status: str, stress_indicators: List[str]) -> List[str]:
    """Generate health recommendations based on crop condition"""
    recommendations = []
    
    if health_status in ["poor", "critical"]:
        recommendations.append("Immediate intervention required - consult agricultural expert")
        recommendations.append("Conduct thorough field inspection")
    
    if "Heat stress risk" in stress_indicators:
        recommendations.append("Increase irrigation frequency and consider shade protection")
    
    if "Water stress" in stress_indicators:
        recommendations.append("Implement immediate irrigation schedule")
    
    if "Low vegetation vigor detected" in stress_indicators:
        recommendations.append("Check for nutrient deficiencies and pest issues")
        recommendations.append("Consider soil testing and fertilization")
    
    if "High humidity disease risk" in stress_indicators:
        recommendations.append("Improve air circulation and consider fungicide application")
    
    if health_status == "excellent":
        recommendations.append("Maintain current management practices")
        recommendations.append("Continue regular monitoring")
    
    return recommendations