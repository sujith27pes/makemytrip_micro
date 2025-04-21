# Travel Agent Management System

A comprehensive microservices-based application for managing travel agents, bookings, sales, and invoicing. This system allows travel agencies to efficiently manage their agents' information, track bookings and commissions, record sales, process payouts, and handle train bookings with seat management.

## 🏗️ Architecture

The system consists of six integrated microservices:

1. **Agent Service** (Port 8000): Manages travel agent profiles and availability
2. **Booking Service** (Port 8001): Handles customer bookings and agent commissions
3. **Sales Service** (Port 8002): Tracks sales data and provides trend analysis
4. **Invoicing Service** (Port 8003): Processes invoices and agent payouts
5. **Train Booking Service** (Port 8084): Manages train bookings, information, and pricing
6. **Train Seat Status Service** (Port 8090): Tracks seat reservations and status

## 🚀 Features

- **Agent Management**
  - Create, update, and delete agent profiles
  - Manage agent availability by days and shifts
  - Track agent performance ratings

- **Booking System**
  - Create bookings linked to specific agents
  - Automatically calculate agent commissions
  - View bookings by agent

- **Sales Tracking**
  - Record sales transactions
  - View sales data by agent
  - Analyze sales trends

- **Invoicing & Payouts**
  - Generate customer invoices
  - Process agent commission payouts
  - Track payout history

- **Train Booking System**
  - Browse available trains with routes and timings
  - Book train tickets with multiple passenger support
  - Select train class with automatic pricing
  - Track and manage bookings by agent
    

- **Train Seat Management**
  - Track seat status for bookings
  - Handle seat reservation confirmations
  - Process seat cancellations

## 🛠️ Technologies

- **Backend**: FastAPI (Python)
- **Containerization**: Docker
- **Service Orchestration**: Docker Compose
- **Service Communication**: httpx
- **Testing**: Shell scripting with curl and jq
- **Documentation**: Markdown

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- jq (for testing script)

## 🚀 Getting Started

### Installation and Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/sujith27pes/makemytrip_micro.git
   cd makemytrip_micro
   ```

2. Build and start the services:
   ```bash
   docker-compose up --build
   ```

3. Verify all services are running:
   ```bash
   docker-compose ps
   ```

### Testing the API

Run the provided test script to verify all endpoints are working correctly:

```bash
chmod +x test_endpoints.sh
./test_endpoints.sh
```

This will generate:
- A text report (`api_test_results.txt`)
- An HTML report (`api_test_results.html`)
- A PDF report if the required dependencies are installed

## 📚 API Documentation

### Agent Service (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | POST | Create a new agent |
| `/agents` | GET | List all agents |
| `/agents/{agent_id}` | GET | Get agent details |
| `/agents/{agent_id}` | PUT | Update agent information |
| `/agents/{agent_id}` | DELETE | Delete an agent |
| `/agents/{agent_id}/availability` | GET | Get agent availability |
| `/agents/{agent_id}/availability` | PUT | Update agent availability |

### Booking Service (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bookings` | POST | Create a new booking |
| `/agents/{agent_id}/bookings` | GET | Get agent's bookings |
| `/agents/{agent_id}/commission` | GET | Get agent's commission details |

### Sales Service (Port 8002)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sales/record` | POST | Record a new sale |
| `/sales/by-agent/{agent_id}` | GET | Get sales by agent |
| `/sales/trends` | GET | Get sales trend analysis |

### Invoicing Service (Port 8003)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/invoice` | POST | Generate a new invoice |
| `/payout` | POST | Process agent payout |
| `/agents/{agent_id}/payouts` | GET | Get agent's payout history |

### Train Booking Service (Port 8084)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/trains` | GET | List all available trains |
| `/trains/{train_number}` | GET | Get details of a specific train |
| `/train-bookings` | POST | Create a new train booking |
| `/train-bookings` | GET | List all train bookings |
| `/train-bookings/{booking_id}` | GET | Get details of a specific train booking |
| `/agents/{agent_id}/train-bookings` | GET | Get all train bookings for a specific agent |



### Train Seat Status Service (Port 8090)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bookings/{booking_id}/seats/status` | GET | Check seat status for a booking |
| `/bookings/{booking_id}/seats/cancel` | PUT | Cancel seat reservations for a booking |


## 📊 Data Models

### Agent

```json
{
  "id": "UUID",
  "name": "string",
  "email": "string",
  "phone": "string",
  "rating": "float (optional)",
  "availability": {
    "days": ["string"],
    "shift": "string"
  }
}
```

### Booking

```json
{
  "agent_id": "UUID",
  "customer_name": "string",
  "service_type": "string",
  "price": "float"
}
```

### Commission

```json
{
  "agent_id": "UUID",
  "booking_id": "UUID",
  "commission_percentage": "float",
  "commission_amount": "float"
}
```

### Invoice

```json
{
  "agent_id": "UUID",
  "customer_name": "string",
  "amount": "float"
}
```

### Payout

```json
{
  "agent_id": "UUID",
  "payout_amount": "float"
}
```

### Train

```json
{
  "train_number": "string",
  "name": "string",
  "source": "string",
  "destination": "string",
  "departure_time": "string",
  "arrival_time": "string",
  "available_classes": ["string"],
  "base_price": {
    "class_name": "float"
  }
}
```

### TrainBooking

```json
{
  "booking_id": "UUID",
  "agent_id": "UUID",
  "train_number": "string",
  "train_name": "string",
  "source": "string",
  "destination": "string",
  "travel_date": "string",
  "departure_time": "string",
  "arrival_time": "string",
  "train_class": "string",
  "price_per_passenger": "float",
  "total_price": "float",
  "passenger_count": "integer",
  "passengers": [
    {
      "name": "string",
      "age": "integer",
      "id_type": "string",
      "id_number": "string"
    }
  ],
  "special_requests": "string (optional)",
  "booking_date": "string",
  "status": "string"
}
```

### SeatStatus

```json
{
  "booking_id": "UUID",
  "train_number": "string",
  "seats": ["string"],
  "travel_date": "string",
  "status": "string"
}
```

## 🔄 Service Integration

The Travel Agent Management System uses a microservices architecture with the following integration points:

- **Agent Service**: Core service for agent management
- **Booking Service**: Integrates with Agent Service to validate agents
- **Train Booking Service**: Integrates with both Agent Service and Booking Service
- **Train Seat Status Service**: Integrates with Train Booking Service
- **Sales Service**: Records sales data from bookings
- **Invoicing Service**: Processes invoices based on booking data

The services communicate via RESTful APIs using httpx, with Docker Compose providing service discovery and networking.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

