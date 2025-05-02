# E‑Commerce Backend API & Demo UI

A lightweight, **async**, completely typed **REST** back‑end plus a tiny HTML + JS demo, built on:

* **Python 3.12**
* **Falcon 4.1** (ASGI mode)
* **SQLAlchemy 2** (async ORM)
* **SQLite** (via **aiosqlite**)
* **Alembic** – migrations
* **Uvicorn** – ASGI server
* **joserfc** – stateless JWT auth
* **Loguru** – structured logging
* **Spectree** – OpenAPI generation (Swagger / ReDoc / Scalar)
* **Bootstrap 5.3** – minimal browser UI (served by the API)

---

## Features

| Domain            | Capabilities                                                                                                                                                                                                                                |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Auth**          | • username + password login<br>• short‑lived JWT (4 h)<br>• single‑place error handling with request‑scoped IDs                                                                                                                             |
| **Users**         | CRUD + pagination/filter (`username_contains`,`email_contains`)                                                                                                                                                                             |
| **Products**      | CRUD + pagination/filter (`name_contains`, price range) <br>• case‑insensitive unique names                                                                                                                                                 |
| **Orders**        | CRUD scoped to user <br>• total‑price updates                                                                                                                                                                                                   |
| **Cross‑cutting** | • Lifespan middleware for DB start/stop<br>• Request/response logging incl. latency & IP<br>• Fully async Unit‑of‑Work & repositories<br>• Simple RBAC middleware<br>• Pydantic v2 schemas with examples |
| **DX**            | • Managed with **uv**<br>• `manage.py` Typer CLI (`dev`, `setup`)<br>• pytest async tests + boundary generators                                                                    |

---

## Requirements

* Python 3.12+
* [uv](https://github.com/astral-sh/uv)
* SQLite (bundled with Python) **or** any SQLAlchemy‑supported DB

---

## Quick Start

```bash
# 1 · clone
git clone https://github.com/rayfordsensei/e-commerce.git
cd e‑commerce

# 2 · install deps
uv sync               # reads uv.lock

# 3 · configure
cp .env.example .env  # fill SECRET_KEY etc.

# 4 · run (runs alembic migration and seeds a demo user [demo / demo1234])
uv run src/manage.py dev # 127.0.0.1:8000

# or plain:
# uvicorn asgi:application --host 0.0.0.0 --port 8000
```

Open:

* `http://localhost:8000/` – tiny single‑page demo UI
* `http://localhost:8000/apidoc/swagger` – Swagger UI
  (`/redoc`, `/scalar`, `openapi.json` also available)

---

## Authentication

1. `POST /login`

   ```json
   { "username": "demo", "password": "demo1234" }
   ```

   → `{"token":"<jwt>"}`

2. Pass to every protected route:

   ```
   Authorization: Bearer <jwt>
   ```

Tokens expire after **4 hours**.

---

## API Outline *(🗸 = auth required)*

| Route            | Method               |  🗸 | Purpose                              |
| ---------------- | -------------------- | :-: | ------------------------------------ |
| `/login`         | POST                 |     | Get JWT                              |
| `/users`         | GET / POST           |  🗸 | List • create                        |
| `/users/{id}`    | GET • PATCH • DELETE |  🗸 | Retrieve / update / delete\*         |
| `/products`      | GET / POST           |  🗸 | Browse (+filter) • add               |
| `/products/{id}` | GET • PATCH • DELETE |  🗸 | Detail / update price‑stock / delete |
| `/orders`        | GET / POST           |  🗸 | List (+user filter) • create         |
| `/orders/{id}`   | GET • PATCH • DELETE |  🗸 | Detail / update total / delete†      |

\* Delete fails with **409** if the user still owns orders
† Delete allowed only for the order owner (403 otherwise)

All list endpoints support:

```
?page=1&per_page=20        # pagination (X-Total-Count header)
```

Additional filters:

```
/products?name_contains=wire&min_price=10&max_price=100
/users?username_contains=jo&email_contains=@example.com
/orders?user_id=123
```

---

## Project Layout (abridged)

```
e‑commerce/
│ .env.example
│ asgi.py               # entry‑point for Uvicorn
│ pyproject.toml
│ src/
│   app/                # wiring & settings
│   api/                # Falcon resources + middleware
│   common/             # Logging + utility helpers
│   domain/             # entities & interfaces
│   infrastructure/     # SQLAlchemy adapters, JWT, DB
│   services/           # use‑cases, UoW
│   manage.py           # Typer CLI (setup/dev)
│ tests/                # tests
└ static/               # demo UI (Bootstrap, vanilla JS)
```

---

## Development

```bash
# run tests (pyright & Ruff pass in CI)
tox -q r -e py312    # or: pytest -q -n auto

# formatting / linting
ruff check src tests
biome check static   # JS/HTML formatter
```

---

## Database Migrations

```bash
# create revision
alembic revision --autogenerate -m "add discount column"

# upgrade / downgrade
alembic upgrade head
alembic downgrade -1
```

`src.infrastructure.databases.db.init_db()` runs Alembic on startup outside of **TESTING** mode.

---

## Environment Variables (`.env`)

| Name          | Example                            | Notes                          |
| ------------- | ---------------------------------- | ------------------------------ |
| `DEBUG`       | `True`                             | Enables demo UI & /**crash**   |
| `SECRET_KEY`  | *(random long string)*             | HMAC SHA‑256 key for JWT       |
| `SQLITE_URI`  | `sqlite+aiosqlite:///ecommerce.db` | Any SQLAlchemy async URL       |
| `ALEMBIC_URI` | `sqlite:///ecommerce.db`           | Sync URL for Alembic           |
| `TESTING`     | `False`                            | Set `True` under pytest (auto) |
