#!/bin/bash
# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

# Output files
OUTPUT_FILE="api_test_results.txt"
HTML_OUTPUT="api_test_results.html"
PDF_OUTPUT="api_test_results.pdf"

# Remove old output files if they exist
rm -f $OUTPUT_FILE $HTML_OUTPUT

# Function to log to both console and file
log() {
    echo -e "$1"
    echo -e "$1" | sed 's/\x1B\[[0-9;]\{1,\}[A-Za-z]//g' >> $OUTPUT_FILE
}

log "${BLUE}=== Travel Agent Management System API Test Script ===${NC}"
log "This script will test all existing endpoints of your microservices application"
log "$(date)"
log ""

# Base URLs
AGENT_SERVICE="http://localhost:8000"
BOOKING_SERVICE="http://localhost:8001"
SALES_SERVICE="http://localhost:8002"
INVOICING_SERVICE="http://localhost:8003"
TRAIN_BOOKING_SERVICE="http://localhost:8084"
TRAIN_SEAT_STATUS_SERVICE="http://localhost:8090"

# Function to make API calls and check responses
call_api() {
    local method=$1
    local url=$2
    local data=$3
    local description=$4
    
    log "${YELLOW}Testing: ${description}${NC}"
    log "URL: ${method} ${url}"
    
    if [ -n "$data" ]; then
        log "Payload: $data"
        response=$(curl -s -X $method $url -H "Content-Type: application/json" -d "$data")
    else
        response=$(curl -s -X $method $url)
    fi
    
    # Check if the response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        log "${GREEN}Success! Response:${NC}"
        log "$(echo "$response" | jq .)"
    else
        log "${RED}Error: Invalid response${NC}"
        log "$response"
    fi
    log ""
    
    # Return the response for further processing
    echo "$response"
}

# Store IDs for cross-service testing
AGENT_ID=""
BOOKING_ID=""
TRAIN_BOOKING_ID=""
TRAIN_NUMBER="TRN001"
TRAVEL_DATE="2025-05-15"

log "${BLUE}=== Testing Agent Service ===${NC}"

# Create an agent
log "${YELLOW}Testing: Create a new agent${NC}"
log "URL: POST ${AGENT_SERVICE}/agents"
payload='{
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "123-456-7890",
    "availability": {
        "days": ["Monday", "Wednesday", "Friday"],
        "shift": "morning"
    }
}'
log "Payload: $payload"

response=$(curl -s -X POST ${AGENT_SERVICE}/agents -H "Content-Type: application/json" -d "$payload")

# Extract agent ID from response
if echo "$response" | jq . >/dev/null 2>&1; then
    AGENT_ID=$(echo $response | jq -r '.id')
    log "${GREEN}Success! Response:${NC}"
    log "$(echo "$response" | jq .)"
    log "Created agent with ID: $AGENT_ID"
else
    log "${RED}Error: Invalid response${NC}"
    log "$response"
fi
log ""

# Test agent service endpoints
call_api "GET" "${AGENT_SERVICE}/agents" "" "List all agents"
call_api "GET" "${AGENT_SERVICE}/agents/${AGENT_ID}" "" "Get specific agent"
call_api "PUT" "${AGENT_SERVICE}/agents/${AGENT_ID}/availability" '{
    "days": ["Tuesday", "Thursday"],
    "shift": "evening"
}' "Update agent availability"
call_api "GET" "${AGENT_SERVICE}/agents/${AGENT_ID}/availability" "" "Get agent availability"

log "${BLUE}=== Testing Booking Service ===${NC}"

# Create a booking
log "${YELLOW}Testing: Create a new booking${NC}"
log "URL: POST ${BOOKING_SERVICE}/bookings"
payload='{
    "agent_id": "'$AGENT_ID'",
    "customer_name": "Alice Johnson",
    "service_type": "Flight",
    "price": 350.00
}'
log "Payload: $payload"

response=$(curl -s -X POST ${BOOKING_SERVICE}/bookings -H "Content-Type: application/json" -d "$payload")

# Extract booking ID from response
if echo "$response" | jq . >/dev/null 2>&1; then
    BOOKING_ID=$(echo $response | jq -r '.booking_id')
    log "${GREEN}Success! Response:${NC}"
    log "$(echo "$response" | jq .)"
    log "Created booking with ID: $BOOKING_ID"
else
    log "${RED}Error: Invalid response${NC}"
    log "$response"
fi
log ""

# Test booking service endpoints
call_api "GET" "${BOOKING_SERVICE}/agents/${AGENT_ID}/bookings" "" "Get agent bookings"
call_api "GET" "${BOOKING_SERVICE}/agents/${AGENT_ID}/commission" "" "Get agent commission"

log "${BLUE}=== Testing Sales Service ===${NC}"

# Record a sale
call_api "POST" "${SALES_SERVICE}/sales/record" '{
    "agent_id": "'$AGENT_ID'",
    "price": 450.00
}' "Record a sale"

# Test sales service endpoints
call_api "GET" "${SALES_SERVICE}/sales/by-agent/${AGENT_ID}" "" "Get sales by agent"
call_api "GET" "${SALES_SERVICE}/sales/trends" "" "Get sales trends"

log "${BLUE}=== Testing Invoicing Service ===${NC}"

# Generate an invoice
call_api "POST" "${INVOICING_SERVICE}/invoice" '{
    "agent_id": "'$AGENT_ID'",
    "customer_name": "Bob Wilson",
    "amount": 550.00
}' "Generate an invoice"

# Process a payout
call_api "POST" "${INVOICING_SERVICE}/payout" '{
    "agent_id": "'$AGENT_ID'",
    "payout_amount": 220.00
}' "Process agent payout"

# Get agent payouts
call_api "GET" "${INVOICING_SERVICE}/agents/${AGENT_ID}/payouts" "" "Get agent payouts"

log "${BLUE}=== Testing Train Booking Service ===${NC}"

# Get list of trains
call_api "GET" "${TRAIN_BOOKING_SERVICE}/trains" "" "List all trains"

# Get specific train details
call_api "GET" "${TRAIN_BOOKING_SERVICE}/trains/TRN001" "" "Get specific train details"

# Create a train booking
log "${YELLOW}Testing: Create a new train booking${NC}"
log "URL: POST ${TRAIN_BOOKING_SERVICE}/train-bookings"
train_booking_payload='{
    "agent_id": "'$AGENT_ID'",
    "train_number": "TRN001",
    "travel_date": "'$TRAVEL_DATE'",
    "passenger_count": 2,
    "train_class": "First Class",
    "passengers": [
        {
            "name": "Jane Smith",
            "age": 35,
            "id_type": "Passport",
            "id_number": "AB123456"
        },
        {
            "name": "David Smith",
            "age": 40,
            "id_type": "Passport",
            "id_number": "CD789012"
        }
    ],
    "special_requests": "Window seats preferred"
}'
log "Payload: $train_booking_payload"

train_booking_response=$(curl -s -X POST ${TRAIN_BOOKING_SERVICE}/train-bookings -H "Content-Type: application/json" -d "$train_booking_payload")

# Extract train booking ID from response
if echo "$train_booking_response" | jq . >/dev/null 2>&1; then
    TRAIN_BOOKING_ID=$(echo $train_booking_response | jq -r '.booking_id')
    log "${GREEN}Success! Response:${NC}"
    log "$(echo "$train_booking_response" | jq .)"
    log "Created train booking with ID: $TRAIN_BOOKING_ID"
else
    log "${RED}Error: Invalid response${NC}"
    log "$train_booking_response"
fi
log ""

# Get list of all train bookings
call_api "GET" "${TRAIN_BOOKING_SERVICE}/train-bookings" "" "List all train bookings"

# Get specific train booking
call_api "GET" "${TRAIN_BOOKING_SERVICE}/train-bookings/${TRAIN_BOOKING_ID}" "" "Get specific train booking details"

# Get agent's train bookings
call_api "GET" "${TRAIN_BOOKING_SERVICE}/agents/${AGENT_ID}/train-bookings" "" "Get agent's train bookings"

# Search train bookings
#call_api "GET" "${TRAIN_BOOKING_SERVICE}/train-bookings/search?agent_id=${AGENT_ID}" "" "Search train bookings by criteria"

log "${BLUE}=== Testing Train Seat Status Service ===${NC}"

# Create a seat reservation
log "${YELLOW}Testing: Reserve seats for a train booking${NC}"
log "URL: POST ${TRAIN_SEAT_STATUS_SERVICE}/seat-reservations"
seat_reservation_payload='{
    "booking_id": "'$TRAIN_BOOKING_ID'",
    "train_number": "'$TRAIN_NUMBER'",
    "seats": ["FC1-1A", "FC1-1B"],
    "travel_date": "'$TRAVEL_DATE'",
    "status": "confirmed"
}'
log "Payload: $seat_reservation_payload"

seat_reservation_response=$(curl -s -X POST ${TRAIN_SEAT_STATUS_SERVICE}/seat-reservations -H "Content-Type: application/json" -d "$seat_reservation_payload")

# Check response for seat reservation
if echo "$seat_reservation_response" | jq . >/dev/null 2>&1; then
    log "${GREEN}Success! Response:${NC}"
    log "$(echo "$seat_reservation_response" | jq .)"
else
    log "${RED}Error: Invalid response${NC}"
    log "$seat_reservation_response"
fi
log ""

# Get seat status for a booking
call_api "GET" "${TRAIN_SEAT_STATUS_SERVICE}/bookings/${TRAIN_BOOKING_ID}/seats/status" "" "Get seat status for booking"

# Cancel the seat reservation
call_api "PUT" "${TRAIN_SEAT_STATUS_SERVICE}/bookings/${TRAIN_BOOKING_ID}/seats/cancel" "" "Cancel seat reservations"

# Cancel a train booking
#call_api "PUT" "${TRAIN_BOOKING_SERVICE}/train-bookings/${TRAIN_BOOKING_ID}/cancel" "" "Cancel train booking"

# Check for canceled bookings
#call_api "GET" "${TRAIN_BOOKING_SERVICE}/train-bookings/search?agent_id=${AGENT_ID}&status=Cancelled" "" "Search for cancelled train bookings"

log "${BLUE}=== Test Complete ===${NC}"
log "All endpoints have been tested."

# Generate HTML report
log "\nGenerating HTML report..."

# Create a basic HTML file from the text output
cat > "$HTML_OUTPUT" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>API Test Results</title>
    <style>
        body {
            font-family: monospace;
            white-space: pre-wrap;
            padding: 20px;
        }
        .header {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .success {
            color: green;
        }
        .error {
            color: red;
        }
        .test {
            color: #AA6600;
        }
        .section {
            color: blue;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
<div class="header">Travel Agent Management System API Test Results</div>
<div class="content">
$(cat "$OUTPUT_FILE" | 
  sed 's/\x1B\[0;32m/<span class="success">/g' | 
  sed 's/\x1B\[0;31m/<span class="error">/g' | 
  sed 's/\x1B\[0;33m/<span class="test">/g' | 
  sed 's/\x1B\[0;34m/<span class="section">/g' | 
  sed 's/\x1B\[0m/<\/span>/g')
</div>
</body>
</html>
EOF

log "${GREEN}HTML report generated successfully: $HTML_OUTPUT${NC}"
log "Text report is available at: $OUTPUT_FILE"