import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'

interface AuthValue {
  session: Session | null
  loading: boolean
  configured: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  deleteAccount: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

function requireClient() {
  if (!supabase) throw new Error('Supabase is not configured. Add the frontend Supabase URL and anonymous key.')
  return supabase
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!supabase) { setLoading(false); return }
    let mounted = true
    void supabase.auth.getSession().then(({ data, error }) => {
      if (error) console.error('Unable to restore the Supabase session', error)
      if (mounted) { setSession(data.session); setLoading(false) }
    })
    const { data: listener } = supabase.auth.onAuthStateChange((_event, next) => setSession(next))
    return () => { mounted = false; listener.subscription.unsubscribe() }
  }, [])

  const value = useMemo<AuthValue>(() => ({
    session,
    loading,
    configured: Boolean(supabase),
    signIn: async (email, password) => {
      const { error } = await requireClient().auth.signInWithPassword({ email, password })
      if (error) throw error
    },
    signUp: async (email, password) => {
      const { error } = await requireClient().auth.signUp({ email, password })
      if (error) throw error
    },
    signOut: async () => {
      const { error } = await requireClient().auth.signOut()
      if (error) throw error
      setSession(null)
    },
    deleteAccount: async () => {
      const client = requireClient()
      const { error } = await client.rpc('delete_my_account')
      if (error) throw error
      await client.auth.signOut()
      setSession(null)
    },
  }), [loading, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
