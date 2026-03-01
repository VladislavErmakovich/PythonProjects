from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager

from .database import get_db, engine, Base
from .models import Ticket_Priority, Ticket_Status, Ticket_Model

class Ticket_Base(BaseModel):
    title: str
    description: str
    priority: Ticket_Priority = Ticket_Priority.MEDIUM

class Ticket_Create(Ticket_Base):
    pass 

class Ticket(Ticket_Base):
    id: int
    status: Ticket_Status  
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Старт работы")
    yield
    print("Прекращение работы")

app = FastAPI(title="CRM support",
              description="API для тех поддержки",
              version="1.0.1",
              lifespan=lifespan)

@app.get("/")
async def root():
    return ({"message": "CRM работает", "status": "ok"})

@app.post("/tickets",response_model=Ticket, tags=["Tickets"])
async def create_ticket(ticket_data: Ticket_Create,
                         db: AsyncSession =Depends(get_db)):
    
    new_ticket = Ticket_Model(title = ticket_data.title,
                              description = ticket_data.description,
                              priority =ticket_data.priority)
    
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    return new_ticket

@app.get("/tickets", response_model=List[Ticket], tags=["Tickets"])
async def get_tickets(skip: int = 0,
                        limit: int = 100,
                        db: AsyncSession= Depends(get_db)):
    
    result = await db.execute(select(Ticket_Model).offset(skip).limit(limit))
    return result.scalars().all()

@app.get("/tickets/{ticket_id}", response_model= Ticket, tags=["Tickets"])
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket_Model).where(Ticket_Model.id==ticket_id))
    ticket = result.scalar_one_or_none()
    
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

    