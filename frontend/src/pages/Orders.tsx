import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api, { apiError } from '../api'
import { useAuth } from '../auth'
import type { Order, Product } from '../types'

const STATUS_LABEL: Record<string, string> = {
  planned: 'Запланирован', released: 'Выпущен', in_progress: 'В работе',
  completed: 'Завершён', cancelled: 'Отменён',
}
const CAN_MANAGE = ['admin', 'director', 'technologist']

export default function Orders() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [err, setErr] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [productId, setProductId] = useState('')
  const [qty, setQty] = useState(10)

  const orders = useQuery<Order[]>({ queryKey: ['orders'], queryFn: async () => (await api.get('/orders')).data })
  const products = useQuery<Product[]>({ queryKey: ['products'], queryFn: async () => (await api.get('/products')).data })

  const create = useMutation({
    mutationFn: async () => (await api.post('/orders', { product_id: Number(productId), qty })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['orders'] }); setShowForm(false) },
    onError: (e) => setErr(apiError(e)),
  })
  const release = useMutation({
    mutationFn: async (id: number) => (await api.post(`/orders/${id}/release`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['orders'] }),
    onError: (e) => setErr(apiError(e)),
  })
  const cancel = useMutation({
    mutationFn: async (id: number) => (await api.post(`/orders/${id}/cancel`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['orders'] }),
    onError: (e) => setErr(apiError(e)),
  })

  const canManage = !!user && CAN_MANAGE.includes(user.role)

  return (
    <>
      <div className="row-between">
        <h1>Производственные заказы</h1>
        {canManage && <button className="btn" onClick={() => setShowForm(!showForm)}>+ Новый заказ</button>}
      </div>
      {err && <div className="alert">{err}</div>}
      {showForm && (
        <div className="card">
          <div className="row">
            <div style={{ maxWidth: 420 }}>
              <label>Изделие</label>
              <select value={productId} onChange={(e) => setProductId(e.target.value)}>
                <option value="">— выберите —</option>
                {products.data?.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
              </select>
            </div>
            <div style={{ width: 120 }}>
              <label>Количество</label>
              <input type="number" min={1} value={qty} onChange={(e) => setQty(Number(e.target.value))} />
            </div>
            <button className="btn" disabled={!productId || create.isPending} onClick={() => create.mutate()}>Создать</button>
          </div>
        </div>
      )}
      <div className="card">
        <table>
          <thead><tr><th>Номер</th><th>Изделие</th><th>Кол-во</th><th>Статус</th><th>Срок</th><th></th></tr></thead>
          <tbody>
            {orders.data?.map((o) => (
              <tr key={o.id}>
                <td><Link to={`/orders/${o.id}`}>{o.number}</Link></td>
                <td>{o.product_sku} — {o.product_name}</td>
                <td>{o.qty}</td>
                <td><span className={`badge ${o.status}`}>{STATUS_LABEL[o.status]}</span></td>
                <td className="muted">{o.due_date ?? '—'}</td>
                <td className="row">
                  {canManage && o.status === 'planned' && (
                    <>
                      <button className="btn btn-sm" onClick={() => release.mutate(o.id)}>Выпустить</button>
                      <button className="btn btn-sm btn-danger" onClick={() => cancel.mutate(o.id)}>Отменить</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
