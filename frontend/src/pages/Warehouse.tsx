import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api, { apiError } from '../api'
import { useAuth } from '../auth'
import type { FgReceipt, MaterialStock, ProductStock, StockMove } from '../types'

const MOVE_LABEL: Record<string, string> = {
  purchase: 'Приход', consumption: 'Расход в цех', writeoff: 'Списание', adjustment: 'Корректировка',
}
const CAN_MOVE = ['admin', 'storekeeper', 'director']

export default function Warehouse() {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [err, setErr] = useState('')
  const [matId, setMatId] = useState('')
  const [qty, setQty] = useState(10)
  const [type, setType] = useState('purchase')
  const [note, setNote] = useState('')

  const stock = useQuery<MaterialStock[]>({ queryKey: ['stock'], queryFn: async () => (await api.get('/stock/materials')).data })
  const moves = useQuery<StockMove[]>({ queryKey: ['moves'], queryFn: async () => (await api.get('/stock/moves')).data })
  const fg = useQuery<ProductStock[]>({ queryKey: ['fg'], queryFn: async () => (await api.get('/stock/finished_goods')).data })
  const receipts = useQuery<FgReceipt[]>({ queryKey: ['fgReceipts'], queryFn: async () => (await api.get('/stock/fg_receipts')).data })

  const move = useMutation({
    mutationFn: async () => api.post('/stock/moves', { material_id: Number(matId), qty: Number(qty), type, note }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['stock'] }); qc.invalidateQueries({ queryKey: ['moves'] }) },
    onError: (e) => setErr(apiError(e)),
  })

  const canMove = !!user && CAN_MOVE.includes(user.role)

  return (
    <>
      <h1>Склад</h1>
      {err && <div className="alert">{err}</div>}
      <div className="grid grid-2">
        <div className="card">
          <h2>Остатки материалов</h2>
          <table>
            <thead><tr><th>Материал</th><th>Остаток</th><th>Порог</th><th></th></tr></thead>
            <tbody>
              {stock.data?.map((s) => (
                <tr key={s.material.id}>
                  <td>{s.material.name}</td>
                  <td className={s.low_stock ? 'low' : ''}>{s.balance} {s.material.unit}</td>
                  <td className="muted">{s.material.min_stock}</td>
                  <td>{s.low_stock && <span className="badge cancelled">ниже порога</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h2>Склад готовой продукции</h2>
          <table>
            <thead><tr><th>Изделие</th><th>Остаток</th></tr></thead>
            <tbody>
              {fg.data?.map((f) => (
                <tr key={f.product.id}><td>{f.product.name}</td><td>{f.balance} шт</td></tr>
              ))}
            </tbody>
          </table>
          <h2>Приёмки ГП</h2>
          <table>
            <thead><tr><th>Заказ</th><th>Изделие</th><th>Кол-во</th><th>Примечание</th></tr></thead>
            <tbody>
              {receipts.data?.slice(0, 10).map((r) => (
                <tr key={r.id}><td>ЗК-{String(r.order_id).padStart(4, '0')}</td><td>{r.product_name}</td><td>{r.qty}</td><td className="muted">{r.note}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {canMove && (
        <div className="card">
          <h2>Новое движение по материалу</h2>
          <div className="row">
            <div style={{ maxWidth: 320 }}>
              <label>Материал</label>
              <select value={matId} onChange={(e) => setMatId(e.target.value)}>
                <option value="">— выберите —</option>
                {stock.data?.map((s) => <option key={s.material.id} value={s.material.id}>{s.material.sku} — {s.material.name}</option>)}
              </select>
            </div>
            <div style={{ width: 100 }}><label>Кол-во</label><input type="number" step="any" value={qty} onChange={(e) => setQty(Number(e.target.value))} /></div>
            <div style={{ width: 160 }}>
              <label>Тип</label>
              <select value={type} onChange={(e) => setType(e.target.value)}>
                <option value="purchase">Приход</option>
                <option value="writeoff">Списание</option>
                <option value="adjustment">Корректировка (+/-)</option>
              </select>
            </div>
            <div style={{ maxWidth: 240 }}><label>Примечание</label><input value={note} onChange={(e) => setNote(e.target.value)} /></div>
            <button className="btn" disabled={!matId || move.isPending} onClick={() => move.mutate()}>Провести</button>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Журнал движений</h2>
        <table>
          <thead><tr><th>Дата</th><th>Материал</th><th>Тип</th><th>Кол-во</th><th>Заказ</th><th>Примечание</th></tr></thead>
          <tbody>
            {moves.data?.slice(0, 30).map((m) => (
              <tr key={m.id}>
                <td className="muted">{m.created_at.slice(0, 16).replace('T', ' ')}</td>
                <td>{m.material_name}</td>
                <td>{MOVE_LABEL[m.type]}</td>
                <td className={m.qty < 0 ? 'low' : ''}>{m.qty > 0 ? '+' : ''}{m.qty}</td>
                <td>{m.order_id ? `ЗК-${String(m.order_id).padStart(4, '0')}` : '—'}</td>
                <td className="muted">{m.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
