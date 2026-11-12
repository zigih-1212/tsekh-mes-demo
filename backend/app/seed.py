"""Идемпотентное наполнение демо-данными в духе производства Artraid.

Запускается один раз при старте, если таблица users пустая.
Пароли демо: admin=admin123, остальные=demo1234.
"""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from . import models
from .security import hash_password


def seed_if_empty(db: Session) -> None:
    if db.query(models.User).first():
        return

    # --- материалы (единицы как на реальном производстве) ---
    materials = [
        ("TKAN-DUSPO", "Ткань Дюспо (Sherpa-like), м", "м", 320.0, 200.0),
        ("TKAN-SATIN", "Ткань Страйп-Сатин, м", "м", 410.0, 150.0),
        ("MICROSPHERE", "Микросферы натрийборосиликатные, кг", "кг", 1850.0, 80.0),
        ("KOVELOS", "Ковелос (диоксид кремния), кг", "кг", 260.0, 60.0),
        ("NITKA-ARM", "Нитки армированные, боб", "шт", 45.0, 100.0),
        ("FURN-LIGHT", "Фурнитура (молнии, липучки), компл", "шт", 30.0, 200.0),
        ("UPAK-KOROB", "Упаковка: коробка + пакет, компл", "шт", 25.0, 300.0),
        ("ETCH-LOGO", "Нашивка/вышивка логотипа Artraid", "шт", 18.0, 150.0),
    ]
    mats = {}
    for sku, name, unit, cost, min_stock in materials:
        m = models.Material(
            sku=sku, name=name, unit=unit, cost_per_unit=cost, min_stock=min_stock
        )
        db.add(m)
        db.flush()
        mats[sku] = m

    # --- изделия (каталог Artraid) ---
    products_data = {
        "POD-3232": (
            "Подушка медицинская с микросферами 32×32",
            "Подушки",
            1490.0,
            [
                ("TKAN-DUSPO", 0.45),
                ("TKAN-SATIN", 0.45),
                ("MICROSPHERE", 0.35),
                ("NITKA-ARM", 1),
                ("UPAK-KOROB", 1),
                ("ETCH-LOGO", 1),
            ],
            [
                (1, "Раскрой чехла", "Раскройный участок", 6, 12),
                (2, "Пошив чехла", "Швейный участок", 14, 28),
                (3, "Вышивка логотипа", "Вышивальный участок", 4, 8),
                (4, "Сборка и дозирование микросфер", "Сборочный участок", 10, 20),
                (5, "Контроль толщины толщиномером (ОТК)", "ОТК", 3, 6),
                (6, "Упаковка", "Упаковочный участок", 3, 6),
            ],
        ),
        "POV-UNI": (
            "Повязка универсальная медицинская",
            "Повязки",
            890.0,
            [
                ("TKAN-DUSPO", 0.25),
                ("MICROSPHERE", 0.12),
                ("NITKA-ARM", 1),
                ("FURN-LIGHT", 1),
                ("UPAK-KOROB", 1),
                ("ETCH-LOGO", 1),
            ],
            [
                (1, "Раскрой", "Раскройный участок", 4, 8),
                (2, "Пошив", "Швейный участок", 9, 18),
                (3, "Дозирование микросфер", "Сборочный участок", 6, 12),
                (4, "ОТК", "ОТК", 2, 4),
                (5, "Упаковка", "Упаковочный участок", 2, 4),
            ],
        ),
        "POV-NOGA-S1": (
            "Повязка на ногу S1",
            "Повязки",
            1150.0,
            [
                ("TKAN-SATIN", 0.35),
                ("MICROSPHERE", 0.2),
                ("NITKA-ARM", 1),
                ("FURN-LIGHT", 1),
                ("UPAK-KOROB", 1),
            ],
            [
                (1, "Раскрой", "Раскройный участок", 5, 10),
                (2, "Пошив", "Швейный участок", 10, 20),
                (3, "Дозирование микросфер", "Сборочный участок", 8, 16),
                (4, "ОТК", "ОТК", 2, 4),
                (5, "Упаковка", "Упаковочный участок", 2, 4),
            ],
        ),
        "STELKA": (
            "Стельки медицинские с микросферами",
            "Стельки",
            640.0,
            [
                ("TKAN-DUSPO", 0.12),
                ("TKAN-SATIN", 0.12),
                ("MICROSPHERE", 0.06),
                ("NITKA-ARM", 1),
                ("UPAK-KOROB", 1),
            ],
            [
                (1, "Раскрой", "Раскройный участок", 2, 4),
                (2, "Оверлок края", "Швейный участок", 4, 8),
                (3, "Дозирование микросфер", "Сборочный участок", 4, 8),
                (4, "ОТК", "ОТК", 1, 2),
                (5, "Упаковка", "Упаковочный участок", 1, 2),
            ],
        ),
        "TAPKI-BOT": (
            "Тапки-боты медицинские",
            "Обувь",
            1250.0,
            [
                ("TKAN-DUSPO", 0.4),
                ("MICROSPHERE", 0.15),
                ("NITKA-ARM", 2),
                ("FURN-LIGHT", 1),
                ("UPAK-KOROB", 1),
                ("ETCH-LOGO", 1),
            ],
            [
                (1, "Раскрой", "Раскройный участок", 5, 10),
                (2, "Пошив верха", "Швейный участок", 12, 24),
                (3, "Вышивка логотипа", "Вышивальный участок", 3, 6),
                (4, "Сборка и дозирование", "Сборочный участок", 8, 16),
                (5, "ОТК", "ОТК", 3, 6),
                (6, "Упаковка", "Упаковочный участок", 2, 4),
            ],
        ),
    }
    products = {}
    for sku, (name, cat, price, bom, routing) in products_data.items():
        p = models.Product(
            sku=sku,
            name=name,
            category=cat,
            unit_price=price,
            description="Медицинское изделие с наполнителем из микросфер. РУ РЗН 2024/24297.",
        )
        db.add(p)
        db.flush()
        for mat_sku, qty in bom:
            db.add(
                models.BomItem(
                    product_id=p.id, material_id=mats[mat_sku].id, qty_per_unit=qty
                )
            )
        for seq, name_op, wc, norm, rate in routing:
            db.add(
                models.RoutingStep(
                    product_id=p.id,
                    seq=seq,
                    name=name_op,
                    workcenter=wc,
                    norm_min=norm,
                    rate_per_unit=rate,
                )
            )
        products[sku] = p

    # --- пользователи ---
    users_data = [
        ("admin@artraid.demo", "Иван Админов", models.Role.ADMIN, "admin123"),
        (
            "director@artraid.demo",
            "Директор производства",
            models.Role.DIRECTOR,
            "demo1234",
        ),
        ("tech@artraid.demo", "Главный технолог", models.Role.TECHNOLOGIST, "demo1234"),
        ("store@artraid.demo", "Кладовщик", models.Role.STOREKEEPER, "demo1234"),
        ("foreman@artraid.demo", "Мастер смены", models.Role.FOREMAN, "demo1234"),
        ("op1@artraid.demo", "Швея-оператор 1", models.Role.OPERATOR, "demo1234"),
        ("op2@artraid.demo", "Швея-оператор 2", models.Role.OPERATOR, "demo1234"),
    ]
    users = {}
    for email, name, role, pwd in users_data:
        u = models.User(
            email=email, name=name, role=role, hashed_password=hash_password(pwd)
        )
        db.add(u)
        db.flush()
        users[email] = u

    admin = users["admin@artraid.demo"]

    # --- приходы материалов (закупки) ---
    purchases = [
        ("TKAN-DUSPO", 400.0),
        ("TKAN-SATIN", 300.0),
        ("MICROSPHERE", 120.0),
        ("KOVELOS", 200.0),
        ("NITKA-ARM", 500.0),
        ("FURN-LIGHT", 600.0),
        ("UPAK-KOROB", 800.0),
        ("ETCH-LOGO", 400.0),
    ]
    for sku, qty in purchases:
        db.add(
            models.StockMove(
                material_id=mats[sku].id,
                qty=qty,
                type=models.MoveType.PURCHASE,
                note="Закупка у поставщика",
                created_by_id=admin.id,
                created_at=datetime.utcnow() - timedelta(days=10),
            )
        )
    # списание, чтобы микросферы оказались ниже порога (low stock алерт)
    db.add(
        models.StockMove(
            material_id=mats["MICROSPHERE"].id,
            qty=-30.0,
            type=models.MoveType.WRITEOFF,
            note="Списание по акту инвентаризации",
            created_by_id=admin.id,
            created_at=datetime.utcnow() - timedelta(days=3),
        )
    )

    # --- заказы в разных статусах ---
    today = date.today()

    # завершённый заказ (подушка), с заданиями и приёмкой ГП
    o1 = models.ProductionOrder(
        number="ЗК-0001",
        product_id=products["POD-3232"].id,
        qty=50,
        status=models.OrderStatus.COMPLETED,
        planned_start=today - timedelta(days=12),
        due_date=today - timedelta(days=5),
        created_by_id=admin.id,
        created_at=datetime.utcnow() - timedelta(days=12),
        released_at=datetime.utcnow() - timedelta(days=11),
        completed_at=datetime.utcnow() - timedelta(days=4),
    )
    db.add(o1)
    db.flush()
    for step in products["POD-3232"].routing:
        t = models.WorkTask(
            order_id=o1.id,
            step_id=step.id,
            qty=50,
            qty_done=48 if step.seq == 4 else 50,  # брак на дозировании
            qty_rejected=2 if step.seq == 4 else 0,
            status=models.TaskStatus.DONE,
            rate=step.rate_per_unit,
            assignee_id=users["op1@artraid.demo"].id
            if step.seq in (2, 3)
            else users["op2@artraid.demo"].id,
            started_at=datetime.utcnow() - timedelta(days=10),
            completed_at=datetime.utcnow() - timedelta(days=5),
            reject_reason="Пересып наполнителя" if step.seq == 4 else "",
        )
        db.add(t)
    for item in products["POD-3232"].bom_items:
        db.add(
            models.StockMove(
                material_id=item.material_id,
                qty=-item.qty_per_unit * 50,
                type=models.MoveType.CONSUMPTION,
                order_id=o1.id,
                note="Выдача под ЗК-0001",
                created_by_id=admin.id,
                created_at=datetime.utcnow() - timedelta(days=11),
            )
        )
    db.add(
        models.FinishedGoodsReceipt(
            order_id=o1.id,
            product_id=o1.product_id,
            qty=48,
            note="Приёмка ОТК, 2 ед. брак",
            accepted_by_id=users["store@artraid.demo"].id,
            created_at=datetime.utcnow() - timedelta(days=4),
        )
    )

    # заказ в работе
    o2 = models.ProductionOrder(
        number="ЗК-0002",
        product_id=products["STELKA"].id,
        qty=200,
        status=models.OrderStatus.IN_PROGRESS,
        planned_start=today - timedelta(days=2),
        due_date=today + timedelta(days=5),
        created_by_id=admin.id,
        created_at=datetime.utcnow() - timedelta(days=3),
        released_at=datetime.utcnow() - timedelta(days=2),
    )
    db.add(o2)
    db.flush()
    for step in products["STELKA"].routing:
        status = (
            models.TaskStatus.DONE
            if step.seq <= 2
            else (
                models.TaskStatus.IN_PROGRESS
                if step.seq == 3
                else models.TaskStatus.PENDING
            )
        )
        t = models.WorkTask(
            order_id=o2.id,
            step_id=step.id,
            qty=200,
            rate=step.rate_per_unit,
            qty_done=200 if step.seq <= 2 else (120 if step.seq == 3 else 0),
            qty_rejected=5 if step.seq == 2 else 0,
            status=status,
            assignee_id=users["op2@artraid.demo"].id if step.seq in (1, 2, 3) else None,
            started_at=datetime.utcnow() - timedelta(days=2)
            if status != models.TaskStatus.PENDING
            else None,
            completed_at=datetime.utcnow() - timedelta(days=1)
            if status == models.TaskStatus.DONE
            else None,
            reject_reason="Край отошёл" if step.seq == 2 else "",
        )
        db.add(t)
    for item in products["STELKA"].bom_items:
        db.add(
            models.StockMove(
                material_id=item.material_id,
                qty=-item.qty_per_unit * 200,
                type=models.MoveType.CONSUMPTION,
                order_id=o2.id,
                note="Выдача под ЗК-0002",
                created_by_id=admin.id,
                created_at=datetime.utcnow() - timedelta(days=2),
            )
        )
    db.add(
        models.FinishedGoodsReceipt(
            order_id=o2.id,
            product_id=o2.product_id,
            qty=150,
            note="Частичная приёмка",
            accepted_by_id=users["store@artraid.demo"].id,
            created_at=datetime.utcnow() - timedelta(days=1),
        )
    )

    # запланированный заказ
    o3 = models.ProductionOrder(
        number="ЗК-0003",
        product_id=products["POV-UNI"].id,
        qty=80,
        status=models.OrderStatus.PLANNED,
        planned_start=today + timedelta(days=1),
        due_date=today + timedelta(days=10),
        created_by_id=admin.id,
        created_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(o3)

    db.commit()
