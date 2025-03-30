from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__: str = "users"

    id: Column[int] = Column[int](Integer, primary_key=True, autoincrement=True)
    username: Column[str] = Column[str](String(length=50), unique=True, nullable=False)
    email: Column[str] = Column[str](String(length=100), unique=True, nullable=False)
    password: Column[str] = Column[str](String(length=255), nullable=False)


class Product(Base):
    __tablename__: str = "products"

    id: Column[int] = Column[int](Integer, primary_key=True, autoincrement=True)
    name: Column[str] = Column[str](String(length=100), nullable=False)
    description: Column[str] = Column[str](String(length=255), nullable=True)
    price: Column[float] = Column[float](Float, nullable=False)
    stock: Column[int] = Column[int](Integer, nullable=False)


class Order(Base):
    __tablename__: str = "orders"

    id: Column[int] = Column[int](Integer, primary_key=True, autoincrement=True)
    user_id: Column[int] = Column[int](Integer, ForeignKey(column="users.id"), nullable=False)
    total_price: Column[float] = Column[float](Float, nullable=False)
    created_at: Column[datetime] = Column[datetime](DateTime, default=datetime.now(tz=UTC))

    user = relationship(argument="User", backref="orders")
