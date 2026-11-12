import { createContext, useContext, useState, type ReactNode } from 'react'
import api from './api'
import type { User } from './types'

interface AuthCtx {
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem('tsekh_user')
    return raw ? (JSON.parse(raw) as User) : null
  })

  async function login(email: string, password: string) {
    const form = new URLSearchParams({ username: email, password })
    const { data } = await api.post<{ access_token: string; user: User }>('/auth/login', form)
    localStorage.setItem('tsekh_token', data.access_token)
    localStorage.setItem('tsekh_user', JSON.stringify(data.user))
    setUser(data.user)
  }

  function logout() {
    localStorage.removeItem('tsekh_token')
    localStorage.removeItem('tsekh_user')
    setUser(null)
  }

  return <Ctx.Provider value={{ user, login, logout }}>{children}</Ctx.Provider>
}

export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth outside provider')
  return ctx
}
