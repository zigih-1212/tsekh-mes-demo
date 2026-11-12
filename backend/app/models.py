import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    DIRECTOR = "director"
    TECHNOLOGIST = "technologist"
    STOREKEEPER = "storekeeper"
    FOREMAN = "foreman"
    OPERATOR = "operator"


class OrderStatus(str, enum.Enum):
    PLANNED = "planned"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class MoveType(str, enum.Enum):
    PURCHASE = "purchase"
    CONSUMPTION = "consumption"
    WRITEOFF = "writeoff"
    ADJUSTMENT = "adjustment"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.OPERATOR)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Material(Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(16))  # м / кг / шт
    cost_per_unit: Mapped[float] = mapped_column(Float, default=0.0)
    min_stock: Mapped[float] = mapped_column(Float, default=0.0)  # порог для алерта
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(128), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    bom_items: Mapped[list["BomItem"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    routing: Mapped[list["RoutingStep"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="RoutingStep.seq",
    )


class BomItem(Base):
    __tablename__ = "bom_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE")
    )
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    qty_per_unit: Mapped[float] = mapped_column(Float)

    product: Mapped[Product] = relationship(back_populates="bom_items")
    material: Mapped[Material] = relationship()


class RoutingStep(Base):
    __tablename__ = "routing_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE")
    )
    seq: Mapped[int] = mapped_column(default=1)
    name: Mapped[str] = mapped_column(
        String(255)
    )  # операция: раскрой, пошив, вышивка...
    workcenter: Mapped[str] = mapped_column(String(128), default="")  # участок
    norm_min: Mapped[float] = mapped_column(Float, default=0.0)  # норма времени, мин/ед
    rate_per_unit: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # сдельная ставка, руб/ед

    product: Mapped[Product] = relationship(back_populates="routing")


class ProductionOrder(Base):
    __tablename__ = "production_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # ЗК-0001
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[float] = mapped_column(Float)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus), default=OrderStatus.PLANNED
    )
    planned_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    released_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    product: Mapped[Product] = relationship()
    tasks: Mapped[list["WorkTask"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class WorkTask(Base):
    __tablename__ = "work_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("production_orders.id", ondelete="CASCADE")
    )
    step_id: Mapped[int] = mapped_column(ForeignKey("routing_steps.id"))
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    qty: Mapped[float] = mapped_column(Float)
    qty_done: Mapped[float] = mapped_column(Float, default=0.0)
    qty_rejected: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus), default=TaskStatus.PENDING
    )
    rate: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # snapshot ставки на момент выпуска
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reject_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    order: Mapped[ProductionOrder] = relationship(back_populates="tasks")
    step: Mapped[RoutingStep] = relationship()
    assignee: Mapped[User | None] = relationship()


class StockMove(Base):
    __tablename__ = "stock_moves"
    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    qty: Mapped[float] = mapped_column(Float)  # знаковое: + приход, - расход
    type: Mapped[MoveType] = mapped_column(SAEnum(MoveType))
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("production_orders.id"), nullable=True
    )
    note: Mapped[str] = mapped_column(Text, default="")
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    material: Mapped[Material] = relationship()


class FinishedGoodsReceipt(Base):
    __tablename__ = "fg_receipts"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("production_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    qty: Mapped[float] = mapped_column(Float)
    note: Mapped[str] = mapped_column(Text, default="")
    accepted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped[Product] = relationship()
