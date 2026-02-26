from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class Ticket_Status(str, Enum):
    OPEN = "open"
    IN_PROCESS = "in_process"
    CLOSED = "closed"

class Ticket_Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Ticket(BaseModel):
    id: int
    title: str
    description: str
    status: Ticket_Status 
    priority: Ticket_Priority
    created_at: datetime
    updated_at: datetime

class Ticket_Create(BaseModel):
    title: str
    description: str
    customer_id: int 
    priority: Ticket_Priority = Ticket_Priority.MEDIUM


app = FastAPI(title="CRM support",
              description="API для тех поддержки",
              version="1.0.0")


@app.get("/")
async def root():
    return ({"message": "CRM работает", "status": "ok"})

