import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import api, { apiError } from '../api'
import { useAuth } from '../auth'
import type { OrderDetail, User } from '../types'

const STATUS_LABEL: Record<string, string> = {
  planned: 'Запланирован', released: 'Выпущен', in_progress: 'В работе',
  completed: 'Завершён', cancelled: 'Отменён',
}
const TASK_LABEL: Record<string, string> = { pending: 'Ожидает', in_progress: 'В работе', done: 'Готово' }

export default function OrderDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const qc = useQueryClient()
  const [err, setErr] = useState('')
  const [fgQty, setFgQty] = useState(1)
  const [fgNote, setFgNote] = useState('')
  const [assignTo, setAssignTo] = useState<Record<number, number>>({})

  const order = useQuery<OrderDetail>({
    queryKey: ['order', id],
    queryFn: async () => (await api.get(`/orders/${id}`)).data,
  })
  const users = useQuery<User[]>({ queryKey: ['users'], queryFn: async () => (await api.get('/users')).data, retry: false })

  const invalidate = () => { qc.invalidateQueries({ queryKey: ['order', id] }); qc.invalidateQueries({ queryKey: ['orders'] }) }
  const release = useMutation({ mutationFn: async () => api.post(`/orders/${id}/release`), onSuccess: invalidate, onError: (e) => setErr(apiError(e)) })
  const cancel = useMutation({ mutationFn: async () => api.post(`/orders/${id}/cancel`), onSuccess: invalidate, onError: (e) => setErr(apiError(e)) })
  const receiveFg = useMutation({
    mutationFn: async () => api.post(`/orders/${id}/receive_fg`, { qty: fgQty, note: fgNote }),
    onSuccess: invalidate, onError: (e) => setErr(apiError(e)),
  })
  const assign = useMutation({
    mutationFn: async (taskId: number) => api.post(`/tasks/${taskId}/assign`, { user_id: assignTo[taskId] }),
    onSuccess: invalidate, onError: (e) => setErr(apiError(e)),
  })

  const o = order.data
  if (order.isLoading) return <h1>Загрузка…</h1>
  if (!o) return <div className="alert">Заказ не найден</div>

  const canManage = !!user && ['admin', 'director', 'technologist'].includes(user.role)
  const canFg = !!user && ['admin', 'storekeeper', 'foreman'].includes(user.role)
  const canAssign = !!user && ['admin', 'foreman', 'director'].includes(user.role)
  const operators = users.data?.filter((u) => u.is_active) ?? []

  return (
    <>
      <div className="row-between">
        <h1>Заказ {o.number}</h1>
        <span className={`badge ${o.status}`}>{STATUS_LABEL[o.status]}</span>
      </div>
      {err && <div className="alert">{err}</div>}
      <div className="card">
        <div className="grid grid-4">
          <div><div className="muted">Изделие</div><b>{o.product_sku} — {o.product_name}</b></div>
          <div><div className="muted">Задание</div><b>{o.qty} шт</b></div>
          <div><div className="muted">Принято ГП</div><b>{o.received_qty} шт</b></div>
          <div><div className="muted">Срок</div><b>{o.due_date ?? '—'}</b></div>
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          {canManage && o.status === 'planned' && (
            <>
              <button className="btn btn-sm" onClick={() => release.mutate()}>Выпустить в производство</button>
              <button className="btn btn-sm btn-danger" onClick={() => cancel.mutate()}>Отменить заказ</button>
            </>
          )}
        </div>
      </div>

      <div className="card">
        <h2>Операции маршрута</h2>
        <table>
          <thead><tr><th>Операция</th><th>Исполнитель</th><th>Задание</th><th>Годные</th><th>Брак</th><th>Ставка</th><th>Статус</th><th></th></tr></thead>
          <tbody>
            {o.tasks.map((t) => (
              <tr key={t.id}>
                <td>{t.step_name}</td>
                <td>
                  {canAssign ? (
                    <select value={assignTo[t.id] ?? t.assignee_id ?? ''} onChange={(e) => setAssignTo({ ...assignTo, [t.id]: Number(e.target.value) })}>
                      <option value="">— не назначен —</option>
                      {operators.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
                    </select>
                  ) : (t.assignee_name || '—')}
                </td>
                <td>{t.qty}</td>
                <td>{t.qty_done}</td>
                <td>{t.qty_rejected}</td>
                <td>{t.rate} ₽/шт</td>
                <td><span className={`badge ${t.status}`}>{TASK_LABEL[t.status]}</span></td>
                <td>{canAssign && <button className="btn btn-sm btn-outline" onClick={() => assign.mutate(t.id)}>Назначить</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {canFg && (o.status === 'released' || o.status === 'in_progress') && (
        <div className="card">
          <h2>Приёмка готовой продукции</h2>
          <div className="row">
            <div style={{ width: 120 }}><label>Количество</label>
              <input type="number" min={1} max={o.qty - o.received_qty} value={fgQty} onChange={(e) => setFgQty(Number(e.target.value))} />
            </div>
            <div style={{ maxWidth: 320 }}><label>Примечание</label>
              <input value={fgNote} onChange={(e) => setFgNote(e.target.value)} placeholder="например, приёмка ОТК" />
            </div>
            <button className="btn" disabled={receiveFg.isPending} onClick={() => receiveFg.mutate()}>Принять на склад ГП</button>
          </div>
        </div>
      )}
    </>
  )
}
