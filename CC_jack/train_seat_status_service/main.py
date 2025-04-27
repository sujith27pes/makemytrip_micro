from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from uuid import UUID
import os
import httpx

app = FastAPI()

# Environment variables for service URLs
TRAIN_BOOKING_SERVICE_URL = os.getenv("TRAIN_BOOKING_SERVICE_URL", "http://train_booking_service:8084")

# Simple in-memory database for seat reservations
# Structure: {booking_id: {"train_number": str, "seats": List[str], "travel_date": str, "status": str}}
seat_reservations_db = {}
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

class SeatStatus(BaseModel):
    booking_id: UUID
    train_number: str
    seats: List[str]
    travel_date: str
    status: str  # "confirmed" or "cancelled"

@app.get("/bookings/{booking_id}/seats/status")
async def check_seat_status(booking_id: UUID):
    """Check if seats for a booking are confirmed"""
    booking_id_str = str(booking_id)
    
    if booking_id_str not in seat_reservations_db:
        # Try to get from train booking service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{TRAIN_BOOKING_SERVICE_URL}/train-bookings/{booking_id}"
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=404, detail="Booking not found")
                
                # Booking exists but no seat reservation yet
                return {
                    "booking_id": booking_id,
                    "status": "unconfirmed",
                    "message": "No seat reservation found for this booking"
                }
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Train booking service unavailable")
    
    reservation = seat_reservations_db[booking_id_str]
    
    return {
        "booking_id": booking_id,
        "train_number": reservation["train_number"],
        "travel_date": reservation["travel_date"],
        "seats": reservation["seats"],
        "status": reservation["status"]
    }

@app.put("/bookings/{booking_id}/seats/cancel")
async def cancel_seat_reservation(booking_id: UUID):
    """Cancel seat reservations for a booking"""
    booking_id_str = str(booking_id)
    
    if booking_id_str not in seat_reservations_db:
        raise HTTPException(status_code=404, detail="No seat reservations found for this booking")
    
    # Update the status to cancelled
    seat_reservations_db[booking_id_str]["status"] = "cancelled"
    
    # Notify the train booking service about the cancellation (in a real system)
    try:
        async with httpx.AsyncClient() as client:
            await client.put(
                f"{TRAIN_BOOKING_SERVICE_URL}/train-bookings/{booking_id}/cancel"
            )
    except httpx.RequestError:
        # Log the error but don't fail - we can reconcile later
        print(f"Error notifying booking service about cancellation: {booking_id}")
    
    return {
        "message": "Seat reservations cancelled successfully",
        "booking_id": booking_id,
        "status": "cancelled"
    }

# This would be called by the train_booking_service when a new booking with seats is created
@app.post("/seat-reservations", response_model=SeatStatus)
async def create_seat_reservation(reservation: SeatStatus):
    """Create a seat reservation record - this would be called internally by the booking service"""
    booking_id_str = str(reservation.booking_id)
    
    seat_reservations_db[booking_id_str] = {
        "train_number": reservation.train_number,
        "seats": reservation.seats,
        "travel_date": reservation.travel_date,
        "status": reservation.status
    }
    
    return reservation