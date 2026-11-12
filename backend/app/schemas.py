from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import MoveType, OrderStatus, Role, TaskStatus


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- users / auth ---
class UserOut(OrmBase):
    id: int
    email: str
    name: str
    role: Role
    is_active: bool


class UserCreate(BaseModel):
    email: str
    name: str
    role: Role = Role.OPERATOR
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    name: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- catalog ---
class MaterialOut(OrmBase):
    id: int
    sku: str
    name: str
    unit: str
    cost_per_unit: float
    min_stock: float
    is_active: bool


class MaterialCreate(BaseModel):
    sku: str
    name: str
    unit: str
    cost_per_unit: float = 0.0
    min_stock: float = 0.0


class MaterialUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    cost_per_unit: float | None = None
    min_stock: float | None = None
    is_active: bool | None = None


class BomItemOut(OrmBase):
    id: int
    material_id: int
    qty_per_unit: float
    material: MaterialOut | None = None


class BomItemIn(BaseModel):
    material_id: int
    qty_per_unit: float = Field(gt=0)


class RoutingStepOut(OrmBase):
    id: int
    seq: int
    name: str
    workcenter: str
    norm_min: float
    rate_per_unit: float


class RoutingStepIn(BaseModel):
    seq: int = Field(ge=1)
    name: str
    workcenter: str = ""
    norm_min: float = Field(ge=0, default=0.0)
    rate_per_unit: float = Field(ge=0, default=0.0)


class ProductOut(OrmBase):
    id: int
    sku: str
    name: str
    category: str
    description: str
    unit_price: float
    is_active: bool


class ProductDetailOut(ProductOut):
    bom_items: list[BomItemOut] = []
    routing: list[RoutingStepOut] = []


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str = ""
    description: str = ""
    unit_price: float = Field(ge=0, default=0.0)


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    unit_price: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


# --- orders / tasks ---
class TaskOut(OrmBase):
    id: int
    order_id: int
    step_id: int
    assignee_id: int | None
    qty: float
    qty_done: float
    qty_rejected: float
    status: TaskStatus
    rate: float
    started_at: datetime | None
    completed_at: datetime | None
    reject_reason: str
    step_name: str = ""
    assignee_name: str = ""


class OrderCreate(BaseModel):
    product_id: int
    qty: float = Field(gt=0)
    planned_start: date | None = None
    due_date: date | None = None


class OrderOut(OrmBase):
    id: int
    number: str
    product_id: int
    qty: float
    status: OrderStatus
    planned_start: date | None
    due_date: date | None
    created_at: datetime
    released_at: datetime | None
    completed_at: datetime | None
    product_name: str = ""
    product_sku: str = ""


class OrderDetailOut(OrderOut):
    tasks: list[TaskOut] = []
    received_qty: float = 0.0


class TaskAssign(BaseModel):
    user_id: int


class TaskComplete(BaseModel):
    qty_done: float = Field(ge=0, default=0.0)
    qty_rejected: float = Field(ge=0, default=0.0)
    reject_reason: str = ""


class ReceiveFg(BaseModel):
    qty: float = Field(gt=0)
    note: str = ""


# --- warehouse ---
class StockMoveOut(OrmBase):
    id: int
    material_id: int
    qty: float
    type: MoveType
    order_id: int | None
    note: str
    created_at: datetime
    material_name: str = ""


class StockMoveCreate(BaseModel):
    material_id: int
    qty: float  # для purchase/adjustment — со знаком; writeoff списывает модуль
    type: MoveType
    note: str = ""


class MaterialStockOut(BaseModel):
    material: MaterialOut
    balance: float
    low_stock: bool


class FgReceiptOut(OrmBase):
    id: int
    order_id: int
    product_id: int
    qty: float
    note: str
    created_at: datetime
    product_name: str = ""


class ProductStockOut(BaseModel):
    product: ProductOut
    balance: float


# --- analytics ---
class OverviewOut(BaseModel):
    orders_total: int
    orders_by_status: dict[str, int]
    tasks_by_status: dict[str, int]
    planned_qty: float
    produced_qty: float
    defect_qty: float
    defect_rate: float
    payroll_total: float
    payroll_by_operator: list[dict]
    low_stock_materials: list[MaterialStockOut]
    production_by_product: list[dict]
    orders_by_day: list[dict]
