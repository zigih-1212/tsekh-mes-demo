import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import api, { apiError } from '../api'
import { useAuth } from '../auth'
import type { BomItem, Material, ProductDetail, RoutingStep } from '../types'

const CAN_EDIT = ['admin', 'technologist', 'director']

export default function ProductEdit() {
  const { id } = useParams()
  const { user } = useAuth()
  const qc = useQueryClient()
  const [err, setErr] = useState('')

  const product = useQuery<ProductDetail>({
    queryKey: ['product', id],
    queryFn: async () => (await api.get(`/products/${id}`)).data,
  })
  const materials = useQuery<Material[]>({ queryKey: ['materials'], queryFn: async () => (await api.get('/materials')).data })

  const [bom, setBom] = useState<BomItem[]>([])
  const [routing, setRouting] = useState<RoutingStep[]>([])
  useEffect(() => {
    if (product.data) {
      setBom(product.data.bom_items)
      setRouting(product.data.routing)
    }
  }, [product.data])

  const saveBom = useMutation({
    mutationFn: async () => api.put(`/products/${id}/bom`, bom.map((b) => ({ material_id: b.material_id, qty_per_unit: b.qty_per_unit }))),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['product', id] }),
    onError: (e) => setErr(apiError(e)),
  })
  const saveRouting = useMutation({
    mutationFn: async () => api.put(`/products/${id}/routing`, routing.map((r) => ({ seq: r.seq, name: r.name, workcenter: r.workcenter, norm_min: r.norm_min, rate_per_unit: r.rate_per_unit }))),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['product', id] }),
    onError: (e) => setErr(apiError(e)),
  })

  const canEdit = !!user && CAN_EDIT.includes(user.role)
  if (product.isLoading) return <h1>Загрузка…</h1>
  const p = product.data
  if (!p) return <div className="alert">Изделие не найдено</div>

  return (
    <>
      <h1>{p.sku} — {p.name}</h1>
      {err && <div className="alert">{err}</div>}
      <div className="grid grid-2">
        <div className="card">
          <div className="row-between"><h2>Спецификация (BOM)</h2>
            {canEdit && <button className="btn btn-sm" onClick={() => saveBom.mutate()}>Сохранить BOM</button>}
          </div>
          <table>
            <thead><tr><th>Материал</th><th>На ед., ед.</th><th></th></tr></thead>
            <tbody>
              {bom.map((b, i) => (
                <tr key={i}>
                  <td>
                    <select value={b.material_id} disabled={!canEdit} onChange={(e) => {
                      const v = bom.slice(); v[i] = { ...b, material_id: Number(e.target.value) }; setBom(v)
                    }}>
                      {materials.data?.map((m) => <option key={m.id} value={m.id}>{m.sku} — {m.name}</option>)}
                    </select>
                  </td>
                  <td><input style={{ width: 90 }} type="number" step="any" min={0} value={b.qty_per_unit} disabled={!canEdit} onChange={(e) => {
                    const v = bom.slice(); v[i] = { ...b, qty_per_unit: Number(e.target.value) }; setBom(v)
                  }} /></td>
                  <td>{canEdit && <button className="btn btn-sm btn-danger" onClick={() => setBom(bom.filter((_, j) => j !== i))}>×</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {canEdit && <button className="btn btn-sm btn-outline" style={{ marginTop: 8 }} onClick={() => setBom([...bom, { id: 0, material_id: materials.data?.[0]?.id ?? 0, qty_per_unit: 1 }])}>+ материал</button>}
        </div>
        <div className="card">
          <div className="row-between"><h2>Маршрут (routing)</h2>
            {canEdit && <button className="btn btn-sm" onClick={() => saveRouting.mutate()}>Сохранить маршрут</button>}
          </div>
          <table>
            <thead><tr><th>№</th><th>Операция</th><th>Участок</th><th>Норма, мин</th><th>Ставка, ₽/шт</th><th></th></tr></thead>
            <tbody>
              {routing.map((r, i) => (
                <tr key={i}>
                  <td><input style={{ width: 50 }} type="number" value={r.seq} disabled={!canEdit} onChange={(e) => { const v = routing.slice(); v[i] = { ...r, seq: Number(e.target.value) }; setRouting(v) }} /></td>
                  <td><input value={r.name} disabled={!canEdit} onChange={(e) => { const v = routing.slice(); v[i] = { ...r, name: e.target.value }; setRouting(v) }} /></td>
                  <td><input value={r.workcenter} disabled={!canEdit} onChange={(e) => { const v = routing.slice(); v[i] = { ...r, workcenter: e.target.value }; setRouting(v) }} /></td>
                  <td><input style={{ width: 80 }} type="number" min={0} value={r.norm_min} disabled={!canEdit} onChange={(e) => { const v = routing.slice(); v[i] = { ...r, norm_min: Number(e.target.value) }; setRouting(v) }} /></td>
                  <td><input style={{ width: 90 }} type="number" min={0} value={r.rate_per_unit} disabled={!canEdit} onChange={(e) => { const v = routing.slice(); v[i] = { ...r, rate_per_unit: Number(e.target.value) }; setRouting(v) }} /></td>
                  <td>{canEdit && <button className="btn btn-sm btn-danger" onClick={() => setRouting(routing.filter((_, j) => j !== i))}>×</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {canEdit && <button className="btn btn-sm btn-outline" style={{ marginTop: 8 }} onClick={() => setRouting([...routing, { id: 0, seq: routing.length + 1, name: '', workcenter: '', norm_min: 0, rate_per_unit: 0 }])}>+ операция</button>}
        </div>
      </div>
    </>
  )
}
