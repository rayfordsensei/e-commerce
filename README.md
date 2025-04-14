# E-Commerce Backend API

A Work-in-Progress lightweight, RESTful e-commerce backend API built with:

- **Python 3.12**
- **Falcon (4.0.2)**
- **SQLAlchemy (2.0)**
- **SQLite**
- **Alembic** for migrations
- **Uvicorn** as the ASGI server
- **uv** as a project manager

## Features

- **User Management**: Create, list, and delete users  
- **Product Management**: Create, list, and delete products  
- **Order Management**: Create, list, and delete orders  

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```
2. **Apply database migrations**:
   ```bash
   alembic upgrade head
   ```
3. **Run the app**:
   ```bash
   uvicorn app:app
   ```
4. **Access endpoints** at:
   - `/users`  
   - `/products`  
   - `/orders`
