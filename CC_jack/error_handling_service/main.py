from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
import httpx
import asyncio
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Error Handling Service")

# Service registry - will be populated dynamically
service_registry = {
    "agent_service": "http://agent_service:8000",
    "booking_service": "http://booking_service:8001",
    "sales_service": "http://sales_service:8002",
    "invoicing_service": "http://invoicing_service:8003",
    "train_booking_service": "http://train_booking_service:8084",
    "train_seat_status_service": "http://train_seat_status_service:8090",
}

# Health status tracking
health_status = {}

# Error history
error_history = []

# Models
class ServiceStatus(BaseModel):
    service_name: str
    status: str  # "up", "down", "degraded"
    last_checked: str
    response_time: float  # in milliseconds
    endpoint: str

class ErrorLog(BaseModel):
    timestamp: str
    service_name: str
    endpoint: str
    status_code: int
    error_message: str
    request_details: Optional[Dict] = None

class ProxyRequest(BaseModel):
    target_service: str
    endpoint: str
    method: str
    data: Optional[Dict] = None
    headers: Optional[Dict] = None

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "message": str(e)}
        )

# Health check endpoints
@app.get("/health", response_model=Dict[str, ServiceStatus])
async def get_all_services_health():
    """Get health status of all registered services"""
    await check_all_services_health()
    return health_status

@app.get("/health/{service_name}", response_model=ServiceStatus)
async def get_service_health(service_name: str):
    """Get health status of a specific service"""
    if service_name not in service_registry:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Service '{service_name}' not found in registry"}
        )
        
    await check_service_health(service_name, service_registry[service_name])
    return health_status.get(service_name)

async def check_service_health(service_name: str, service_url: str):
    """Check health of a specific service"""
    health_endpoint = f"{service_url}/"
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(health_endpoint)
            
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        status = "up" if response.status_code < 300 else "degraded"
        
        health_status[service_name] = ServiceStatus(
            service_name=service_name,
            status=status,
            last_checked=datetime.now().isoformat(),
            response_time=response_time,
            endpoint=health_endpoint
        )
    except Exception as e:
        health_status[service_name] = ServiceStatus(
            service_name=service_name,
            status="down",
            last_checked=datetime.now().isoformat(),
            response_time=0,
            endpoint=health_endpoint
        )
        
        # Log the error
        log_error(
            service_name=service_name,
            endpoint=health_endpoint,
            status_code=503,
            error_message=str(e)
        )

async def check_all_services_health():
    """Check health of all registered services"""
    tasks = []
    for service_name, service_url in service_registry.items():
        tasks.append(check_service_health(service_name, service_url))
    
    await asyncio.gather(*tasks)

# Error logging and reporting
@app.get("/errors", response_model=List[ErrorLog])
async def get_error_history(limit: int = 50):
    """Get recent error history with limit"""
    return error_history[-limit:] if len(error_history) > limit else error_history

@app.get("/errors/{service_name}", response_model=List[ErrorLog])
async def get_service_errors(service_name: str):
    """Get errors for a specific service"""
    if service_name not in service_registry:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Service '{service_name}' not found in registry"}
        )
        
    service_errors = [error for error in error_history if error.service_name == service_name]
    return service_errors

def log_error(service_name: str, endpoint: str, status_code: int, error_message: str, request_details: Dict = None):
    """Log an error to the error history"""
    error = ErrorLog(
        timestamp=datetime.now().isoformat(),
        service_name=service_name,
        endpoint=endpoint,
        status_code=status_code,
        error_message=error_message,
        request_details=request_details
    )
    error_history.append(error)
    logger.error(f"Service Error: {service_name} - {endpoint} - {status_code} - {error_message}")
    return error

# Service proxy - allows making requests through this service for monitoring
@app.post("/proxy")
async def proxy_request(request: ProxyRequest):
    """Proxy a request to another service with error handling"""
    if request.target_service not in service_registry:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Service '{request.target_service}' not found in registry"}
        )
    
    service_url = service_registry[request.target_service]
    endpoint = request.endpoint.lstrip("/")  # Remove leading slash if present
    full_url = f"{service_url}/{endpoint}"
    
    request_details = {
        "method": request.method,
        "url": full_url,
        "data": request.data,
        "headers": request.headers
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if request.method.lower() == "get":
                response = await client.get(
                    full_url, 
                    params=request.data,
                    headers=request.headers
                )
            elif request.method.lower() == "post":
                response = await client.post(
                    full_url, 
                    json=request.data,
                    headers=request.headers
                )
            elif request.method.lower() == "put":
                response = await client.put(
                    full_url, 
                    json=request.data,
                    headers=request.headers
                )
            elif request.method.lower() == "delete":
                response = await client.delete(
                    full_url, 
                    params=request.data,
                    headers=request.headers
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Unsupported method: {request.method}"}
                )
                
        # Return the response data and status code
        if response.status_code >= 400:
            # Log error for non-success responses
            log_error(
                service_name=request.target_service,
                endpoint=endpoint,
                status_code=response.status_code,
                error_message=str(response.text),
                request_details=request_details
            )
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "data": response.json() if response.headers.get("content-type") == "application/json" else response.text,
            "service": request.target_service
        }
    except httpx.RequestError as e:
        error_message = f"Request to {request.target_service} failed: {str(e)}"
        
        # Log the error
        error = log_error(
            service_name=request.target_service,
            endpoint=endpoint,
            status_code=503,
            error_message=error_message,
            request_details=request_details
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Service Unavailable",
                "message": error_message,
                "error_id": len(error_history) - 1  # Reference to the error in the history
            }
        )
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        
        # Log the error
        error = log_error(
            service_name=request.target_service,
            endpoint=endpoint,
            status_code=500,
            error_message=error_message,
            request_details=request_details
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "message": error_message,
                "error_id": len(error_history) - 1
            }
        )

# Service registry management
@app.get("/registry")
async def get_service_registry():
    """Get the current service registry"""
    return service_registry

@app.post("/registry/{service_name}")
async def register_service(service_name: str, url: str):
    """Register a new service or update existing one"""
    service_registry[service_name] = url
    return {"message": f"Service '{service_name}' registered at {url}"}

@app.delete("/registry/{service_name}")
async def deregister_service(service_name: str):
    """Remove a service from the registry"""
    if service_name in service_registry:
        del service_registry[service_name]
        return {"message": f"Service '{service_name}' deregistered"}
    return JSONResponse(
        status_code=404,
        content={"detail": f"Service '{service_name}' not found in registry"}
    )

# Background task to check service health periodically
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_health_check())

async def periodic_health_check():
    """Periodically check the health of all services"""
    while True:
        await check_all_services_health()
        await asyncio.sleep(30)  # Check every 30 seconds
