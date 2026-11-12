import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiError } from '../api'

export default function Login() {
  const { login, user } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" />

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email, password)
      nav('/')
    } catch (err) {
      setError(apiError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1>ЦЕХ</h1>
        <div className="sub">MES швейного производства Artraid</div>
        {error && <div className="alert">{error}</div>}
        <form onSubmit={submit}>
          <label>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@artraid.demo" required />
          <label>Пароль</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <div style={{ marginTop: 16 }}>
            <button className="btn" style={{ width: '100%' }} disabled={busy}>{busy ? 'Вход…' : 'Войти'}</button>
          </div>
        </form>
        <div className="login-demo">
          Демо: admin@artraid.demo / admin123<br />
          Мастер: foreman@artraid.demo / demo1234 · Оператор: op1@artraid.demo / demo1234
        </div>
      </div>
    </div>
  )
}
