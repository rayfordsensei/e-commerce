# E-Commerce Backend API

A lightweight, asynchronous **RESTful** e-commerce backend API built with:

- **Python 3.12**
- **Falcon 4.0.2** for the ASGI web framework
- **SQLAlchemy 2.0** for ORM
- **SQLite** (via **aiosqlite**)
- **Alembic** for database migrations
- **Uvicorn** as the ASGI server
- **joserfc** for JWT handling and authentication
- **Loguru** for structured logging
- **Pydantic Settings** for configuration management

## Features

- **User Management**: Register, list, retrieve, and delete users
- **Product Management**: Create, list, retrieve, update, and delete products
- **Order Management**: Create, list, retrieve, update, and delete orders
- **JWT-Based Authentication**: Secure endpoints with JWT tokens issued via `/login`
- **Request Logging**: Middleware to log incoming requests and outgoing responses with request IDs
- **ASGI Lifespan**: Middleware to initialize and dispose database connections on startup/shutdown

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) project manager
- SQLite

## Quick Start

1. **Install dependencies**:

   ```bash
   uv sync
   ```

2. **Configure environment**:

   Create a `.env` file in the project root based on `.env.example`:

   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key
   SQLITE_URI=sqlite+aiosqlite:///ecommerce.db
   ALEMBIC_URI=sqlite:///ecommerce.db
   ```

3. **Apply database migrations**:

   ```bash
   alembic upgrade head
   ```

4. **Run the application**:

   ```bash
   uvicorn asgi:application
   ```

5. **Access the API endpoints** at:
   _All endpoints (except `/login`) require an `Authorization: Bearer <token>` header._

   - `POST /login` – Obtain a JWT (`{"username": "...", "password": "..."}`)
   - `POST /users` – Register a new user
   - `GET /users` - List all users
   - `GET /users/{id}` - Retrieve a user by ID
   - `DELETE /users/{id}` - Delete a user (fails if they have existing orders)
   - `POST /products` – Create a product
   - `GET /products` - List all products
   - `GET /products/{id}` - Retrieve a product by ID
   - `PATCH /products/{id}` - Update price and/or stock
   - `DELETE /products/{id}` - Delete a product
   - `POST /orders` – Create an order
   - `GET /orders` - List all orders, optional filter by user (?`user_id=`1)
   - `GET /orders/{id}` - Retrieve an order by ID
   - `PATCH /orders/{id}` - Update total price
   - `DELETE /orders/{id}` - Delete an order

## Authentication

- Send a `POST` to `/login` with JSON:

  ```json
  {
    "username": "your_username",
    "password": "your_password"
  }
  ```

- You'll receive a JWT valid for 4 hours.
- Include it in the `Authorization` header for all other endpoints:

  ```
  Authorization: Bearer <token>
  ```


## Configuration

- **Logging** is configured via `src/app/logging_conf.py` and `src/common/logging.py`.
- **Database** connection and sessions are managed in `src/infrastructure/databases/db.py`.
- **JWT** service implementation in `src/infrastructure/jwt/service.py`.
- **Settings** loaded from `.env` via Pydantic in `src/app/settings.py`.
