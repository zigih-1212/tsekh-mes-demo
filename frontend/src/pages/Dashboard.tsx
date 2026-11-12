import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import api from '../api'
import type { Overview } from '../types'

const STATUS_LABEL: Record<string, string> = {
  planned: 'Запланированы', released: 'Выпущены', in_progress: 'В работе',
  completed: 'Завершены', cancelled: 'Отменены',
}
const STATUS_COLORS: Record<string, string> = {
  planned: '#818cf8', released: '#fbbf24', in_progress: '#60a5fa', completed: '#34d399', cancelled: '#f87171',
}

export default function Dashboard() {
  const { data: o, isLoading, error } = useQuery<Overview>({
    queryKey: ['overview'],
    queryFn: async () => (await api.get('/analytics/overview')).data,
  })
  if (isLoading) return <h1>Загрузка…</h1>
  if (error || !o) return <div className="alert">Не удалось загрузить аналитику</div>

  const pieData = Object.entries(o.orders_by_status).map(([k, v]) => ({
    name: STATUS_LABEL[k] ?? k, value: v,
  }))
  const dayData = o.orders_by_day.map((d) => ({ date: d.date.slice(5), qty: d.qty }))

  return (
    <>
      <h1>Дашборд производства</h1>
      <div className="grid grid-4">
        <div className="stat"><div className="num">{o.orders_total}</div><div className="lbl">Заказов всего</div></div>
        <div className="stat"><div className="num">{o.produced_qty}</div><div className="lbl">Произведено, шт</div></div>
        <div className="stat"><div className="num">{o.defect_rate}%</div><div className="lbl">Брак, % (шт: {o.defect_qty})</div></div>
        <div className="stat"><div className="num">{o.payroll_total.toLocaleString('ru-RU')} ₽</div><div className="lbl">ФОТ по сдельщине</div></div>
      </div>

      <div className="grid grid-2" style={{ marginTop: 16 }}>
        <div className="card">
          <h2>Заказы по статусам</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={90} label>
                {pieData.map((p) => (
                  <Cell key={p.name} fill={STATUS_COLORS[Object.keys(o.orders_by_status).find((k) => STATUS_LABEL[k] === p.name) ?? ''] ?? '#94a3b8'} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h2>Выпуск ГП по дням</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={dayData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="qty" fill="#0e7c86" name="шт" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <h2>ФОТ по операторам</h2>
          <table>
            <thead><tr><th>Оператор</th><th>Сделано, шт</th><th>Начислено</th></tr></thead>
            <tbody>
              {o.payroll_by_operator.map((p) => (
                <tr key={p.user_id}><td>{p.name}</td><td>{p.done}</td><td>{p.earned.toLocaleString('ru-RU')} ₽</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h2>Материалы ниже порога</h2>
          {o.low_stock_materials.length === 0 && <div className="muted">Все запасы в норме</div>}
          <table>
            <thead><tr><th>Материал</th><th>Остаток</th><th>Порог</th></tr></thead>
            <tbody>
              {o.low_stock_materials.map((m) => (
                <tr key={m.material.id}>
                  <td>{m.material.name}</td>
                  <td className="low">{m.balance} {m.material.unit}</td>
                  <td>{m.material.min_stock} {m.material.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
