# CRM 

**Краткое описание:** данный проект представляет собой сервис технической поддержки с системой тикетов, ролевой моделью и чатом для пользователей.  

## Стек
**Язык:** Python 3.10
*   **Web Framework:** FastAPI (Asynchronous)
*   **Database:** PostgreSQL 15
*   **ORM:** SQLAlchemy (asyncpg)
*   **Validation:** Pydantic v2 (JSON Serialization/Deserialization)
*   **Real-time:** WebSockets (Chat system)
*   **Auth:** JWT (Access Tokens) + Passlib (Bcrypt hashing)
*   **Infrastructure:** Docker & Docker Compose

## Роли в проекте

В данном проекте выделяется три роли: **admin**, **moderator** и **user**. В таблице с низу описан функционал ролей, а также логин и пароль для проверки их работоспособности.

 Роль | Логин | Пароль | Описание |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin123` | Полный доступ (CRUD пользователей, тикетов, управление ролями) |
| **Moderator** | `moder` | `Moder123` | Управление тикетами, просмотр(удаление) пользователей |
| **User** | *(регистрация)* | — | Может создавать тикеты, изменять и просматривать только свои |

## Запуск и тестирование проекта

1. Склонировать репзиторий через ```git clone```
2. Перейдя в папку проекта пропишите в консоль ```docker-compose up --build```
3. Для тестирования CRUD зайдите в Swagger UI в браузере по http://localhost:8000/docs
4. Для тестирования чата зайдите в браузере по http://localhost:8000/

