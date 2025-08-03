🚀 FastAPI Backend Application
A modern, scalable, and production-ready backend application built with FastAPI featuring:

JWT authentication with access and refresh tokens

Token blacklisting using Redis

Background tasks for sending emails

PDF generation and email attachment using Celery

Fine-grained access control using scopes

Modular architecture with Repository Pattern

Fully async & production-ready

Docker deployment support

Basic XSS protection measures

📦 Features
✅ JWT Authentication
Secure login system using Access and Refresh tokens

Token expiration, renewal, and revocation via Redis-based blacklisting

✅ Email System
Background tasks to send registration, reset, or alert emails using FastAPI's background tasks

Celery integration for heavy-lifting tasks like PDF generation and email attachment

✅ Permissions & Scopes
Role-based access using JWT scopes for fine-grained authorization

Supports multi-scope access control per endpoint

✅ Repository Pattern
Clear separation of concerns between database logic and business logic

Easily testable and maintainable service layer

✅ CRUD Operations
Fully functional endpoints with Create, Read, Update, Delete capabilities

Extendable to new models with minimal boilerplate

✅ Tech Stack
FastAPI

SQLAlchemy / async ORM

Redis for token blacklist

Celery + Redis for background workers

PostgreSQL or SQLite (configurable)

Pydantic for data validation

Docker and Docker Compose for containerization


🛠️ Production Deployment with AWS Managed Services
Replace local Redis and Postgres containers with AWS services
Service	Local Docker Container	Production AWS Service
Redis	redis:7.2.10 Docker image	AWS ElastiCache Redis cluster endpoint
Postgres	postgres Docker image	AWS RDS PostgreSQL instance endpoint
Email Server	SMTP port 587 (blocked by AWS)	AWS Simple Email Service (SES) via API or SMTP on allowed ports
