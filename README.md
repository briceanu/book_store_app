# 🚀 FastAPI Backend Application

A modern, scalable, and production-ready backend application built with [FastAPI](https://fastapi.tiangolo.com/) featuring:

- JWT authentication with access and refresh tokens
- Token blacklisting using Redis
- Background tasks for sending emails
- PDF generation and email attachment using Celery
- Fine-grained access control using scopes
- Modular architecture with Repository Pattern
- Fully async & production-ready

---

## 📦 Features

✅ **JWT Authentication**
- Secure login system using Access and Refresh tokens  
- Token expiration, renewal, and revocation via Redis-based blacklisting  

✅ **Email System**
- Background tasks to send registration, reset, or alert emails using FastAPI's background tasks  
- Celery integration for heavy-lifting tasks like PDF generation and email attachment  

✅ **Permissions & Scopes**
- Role-based access using JWT scopes for fine-grained authorization  
- Supports multi-scope access control per endpoint

✅ **Repository Pattern**
- Clear separation of concerns between database logic and business logic  
- Easily testable and maintainable service layer

✅ **CRUD Operations**
- Fully functional endpoints with Create, Read, Update, Delete capabilities  
- Extendable to new models with minimal boilerplate

✅ **Tech Stack**
- **FastAPI**
- **SQLAlchemy / async ORM**
- **Redis** for token blacklist
- **Celery + Redis** for background workers
- **PostgreSQL** or SQLite (configurable)
- **Pydantic** for data validation

---

## 🛠️ Installation

1. **Clone the repo**
```bash
git clone https://github.com/yourusername/your-fastapi-app.git
cd your-fastapi-app
