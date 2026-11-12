from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import get_current_user, require_roles

router = APIRouter(prefix="/api/stock", tags=["stock"])

STORE_ROLES = (models.Role.ADMIN, models.Role.STOREKEEPER, models.Role.DIRECTOR)


def _balance(db: Session, material_id: int) -> float:
    row = (
        db.query(func.coalesce(func.sum(models.StockMove.qty), 0.0))
        .filter(models.StockMove.material_id == material_id)
        .scalar()
    )
    return float(row)


@router.get("/materials", response_model=list[schemas.MaterialStockOut])
def materials_stock(
    low_only: bool = False,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    materials = (
        db.query(models.Material)
        .filter(models.Material.is_active.is_(True))
        .order_by(models.Material.name)
        .all()
    )
    out = []
    for m in materials:
        balance = _balance(db, m.id)
        item = schemas.MaterialStockOut(
            material=schemas.MaterialOut.model_validate(m),
            balance=balance,
            low_stock=balance <= m.min_stock,
        )
        if low_only and not item.low_stock:
            continue
        out.append(item)
    return out


@router.get("/moves", response_model=list[schemas.StockMoveOut])
def list_moves(
    material_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = db.query(models.StockMove)
    if material_id:
        q = q.filter(models.StockMove.material_id == material_id)
    moves = (
        q.order_by(models.StockMove.created_at.desc(), models.StockMove.id.desc())
        .limit(500)
        .all()
    )
    return [
        schemas.StockMoveOut(
            id=m.id,
            material_id=m.material_id,
            qty=m.qty,
            type=m.type,
            order_id=m.order_id,
            note=m.note,
            created_at=m.created_at,
            material_name=m.material.name if m.material else "",
        )
        for m in moves
    ]


@router.post("/moves", response_model=schemas.StockMoveOut, status_code=201)
def create_move(
    data: schemas.StockMoveCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles(*STORE_ROLES)),
):
    material = db.get(models.Material, data.material_id)
    if not material or not material.is_active:
        raise HTTPException(400, "Материал не найден")
    if data.type == models.MoveType.WRITEOFF and data.qty > 0:
        # списание — всегда расход, модуль qty
        data.qty = -data.qty
    if (
        data.type in (models.MoveType.PURCHASE, models.MoveType.ADJUSTMENT)
        and data.qty == 0
    ):
        raise HTTPException(400, "Количество не должно быть нулевым")
    if data.type == models.MoveType.CONSUMPTION:
        raise HTTPException(400, "Расход под заказ создаётся при выпуске заказа")
    move = models.StockMove(
        material_id=material.id,
        qty=data.qty,
        type=data.type,
        note=data.note,
        created_by_id=user.id,
    )
    db.add(move)
    db.commit()
    db.refresh(move)
    return schemas.StockMoveOut(
        id=move.id,
        material_id=move.material_id,
        qty=move.qty,
        type=move.type,
        order_id=move.order_id,
        note=move.note,
        created_at=move.created_at,
        material_name=material.name,
    )


@router.get("/finished_goods", response_model=list[schemas.ProductStockOut])
def finished_goods(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    products = (
        db.query(models.Product)
        .filter(models.Product.is_active.is_(True))
        .order_by(models.Product.name)
        .all()
    )
    out = []
    for p in products:
        balance = float(
            db.query(func.coalesce(func.sum(models.FinishedGoodsReceipt.qty), 0.0))
            .filter(models.FinishedGoodsReceipt.product_id == p.id)
            .scalar()
        )
        out.append(
            schemas.ProductStockOut(
                product=schemas.ProductOut.model_validate(p), balance=balance
            )
        )
    return out


@router.get("/fg_receipts", response_model=list[schemas.FgReceiptOut])
def fg_receipts(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    rows = (
        db.query(models.FinishedGoodsReceipt)
        .order_by(models.FinishedGoodsReceipt.created_at.desc())
        .limit(500)
        .all()
    )
    return [
        schemas.FgReceiptOut(
            id=r.id,
            order_id=r.order_id,
            product_id=r.product_id,
            qty=r.qty,
            note=r.note,
            created_at=r.created_at,
            product_name=r.product.name if r.product else "",
        )
        for r in rows
    ]
