from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
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

class Ticket_Update(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Ticket_Priority] = None
    status: Optional[Ticket_Status] = None

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

# проверка статуса
@app.get("/")
async def root():
    return ({"message": "CRM работает", "status": "ok"})

# create
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

# read one
@app.get("/tickets", response_model=List[Ticket], tags=["Tickets"])
async def get_tickets(skip: int = 0,
                        limit: int = 100,
                        db: AsyncSession= Depends(get_db)):
    
    result = await db.execute(select(Ticket_Model).offset(skip).limit(limit))
    return result.scalars().all()

# read one
@app.get("/tickets/{ticket_id}", response_model= Ticket, tags=["Tickets"])
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket_Model).where(Ticket_Model.id==ticket_id))
    ticket = result.scalar_one_or_none()
    
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

# update
@app.patch("/tickets/{ticket_id}", response_model=Ticket, tags=["Tickets"])
async def update_ticket(ticket_id: int, ticket_update: Ticket_Update, db: AsyncSession = Depends(get_db)):
    query = select(Ticket_Model).where(Ticket_Model.id==ticket_id)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    
    update_data = ticket_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(ticket, key, value) 

    await db.commit()
    await db.refresh(ticket)
    return ticket

# delete
@app.delete("/tickets/{ticket_id}", tags=["Tickets"])
async def delete_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Ticket_Model).where(Ticket_Model.id == ticket_id)
    result = await db.execute(query)

    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    
    await db.delete(ticket)
    await db.commit()

    return {"message": "Тикет успешно удален", "id": ticket_id}



# uvicorn app.main:app --reload -- запуск