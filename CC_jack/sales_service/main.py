from fastapi import FastAPI
from typing import List, Dict
from pydantic import BaseModel

app = FastAPI()

# In-memory sales store
sales_data: Dict[str, float] = {}

class BookingData(BaseModel):
    agent_id: str
    price: float

class SalesSummary(BaseModel):
    total_sales: float
    agent_sales: List[Dict[str, float]]

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

@app.get("/sales/summary", response_model=SalesSummary)
def get_sales_summary():
    agent_sales = [{"agent_id": k, "sales": v} for k, v in sales_data.items()]
    total_sales = sum(sales_data.values())
    return SalesSummary(total_sales=total_sales, agent_sales=agent_sales)

@app.get("/sales/trends")
def get_sales_trends():
    return {"trend": "positive", "growth_percentage": 10}
