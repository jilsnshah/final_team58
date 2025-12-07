from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
from typing import List

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
try:
    model = joblib.load('model.pkl')
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

class PredictionRequest(BaseModel):
    features: List[float]

class PredictionResponse(BaseModel):
    prediction: float
    confidence: float

@app.get("/")
async def root():
    return {"message": "ML Model API is running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Convert features to numpy array with proper shape
        features_array = np.array(request.features).reshape(1, -1)
        
        # Make prediction
        prediction = model.predict(features_array)
        
        # Get confidence if available (for classifiers)
        confidence = 0.0
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(features_array)
            confidence = float(np.max(proba))
        
        return PredictionResponse(
            prediction=float(prediction[0]),
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
