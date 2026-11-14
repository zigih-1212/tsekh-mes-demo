// Демо-данные для live-режима без backend (VITE_DEMO_MODE=true, см. .env.demo)
import type { Material, OrderDetail, Overview, Product, ProductDetail, StockMove, MaterialStock, ProductStock, FgReceipt, Task, User } from '../types'

export const users: User[] = [
  { id: 1, email: 'admin@artraid.demo', name: 'Иван Админов', role: 'admin', is_active: true },
  { id: 2, email: 'director@artraid.demo', name: 'Директор производства', role: 'director', is_active: true },
  { id: 3, email: 'tech@artraid.demo', name: 'Главный технолог', role: 'technologist', is_active: true },
  { id: 4, email: 'store@artraid.demo', name: 'Кладовщик', role: 'storekeeper', is_active: true },
  { id: 5, email: 'foreman@artraid.demo', name: 'Мастер смены', role: 'foreman', is_active: true },
  { id: 6, email: 'op1@artraid.demo', name: 'Швея-оператор 1', role: 'operator', is_active: true },
  { id: 7, email: 'op2@artraid.demo', name: 'Швея-оператор 2', role: 'operator', is_active: true },
]

export const materials: Material[] = [
  { id: 1, sku: 'TKAN-DUSPO', name: 'Ткань Дюспо, м', unit: 'м', cost_per_unit: 320, min_stock: 200, is_active: true },
  { id: 2, sku: 'TKAN-SATIN', name: 'Ткань Страйп-Сатин, м', unit: 'м', cost_per_unit: 410, min_stock: 150, is_active: true },
  { id: 3, sku: 'MICROSPHERE', name: 'Микросферы натрийборосиликатные, кг', unit: 'кг', cost_per_unit: 1850, min_stock: 80, is_active: true },
  { id: 4, sku: 'KOVELOS', name: 'Ковелос (диоксид кремния), кг', unit: 'кг', cost_per_unit: 260, min_stock: 60, is_active: true },
  { id: 5, sku: 'NITKA-ARM', name: 'Нитки армированные, боб', unit: 'шт', cost_per_unit: 45, min_stock: 100, is_active: true },
  { id: 6, sku: 'FURN-LIGHT', name: 'Фурнитура (молнии, липучки), компл', unit: 'шт', cost_per_unit: 30, min_stock: 200, is_active: true },
  { id: 7, sku: 'UPAK-KOROB', name: 'Упаковка: коробка + пакет, компл', unit: 'шт', cost_per_unit: 25, min_stock: 300, is_active: true },
  { id: 8, sku: 'ETCH-LOGO', name: 'Нашивка/вышивка логотипа Artraid', unit: 'шт', cost_per_unit: 18, min_stock: 150, is_active: true },
]

export const products: Product[] = [
  { id: 1, sku: 'POD-3232', name: 'Подушка медицинская с микросферами 32×32', category: 'Подушки', description: 'РУ РЗН 2024/24297', unit_price: 1490, is_active: true },
  { id: 2, sku: 'POV-UNI', name: 'Повязка универсальная медицинская', category: 'Повязки', description: 'РУ РЗН 2024/24297', unit_price: 890, is_active: true },
  { id: 3, sku: 'POV-NOGA-S1', name: 'Повязка на ногу S1', category: 'Повязки', description: 'РУ РЗН 2024/24297', unit_price: 1150, is_active: true },
  { id: 4, sku: 'STELKA', name: 'Стельки медицинские с микросферами', category: 'Стельки', description: 'РУ РЗН 2024/24297', unit_price: 640, is_active: true },
  { id: 5, sku: 'TAPKI-BOT', name: 'Тапки-боты медицинские', category: 'Обувь', description: 'РУ РЗН 2024/24297', unit_price: 1250, is_active: true },
]

const bom = (pid: number) =>
  [
    [1, 0.45], [2, 0.45], [3, 0.35], [5, 1], [7, 1], [8, 1],
  ].map(([mid, q], i) => ({ id: pid * 100 + i, material_id: mid as number, qty_per_unit: q as number, material: materials.find((m) => m.id === mid) }))

const routing = (pid: number) =>
  [
    [1, 'Раскрой чехла', 'Раскройный участок', 6, 12],
    [2, 'Пошив чехла', 'Швейный участок', 14, 28],
    [3, 'Вышивка логотипа', 'Вышивальный участок', 4, 8],
    [4, 'Сборка и дозирование микросфер', 'Сборочный участок', 10, 20],
    [5, 'Контроль толщины (ОТК)', 'ОТК', 3, 6],
    [6, 'Упаковка', 'Упаковочный участок', 3, 6],
  ].map(([seq, name, wc, norm, rate], i) => ({ id: pid * 100 + i, seq: seq as number, name: name as string, workcenter: wc as string, norm_min: norm as number, rate_per_unit: rate as number }))

export const productDetails: ProductDetail[] = products.map((p) => ({ ...p, bom_items: bom(p.id), routing: routing(p.id) }))

const mkTasks = (orderId: number, pid: number): Task[] =>
  routing(pid).map((s, i) => ({
    id: orderId * 100 + i,
    order_id: orderId,
    step_id: s.id,
    assignee_id: orderId === 1 ? (s.seq === 2 || s.seq === 3 ? 6 : 7) : s.seq <= 3 ? 7 : null,
    qty: orderId === 1 ? 50 : 200,
    qty_done: orderId === 1 ? (s.seq === 4 ? 48 : 50) : s.seq <= 2 ? 200 : s.seq === 3 ? 120 : 0,
    qty_rejected: orderId === 1 && s.seq === 4 ? 2 : orderId === 2 && s.seq === 2 ? 5 : 0,
    status: (orderId === 1 ? 'done' : s.seq <= 2 ? 'done' : s.seq === 3 ? 'in_progress' : 'pending') as Task['status'],
    rate: s.rate_per_unit,
    started_at: '2026-11-10T08:00:00',
    completed_at: orderId === 1 || s.seq <= 2 ? '2026-11-11T17:00:00' : null,
    reject_reason: s.seq === 4 && orderId === 1 ? 'Пересып наполнителя' : '',
    step_name: s.name,
    assignee_name: users.find((u) => u.id === (orderId === 1 ? (s.seq === 2 || s.seq === 3 ? 6 : 7) : s.seq <= 3 ? 7 : 0))?.name ?? '',
  }))

export const orders: OrderDetail[] = [
  { id: 1, number: 'ЗК-0001', product_id: 1, qty: 50, status: 'completed', planned_start: '2026-11-01', due_date: '2026-11-08', created_at: '2026-11-01T09:00:00', released_at: '2026-11-02T09:00:00', completed_at: '2026-11-11T17:00:00', product_name: products[0].name, product_sku: products[0].sku, tasks: mkTasks(1, 1), received_qty: 48 },
  { id: 2, number: 'ЗК-0002', product_id: 4, qty: 200, status: 'in_progress', planned_start: '2026-11-11', due_date: '2026-11-18', created_at: '2026-11-10T09:00:00', released_at: '2026-11-11T09:00:00', completed_at: null, product_name: products[3].name, product_sku: products[3].sku, tasks: mkTasks(2, 4), received_qty: 150 },
  { id: 3, number: 'ЗК-0003', product_id: 2, qty: 80, status: 'planned', planned_start: '2026-11-14', due_date: '2026-11-23', created_at: '2026-11-12T09:00:00', released_at: null, completed_at: null, product_name: products[1].name, product_sku: products[1].sku, tasks: [], received_qty: 0 },
]

export const stock: MaterialStock[] = [
  { material: materials[3], balance: 200, low_stock: false },
  { material: materials[2], balance: 60.5, low_stock: true },
  { material: materials[7], balance: 350, low_stock: false },
  { material: materials[4], balance: 250, low_stock: false },
  { material: materials[0], balance: 353.5, low_stock: false },
  { material: materials[1], balance: 253.5, low_stock: false },
  { material: materials[6], balance: 550, low_stock: false },
  { material: materials[5], balance: 600, low_stock: false },
]

export const fgStock: ProductStock[] = products.map((p) => ({
  product: p,
  balance: p.id === 1 ? 48 : p.id === 4 ? 150 : 0,
}))

export const fgReceipts: FgReceipt[] = [
  { id: 2, order_id: 2, product_id: 4, qty: 150, note: 'Частичная приёмка', created_at: '2026-11-12T15:00:00', product_name: products[3].name },
  { id: 1, order_id: 1, product_id: 1, qty: 48, note: 'Приёмка ОТК, 2 ед. брак', created_at: '2026-11-11T17:00:00', product_name: products[0].name },
]

export const moves: StockMove[] = [
  { id: 3, material_id: 7, qty: -200, type: 'consumption', order_id: 2, note: 'Выдача под ЗК-0002', created_at: '2026-11-11T09:30:00', material_name: materials[6].name },
  { id: 2, material_id: 3, qty: -29.5, type: 'consumption', order_id: 1, note: 'Выдача под ЗК-0001', created_at: '2026-11-02T09:30:00', material_name: materials[2].name },
  { id: 1, material_id: 3, qty: 120, type: 'purchase', order_id: null, note: 'Закупка у поставщика', created_at: '2026-11-02T08:00:00', material_name: materials[2].name },
]

export const overview: Overview = {
  orders_total: 3,
  orders_by_status: { completed: 1, in_progress: 1, planned: 1 },
  tasks_by_status: { done: 7, in_progress: 1, pending: 3 },
  planned_qty: 80,
  produced_qty: 198,
  defect_qty: 7,
  defect_rate: 0.85,
  payroll_total: 7320,
  payroll_by_operator: [
    { user_id: 7, name: 'Швея-оператор 2', earned: 5520, done: 718 },
    { user_id: 6, name: 'Швея-оператор 1', earned: 1800, done: 100 },
  ],
  low_stock_materials: [stock[1]],
  production_by_product: [
    { product_id: 4, name: products[3].name, qty: 150 },
    { product_id: 1, name: products[0].name, qty: 48 },
  ],
  orders_by_day: [
    { date: '2026-11-08', qty: 48 },
    { date: '2026-11-11', qty: 150 },
  ],
}
