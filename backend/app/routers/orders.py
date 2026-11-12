from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import get_current_user, require_roles

router = APIRouter(prefix="/api/orders", tags=["orders"])

# роли, которые могут создавать/выпускать/отменять заказы
MANAGE_ROLES = (models.Role.ADMIN, models.Role.DIRECTOR, models.Role.TECHNOLOGIST)
# роли, которые могут принимать готовую продукцию
FG_ROLES = (models.Role.ADMIN, models.Role.STOREKEEPER, models.Role.FOREMAN)


def _order_out(order: models.ProductionOrder) -> schemas.OrderOut:
    return schemas.OrderOut(
        id=order.id,
        number=order.number,
        product_id=order.product_id,
        qty=order.qty,
        status=order.status,
        planned_start=order.planned_start,
        due_date=order.due_date,
        created_at=order.created_at,
        released_at=order.released_at,
        completed_at=order.completed_at,
        product_name=order.product.name if order.product else "",
        product_sku=order.product.sku if order.product else "",
    )


def _task_out(task: models.WorkTask) -> schemas.TaskOut:
    return schemas.TaskOut(
        id=task.id,
        order_id=task.order_id,
        step_id=task.step_id,
        assignee_id=task.assignee_id,
        qty=task.qty,
        qty_done=task.qty_done,
        qty_rejected=task.qty_rejected,
        status=task.status,
        rate=task.rate,
        started_at=task.started_at,
        completed_at=task.completed_at,
        reject_reason=task.reject_reason,
        step_name=task.step.name if task.step else "",
        assignee_name=task.assignee.name if task.assignee else "",
    )


def _get_order(db: Session, order_id: int) -> models.ProductionOrder:
    order = db.get(models.ProductionOrder, order_id)
    if not order:
        raise HTTPException(404, "Заказ не найден")
    return order


def _stock_balance(db: Session, material_id: int) -> float:
    moves = (
        db.query(models.StockMove)
        .filter(models.StockMove.material_id == material_id)
        .all()
    )
    return sum(m.qty for m in moves)


@router.get("", response_model=list[schemas.OrderOut])
def list_orders(
    status: models.OrderStatus | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = db.query(models.ProductionOrder)
    if status:
        q = q.filter(models.ProductionOrder.status == status)
    return [
        _order_out(o)
        for o in q.order_by(models.ProductionOrder.created_at.desc()).all()
    ]


@router.post("", response_model=schemas.OrderOut, status_code=201)
def create_order(
    data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(*MANAGE_ROLES)),
):
    product = db.get(models.Product, data.product_id)
    if not product or not product.is_active:
        raise HTTPException(400, "Изделие не найдено или неактивно")
    last = (
        db.query(models.ProductionOrder)
        .order_by(models.ProductionOrder.id.desc())
        .first()
    )
    next_num = (last.id + 1) if last else 1
    order = models.ProductionOrder(
        number=f"ЗК-{next_num:04d}",
        product_id=product.id,
        qty=data.qty,
        status=models.OrderStatus.PLANNED,
        planned_start=data.planned_start,
        due_date=data.due_date,
        created_by_id=user.id,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return _order_out(order)


@router.get("/{order_id}", response_model=schemas.OrderDetailOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    order = _get_order(db, order_id)
    received = (
        db.query(models.FinishedGoodsReceipt)
        .filter(models.FinishedGoodsReceipt.order_id == order_id)
        .all()
    )
    out = schemas.OrderDetailOut(
        **_order_out(order).model_dump(),
        tasks=[_task_out(t) for t in order.tasks],
        received_qty=sum(r.qty for r in received),
    )
    return out


@router.post("/{order_id}/release", response_model=schemas.OrderDetailOut)
def release_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(*MANAGE_ROLES)),
):
    order = _get_order(db, order_id)
    if order.status != models.OrderStatus.PLANNED:
        raise HTTPException(
            409, "Выпустить можно только заказ в статусе «запланирован»"
        )
    product = order.product
    if not product.bom_items:
        raise HTTPException(409, "У изделия нет спецификации (BOM)")
    if not product.routing:
        raise HTTPException(409, "У изделия нет маршрута (routing)")

    # проверка остатков под весь заказ
    shortages = []
    for item in product.bom_items:
        need = item.qty_per_unit * order.qty
        balance = _stock_balance(db, item.material_id)
        if balance + 1e-9 < need:
            shortages.append(
                f"{item.material.name}: нужно {need:g}, на складе {balance:g}"
            )
    if shortages:
        raise HTTPException(
            409, "Не хватает материалов на складе: " + "; ".join(shortages)
        )

    # списание материалов в цех
    for item in product.bom_items:
        db.add(
            models.StockMove(
                material_id=item.material_id,
                qty=-item.qty_per_unit * order.qty,
                type=models.MoveType.CONSUMPTION,
                order_id=order.id,
                note=f"Выдача под {order.number}",
                created_by_id=user.id,
            )
        )
    # по заданию на каждую операцию маршрута, ставка — snapshot
    for step in product.routing:
        db.add(
            models.WorkTask(
                order_id=order.id,
                step_id=step.id,
                qty=order.qty,
                rate=step.rate_per_unit,
            )
        )
    order.status = models.OrderStatus.RELEASED
    order.released_at = datetime.utcnow()
    db.commit()
    return get_order(order_id, db, user)


@router.post("/{order_id}/cancel", response_model=schemas.OrderOut)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(*MANAGE_ROLES)),
):
    order = _get_order(db, order_id)
    if order.status != models.OrderStatus.PLANNED:
        raise HTTPException(409, "Отменить можно только заказ в статусе «запланирован»")
    order.status = models.OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return _order_out(order)


@router.get("/{order_id}/tasks", response_model=list[schemas.TaskOut])
def order_tasks(
    order_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    order = _get_order(db, order_id)
    return [_task_out(t) for t in order.tasks]


@router.post("/{order_id}/receive_fg", response_model=schemas.OrderDetailOut)
def receive_fg(
    order_id: int,
    data: schemas.ReceiveFg,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(*FG_ROLES)),
):
    order = _get_order(db, order_id)
    if order.status not in (
        models.OrderStatus.RELEASED,
        models.OrderStatus.IN_PROGRESS,
    ):
        raise HTTPException(409, "Принимать ГП можно только по выпущенному заказу")
    received = (
        db.query(models.FinishedGoodsReceipt)
        .filter(models.FinishedGoodsReceipt.order_id == order_id)
        .all()
    )
    already = sum(r.qty for r in received)
    if already + data.qty > order.qty + 1e-9:
        raise HTTPException(
            409, f"Приёмка сверх задания: уже принято {already:g} из {order.qty:g}"
        )
    db.add(
        models.FinishedGoodsReceipt(
            order_id=order.id,
            product_id=order.product_id,
            qty=data.qty,
            note=data.note,
            accepted_by_id=user.id,
        )
    )
    if order.status == models.OrderStatus.RELEASED:
        order.status = models.OrderStatus.IN_PROGRESS
    if already + data.qty >= order.qty - 1e-9:
        order.status = models.OrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()
    db.commit()
    return get_order(order_id, db, user)


# --- задания ---

task_router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _get_task(db: Session, task_id: int) -> models.WorkTask:
    task = db.get(models.WorkTask, task_id)
    if not task:
        raise HTTPException(404, "Задание не найдено")
    return task


@task_router.get("", response_model=list[schemas.TaskOut])
def list_tasks(
    mine: bool = False,
    status: models.TaskStatus | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = db.query(models.WorkTask)
    if mine:
        q = q.filter(models.WorkTask.assignee_id == user.id)
    if status:
        q = q.filter(models.WorkTask.status == status)
    tasks = q.order_by(models.WorkTask.id.asc()).all()
    return [_task_out(t) for t in tasks]


@task_router.post("/{task_id}/assign", response_model=schemas.TaskOut)
def assign_task(
    task_id: int,
    data: schemas.TaskAssign,
    db: Session = Depends(get_db),
    user: models.User = Depends(
        require_roles(models.Role.ADMIN, models.Role.FOREMAN, models.Role.DIRECTOR)
    ),
):
    task = _get_task(db, task_id)
    target = db.get(models.User, data.user_id)
    if not target or not target.is_active:
        raise HTTPException(400, "Исполнитель не найден")
    task.assignee_id = target.id
    db.commit()
    db.refresh(task)
    return _task_out(task)


@task_router.post("/{task_id}/start", response_model=schemas.TaskOut)
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = _get_task(db, task_id)
    if task.assignee_id != user.id and user.role not in (
        models.Role.ADMIN,
        models.Role.FOREMAN,
    ):
        raise HTTPException(403, "Задание назначено другому исполнителю")
    if task.status != models.TaskStatus.PENDING:
        raise HTTPException(409, "Задание уже в работе или завершено")
    task.status = models.TaskStatus.IN_PROGRESS
    task.started_at = datetime.utcnow()
    order = task.order
    if order.status == models.OrderStatus.RELEASED:
        order.status = models.OrderStatus.IN_PROGRESS
    db.commit()
    db.refresh(task)
    return _task_out(task)


@task_router.post("/{task_id}/complete", response_model=schemas.TaskOut)
def complete_task(
    task_id: int,
    data: schemas.TaskComplete,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    task = _get_task(db, task_id)
    if task.assignee_id != user.id and user.role not in (
        models.Role.ADMIN,
        models.Role.FOREMAN,
    ):
        raise HTTPException(403, "Задание назначено другому исполнителю")
    if task.status == models.TaskStatus.DONE:
        raise HTTPException(409, "Задание уже завершено")
    if data.qty_done + data.qty_rejected > task.qty + 1e-9:
        raise HTTPException(
            409,
            f"Сумма годных ({data.qty_done:g}) и брака ({data.qty_rejected:g}) "
            f"не может превышать задание ({task.qty:g})",
        )
    task.qty_done = data.qty_done
    task.qty_rejected = data.qty_rejected
    task.reject_reason = data.reject_reason
    task.status = models.TaskStatus.DONE
    task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return _task_out(task)
