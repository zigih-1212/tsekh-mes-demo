from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=schemas.OverviewOut)
def overview(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    orders = db.query(models.ProductionOrder).all()
    tasks = db.query(models.WorkTask).all()

    by_status: dict[str, int] = defaultdict(int)
    for o in orders:
        by_status[o.status.value] += 1
    tasks_by_status: dict[str, int] = defaultdict(int)
    for t in tasks:
        tasks_by_status[t.status.value] += 1

    produced = sum(r.qty for r in db.query(models.FinishedGoodsReceipt).all())
    defect = sum(t.qty_rejected for t in tasks)
    good_done = sum(t.qty_done for t in tasks)
    defect_rate = (defect / (good_done + defect) * 100) if (good_done + defect) else 0.0
    payroll = sum(t.qty_done * t.rate for t in tasks)

    by_operator: dict[int, dict] = {}
    for t in tasks:
        if t.assignee_id is None:
            continue
        entry = by_operator.setdefault(
            t.assignee_id,
            {
                "user_id": t.assignee_id,
                "name": t.assignee.name if t.assignee else "",
                "earned": 0.0,
                "done": 0.0,
            },
        )
        entry["earned"] += t.qty_done * t.rate
        entry["done"] += t.qty_done
    payroll_by_operator = sorted(by_operator.values(), key=lambda x: -x["earned"])

    low_stock = []
    for m in (
        db.query(models.Material).filter(models.Material.is_active.is_(True)).all()
    ):
        balance = float(
            db.query(func.coalesce(func.sum(models.StockMove.qty), 0.0))
            .filter(models.StockMove.material_id == m.id)
            .scalar()
        )
        if balance <= m.min_stock:
            low_stock.append(
                schemas.MaterialStockOut(
                    material=schemas.MaterialOut.model_validate(m),
                    balance=balance,
                    low_stock=True,
                )
            )

    by_product: dict[int, dict] = {}
    for r in db.query(models.FinishedGoodsReceipt).all():
        entry = by_product.setdefault(
            r.product_id,
            {
                "product_id": r.product_id,
                "name": r.product.name if r.product else "",
                "qty": 0.0,
            },
        )
        entry["qty"] += r.qty
    production_by_product = sorted(by_product.values(), key=lambda x: -x["qty"])

    by_day: dict[str, float] = defaultdict(float)
    for r in db.query(models.FinishedGoodsReceipt).all():
        by_day[r.created_at.date().isoformat()] += r.qty
    orders_by_day = [{"date": d, "qty": q} for d, q in sorted(by_day.items())]

    return schemas.OverviewOut(
        orders_total=len(orders),
        orders_by_status=dict(by_status),
        tasks_by_status=dict(tasks_by_status),
        planned_qty=sum(
            o.qty for o in orders if o.status == models.OrderStatus.PLANNED
        ),
        produced_qty=produced,
        defect_qty=defect,
        defect_rate=round(defect_rate, 2),
        payroll_total=round(payroll, 2),
        payroll_by_operator=payroll_by_operator,
        low_stock_materials=low_stock,
        production_by_product=production_by_product,
        orders_by_day=orders_by_day,
    )
