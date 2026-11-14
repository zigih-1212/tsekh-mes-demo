// Mock-адаптер axios для live-демо без backend: VITE_DEMO_MODE=true (см. .env.demo)
import type { AxiosAdapter, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { users, materials, products, productDetails, orders, stock, fgStock, fgReceipts, moves, overview } from './mockData'

function resp<T>(data: T, status = 200): Promise<AxiosResponse<T>> {
  return Promise.resolve({ data, status, statusText: 'OK', headers: {}, config: {} as InternalAxiosRequestConfig })
}
function err(status: number, detail: string) {
  return Promise.reject({ response: { status, data: { detail } } })
}

const state = { orders: [...orders], nextOrderId: 4, nextTaskId: 1000 }

export const mockAdapter: AxiosAdapter = async (config) => {
  const url = (config.url ?? '').replace(/^\/api/, '')
  const method = (config.method ?? 'get').toUpperCase()
  const body = typeof config.data === 'string' ? new URLSearchParams(config.data) : config.data ?? {}
  const json = (d: unknown) => (typeof d === 'string' ? JSON.parse(d) : d)

  // --- auth ---
  if (url === '/auth/login' && method === 'POST') {
    const email = body.get('username')
    const password = body.get('password')
    const user = users.find((u) => u.email === email)
    const okPw = email === 'admin@artraid.demo' ? password === 'admin123' : password === 'demo1234'
    if (!user || !okPw) return err(401, 'Неверный email или пароль')
    return resp({ access_token: 'demo-token', token_type: 'bearer', user })
  }
  if (url === '/auth/me') return resp(users[0])

  // --- users ---
  if (url === '/users' && method === 'GET') return resp(users)

  // --- catalog ---
  if (url === '/materials' && method === 'GET') return resp(materials)
  if (url === '/products' && method === 'GET') return resp(products)
  const pm = url.match(/^\/products\/(\d+)$/)
  if (pm && method === 'GET') return resp(productDetails.find((p) => p.id === Number(pm[1])))

  // --- orders ---
  if (url === '/orders' && method === 'GET') return resp(state.orders.map(({ tasks, received_qty, ...o }) => o))
  if (url === '/orders' && method === 'POST') {
    const b = json(config.data)
    const product = products.find((p) => p.id === b.product_id)!
    const o = {
      id: state.nextOrderId++, number: `ЗК-000${state.nextOrderId - 1}`, product_id: product.id, qty: b.qty,
      status: 'planned', planned_start: null, due_date: null, created_at: new Date().toISOString(),
      released_at: null, completed_at: null, product_name: product.name, product_sku: product.sku,
      tasks: [], received_qty: 0,
    }
    state.orders.push(o as never)
    const { tasks, received_qty, ...out } = o as never as (typeof state.orders)[number] & { tasks: unknown }
    return resp(out, 201)
  }
  const om = url.match(/^\/orders\/(\d+)$/)
  if (om && method === 'GET') {
    const o = state.orders.find((x) => x.id === Number(om[1]))
    if (!o) return err(404, 'Заказ не найден')
    return resp(o)
  }
  const am = url.match(/^\/orders\/(\d+)\/(release|cancel|receive_fg|tasks)$/)
  if (am) {
    const o = state.orders.find((x) => x.id === Number(am[1]))!
    const action = am[2]
    if (action === 'tasks') return resp(o.tasks)
    if (action === 'release') {
      const detail = productDetails.find((p) => p.id === o.product_id)!
      o.tasks = detail.routing.map((s) => ({
        id: state.nextTaskId++, order_id: o.id, step_id: s.id, assignee_id: null, qty: o.qty,
        qty_done: 0, qty_rejected: 0, status: 'pending', rate: s.rate_per_unit,
        started_at: null, completed_at: null, reject_reason: '', step_name: s.name, assignee_name: '',
      }))
      o.status = 'released'
      o.released_at = new Date().toISOString()
      return resp(o)
    }
    if (action === 'cancel') { o.status = 'cancelled'; const { tasks, received_qty, ...out } = o; return resp(out) }
    if (action === 'receive_fg') {
      const b = json(config.data)
      o.received_qty += b.qty
      if (o.received_qty >= o.qty) { o.status = 'completed'; o.completed_at = new Date().toISOString() }
      else if (o.status === 'released') o.status = 'in_progress'
      return resp(o)
    }
  }

  // --- tasks ---
  if (url === '/tasks' && method === 'GET') {
    const all = state.orders.flatMap((o) => o.tasks)
    const mine = new URLSearchParams(config.params as never).get('mine')
    return resp(mine ? all.filter((t) => t.assignee_id === 6) : all)
  }
  const tm = url.match(/^\/tasks\/(\d+)\/(assign|start|complete)$/)
  if (tm) {
    const t = state.orders.flatMap((o) => o.tasks).find((x) => x.id === Number(tm[1]))
    if (!t) return err(404, 'Задание не найдено')
    const b = json(config.data)
    if (tm[2] === 'assign') { t.assignee_id = b.user_id; t.assignee_name = users.find((u) => u.id === b.user_id)?.name ?? '' }
    if (tm[2] === 'start') { t.status = 'in_progress'; t.started_at = new Date().toISOString() }
    if (tm[2] === 'complete') {
      t.qty_done = b.qty_done; t.qty_rejected = b.qty_rejected; t.reject_reason = b.reject_reason ?? ''
      t.status = 'done'; t.completed_at = new Date().toISOString()
    }
    return resp(t)
  }

  // --- stock ---
  if (url === '/stock/materials' && method === 'GET') return resp(stock)
  if (url === '/stock/moves' && method === 'GET') return resp(moves)
  if (url === '/stock/moves' && method === 'POST') return resp({ id: 99, ...json(config.data), created_at: new Date().toISOString(), material_name: '' }, 201)
  if (url === '/stock/finished_goods') return resp(fgStock)
  if (url === '/stock/fg_receipts') return resp(fgReceipts)

  // --- analytics ---
  if (url === '/analytics/overview') return resp(overview)

  return err(404, `Mock: нет маршрута ${method} ${url}`)
}
