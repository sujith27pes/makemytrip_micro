# Travel Agent Management System

A microservices-based application for managing travel agents, bookings, sales, and invoicing. This system allows travel agencies to efficiently manage their agents' information, track bookings and commissions, record sales, and process payouts.

## 🏗️ Architecture

The system consists of four microservices:

1. **Agent Service** (Port 8000): Manages travel agent profiles and availability
2. **Booking Service** (Port 8001): Handles customer bookings and agent commissions
3. **Sales Service** (Port 8002): Tracks sales data and provides trend analysis
4. **Invoicing Service** (Port 8003): Processes invoices and agent payouts

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

## 🛠️ Technologies

- **Backend**: FastAPI (Python)
- **Containerization**: Docker
- **Service Orchestration**: Docker Compose
- **Testing**: Shell scripting with curl and jq

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- jq (for testing script)

## 🚀 Getting Started

### Installation and Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/travel-agent-management.git
   cd travel-agent-management
   ```

2. Build and start the services:
   ```bash
   docker-compose up -d --build
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

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🔮 Future Enhancements

- Add user authentication and authorization
- Implement persistent database storage
- Create a web frontend for easier management
- Add reporting and analytics features
- Implement notification system for agents
