"""
Researcher-specific routes for data analysis and export
"""
from fastapi import APIRouter, HTTPException, Depends, status, Response
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
import csv
import io
from datetime import datetime, timedelta

from ..models.schemas import (
    ResearchDataCreate, ResearchDataResponse, AggregatedInsights, SuccessResponse
)
from ..models.database import get_supabase_client
from .auth import get_current_user

router = APIRouter()

def require_researcher_role(current_user: dict = Depends(get_current_user)):
    """Ensure current user is a researcher"""
    if current_user["role"] != "researcher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only researchers can access this endpoint"
        )
    return current_user

@router.get("/aggregate-data", response_model=AggregatedInsights)
async def get_aggregated_data(
    region: Optional[str] = None,
    crop_type: Optional[str] = None,
    days_back: Optional[int] = 30,
    current_user: dict = Depends(require_researcher_role)
):
    """Get aggregated agricultural data for research purposes"""
    try:
        supabase = get_supabase_client()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get farmers data
        farmers_query = supabase.table("farmers").select("*")
        if region:
            farmers_query = farmers_query.ilike("location", f"%{region}%")
        farmers_result = farmers_query.execute()
        
        # Get predictions data
        predictions_query = supabase.table("predictions").select(
            "*, farmers(location, crops)"
        ).gte("created_at", start_date.isoformat())
        if crop_type:
            predictions_query = predictions_query.eq("crop", crop_type)
        predictions_result = predictions_query.execute()
        
        # Get alerts data
        alerts_result = supabase.table("alerts").select("*").gte(
            "created_at", start_date.isoformat()
        ).execute()
        
        # Process data for insights
        total_farmers = len(farmers_result.data)
        total_predictions = len(predictions_result.data)
        
        # Calculate average yield
        avg_yield = 0
        if predictions_result.data:
            avg_yield = sum(p["prediction"] for p in predictions_result.data) / len(predictions_result.data)
        
        # Top performing crops
        crop_performance = {}
        for pred in predictions_result.data:
            crop = pred["crop"]
            if crop not in crop_performance:
                crop_performance[crop] = {"total_yield": 0, "count": 0, "avg_confidence": 0}
            crop_performance[crop]["total_yield"] += pred["prediction"]
            crop_performance[crop]["count"] += 1
            crop_performance[crop]["avg_confidence"] += pred["confidence"]
        
        # Calculate averages and sort
        top_performing_crops = []
        for crop, data in crop_performance.items():
            avg_yield_crop = data["total_yield"] / data["count"]
            avg_confidence = data["avg_confidence"] / data["count"]
            top_performing_crops.append({
                "crop": crop,
                "avg_yield": avg_yield_crop,
                "avg_confidence": avg_confidence,
                "prediction_count": data["count"]
            })
        
        top_performing_crops.sort(key=lambda x: x["avg_yield"], reverse=True)
        top_performing_crops = top_performing_crops[:5]  # Top 5
        
        # Regional performance
        regional_performance = {}
        for pred in predictions_result.data:
            if pred["farmers"] and pred["farmers"]["location"]:
                location = pred["farmers"]["location"]
                if location not in regional_performance:
                    regional_performance[location] = {"total_yield": 0, "count": 0}
                regional_performance[location]["total_yield"] += pred["prediction"]
                regional_performance[location]["count"] += 1
        
        # Calculate regional averages
        for region_name, data in regional_performance.items():
            data["avg_yield"] = data["total_yield"] / data["count"]
        
        # Seasonal trends (mock data for demonstration)
        seasonal_trends = {
            "spring": {"avg_yield": avg_yield * 0.9, "prediction_count": total_predictions // 4},
            "summer": {"avg_yield": avg_yield * 1.1, "prediction_count": total_predictions // 3},
            "fall": {"avg_yield": avg_yield * 1.2, "prediction_count": total_predictions // 3},
            "winter": {"avg_yield": avg_yield * 0.8, "prediction_count": total_predictions // 6}
        }
        
        # Alert statistics
        alert_stats = {}
        for alert in alerts_result.data:
            alert_type = alert["alert_type"]
            severity = alert["severity"]
            
            if alert_type not in alert_stats:
                alert_stats[alert_type] = {"total": 0, "by_severity": {}}
            
            alert_stats[alert_type]["total"] += 1
            
            if severity not in alert_stats[alert_type]["by_severity"]:
                alert_stats[alert_type]["by_severity"][severity] = 0
            alert_stats[alert_type]["by_severity"][severity] += 1
        
        return AggregatedInsights(
            total_farmers=total_farmers,
            total_predictions=total_predictions,
            average_yield=avg_yield,
            top_performing_crops=top_performing_crops,
            regional_performance=regional_performance,
            seasonal_trends=seasonal_trends,
            alert_statistics=alert_stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch aggregated data: {str(e)}"
        )

@router.get("/download-dataset")
async def download_dataset(
    dataset_type: str = "predictions",  # predictions, farmers, alerts
    format: str = "csv",  # csv, json
    region: Optional[str] = None,
    crop_type: Optional[str] = None,
    days_back: Optional[int] = 30,
    current_user: dict = Depends(require_researcher_role)
):
    """Download dataset for research purposes"""
    try:
        supabase = get_supabase_client()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get data based on dataset type
        if dataset_type == "predictions":
            query = supabase.table("predictions").select(
                "*, farmers(location, crops, acres, soil_data, water_level)"
            ).gte("created_at", start_date.isoformat())
            
            if crop_type:
                query = query.eq("crop", crop_type)
            
            result = query.execute()
            data = result.data
            
            # Flatten data for CSV export
            flattened_data = []
            for pred in data:
                flat_record = {
                    "prediction_id": pred["id"],
                    "crop": pred["crop"],
                    "prediction": pred["prediction"],
                    "confidence": pred["confidence"],
                    "validated": pred["validated_by_agronomist"],
                    "created_at": pred["created_at"],
                    "farmer_location": pred["farmers"]["location"] if pred["farmers"] else "",
                    "farmer_acres": pred["farmers"]["acres"] if pred["farmers"] else 0,
                    "farmer_crops": pred["farmers"]["crops"] if pred["farmers"] else "",
                }
                
                # Add soil data fields
                if pred["farmers"] and pred["farmers"]["soil_data"]:
                    soil_data = pred["farmers"]["soil_data"]
                    flat_record.update({
                        "soil_ph": soil_data.get("ph", ""),
                        "soil_nitrogen": soil_data.get("nitrogen", ""),
                        "soil_phosphorus": soil_data.get("phosphorus", ""),
                        "soil_potassium": soil_data.get("potassium", ""),
                    })
                
                # Add input data fields
                if pred["input_data"]:
                    input_data = pred["input_data"]
                    flat_record.update({
                        "input_temperature": input_data.get("temperature", ""),
                        "input_humidity": input_data.get("humidity", ""),
                        "input_rainfall": input_data.get("rainfall", ""),
                    })
                
                flattened_data.append(flat_record)
            
            data = flattened_data
            
        elif dataset_type == "farmers":
            query = supabase.table("farmers").select("*, users(name, email)")
            if region:
                query = query.ilike("location", f"%{region}%")
            
            result = query.execute()
            data = []
            for farmer in result.data:
                data.append({
                    "farmer_id": farmer["id"],
                    "name": farmer["users"]["name"] if farmer["users"] else "",
                    "email": farmer["users"]["email"] if farmer["users"] else "",
                    "location": farmer["location"],
                    "crops": farmer["crops"],
                    "acres": farmer["acres"],
                    "water_level": farmer.get("water_level", ""),
                    "created_at": farmer["created_at"]
                })
            
        elif dataset_type == "alerts":
            result = supabase.table("alerts").select(
                "*, farmers(location)"
            ).gte("created_at", start_date.isoformat()).execute()
            
            data = []
            for alert in result.data:
                data.append({
                    "alert_id": alert["id"],
                    "alert_type": alert["alert_type"],
                    "severity": alert["severity"],
                    "title": alert["title"],
                    "message": alert["message"],
                    "is_resolved": alert["is_resolved"],
                    "farmer_location": alert["farmers"]["location"] if alert["farmers"] else "",
                    "created_at": alert["created_at"]
                })
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid dataset type. Use 'predictions', 'farmers', or 'alerts'"
            )
        
        # Generate response based on format
        if format.lower() == "csv":
            if not data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No data found for the specified criteria"
                )
            
            # Create CSV
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            csv_content = output.getvalue()
            output.close()
            
            # Create streaming response
            def generate():
                yield csv_content
            
            filename = f"{dataset_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        elif format.lower() == "json":
            filename = f"{dataset_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_content = json.dumps(data, indent=2, default=str)
            
            return StreamingResponse(
                io.StringIO(json_content),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Use 'csv' or 'json'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dataset: {str(e)}"
        )

@router.post("/research-data", response_model=SuccessResponse)
async def create_research_data(
    research_data: ResearchDataCreate,
    current_user: dict = Depends(require_researcher_role)
):
    """Create a new research data entry"""
    try:
        supabase = get_supabase_client()
        
        # Prepare data for insertion
        insert_data = {
            "title": research_data.title,
            "description": research_data.description,
            "region": research_data.region,
            "crop_type": research_data.crop_type,
            "season": research_data.season,
            "aggregated_results": research_data.aggregated_results,
            "ndvi_scores": research_data.ndvi_scores,
            "yield_predictions": research_data.yield_predictions,
            "data_source": "researcher_input"
        }
        
        result = supabase.table("research_data").insert(insert_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create research data entry"
            )
        
        return SuccessResponse(
            message="Research data created successfully",
            data=result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create research data: {str(e)}"
        )

@router.get("/research-data", response_model=List[ResearchDataResponse])
async def get_research_data(
    limit: Optional[int] = 50,
    region: Optional[str] = None,
    crop_type: Optional[str] = None,
    current_user: dict = Depends(require_researcher_role)
):
    """Get research data entries"""
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("research_data").select("*").order("created_at", desc=True)
        
        if region:
            query = query.eq("region", region)
        if crop_type:
            query = query.eq("crop_type", crop_type)
        
        result = query.limit(limit).execute()
        
        research_data = []
        for data in result.data:
            research_data.append(ResearchDataResponse(
                id=data["id"],
                title=data["title"],
                description=data.get("description"),
                region=data.get("region"),
                crop_type=data.get("crop_type"),
                season=data.get("season"),
                created_at=data["created_at"]
            ))
        
        return research_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch research data: {str(e)}"
        )

@router.get("/analytics/trends")
async def get_trends_analysis(
    time_period: str = "monthly",  # daily, weekly, monthly, yearly
    crop_type: Optional[str] = None,
    region: Optional[str] = None,
    current_user: dict = Depends(require_researcher_role)
):
    """Get trends analysis for research dashboard"""
    try:
        supabase = get_supabase_client()
        
        # Get predictions data
        query = supabase.table("predictions").select(
            "crop, prediction, confidence, created_at, farmers(location)"
        )
        
        if crop_type:
            query = query.eq("crop", crop_type)
        
        result = query.order("created_at", desc=True).limit(1000).execute()
        
        # Process data for trends
        trends = {}
        for pred in result.data:
            # Filter by region if specified
            if region and pred["farmers"] and region.lower() not in pred["farmers"]["location"].lower():
                continue
            
            # Group by time period
            created_at = datetime.fromisoformat(pred["created_at"].replace("Z", "+00:00"))
            
            if time_period == "daily":
                period_key = created_at.strftime("%Y-%m-%d")
            elif time_period == "weekly":
                period_key = f"{created_at.year}-W{created_at.isocalendar()[1]}"
            elif time_period == "monthly":
                period_key = created_at.strftime("%Y-%m")
            else:  # yearly
                period_key = str(created_at.year)
            
            if period_key not in trends:
                trends[period_key] = {
                    "period": period_key,
                    "total_predictions": 0,
                    "avg_yield": 0,
                    "avg_confidence": 0,
                    "crops": {}
                }
            
            trends[period_key]["total_predictions"] += 1
            trends[period_key]["avg_yield"] += pred["prediction"]
            trends[period_key]["avg_confidence"] += pred["confidence"]
            
            crop = pred["crop"]
            if crop not in trends[period_key]["crops"]:
                trends[period_key]["crops"][crop] = {"count": 0, "total_yield": 0}
            trends[period_key]["crops"][crop]["count"] += 1
            trends[period_key]["crops"][crop]["total_yield"] += pred["prediction"]
        
        # Calculate averages
        trend_list = []
        for period_key, data in trends.items():
            if data["total_predictions"] > 0:
                data["avg_yield"] = data["avg_yield"] / data["total_predictions"]
                data["avg_confidence"] = data["avg_confidence"] / data["total_predictions"]
                
                # Calculate crop averages
                for crop in data["crops"]:
                    data["crops"][crop]["avg_yield"] = data["crops"][crop]["total_yield"] / data["crops"][crop]["count"]
                
                trend_list.append(data)
        
        # Sort by period
        trend_list.sort(key=lambda x: x["period"])
        
        return {
            "time_period": time_period,
            "crop_type": crop_type,
            "region": region,
            "trends": trend_list,
            "summary": {
                "total_periods": len(trend_list),
                "overall_avg_yield": sum(t["avg_yield"] for t in trend_list) / len(trend_list) if trend_list else 0,
                "overall_avg_confidence": sum(t["avg_confidence"] for t in trend_list) / len(trend_list) if trend_list else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends analysis: {str(e)}"
        )