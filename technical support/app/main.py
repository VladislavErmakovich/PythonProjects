from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager

from .database import get_db, engine, Base
from .models import Ticket_Priority, Ticket_Status, Ticket_Model
from .models import User_Role, User_Model
from .security import get_password_hash

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

class User_Create(BaseModel):
    login: str
    email: str
    password: str
    role: User_Role = User_Role.USER 

class User(BaseModel):
    id: int
    login: str
    email: str
    role: User_Role
    created_at : datetime

    class Config:
        from_attributes = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="CRM support",
              description="API для тех поддержки",
              version="1.0.2",
              lifespan=lifespan)

# проверка статуса
@app.get("/")
async def root():
    return ({"message": "CRM работает", "status": "ok"})

# create user
@app.post("/register", response_model=User, tags=["Auth"])
async def  register_user(user_data: User_Create, db: AsyncSession = Depends(get_db)):
    query = select(User_Model).where(User_Model.email == user_data.email or User_Model.login == user_data.login)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user is None:
        raise HTTPException(status_code=400, detail="Пользователь с такой почтой уже существует")

    hashed_password = get_password_hash(user_data.password)

    new_user = User_Model(login = user_data.login,
                          email = user_data.email,
                          password_hash = hashed_password,
                          role = user_data.role)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

# create ticket
@app.post("/tickets",response_model=Ticket, tags=["Tickets"])
async def create_ticket(ticket_data: Ticket_Create, db: AsyncSession = Depends(get_db)):
    
    new_ticket = Ticket_Model(title = ticket_data.title,
                              description = ticket_data.description,
                              priority =ticket_data.priority)
    
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    return new_ticket

# read tickets (limit)
@app.get("/tickets", response_model=List[Ticket], tags=["Tickets"])
async def get_tickets(skip: int = 0, limit: int = 50, db: AsyncSession= Depends(get_db)):
    result = await db.execute(select(Ticket_Model).offset(skip).limit(limit))
    return result.scalars().all()

# read one ticket (id)
@app.get("/tickets/{ticket_id}", response_model= Ticket, tags=["Tickets"])
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket_Model).where(Ticket_Model.id==ticket_id))
    ticket = result.scalar_one_or_none()
    
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

# read users (limit)
@app.get("/user", response_model=List[User], tags=["Users"])
async def get_users(skip: int = 0, limit: int = 100,  db: AsyncSession = Depends(get_password_hash)):
    result = await db.execute(select(User_Model).offset(skip).limit(50))
    return result.scalars().all()

# read user ()

# update ticket (id)
@app.patch("/tickets/{ticket_id}", response_model=Ticket, tags=["Tickets"])
async def update_ticket(ticket_id: int, ticket_update: Ticket_Update, db: AsyncSession = Depends(get_db)):
    query = select(Ticket_Model).where(Ticket_Model.id==ticket_id and Ticket_Model.status != Ticket_Status.CLOSED)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Тикет не найден или закрыт")
    
    update_data = ticket_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(ticket, key, value) 

    await db.commit()
    await db.refresh(ticket)
    return ticket

# delete ticket (id)
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