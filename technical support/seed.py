import asyncio
from sqlalchemy import select

from app.database import new_session, engine, Base
from app.models import Ticket_Model, Ticket_Status, Ticket_Priority, User_Model, User_Role
from app.security import get_password_hash

TICKETS = [
    {
        "title" : "Не работает VPN",
        "description" : "Пытаюсь подключиться к сайту, не получается",
        "priority" : Ticket_Priority.MEDIUM,
        "status" : Ticket_Status.OPEN
    },

    {
        "title" : "Неn подключения к интернету",
        "description" : "На роуторе горит две лампочки из трех, одна красная, другая зеленая",
        "priority" : Ticket_Priority.HIGH,
        "status" : Ticket_Status.OPEN
    },

    {
        "title" : "Поломка монитора",
        "description" : "На мониторе мерцающие полосы, слышен треск",
        "priority" : Ticket_Priority.HIGH,
        "status" : Ticket_Status.OPEN
    },

    {
        "title" : "Медленая загрузка сайта",
        "description" : "Сайт грузиться по одной минуте",
        "priority" : Ticket_Priority.LOW,
        "status" : Ticket_Status.IN_PROCESS
    },

    {
        "title" : "Ошибка 500 на сайте",
        "description" : "При оформлении заказа вылетает Internal Server Error.",
        "priority" : Ticket_Priority.HIGH,
        "status" : Ticket_Status.IN_PROCESS
    },

    {
        "title" : "Не работает сервер",
        "description" : "Сервер не подает сигналов жизни",
        "priority" : Ticket_Priority.HIGH,
        "status" : Ticket_Status.CLOSED
    },

    {
        "title" : "Нет прав доступа",
        "description" : "При подключении выдает ошибку с правами доступа",
        "priority" : Ticket_Priority.MEDIUM,
        "status" : Ticket_Status.IN_PROCESS
    },

    {
        "title" : "Не работает кондиционер",
        "description" : "Кондиционер страно работает, охлаждает, но плохо (сейчас зима)",
        "priority" : Ticket_Priority.LOW,
        "status" : Ticket_Status.IN_PROCESS
    },
]

async def seed_data():

    print("Заполение БД")

    async with new_session() as session:

        query = select(User_Model).where(User_Model.login == "admin")
        result = await session.execute(query)
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User_Model(
                login="admin",
                email="supesu@ntc.com",
                password_hash=get_password_hash("Admin123"),
                role=User_Role.ADMIN
            )
            session.add(admin)
            await session.flush()

        admin_id = admin.id

        ticket_check = await session.execute(select(Ticket_Model).limit(1))
        if ticket_check.scalar_one_or_none():
            print("Тикеты уже есть в базе, пропускаем заполнение.")
        else:
            for ticket_data in TICKETS:
                ticket = Ticket_Model(
                    title = ticket_data["title"],
                    description = ticket_data["description"],
                    priority = ticket_data["priority"],
                    status = ticket_data["status"],
                    owner_id = admin_id
                )
                session.add(ticket)
            print(f"Добавлено {len(TICKETS)} стартовых тикотов")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_data())
