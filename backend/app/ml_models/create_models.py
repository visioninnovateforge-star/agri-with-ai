"""
Sample ML models for agriculture predictions
This file creates mock ML models for demonstration purposes.
In production, these would be trained models saved as .pkl files.
"""
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import os

def create_mock_yield_model():
    """Create a mock yield prediction model"""
    # Generate synthetic training data
    np.random.seed(42)
    n_samples = 1000
    
    # Features: [soil_ph, soil_moisture, nitrogen, phosphorus, potassium, temperature, humidity, rainfall, acres]
    X = np.random.rand(n_samples, 9)
    
    # Scale features to realistic ranges
    X[:, 0] = X[:, 0] * 4 + 5    # pH: 5-9
    X[:, 1] = X[:, 1] * 100      # soil_moisture: 0-100%
    X[:, 2] = X[:, 2] * 200      # nitrogen: 0-200 ppm
    X[:, 3] = X[:, 3] * 100      # phosphorus: 0-100 ppm
    X[:, 4] = X[:, 4] * 400      # potassium: 0-400 ppm
    X[:, 5] = X[:, 5] * 40 + 5   # temperature: 5-45°C
    X[:, 6] = X[:, 6] * 100      # humidity: 0-100%
    X[:, 7] = X[:, 7] * 2000     # rainfall: 0-2000mm
    X[:, 8] = X[:, 8] * 10 + 1   # acres: 1-11
    
    # Create synthetic yield data with realistic relationships
    y = (
        50 +  # base yield
        (X[:, 0] - 7) * -5 +  # pH effect (optimal around 7)
        X[:, 1] * 0.3 +  # soil moisture positive effect
        X[:, 2] * 0.1 +  # nitrogen positive effect
        X[:, 3] * 0.2 +  # phosphorus positive effect
        X[:, 4] * 0.05 + # potassium positive effect
        (25 - np.abs(X[:, 5] - 25)) * 0.5 +  # temperature (optimal around 25°C)
        X[:, 6] * 0.1 +  # humidity positive effect
        np.minimum(X[:, 7], 1000) * 0.02 +  # rainfall (diminishing returns after 1000mm)
        np.random.normal(0, 5, n_samples)  # noise
    ) * X[:, 8]  # scale by acres
    
    # Ensure positive yields
    y = np.maximum(y, 10)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model

def create_mock_crop_health_model():
    """Create a mock crop health analysis model"""
    # Generate synthetic training data
    np.random.seed(123)
    n_samples = 800
    
    # Features: [ndvi_index, temperature, humidity, soil_moisture]
    X = np.random.rand(n_samples, 4)
    
    # Scale features to realistic ranges
    X[:, 0] = X[:, 0] * 1.0 - 0.2  # NDVI: -0.2 to 0.8
    X[:, 1] = X[:, 1] * 40 + 5     # temperature: 5-45°C
    X[:, 2] = X[:, 2] * 100        # humidity: 0-100%
    X[:, 3] = X[:, 3] * 100        # soil_moisture: 0-100%
    
    # Create synthetic health scores (0-1)
    y = (
        0.5 +  # base health
        np.maximum(X[:, 0], 0) * 0.6 +  # NDVI positive effect (main factor)
        (25 - np.abs(X[:, 1] - 25)) * 0.01 +  # temperature (optimal around 25°C)
        (60 - np.abs(X[:, 2] - 60)) * 0.003 +  # humidity (optimal around 60%)
        (70 - np.abs(X[:, 3] - 70)) * 0.002 +  # soil moisture (optimal around 70%)
        np.random.normal(0, 0.1, n_samples)  # noise
    )
    
    # Clamp between 0 and 1
    y = np.clip(y, 0, 1)
    
    # Train model
    model = LinearRegression()
    model.fit(X, y)
    
    return model

def save_models():
    """Create and save mock ML models"""
    # Create models directory if it doesn't exist
    models_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create yield prediction model
    yield_model = create_mock_yield_model()
    with open(os.path.join(models_dir, "yield_model.pkl"), "wb") as f:
        pickle.dump(yield_model, f)
    print("Yield prediction model saved")
    
    # Create crop health model
    health_model = create_mock_crop_health_model()
    with open(os.path.join(models_dir, "crop_health_model.pkl"), "wb") as f:
        pickle.dump(health_model, f)
    print("Crop health model saved")

if __name__ == "__main__":
    save_models()