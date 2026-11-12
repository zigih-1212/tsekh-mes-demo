export type Role = 'admin' | 'director' | 'technologist' | 'storekeeper' | 'foreman' | 'operator'
export type OrderStatus = 'planned' | 'released' | 'in_progress' | 'completed' | 'cancelled'
export type TaskStatus = 'pending' | 'in_progress' | 'done'
export type MoveType = 'purchase' | 'consumption' | 'writeoff' | 'adjustment'

export interface User {
  id: number
  email: string
  name: string
  role: Role
  is_active: boolean
}

export interface Material {
  id: number
  sku: string
  name: string
  unit: string
  cost_per_unit: number
  min_stock: number
  is_active: boolean
}

export interface BomItem {
  id: number
  material_id: number
  qty_per_unit: number
  material?: Material
}

export interface RoutingStep {
  id: number
  seq: number
  name: string
  workcenter: string
  norm_min: number
  rate_per_unit: number
}

export interface Product {
  id: number
  sku: string
  name: string
  category: string
  description: string
  unit_price: number
  is_active: boolean
}

export interface ProductDetail extends Product {
  bom_items: BomItem[]
  routing: RoutingStep[]
}

export interface Task {
  id: number
  order_id: number
  step_id: number
  assignee_id: number | null
  qty: number
  qty_done: number
  qty_rejected: number
  status: TaskStatus
  rate: number
  started_at: string | null
  completed_at: string | null
  reject_reason: string
  step_name: string
  assignee_name: string
}

export interface Order {
  id: number
  number: string
  product_id: number
  qty: number
  status: OrderStatus
  planned_start: string | null
  due_date: string | null
  created_at: string
  released_at: string | null
  completed_at: string | null
  product_name: string
  product_sku: string
}

export interface OrderDetail extends Order {
  tasks: Task[]
  received_qty: number
}

export interface StockMove {
  id: number
  material_id: number
  qty: number
  type: MoveType
  order_id: number | null
  note: string
  created_at: string
  material_name: string
}

export interface MaterialStock {
  material: Material
  balance: number
  low_stock: boolean
}

export interface ProductStock {
  product: Product
  balance: number
}

export interface FgReceipt {
  id: number
  order_id: number
  product_id: number
  qty: number
  note: string
  created_at: string
  product_name: string
}

export interface Overview {
  orders_total: number
  orders_by_status: Record<string, number>
  tasks_by_status: Record<string, number>
  planned_qty: number
  produced_qty: number
  defect_qty: number
  defect_rate: number
  payroll_total: number
  payroll_by_operator: { user_id: number; name: string; earned: number; done: number }[]
  low_stock_materials: MaterialStock[]
  production_by_product: { product_id: number; name: string; qty: number }[]
  orders_by_day: { date: string; qty: number }[]
}
