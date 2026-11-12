import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api, { apiError } from '../api'
import { useAuth } from '../auth'
import type { Task } from '../types'

const TASK_LABEL: Record<string, string> = { pending: 'Ожидает', in_progress: 'В работе', done: 'Готово' }

export default function Tasks() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [err, setErr] = useState('')
  const [filter, setFilter] = useState<'all' | 'mine'>('all')
  const [doneQty, setDoneQty] = useState<Record<number, string>>({})
  const [rejQty, setRejQty] = useState<Record<number, string>>({})
  const [reason, setReason] = useState<Record<number, string>>({})

  const tasks = useQuery<Task[]>({
    queryKey: ['tasks', filter],
    queryFn: async () => (await api.get('/tasks', { params: { mine: filter === 'mine' ? true : undefined } })).data,
  })

  const invalidate = () => qc.invalidateQueries({ queryKey: ['tasks'] })
  const wrap = (fn: (t: Task) => Promise<unknown>) => async (t: Task) => {
    setErr('')
    try { await fn(t); invalidate() } catch (e) { setErr(apiError(e)) }
  }
  const start = useMutation({ mutationFn: (t: Task) => api.post(`/tasks/${t.id}/start`), onSuccess: invalidate, onError: (e) => setErr(apiError(e)) })
  const complete = useMutation({
    mutationFn: (t: Task) => api.post(`/tasks/${t.id}/complete`, {
      qty_done: Number(doneQty[t.id] ?? 0), qty_rejected: Number(rejQty[t.id] ?? 0), reject_reason: reason[t.id] ?? '',
    }),
    onSuccess: invalidate, onError: (e) => setErr(apiError(e)),
  })

  const mine = (t: Task) => t.assignee_id === user?.id
  const canTouch = (t: Task) => mine(t) || user?.role === 'admin' || user?.role === 'foreman'

  return (
    <>
      <div className="row-between">
        <h1>Задания на операциях</h1>
        <div className="row">
          <button className={`btn btn-sm ${filter === 'all' ? '' : 'btn-outline'}`} onClick={() => setFilter('all')}>Все</button>
          <button className={`btn btn-sm ${filter === 'mine' ? '' : 'btn-outline'}`} onClick={() => setFilter('mine')}>Мои</button>
        </div>
      </div>
      {err && <div className="alert">{err}</div>}
      <div className="card">
        <table>
          <thead><tr><th>Заказ</th><th>Операция</th><th>Исполнитель</th><th>Задание</th><th>Годные/брак</th><th>Заработано</th><th>Статус</th><th></th></tr></thead>
          <tbody>
            {tasks.data?.map((t) => (
              <tr key={t.id}>
                <td>ЗК-{String(t.order_id).padStart(4, '0')}</td>
                <td>{t.step_name}</td>
                <td>{t.assignee_name || '—'}</td>
                <td>{t.qty}</td>
                <td>{t.qty_done} / {t.qty_rejected}</td>
                <td>{(t.qty_done * t.rate).toLocaleString('ru-RU')} ₽</td>
                <td><span className={`badge ${t.status}`}>{TASK_LABEL[t.status]}</span></td>
                <td className="row">
                  {canTouch(t) && t.status === 'pending' && (
                    <button className="btn btn-sm" onClick={() => wrap((tt) => start.mutateAsync(tt))(t)}>Начать</button>
                  )}
                  {canTouch(t) && t.status === 'in_progress' && (
                    <>
                      <input style={{ width: 70 }} type="number" min={0} placeholder="годные" value={doneQty[t.id] ?? ''} onChange={(e) => setDoneQty({ ...doneQty, [t.id]: e.target.value })} />
                      <input style={{ width: 70 }} type="number" min={0} placeholder="брак" value={rejQty[t.id] ?? ''} onChange={(e) => setRejQty({ ...rejQty, [t.id]: e.target.value })} />
                      <input style={{ width: 140 }} placeholder="причина брака" value={reason[t.id] ?? ''} onChange={(e) => setReason({ ...reason, [t.id]: e.target.value })} />
                      <button className="btn btn-sm" onClick={() => wrap((tt) => complete.mutateAsync(tt))(t)}>Завершить</button>
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
