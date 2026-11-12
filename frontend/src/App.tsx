import { BrowserRouter, Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './auth'
import type { Role } from './types'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Orders from './pages/Orders'
import OrderDetail from './pages/OrderDetail'
import Tasks from './pages/Tasks'
import Catalog from './pages/Catalog'
import ProductEdit from './pages/ProductEdit'
import Warehouse from './pages/Warehouse'
import Users from './pages/Users'

const queryClient = new QueryClient()

const NAV: { to: string; label: string; roles?: Role[] }[] = [
  { to: '/', label: 'Дашборд' },
  { to: '/orders', label: 'Заказы' },
  { to: '/tasks', label: 'Задания' },
  { to: '/catalog', label: 'Каталог' },
  { to: '/warehouse', label: 'Склад' },
  { to: '/users', label: 'Пользователи', roles: ['admin'] },
]

function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  if (!user) return <Navigate to="/login" />
  const links = NAV.filter((n) => !n.roles || n.roles.includes(user.role))
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="logo">ЦЕХ</div>
        <div className="logo-sub">MES швейного производства</div>
        <nav>
          {links.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.to === '/'} className={({ isActive }) => (isActive ? 'active' : '')}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-name">{user.name}</div>
          <div className="user-role">{user.role}</div>
          <button className="btn btn-ghost" onClick={logout}>Выйти</button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout><Dashboard /></Layout>} />
            <Route path="/orders" element={<Layout><Orders /></Layout>} />
            <Route path="/orders/:id" element={<Layout><OrderDetail /></Layout>} />
            <Route path="/tasks" element={<Layout><Tasks /></Layout>} />
            <Route path="/catalog" element={<Layout><Catalog /></Layout>} />
            <Route path="/catalog/:id" element={<Layout><ProductEdit /></Layout>} />
            <Route path="/warehouse" element={<Layout><Warehouse /></Layout>} />
            <Route path="/users" element={<Layout><Users /></Layout>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
