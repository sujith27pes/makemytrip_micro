from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
from uuid import UUID
import os
import httpx
from enum import Enum

app = FastAPI()

# Environment variables for service URLs
TRAIN_BOOKING_SERVICE_URL = os.getenv("TRAIN_BOOKING_SERVICE_URL", "http://train_booking_service:8084")

# Sample seat layout definitions (in a real system, this would be in a database)
# Format: {"coach_type": {"rows": int, "seats_per_row": int, "layout": str}}
COACH_LAYOUTS = {
    "First Class": {"rows": 5, "seats_per_row": 2, "layout": "1-1"},  # Single seats on each side
    "Business": {"rows": 8, "seats_per_row": 3, "layout": "2-1"},     # 2 seats on left, 1 on right
    "Economy": {"rows": 12, "seats_per_row": 4, "layout": "2-2"}      # 2 seats on each side
}

# In-memory database for train seat maps
# Structure: {train_number: {coach_number: {seat_id: seat_data}}}
train_seats_db = {}

# In-memory database for seat reservations
# Structure: {booking_id: [seat_ids]}
seat_reservations_db = {}

class SeatStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"

class SeatType(str, Enum):
    WINDOW = "window"
    MIDDLE = "middle"
    AISLE = "aisle"
    SINGLE = "single"

class CoachClass(str, Enum):
    FIRST_CLASS = "First Class"
    BUSINESS = "Business" 
    ECONOMY = "Economy"

class Seat(BaseModel):
    seat_id: str  # e.g., "1A", "2B"
    coach_number: str
    coach_class: CoachClass
    row_number: int
    seat_position: str
    seat_type: SeatType
    status: SeatStatus = SeatStatus.AVAILABLE
    price_adjustment: float = 0.0  # Price adjustment for premium seats
    features: List[str] = []  # e.g., ["power_outlet", "extra_legroom"]

class CoachInfo(BaseModel):
    coach_number: str
    coach_class: CoachClass
    rows: int
    seats_per_row: int
    layout: str
    total_seats: int
    available_seats: int

class TrainSeatMap(BaseModel):
    train_number: str
    coaches: List[CoachInfo]
    total_seats: int
    available_seats: int

class SeatReservation(BaseModel):
    booking_id: UUID
    train_number: str
    seats: List[str]  # List of seat_ids
    travel_date: str  # YYYY-MM-DD format

class SeatReservationRequest(BaseModel):
    booking_id: UUID
    train_number: str
    coach_class: CoachClass
    preferred_seats: Optional[List[str]] = None
    seat_preferences: Optional[List[str]] = []  # e.g., ["window", "aisle"]
    passengers: int
    travel_date: str  # YYYY-MM-DD format

# Initialize sample data for trains from train_booking_service
@app.on_event("startup")
async def initialize_train_data():
    # Generate seat maps for trains in the train_booking_service
    train_numbers = ["TRN001", "TRN002", "TRN003"]
    
    for train_number in train_numbers:
        # Create seat map for this train
        train_seats_db[train_number] = {}
        
        # Add First Class coaches
        coach_num = 1
        add_coaches(train_number, "FC", CoachClass.FIRST_CLASS, 2, coach_num)
        coach_num += 2
        
        # Add Business coaches for trains that have them
        if train_number != "TRN002":  # TRN002 doesn't have business class
            add_coaches(train_number, "BC", CoachClass.BUSINESS, 3, coach_num)
            coach_num += 3
        
        # Add Economy coaches
        add_coaches(train_number, "EC", CoachClass.ECONOMY, 5, coach_num)

def add_coaches(train_number, prefix, coach_class, count, start_num):
    """Helper function to add coaches of a specific class to a train"""
    layout = COACH_LAYOUTS[coach_class]
    
    for i in range(count):
        coach_number = f"{prefix}{start_num + i}"
        train_seats_db[train_number][coach_number] = {}
        
        # Generate seats in this coach
        for row in range(1, layout["rows"] + 1):
            for seat_pos in range(1, layout["seats_per_row"] + 1):
                # Map seat position to letter
                seat_letter = chr(64 + seat_pos)  # 1 -> A, 2 -> B, etc.
                seat_id = f"{row}{seat_letter}"
                
                # Determine seat type based on position and layout
                seat_type = determine_seat_type(seat_pos, layout["layout"])
                
                # Create seat
                seat = Seat(
                    seat_id=seat_id,
                    coach_number=coach_number,
                    coach_class=coach_class,
                    row_number=row,
                    seat_position=seat_letter,
                    seat_type=seat_type,
                    status=SeatStatus.AVAILABLE,
                    price_adjustment=get_price_adjustment(seat_type, coach_class),
                    features=get_seat_features(seat_type, coach_class, row)
                )
                
                # Add to database
                train_seats_db[train_number][coach_number][seat_id] = seat

def determine_seat_type(position, layout):
    """Determine seat type based on position and coach layout"""
    if layout == "1-1":
        return SeatType.WINDOW
    elif layout == "2-1":
        if position == 1:
            return SeatType.WINDOW
        elif position == 2:
            return SeatType.AISLE
        else:  # position == 3
            return SeatType.SINGLE
    elif layout == "2-2":
        if position == 1 or position == 4:
            return SeatType.WINDOW
        else:  # position == 2 or position == 3
            return SeatType.AISLE

def get_price_adjustment(seat_type, coach_class):
    """Get price adjustment based on seat type and coach class"""
    adjustments = {
        CoachClass.FIRST_CLASS: {
            SeatType.WINDOW: 15.0,
            SeatType.SINGLE: 20.0
        },
        CoachClass.BUSINESS: {
            SeatType.WINDOW: 10.0,
            SeatType.AISLE: 5.0,
            SeatType.SINGLE: 15.0
        },
        CoachClass.ECONOMY: {
            SeatType.WINDOW: 5.0,
            SeatType.AISLE: 3.0
        }
    }
    
    return adjustments.get(coach_class, {}).get(seat_type, 0.0)

def get_seat_features(seat_type, coach_class, row):
    """Get seat features based on seat type, coach class and row"""
    features = []
    
    # Extra legroom in first row of each coach
    if row == 1:
        features.append("extra_legroom")
    
    # Power outlets in First Class and Business
    if coach_class in [CoachClass.FIRST_CLASS, CoachClass.BUSINESS]:
        features.append("power_outlet")
    
    # USB ports everywhere except Economy middle seats
    if not (coach_class == CoachClass.ECONOMY and seat_type == SeatType.MIDDLE):
        features.append("usb_port")
    
    # First class gets extra features
    if coach_class == CoachClass.FIRST_CLASS:
        features.extend(["adjustable_headrest", "footrest", "personal_screen"])
    
    return features

@app.get("/trains/{train_number}/seats", response_model=TrainSeatMap)
async def get_train_seat_map(train_number: str, travel_date: str):
    """Get the seat map for a specific train on a specific date"""
    if train_number not in train_seats_db:
        raise HTTPException(status_code=404, detail="Train not found")
    
    coaches_info = []
    total_seats = 0
    available_seats = 0
    
    for coach_number, seats in train_seats_db[train_number].items():
        # Get one seat to determine the coach class
        sample_seat = next(iter(seats.values()))
        coach_class = sample_seat.coach_class
        layout = COACH_LAYOUTS[coach_class]
        
        # Count available seats
        coach_total_seats = len(seats)
        coach_available_seats = sum(1 for seat in seats.values() 
                                  if seat.status == SeatStatus.AVAILABLE)
        
        coaches_info.append(CoachInfo(
            coach_number=coach_number,
            coach_class=coach_class,
            rows=layout["rows"],
            seats_per_row=layout["seats_per_row"],
            layout=layout["layout"],
            total_seats=coach_total_seats,
            available_seats=coach_available_seats
        ))
        
        total_seats += coach_total_seats
        available_seats += coach_available_seats
    
    return TrainSeatMap(
        train_number=train_number,
        coaches=coaches_info,
        total_seats=total_seats,
        available_seats=available_seats
    )

@app.get("/trains/{train_number}/coaches/{coach_number}/seats")
async def get_coach_seats(train_number: str, coach_number: str, travel_date: str):
    """Get all seats in a specific coach"""
    if train_number not in train_seats_db:
        raise HTTPException(status_code=404, detail="Train not found")
    
    if coach_number not in train_seats_db[train_number]:
        raise HTTPException(status_code=404, detail="Coach not found")
    
    # Adjust seat statuses based on reservations for this date
    seats = list(train_seats_db[train_number][coach_number].values())
    
    # Check reservations and update status
    for booking_id, reservation in seat_reservations_db.items():
        if reservation["train_number"] == train_number and reservation["travel_date"] == travel_date:
            for seat_id in reservation["seats"]:
                coach, seat = parse_seat_id(seat_id)
                if coach == coach_number:
                    for s in seats:
                        if s.seat_id == seat:
                            s.status = SeatStatus.RESERVED
    
    return seats

@app.post("/seat-reservations", response_model=SeatReservation)
async def reserve_seats(reservation_request: SeatReservationRequest):
    """Reserve seats for a booking"""
    # Verify booking exists by calling train_booking_service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TRAIN_BOOKING_SERVICE_URL}/train-bookings/{reservation_request.booking_id}"
            )
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Booking not found")
            
            # Verify train exists
            if reservation_request.train_number not in train_seats_db:
                raise HTTPException(status_code=404, detail="Train not found")
            
            # Get all coaches of requested class
            class_coaches = {}
            for coach_number, seats in train_seats_db[reservation_request.train_number].items():
                sample_seat = next(iter(seats.values()))
                if sample_seat.coach_class == reservation_request.coach_class:
                    class_coaches[coach_number] = seats
            
            if not class_coaches:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No coaches available for class {reservation_request.coach_class}"
                )
            
            # Handle specific seat requests
            seats_to_reserve = []
            
            if reservation_request.preferred_seats:
                # Validate and collect specific requested seats
                for seat_id in reservation_request.preferred_seats:
                    coach_number, seat_id_short = parse_seat_id(seat_id)
                    
                    # Verify coach exists and is of requested class
                    if coach_number not in class_coaches:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Coach {coach_number} does not exist or is not {reservation_request.coach_class}"
                        )
                    
                    # Verify seat exists
                    if seat_id_short not in train_seats_db[reservation_request.train_number][coach_number]:
                        raise HTTPException(status_code=400, detail=f"Seat {seat_id} does not exist")
                    
                    # Verify seat is available
                    seat = train_seats_db[reservation_request.train_number][coach_number][seat_id_short]
                    if seat.status != SeatStatus.AVAILABLE:
                        raise HTTPException(status_code=400, detail=f"Seat {seat_id} is not available")
                    
                    seats_to_reserve.append(f"{coach_number}-{seat_id_short}")
                
                # Check if we have enough seats
                if len(seats_to_reserve) != reservation_request.passengers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Number of preferred seats ({len(seats_to_reserve)}) does not match passengers ({reservation_request.passengers})"
                    )
            else:
                # Auto-allocate seats based on preferences
                seats_to_reserve = find_best_seats(
                    reservation_request.train_number,
                    class_coaches,
                    reservation_request.passengers,
                    reservation_request.seat_preferences
                )
            
            # Reserve the seats
            booking_id = reservation_request.booking_id
            seat_reservations_db[booking_id] = {
                "train_number": reservation_request.train_number,
                "seats": seats_to_reserve,
                "travel_date": reservation_request.travel_date
            }
            
            # Update seat status
            for seat_id in seats_to_reserve:
                coach_number, seat_id_short = parse_seat_id(seat_id)
                seat = train_seats_db[reservation_request.train_number][coach_number][seat_id_short]
                seat.status = SeatStatus.RESERVED
            
            return SeatReservation(
                booking_id=booking_id,
                train_number=reservation_request.train_number,
                seats=seats_to_reserve,
                travel_date=reservation_request.travel_date
            )
    
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Train booking service unavailable")

def parse_seat_id(seat_id):
    """Parse combined seat ID like 'FC1-2A' into coach_number and seat_id"""
    if "-" in seat_id:
        return seat_id.split("-")
    return None, seat_id

def find_best_seats(train_number, coaches, passenger_count, preferences):
    """Find the best seats based on preferences and passenger count"""
    # Simple algorithm: try to find seats together in one row if possible
    
    available_seats = []
    
    # First, collect all available seats
    for coach_number, seats in coaches.items():
        for seat_id, seat in seats.items():
            if seat.status == SeatStatus.AVAILABLE:
                # Compute a score for this seat based on preferences
                score = compute_seat_score(seat, preferences)
                available_seats.append((coach_number, seat_id, seat, score))
    
    # Sort by coach, row, and score
    available_seats.sort(key=lambda x: (x[0], x[2].row_number, -x[3]))
    
    # Try to find consecutive seats in the same row
    best_seats = []
    current_row_seats = []
    current_coach = None
    current_row = None
    
    for coach_number, seat_id, seat, score in available_seats:
        if current_coach != coach_number or current_row != seat.row_number:
            # New row or coach, check if we already have enough seats
            if len(current_row_seats) >= passenger_count:
                # Take the highest scoring seats from this row
                current_row_seats.sort(key=lambda x: -x[3])
                best_seats = current_row_seats[:passenger_count]
                break
            
            # Start a new row
            current_coach = coach_number
            current_row = seat.row_number
            current_row_seats = [(coach_number, seat_id, seat, score)]
        else:
            # Same row, add this seat
            current_row_seats.append((coach_number, seat_id, seat, score))
    
    # If we didn't find enough consecutive seats, just take the best individual seats
    if len(best_seats) < passenger_count:
        available_seats.sort(key=lambda x: -x[3])
        best_seats = available_seats[:passenger_count]
    
    # Format the seat IDs
    return [f"{coach}-{seat_id}" for coach, seat_id, _, _ in best_seats]

def compute_seat_score(seat, preferences):
    """Compute a score for a seat based on preferences"""
    score = 0
    
    for pref in preferences:
        if pref == "window" and seat.seat_type == SeatType.WINDOW:
            score += 10
        elif pref == "aisle" and seat.seat_type == SeatType.AISLE:
            score += 8
        elif pref == "extra_legroom" and "extra_legroom" in seat.features:
            score += 5
        elif pref == "power_outlet" and "power_outlet" in seat.features:
            score += 3
    
    # Bonus for premium seats
    score += seat.price_adjustment / 5
    
    return score

@app.get("/bookings/{booking_id}/seats")
async def get_booking_seats(booking_id: UUID):
    """Get the seats reserved for a specific booking"""
    booking_id_str = str(booking_id)
    if booking_id_str not in seat_reservations_db:
        raise HTTPException(status_code=404, detail="No seat reservations found for this booking")
    
    reservation = seat_reservations_db[booking_id_str]
    seat_details = []
    
    for seat_id in reservation["seats"]:
        coach_number, seat_id_short = parse_seat_id(seat_id)
        if (reservation["train_number"] in train_seats_db and
            coach_number in train_seats_db[reservation["train_number"]] and
            seat_id_short in train_seats_db[reservation["train_number"]][coach_number]):
            
            seat = train_seats_db[reservation["train_number"]][coach_number][seat_id_short]
            seat_details.append(seat)
    
    return {
        "booking_id": booking_id,
        "train_number": reservation["train_number"],
        "travel_date": reservation["travel_date"],
        "seats": seat_details
    }

@app.put("/bookings/{booking_id}/seats/cancel")
async def cancel_seat_reservation(booking_id: UUID):
    """Cancel seat reservations for a booking"""
    booking_id_str = str(booking_id)
    if booking_id_str not in seat_reservations_db:
        raise HTTPException(status_code=404, detail="No seat reservations found for this booking")
    
    reservation = seat_reservations_db[booking_id_str]
    
    # Free up the seats
    for seat_id in reservation["seats"]:
        coach_number, seat_id_short = parse_seat_id(seat_id)
        if (reservation["train_number"] in train_seats_db and
            coach_number in train_seats_db[reservation["train_number"]] and
            seat_id_short in train_seats_db[reservation["train_number"]][coach_number]):
            
            seat = train_seats_db[reservation["train_number"]][coach_number][seat_id_short]
            seat.status = SeatStatus.AVAILABLE
    
    # Remove the reservation
    del seat_reservations_db[booking_id_str]
    
    return {"message": "Seat reservations cancelled successfully"}

@app.get("/trains/{train_number}/availability")
async def get_seat_availability(
    train_number: str, 
    travel_date: str, 
    coach_class: Optional[CoachClass] = None
):
    """Get seat availability summary for a train, optionally filtered by class"""
    if train_number not in train_seats_db:
        raise HTTPException(status_code=404, detail="Train not found")
    
    availability = {}
    
    for coach_number, seats in train_seats_db[train_number].items():
        sample_seat = next(iter(seats.values()))
        current_class = sample_seat.coach_class
        
        # Skip if filtering by class and this isn't the requested class
        if coach_class and current_class != coach_class:
            continue
        
        # Count available seats
        total_seats = len(seats)
        reserved_seats = 0
        
        # Check reservations for this date
        for reservation in seat_reservations_db.values():
            if (reservation["train_number"] == train_number and 
                reservation["travel_date"] == travel_date):
                for seat_id in reservation["seats"]:
                    res_coach, _ = parse_seat_id(seat_id)
                    if res_coach == coach_number:
                        reserved_seats += 1
        
        available_seats = total_seats - reserved_seats
        
        if current_class not in availability:
            availability[current_class] = {
                "total_coaches": 0,
                "total_seats": 0,
                "available_seats": 0,
                "coaches": {}
            }
        
        availability[current_class]["total_coaches"] += 1
        availability[current_class]["total_seats"] += total_seats
        availability[current_class]["available_seats"] += available_seats
        availability[current_class]["coaches"][coach_number] = {
            "total_seats": total_seats,
            "available_seats": available_seats
        }
    
    # Add overall summary
    total_all = sum(data["total_seats"] for data in availability.values())
    available_all = sum(data["available_seats"] for data in availability.values())
    
    return {
        "train_number": train_number,
        "travel_date": travel_date,
        "total_seats": total_all,
        "available_seats": available_all,
        "availability_by_class": availability
    }

@app.get("/trains/{train_number}/coach-layout/{coach_class}")
async def get_coach_layout(train_number: str, coach_class: CoachClass):
    """Get the visual layout of a coach for a specific class"""
    if coach_class not in COACH_LAYOUTS:
        raise HTTPException(status_code=404, detail=f"Coach class {coach_class} not found")
    
    layout = COACH_LAYOUTS[coach_class]
    
    # Create a visual representation of the coach layout
    rows = layout["rows"]
    seats_per_row = layout["seats_per_row"]
    layout_pattern = layout["layout"]
    
    visual_layout = []
    for row in range(1, rows + 1):
        row_layout = {"row": row, "seats": []}
        
        seat_position = 1
        for segment in layout_pattern.split('-'):
            segment_seats = []
            for _ in range(int(segment)):
                seat_letter = chr(64 + seat_position)  # A, B, C, etc.
                seat_position += 1
                segment_seats.append(f"{row}{seat_letter}")
            
            row_layout["seats"].append(segment_seats)
        
        visual_layout.append(row_layout)
    
    return {
        "coach_class": coach_class,
        "rows": rows,
        "seats_per_row": seats_per_row,
        "layout_pattern": layout_pattern,
        "visual_layout": visual_layout
    }

@app.put("/trains/{train_number}/seats/{seat_id}/status")
async def update_seat_status(
    train_number: str, 
    seat_id: str, 
    status: SeatStatus,
    travel_date: str
):
    """Update the status of a specific seat"""
    coach_number, seat_id_short = parse_seat_id(seat_id)
    
    if train_number not in train_seats_db:
        raise HTTPException(status_code=404, detail="Train not found")
    
    if coach_number not in train_seats_db[train_number]:
        raise HTTPException(status_code=404, detail="Coach not found")
    
    if seat_id_short not in train_seats_db[train_number][coach_number]:
        raise HTTPException(status_code=404, detail="Seat not found")
    
    # Update seat status
    seat = train_seats_db[train_number][coach_number][seat_id_short]
    seat.status = status
    
    return seat