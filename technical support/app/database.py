from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

data_base_url = "postgresql+asyncpg://postgres:1234@localhost:5432/crm_db"

engine = create_async_engine(data_base_url, echo = True) # echo - для логирования

new_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with new_session() as session:
        yield session