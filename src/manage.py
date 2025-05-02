import asyncio

import typer
import uvicorn

from infrastructure.databases.db import init_db

cli = typer.Typer(add_completion=False)


@cli.command(help="Run migrations + seed demo user")
def setup() -> None:
    asyncio.run(init_db(seed=True))


@cli.command(help="Full dev server (default host/port 127.0.0.1:8000)")
def dev(host: str = "127.0.0.1", port: int = 8000) -> None:
    asyncio.run(init_db(seed=True))
    uvicorn.run("asgi:application", host=host, port=port)  # A little noisy with [init_db].


if __name__ == "__main__":
    cli()
