from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from uuid import uuid4, UUID
import os
import httpx
from datetime import datetime

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

# Environment variables for service URLs
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent_service:8000")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking_service:8001")

# In-memory database for train bookings
train_bookings_db = {}

# Train data store (simplified)
trains_db = {
    "TRN001": {
        "train_number": "TRN001",
        "name": "Express 505",
        "source": "New York",
        "destination": "Washington DC",
        "departure_time": "08:30",
        "arrival_time": "12:00",
        "available_classes": ["First Class", "Business", "Economy"],
        "base_price": {
            "First Class": 150.00,
            "Business": 100.00,
            "Economy": 50.00
        }
    },
    "TRN002": {
        "train_number": "TRN002",
        "name": "Coastal Link",
        "source": "Boston",
        "destination": "New York",
        "departure_time": "10:15",
        "arrival_time": "13:45",
        "available_classes": ["First Class", "Economy"],
        "base_price": {
            "First Class": 120.00,
            "Economy": 45.00
        }
    },
    "TRN003": {
        "train_number": "TRN003",
        "name": "Western Eagle",
        "source": "Chicago",
        "destination": "Denver",
        "departure_time": "14:20",
        "arrival_time": "22:35",
        "available_classes": ["First Class", "Business", "Economy"],
        "base_price": {
            "First Class": 280.00,
            "Business": 180.00,
            "Economy": 120.00
        }
    }
}

class TrainClass(str):
    """Enum for train classes"""
    FIRST_CLASS = "First Class"
    BUSINESS = "Business"
    ECONOMY = "Economy"

class PassengerInfo(BaseModel):
    """Passenger information"""
    name: str
    age: int
    id_type: str  # Passport, ID card, etc.
    id_number: str

class TrainBookingCreate(BaseModel):
    """Data required to create a train booking"""
    agent_id: UUID
    train_number: str
    travel_date: str  # YYYY-MM-DD format
    passenger_count: int
    train_class: str  # First Class, Business, Economy
    passengers: List[PassengerInfo]
    special_requests: Optional[str] = None

class TrainBooking(BaseModel):
    """Complete train booking information"""
    booking_id: UUID
    agent_id: UUID
    train_number: str
    train_name: str
    source: str
    destination: str
    travel_date: str
    departure_time: str
    arrival_time: str
    train_class: str
    price_per_passenger: float
    total_price: float
    passenger_count: int
    passengers: List[PassengerInfo]
    special_requests: Optional[str] = None
    booking_date: str
    status: str = "Confirmed"  # Confirmed, Cancelled, Pending

class TrainInfo(BaseModel):
    """Train information"""
    train_number: str
    name: str
    source: str
    destination: str
    departure_time: str
    arrival_time: str
    available_classes: List[str]
    base_price: Dict[str, float]

@app.get("/trains", response_model=List[TrainInfo])
def list_trains():
    """List all available trains"""
    return [TrainInfo(**train) for train in trains_db.values()]

@app.get("/trains/{train_number}", response_model=TrainInfo)
def get_train(train_number: str):
    """Get details of a specific train"""
    if train_number not in trains_db:
        raise HTTPException(status_code=404, detail="Train not found")
    return TrainInfo(**trains_db[train_number])

@app.post("/train-bookings", response_model=TrainBooking)
async def create_train_booking(booking: TrainBookingCreate):
    """Create a new train booking"""
    # Validate agent exists via Agent Service
    async with httpx.AsyncClient() as client:
        agent_resp = await client.get(f"{AGENT_SERVICE_URL}/agents/{booking.agent_id}")
        if agent_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    # Validate train exists
    if booking.train_number not in trains_db:
        raise HTTPException(status_code=404, detail="Train not found")
    
    train = trains_db[booking.train_number]
    
    # Validate train class
    if booking.train_class not in train["available_classes"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid train class. Available classes: {train['available_classes']}"
        )
    
    # Validate passenger count
    if booking.passenger_count != len(booking.passengers):
        raise HTTPException(
            status_code=400,
            detail="Passenger count does not match number of passenger details provided"
        )
    
    # Calculate pricing
    price_per_passenger = train["base_price"][booking.train_class]
    total_price = price_per_passenger * booking.passenger_count
    
    # Create booking
    booking_id = uuid4()
    
    # Create train booking record
    new_booking = TrainBooking(
        booking_id=booking_id,
        agent_id=booking.agent_id,
        train_number=booking.train_number,
        train_name=train["name"],
        source=train["source"],
        destination=train["destination"],
        travel_date=booking.travel_date,
        departure_time=train["departure_time"],
        arrival_time=train["arrival_time"],
        train_class=booking.train_class,
        price_per_passenger=price_per_passenger,
        total_price=total_price,
        passenger_count=booking.passenger_count,
        passengers=booking.passengers,
        special_requests=booking.special_requests,
        booking_date=datetime.now().strftime("%Y-%m-%d"),
        status="Confirmed"
    )
    
    train_bookings_db[booking_id] = new_booking
    
    # Record this booking in the main booking service (for commission processing)
    try:
        async with httpx.AsyncClient() as client:
            booking_payload = {
                "agent_id": str(booking.agent_id),
                "customer_name": booking.passengers[0].name,
                "service_type": f"Train - {booking.train_class}",
                "price": total_price
            }
            await client.post(f"{BOOKING_SERVICE_URL}/bookings", json=booking_payload)
    except Exception as e:
        # Log the error but don't fail the booking - we can reconcile later
        print(f"Error recording booking with booking service: {e}")
    
    return new_booking

@app.get("/train-bookings", response_model=List[TrainBooking])
def list_train_bookings():
    """List all train bookings"""
    return list(train_bookings_db.values())

@app.get("/train-bookings/{booking_id}", response_model=TrainBooking)
def get_train_booking(booking_id: UUID):
    """Get details of a specific train booking"""
    if booking_id not in train_bookings_db:
        raise HTTPException(status_code=404, detail="Train booking not found")
    return train_bookings_db[booking_id]

@app.get("/agents/{agent_id}/train-bookings", response_model=List[TrainBooking])
def get_agent_train_bookings(agent_id: UUID):
    """Get all train bookings for a specific agent"""
    agent_bookings = [
        booking for booking in train_bookings_db.values() 
        if booking.agent_id == agent_id
    ]
    return agent_bookings

@app.put("/train-bookings/{booking_id}/cancel")
def cancel_train_booking(booking_id: UUID):
    """Cancel a train booking"""
    if booking_id not in train_bookings_db:
        raise HTTPException(status_code=404, detail="Train booking not found")
    
    booking = train_bookings_db[booking_id]
    if booking.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled")
    
    # Update booking status
    booking.status = "Cancelled"
    train_bookings_db[booking_id] = booking
    
    return {"message": "Booking cancelled successfully"}

@app.get("/train-bookings/search")
def search_train_bookings(
    agent_id: Optional[UUID] = None,
    train_number: Optional[str] = None,
    travel_date: Optional[str] = None,
    status: Optional[str] = None
):
    """Search train bookings by various criteria"""
    results = list(train_bookings_db.values())
    
    if agent_id:
        results = [booking for booking in results if booking.agent_id == agent_id]
    
    if train_number:
        results = [booking for booking in results if booking.train_number == train_number]
    
    if travel_date:
        results = [booking for booking in results if booking.travel_date == travel_date]
    
    if status:
        results = [booking for booking in results if booking.status == status]
    
    return results