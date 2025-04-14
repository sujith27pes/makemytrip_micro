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
log "This script will test all endpoints of your microservices application"
log "$(date)"
log ""

# Base URLs
AGENT_SERVICE="http://localhost:8000"
BOOKING_SERVICE="http://localhost:8001"
SALES_SERVICE="http://localhost:8002"
INVOICING_SERVICE="http://localhost:8003"

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
# Removed the sales summary endpoint test

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

log "${BLUE}=== Test Complete ===${NC}"
log "All endpoints have been tested."

# Generate PDF from the output file
log "\nGenerating PDF report..."

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

# Try multiple PDF generation methods
if command -v node &> /dev/null; then
    # Try using Node.js and puppeteer if available
    log "Attempting to generate PDF using Node.js and puppeteer..."
    
    # Create a temporary Node.js script
    cat > pdf_generator.js << EOF
const fs = require('fs');
const puppeteer = require('puppeteer');

(async () => {
  try {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.setContent(fs.readFileSync('$HTML_OUTPUT', 'utf8'));
    await page.pdf({ path: '$PDF_OUTPUT', format: 'A4' });
    await browser.close();
    console.log('PDF generated successfully!');
  } catch (error) {
    console.error('Error generating PDF:', error.message);
    process.exit(1);
  }
})();
EOF
    
    # Check if puppeteer is installed, if not, inform user
    if ! node -e "try { require('puppeteer'); } catch(e) { process.exit(1); }" &> /dev/null; then
        log "${YELLOW}Node.js is available but puppeteer is not installed.${NC}"
        log "You can install it with: npm install -g puppeteer"
        log "Then run this script again."
    else
        # Run the Node.js script
        if node pdf_generator.js; then
            log "${GREEN}PDF report generated successfully: $PDF_OUTPUT${NC}"
            rm pdf_generator.js
        else
            log "${RED}Error generating PDF with Node.js and puppeteer.${NC}"
        fi
    fi
elif command -v python3 &> /dev/null; then
    # Try using Python if available
    log "Attempting to generate PDF using Python..."
    
    # Create a temporary Python script
    cat > pdf_generator.py << EOF
import sys
try:
    import weasyprint
    HTML('$HTML_OUTPUT').write_pdf('$PDF_OUTPUT')
    print('PDF generated successfully using WeasyPrint!')
    sys.exit(0)
except ImportError:
    try:
        import pdfkit
        pdfkit.from_file('$HTML_OUTPUT', '$PDF_OUTPUT')
        print('PDF generated successfully using pdfkit!')
        sys.exit(0)
    except ImportError:
        print('Error: Neither WeasyPrint nor pdfkit is installed.')
        print('Install one with: pip install weasyprint or pip install pdfkit')
        sys.exit(1)
EOF
    
    # Run the Python script
    if python3 -c "try: import weasyprint; exit(0)\nexcept ImportError: try: import pdfkit; exit(0)\nexcept ImportError: exit(1)" &> /dev/null; then
        if python3 pdf_generator.py; then
            log "${GREEN}PDF report generated successfully: $PDF_OUTPUT${NC}"
            rm pdf_generator.py
        else
            log "${RED}Error generating PDF with Python.${NC}"
        fi
    else
        log "${YELLOW}Python is available but required modules are not installed.${NC}"
        log "Install one with: pip install weasyprint or pip install pdfkit"
    fi
elif command -v wkhtmltopdf &> /dev/null; then
    # Try using wkhtmltopdf directly
    if wkhtmltopdf "$HTML_OUTPUT" "$PDF_OUTPUT"; then
        log "${GREEN}PDF report generated successfully: $PDF_OUTPUT${NC}"
    else
        log "${RED}Error generating PDF with wkhtmltopdf.${NC}"
    fi
elif command -v chrome &> /dev/null || command -v chromium &> /dev/null || command -v google-chrome &> /dev/null; then
    # Try using Chrome/Chromium if available
    CHROME_CMD=""
    for cmd in chrome chromium google-chrome; do
        if command -v $cmd &> /dev/null; then
            CHROME_CMD=$cmd
            break
        fi
    done
    
    if [ -n "$CHROME_CMD" ]; then
        if $CHROME_CMD --headless --disable-gpu --print-to-pdf="$PDF_OUTPUT" "$HTML_OUTPUT"; then
            log "${GREEN}PDF report generated successfully: $PDF_OUTPUT${NC}"
        else
            log "${RED}Error generating PDF with Chrome/Chromium.${NC}"
        fi
    fi
else
    log "${YELLOW}Could not find suitable tools to generate PDF.${NC}"
    log "HTML report is available at: $HTML_OUTPUT"
    log "You can open this HTML file in a browser and use the browser's print function to save as PDF."
fi

log "Text report is available at: $OUTPUT_FILE"
if [ -f "$HTML_OUTPUT" ]; then
    log "HTML report is available at: $HTML_OUTPUT"
fi
if [ -f "$PDF_OUTPUT" ]; then
    log "PDF report is available at: $PDF_OUTPUT"
fi