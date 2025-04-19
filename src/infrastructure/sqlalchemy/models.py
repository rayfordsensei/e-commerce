import datetime
from typing import Any, final, override

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


@final
class Order(Base):
    @property
    def created_at_iso(self) -> str:
        return self.created_at.isoformat()

    __tablename__: str = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="orders")

    __table_args__: tuple[Any, ...] | dict[str, Any] = (  # pyright:ignore[reportExplicitAny]
        CheckConstraint("total_price >= 0", name="check_total_price_non_negative"),
    )

    @override
    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, "
            f"User id='{self.user_id}', "
            f"total='{self.total_price}', "
            f"created at='{self.created_at}')>"
        )


@final
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")

    __table_args__: tuple[Any, ...] | dict[str, Any] = (  # pyright:ignore[reportExplicitAny]
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
    )

    @override
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


@final
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(length=255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__: tuple[Any, ...] | dict[str, Any] = (  # pyright:ignore[reportExplicitAny]
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
