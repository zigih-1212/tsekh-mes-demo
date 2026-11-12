import { useQuery } from '@tanstack/react-query'
import api from '../api'
import { useAuth } from '../auth'
import type { User } from '../types'

const ROLE_LABEL: Record<string, string> = {
  admin: 'Администратор', director: 'Директор', technologist: 'Технолог',
  storekeeper: 'Кладовщик', foreman: 'Мастер', operator: 'Оператор',
}

export default function Users() {
  const { user } = useAuth()
  const users = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: async () => (await api.get('/users')).data,
    enabled: user?.role === 'admin',
    retry: false,
  })

  if (user?.role !== 'admin') return <div className="alert">Раздел доступен только администратору</div>

  return (
    <>
      <h1>Пользователи</h1>
      <div className="card">
        <table>
          <thead><tr><th>Имя</th><th>Email</th><th>Роль</th><th>Активен</th></tr></thead>
          <tbody>
            {users.data?.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{ROLE_LABEL[u.role] ?? u.role}</td>
                <td>{u.is_active ? 'да' : 'нет'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="muted" style={{ marginTop: 10, fontSize: 13 }}>
          Демо-пароли: admin — admin123, остальные — demo1234
        </div>
      </div>
    </>
  )
}
