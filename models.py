from typing import final, override

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()  # pyright:ignore[reportAny]


@final
class User(Base):  # pyright:ignore[reportAny]
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # TODO: consider security?

    orders = relationship("Order", back_populates="user")

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
    )

    @override
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


@final
class Product(Base):  # pyright:ignore[reportAny]
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(length=255), nullable=True)
    price = Column[float](Float, nullable=False)
    stock = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_non_negative"),
        CheckConstraint("stock >= 0", name="check_stock_non_negative"),
        Index("ix_products_name", "name"),
    )

    @override
    def __repr__(self) -> str:
        return (
            f"<Product(id={self.id}, "
            f"name='{self.name}', "
            f"description='{self.description}', "
            f"price='{self.price}', "
            f"stock='{self.stock}')>"
        )


@final
class Order(Base):  # pyright:ignore[reportAny]
    __tablename__: str = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_price = Column[float](Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")

    __table_args__ = (CheckConstraint("total_price >= 0", name="check_total_price_non_negative"),)

    @override
    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, "
            f"User id='{self.user_id}', "
            f"total='{self.total_price}', "
            f"created at='{self.created_at}')>"
        )
