from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.utils.predict_utils import (
    predict,
    recommend_products
)

app = FastAPI(title="Fashion AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestBody(BaseModel):
    text: str

@app.get("/")
def home():
    return {
        "message": "Fashion AI API Running"
    }

@app.post("/predict")
def get_prediction(data: RequestBody):

    prediction = predict(data.text)

    recommendations = recommend_products(
        data.text
    )

    return {
        "prediction": prediction,
        "recommendations": recommendations.to_dict(
            orient="records"
        )
    }