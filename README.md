# E-Commerce Backend API

A lightweight, RESTful e-commerce backend API built with:

- **Python 3.12**
- **Falcon (4.0.2)**
- **SQLAlchemy (2.0)**
- **SQLite**
- **Alembic** for migrations
- **Uvicorn** as the ASGI server
- **joserfc** for JWT handling

## Features

- **User Management**: Create, list, and delete users  
- **Product Management**: Create, list, and delete products  
- **Order Management**: Create, list, and delete orders  
- **JWT-Based Authentication**: Log in to retrieve a token via `/login` (credentials checked using bcrypt)

## Quick Start

1. **Install dependencies using `uv` project manager**:
   ```bash
   uv sync
   ```

2. **Configure environment** via `.env`.  
   Dev variables:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   SQLITE_URI=sqlite+aiosqlite:///ecommerce.db
   ```

3. **Apply database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Run the app**:
   ```bash
   uvicorn app:app
   ```

5. **Access endpoints** at:
   - `/login` – Obtain a JWT with valid credentials
   - `/users` – Create, list, or delete users
   - `/products` – Create, list, or delete products
   - `/orders` – Create, list, or delete orders

## Authentication

- Send a POST request to `/login` with JSON `{"username": "...", "password": "..."}`.
- On success, the server returns a JWT token (by default valid for 4 hours).
- Currently there are no available protected endpoints, so authentication is unnecessary.

## Additional Notes

- **Request Logging** is handled by custom middleware (`RequestLoggerMiddleware`), logging both incoming requests and outgoing responses.
- **Database Initialization** is managed via Alembic migrations. The application calls `init_db` and `close_db` using Falcon’s lifespan.
