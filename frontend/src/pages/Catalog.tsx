import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../api'
import type { Material, Product } from '../types'

export default function Catalog() {
  const products = useQuery<Product[]>({ queryKey: ['products'], queryFn: async () => (await api.get('/products')).data })
  const materials = useQuery<Material[]>({ queryKey: ['materials'], queryFn: async () => (await api.get('/materials')).data })

  return (
    <>
      <h1>Каталог изделий и материалов</h1>
      <div className="grid grid-2">
        <div className="card">
          <h2>Изделия (номенклатура)</h2>
          <table>
            <thead><tr><th>Артикул</th><th>Наименование</th><th>Категория</th><th>Цена</th><th></th></tr></thead>
            <tbody>
              {products.data?.map((p) => (
                <tr key={p.id}>
                  <td>{p.sku}</td>
                  <td>{p.name}</td>
                  <td className="muted">{p.category}</td>
                  <td>{p.unit_price.toLocaleString('ru-RU')} ₽</td>
                  <td><Link to={`/catalog/${p.id}`}>BOM / маршрут →</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h2>Материалы</h2>
          <table>
            <thead><tr><th>Артикул</th><th>Наименование</th><th>Ед.</th><th>Цена</th><th>Порог</th></tr></thead>
            <tbody>
              {materials.data?.map((m) => (
                <tr key={m.id}>
                  <td>{m.sku}</td>
                  <td>{m.name}</td>
                  <td>{m.unit}</td>
                  <td>{m.cost_per_unit.toLocaleString('ru-RU')} ₽</td>
                  <td>{m.min_stock}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
