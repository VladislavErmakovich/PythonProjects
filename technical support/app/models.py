from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, func
from datetime import datetime
from enum import Enum
from .database import Base

class Ticket_Status(str, Enum):
    OPEN = "open"
    IN_PROCESS = "in_process"
    CLOSED = "closed"

class Ticket_Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class User_Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

class User_Model(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index = True)
    login: Mapped[str] = mapped_column(String, unique=True, index = True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)

    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[User_Role] = mapped_column(default=User_Role.USER)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Ticket_Model(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)

    status: Mapped[Ticket_Status] = mapped_column(default=Ticket_Status.OPEN)
    priority: Mapped[Ticket_Priority] = mapped_column(default=Ticket_Priority.MEDIUM)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

