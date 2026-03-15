from fastapi import FastAPI, Depends, HTTPException, WebSocket, Query, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_ 
from contextlib import asynccontextmanager
from jose import JWTError, jwt

from .database import get_db, engine, Base
from .models import Ticket_Priority, Ticket_Status, Ticket_Model
from .models import User_Role, User_Model
from .security import get_password_hash, verify_password,create_access_token
from .security import SECRET_KEY, ALGORITHM
from .chat_manager import manager

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
    login: str = Field(...,min_length=3, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str= Field(..., min_length=8)
    role: User_Role = User_Role.USER 

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str):
        if not any(char.isdigit() for char in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not any(char.isupper() for char in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        return v
    
class User(BaseModel):
    id: int
    login: str
    email: str
    role: User_Role
    created_at : datetime

    class Config:
        from_attributes = True

class User_Role_Update(BaseModel):
    new_role: User_Role

class Token(BaseModel):
    access_token: str
    token_type: str

# проверка токена для websocket
async def get_current_user_wb(token:str, db:AsyncSession):
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=ALGORITHM)
        login: str = payload.get("sub")
        if login is None:
            return None
    except JWTError:
        return None

    query = select(User_Model).where(User_Model.login==login)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return user

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="CRM support",
              description="**API для тех поддержки**",
              version="1.0.2",
              lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# подключение папки со статикой
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# функция для получения пользователя
async def get_current_user(token: str = Depends(oauth2_scheme),
                           db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Не удалось валидировать токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    query = select(User_Model).where(User_Model.login == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

# проверка статуса
@app.get("/")
async def read_index():
    return FileResponse("app/static/index.html")

# create user
@app.post("/register", response_model=User, tags=["Auth"])
async def  register_user(user_data: User_Create, db: AsyncSession = Depends(get_db)):
    query = select(User_Model).where(or_(User_Model.email == user_data.email,
                                        User_Model.login == user_data.login)
                                        )
    
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с такой почтой или логином уже существует")

    hashed_password = get_password_hash(user_data.password)

    new_user = User_Model(login = user_data.login,
                          email = user_data.email,
                          password_hash = hashed_password,
                          role = User_Role.USER)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

# login
@app.post("/token", response_model=Token, tags=["Auth"])
async def login_for_accsess_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                  db: AsyncSession=Depends(get_db)):
    query = select(User_Model).where(User_Model.login == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user.password_hash, form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.login, "role": user.role})
    
    return {"access_token": access_token, "token_type": "bearer"}

# create ticket
@app.post("/tickets",response_model=Ticket, tags=["Tickets"])
async def create_ticket(ticket_data: Ticket_Create, db: AsyncSession = Depends(get_db), current_user: User_Model = Depends(get_current_user)):
    
    new_ticket = Ticket_Model(title = ticket_data.title,
                              description = ticket_data.description,
                              priority =ticket_data.priority,
                              owner_id = current_user.id)
    
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    return new_ticket

# read tickets (limit)
@app.get("/tickets", response_model=List[Ticket], tags=["Tickets"])
async def get_tickets(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user: User_Model= Depends(get_current_user)):
    if current_user.role == User_Role.ADMIN or current_user.role == User_Role.MODERATOR:
        query = select(Ticket_Model).offset(skip).limit(limit)
    else:
        query = select(Ticket_Model).where(Ticket_Model.owner_id == current_user.id).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

# read one ticket (id)
@app.get("/tickets/{ticket_id}", response_model= Ticket, tags=["Tickets"])
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db), current_user: User_Model= Depends(get_current_user)):
    if current_user.role == User_Role.ADMIN or current_user.role == User_Role.MODERATOR:
        query = select(Ticket_Model).where(Ticket_Model.id==ticket_id)
    else:
        query = select(Ticket_Model).where(Ticket_Model.owner_id == current_user.id, Ticket_Model.id==ticket_id)
    
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket не был найден или у вас не хватает прав доступа")
    return ticket

# read users (limit)
@app.get("/users", response_model=List[User], tags=["Users"])
async def get_users(skip: int = 0, limit: int = 50,  db: AsyncSession = Depends(get_db), current_user: User_Model= Depends(get_current_user)):
    if current_user.role != User_Role.ADMIN and current_user.role != User_Role.MODERATOR:
        raise HTTPException(status_code=403, detail="Нет доступа для просмотра")
    
    result = await db.execute(select(User_Model).offset(skip).limit(limit))
    return result.scalars().all()

# read user (login)
@app.get("/users/{user_login}", response_model=User, tags=['Users'])
async def get_user(user_login: str, db: AsyncSession = Depends(get_db), current_user: User_Model= Depends(get_current_user)):
    if current_user.role != User_Role.ADMIN and current_user.role != User_Role.MODERATOR:
        raise HTTPException(status_code=403, detail="Нет доступа для просмотра")
    
    result = await db.execute(select(User_Model).where(User_Model.login == user_login))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# update ticket (id)
@app.patch("/tickets/{ticket_id}", response_model=Ticket, tags=["Tickets"])
async def update_ticket(ticket_id: int, ticket_update: Ticket_Update, db: AsyncSession = Depends(get_db),  current_user: User_Model = Depends(get_current_user)):
    query = select(Ticket_Model).where(Ticket_Model.id==ticket_id,
                                        Ticket_Model.status != Ticket_Status.CLOSED)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Тикет не найден или закрыт")
    
    if current_user.role!= User_Role.ADMIN and current_user.role!= User_Role.MODERATOR and ticket.owner_id != current_user.id :
        raise HTTPException(status_code=403, detail="Нет доступа для изменения") 

    update_data = ticket_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(ticket, key, value) 

    await db.commit()
    await db.refresh(ticket)
    return ticket

# update role (login)
@app.patch("/users/{target_login}/role", response_model=User, tags=["Users"])
async def change_user_role(target_login: str, role_data: User_Role_Update,
                           db: AsyncSession = Depends(get_db), current_user: User_Model = Depends(get_current_user)):
    if current_user.role != User_Role.ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Нет доступа для изменения роли."
        )
    
    query = select(User_Model).where(User_Model.login == target_login)
    result = await db.execute(query)
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    target_user.role = role_data.new_role
    await db.commit()
    await db.refresh(target_user)
    
    return target_user

# delete user (login)
@app.delete("/users/{user_login}", tags=["Users"])
async def delete_user(user_login: str, db:AsyncSession = Depends(get_db), current_user: User_Model = Depends(get_current_user)):
    if current_user.role != User_Role.ADMIN and current_user.role != User_Role.MODERATOR :
        raise HTTPException(status_code=403, detail="Нет доступа для изменения")
    
    query = select(User_Model).where(User_Model.login == user_login)
    result = await db.execute(query)

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="пользователь не найден")
    
    await db.delete(user)
    await db.commit()

    return {"message": "Пользователь успешно удален", "login": user_login}

# delete ticket (id)
@app.delete("/tickets/{ticket_id}", tags=["Tickets"])
async def delete_ticket(ticket_id: int, db: AsyncSession = Depends(get_db), current_user: User_Model = Depends(get_current_user)):
    
    query = select(Ticket_Model).where(Ticket_Model.id == ticket_id)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    
    is_admin_or_mod = current_user.role in [User_Role.ADMIN, User_Role.MODERATOR]
    is_owner = ticket.owner_id == current_user.id

    if not (is_admin_or_mod or is_owner):
        raise HTTPException(status_code=403, detail="У вас нет прав на удаление этого тикета")

    await db.delete(ticket)
    await db.commit()

    return {"message": "Тикет успешно удален", "id": ticket_id}

# websocket
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    user = await get_current_user_wb(token, db)

    if user is None:
        await websocket.close(code=1008) 
        return
    
    await manager.connect(websocket)

    await manager.broadcast({
        "type": "system",
        "message": f"📢 {user.login} вошел в чат",
        "count": manager.get_count()
    })

    try:
        while True:
            data = await websocket.receive_text()
            
            await manager.broadcast({
                "type": "user",
                "sender": user.login,
                "message": data,
                "count": manager.get_count()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast({
            "type": "system",
            "message": f"🚪 {user.login} покинул чат",
            "count": manager.get_count()
        })


# uvicorn app.main:app --reload -- запуск