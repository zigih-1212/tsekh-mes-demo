from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..deps import require_roles

router = APIRouter(prefix="/api", tags=["catalog"])

EDIT_ROLES = (models.Role.ADMIN, models.Role.TECHNOLOGIST, models.Role.DIRECTOR)


# ---------- materials ----------
@router.get("/materials", response_model=list[schemas.MaterialOut])
def list_materials(db: Session = Depends(get_db)):
    return db.query(models.Material).order_by(models.Material.id).all()


@router.post(
    "/materials",
    response_model=schemas.MaterialOut,
    status_code=201,
    dependencies=[Depends(require_roles(*EDIT_ROLES))],
)
def create_material(payload: schemas.MaterialCreate, db: Session = Depends(get_db)):
    if db.query(models.Material).filter(models.Material.sku == payload.sku).first():
        raise HTTPException(
            status_code=409, detail="Материал с таким артикулом уже существует"
        )
    m = models.Material(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.patch(
    "/materials/{material_id}",
    response_model=schemas.MaterialOut,
    dependencies=[Depends(require_roles(*EDIT_ROLES))],
)
def update_material(
    material_id: int, payload: schemas.MaterialUpdate, db: Session = Depends(get_db)
):
    m = db.get(models.Material, material_id)
    if not m:
        raise HTTPException(status_code=404, detail="Материал не найден")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    return m


# ---------- products ----------
@router.get("/products", response_model=list[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.id).all()


@router.post(
    "/products",
    response_model=schemas.ProductOut,
    status_code=201,
    dependencies=[Depends(require_roles(*EDIT_ROLES))],
)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    if db.query(models.Product).filter(models.Product.sku == payload.sku).first():
        raise HTTPException(
            status_code=409, detail="Изделие с таким артикулом уже существует"
        )
    p = models.Product(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/products/{product_id}", response_model=schemas.ProductDetailOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Изделие не найдено")
    return p


@router.patch(
    "/products/{product_id}",
    response_model=schemas.ProductOut,
    dependencies=[Depends(require_roles(*EDIT_ROLES))],
)
def update_product(
    product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    p = db.get(models.Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Изделие не найдено")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.put(
    "/products/{product_id}/bom",
    response_model=schemas.ProductDetailOut,
    dependencies=[Depends(require_roles(*EDIT_ROLES))],
)
def set_bom(
    product_id: int, items: list[schemas.BomItemIn], db: Session = Depends(get_db)
):
    p = db.get(models.Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Изделие не найдено")
    for item in items:
        if not db.get(models.Material, item.material_id):
            raise HTTPException(
                status_code=400, detail=f"Материал {item.material_id} не найден"
            )
    db.query(models.BomItem).filter(models.BomItem.product_id == product_id).delete()
    for item in items:
        db.add(
            models.BomItem(
                product_id=product_id,
                material_id=item.material_id,
                qty_per_unit=item.qty_per_unit,
            )
        )
    db.commit()
    db.refresh(p)
    return p


@router.put(
    "/products/{product_id}/routing",
    response_model=schemas.ProductDetailOut,
    dependencies=[Depends(require_roles(*EDIT_ROLES))],
)
def set_routing(
    product_id: int, steps: list[schemas.RoutingStepIn], db: Session = Depends(get_db)
):
    p = db.get(models.Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Изделие не найдено")
    db.query(models.RoutingStep).filter(
        models.RoutingStep.product_id == product_id
    ).delete()
    for s in sorted(steps, key=lambda x: x.seq):
        db.add(
            models.RoutingStep(
                product_id=product_id,
                seq=s.seq,
                name=s.name,
                workcenter=s.workcenter,
                norm_min=s.norm_min,
                rate_per_unit=s.rate_per_unit,
            )
        )
    db.commit()
    db.refresh(p)
    return p
