from fastapi import FastAPI
from typing import Dict
from pydantic import BaseModel

app = FastAPI()
@app.get("/")
def read_root():
    """Root endpoint for health checks"""
    return {
        "service": "Agent Service",
        "status": "running",
        "endpoints": [
            "/agents",
            "/agents/{agent_id}",
            "/agents/{agent_id}/availability"
        ]
    }

# In-memory sales store
sales_data: Dict[str, float] = {}

class BookingData(BaseModel):
    agent_id: str
    price: float

@app.post("/sales/record")
def record_sale(booking: BookingData):
    if booking.agent_id in sales_data:
        sales_data[booking.agent_id] += booking.price
    else:
        sales_data[booking.agent_id] = booking.price
    return {"message": "Sale recorded"}

@app.get("/sales/by-agent/{agent_id}")
def get_sales_by_agent(agent_id: str):
    return [{"agent_id": agent_id, "sales": sales_data.get(agent_id, 0.0)}]

@app.get("/sales/trends")
def get_sales_trends():
    return {"trend": "positive", "growth_percentage": 10}